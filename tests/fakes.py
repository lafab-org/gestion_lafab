"""Simulated Paheko API."""

import asyncio
import base64
import sqlite3
from datetime import datetime

import httpx

URL = "https://lafab.paheko.cloud"
API_ID = "test-id"
API_TOKEN = "test-token"
ENV = {"PAHEKO_URL": URL, "PAHEKO_API_ID": API_ID, "PAHEKO_API_TOKEN": API_TOKEN}

MEMBERSHIP = 1
OTHER_SERVICE = 23

SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, nom TEXT, prenom TEXT, numero INTEGER);
CREATE TABLE services (id INTEGER PRIMARY KEY, label TEXT NOT NULL,
    duration INTEGER NULL);
CREATE TABLE services_users (
    id INTEGER NOT NULL PRIMARY KEY,
    id_user INTEGER NOT NULL,
    id_service INTEGER NOT NULL,
    id_fee INTEGER NULL,
    paid INTEGER NOT NULL DEFAULT 0,
    expected_amount INTEGER NULL,
    date TEXT NOT NULL,
    expiry_date TEXT NULL
);
INSERT INTO services (id, label, duration) VALUES
    (1, '- Adhésion', 365), (23, 'Initiation laser', NULL);
"""


def basic_auth(api_id: str, token: str) -> str:
    return "Basic " + base64.b64encode(f"{api_id}:{token}".encode()).decode()


def run_sql(query: str, registrations: list[tuple[int, int, str]]) -> dict:
    """Run a query of the SQL API on a database holding the registrations.

    registrations: (id_user, id_service, ISO date) rows of services_users.
    """
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    users = sorted({user for user, _, _ in registrations})
    db.executemany(
        "INSERT INTO users (id, nom, prenom, numero) VALUES (?, 'Nom', 'Prénom', ?)",
        [(user, user) for user in users],
    )
    db.executemany(
        "INSERT INTO services_users (id_user, id_service, paid, date)"
        " VALUES (?, ?, 1, ?)",
        registrations,
    )
    rows = [dict(row) for row in db.execute(query).fetchall()]
    db.close()
    return {"count": len(rows), "results": rows}


class FakePaheko:
    """Accepts the configured credentials, unless told otherwise.

    status: HTTP status answered to accepted credentials.
    error: exception raised instead of answering.
    held: while True, requests wait before being answered.
    registrations: (id_user, id_service, ISO date) rows of services_users,
    queried by the SQL API.
    """

    def __init__(self) -> None:
        self.status = 200
        self.error: Exception | None = None
        self.held = False
        self.calls = 0
        self.registrations: list[tuple[int, int, str]] = []

    async def handle(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        while self.held:
            await asyncio.sleep(0.01)
        if self.error is not None:
            raise self.error
        if request.headers.get("authorization") != basic_auth(API_ID, API_TOKEN):
            return httpx.Response(401, json={"error": "unauthorized"})
        if self.status != 200:
            return httpx.Response(self.status, json={"error": "error"})
        try:
            body = run_sql(request.content.decode(), self.registrations)
        except sqlite3.Error as e:
            return httpx.Response(400, json={"error": str(e)})
        return httpx.Response(200, json=body)

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)


class Clock:
    """A settable clock, passed to the application as its `now`."""

    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value
