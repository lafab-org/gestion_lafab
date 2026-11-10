"""Simulated Paheko API."""

import asyncio
import base64
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

URL = "https://lafab.paheko.cloud"
API_ID = "test-id"
API_TOKEN = "test-token"
ENV = {"PAHEKO_URL": URL, "PAHEKO_API_ID": API_ID, "PAHEKO_API_TOKEN": API_TOKEN}

MEMBERSHIP = 1
OTHER_SERVICE = 23

SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, numero INTEGER,
    prenom TEXT COLLATE NOCASE, nom TEXT COLLATE NOCASE, email TEXT COLLATE NOCASE);
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
    (1, '- Adhésion', 365),
    (19, 'Atelier libre', NULL),
    (20, 'Initiation assemblage bois', NULL),
    (21, 'Initiation assemblage main', NULL),
    (22, 'Initiation dégau-rabo', NULL),
    (23, 'Initiation laser', NULL),
    (24, 'Initiation projet cordonnerie', NULL),
    (25, 'Initiation scie à format', NULL),
    (26, 'Initiation hors catégorie', NULL),
    (27, 'Initiation soudage électrode enrobée', NULL),
    (28, 'Initiation tour à bois', NULL),
    (29, 'Initiation électro-portatif bois', NULL),
    (30, 'Initiation soudage TIG', NULL),
    (31, 'Initiation impression 3D', NULL),
    (32, 'Initiation couture', NULL),
    (33, 'Initiation électro-portatif bois NV2', NULL),
    (34, 'Initiation soudage semi-auto', NULL),
    (35, 'Initiation nouvelle', NULL);
CREATE TABLE plugin_pos_categories (id INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL, account TEXT NULL);
CREATE TABLE plugin_pos_products (id INTEGER NOT NULL PRIMARY KEY,
    category INTEGER NOT NULL, name TEXT NOT NULL, description TEXT NULL,
    price INTEGER NOT NULL, qty INTEGER NOT NULL DEFAULT 1,
    archived INTEGER NOT NULL DEFAULT 0);
CREATE TABLE plugin_pos_sessions (id INTEGER NOT NULL PRIMARY KEY,
    opened TEXT NOT NULL, closed TEXT NULL);
CREATE TABLE plugin_pos_tabs (id INTEGER NOT NULL PRIMARY KEY,
    session INTEGER NOT NULL, name TEXT NULL, user_id INTEGER NULL,
    opened TEXT NOT NULL, closed TEXT NULL);
CREATE TABLE plugin_pos_tabs_items (id INTEGER NOT NULL PRIMARY KEY,
    tab INTEGER NOT NULL, added TEXT NOT NULL, product INTEGER NULL,
    qty INTEGER NOT NULL, price INTEGER NOT NULL, total INTEGER NOT NULL,
    name TEXT NOT NULL, category_name TEXT NOT NULL, description TEXT NULL,
    account TEXT NULL, type INTEGER NOT NULL DEFAULT 0);
INSERT INTO plugin_pos_categories (id, name) VALUES
    (1, 'A - Adhésion'),
    (2, 'B - Tickets'),
    (4, 'C - Abonnements'),
    (5, 'D - Initiations'),
    (6, 'D - Accompagnement'),
    (9, 'U - Consommable métal');
INSERT INTO plugin_pos_products (id, category, name, price)
    SELECT 100 + id, id, 'Produit ' || name, 1500 FROM plugin_pos_categories;
"""

# Paheko activities of initiation, by category.
WOOD = [20, 21, 22, 25, 28, 29, 33]
METAL = [27, 30, 34]
SOFT = [24, 32]
DIGITAL = [23, 31]
# Activities that are not initiations of a category.
NOT_INITIATIONS = [1, 19, 26, 35]

# Categories of the cash register (extension Caisse).
CASH_INITIATIONS = 5
CASH_COACHING = 6
CASH_TICKETS = 2
CASH_METAL_SUPPLIES = 9


@dataclass(frozen=True)
class Member:
    """A row of users."""

    id: int
    numero: int
    prenom: str
    nom: str
    email: str | None = None


@dataclass(frozen=True)
class Tab:
    """A note of the cash register, opened at `opened` (`YYYY-MM-DD HH:MM:SS`).

    lines: (name, quantity, category id) of its items, added after the opening.
    """

    opened: str
    lines: list[tuple[str, int, int]]
    name: str | None = None
    user_id: int | None = None
    added: str | None = None  # when its items were added; an hour later if None


def basic_auth(api_id: str, token: str) -> str:
    return "Basic " + base64.b64encode(f"{api_id}:{token}".encode()).decode()


def run_sql(
    query: str,
    registrations: list[tuple[int, int, str]],
    members: Iterable[Member] = (),
    tabs: Iterable[Tab] = (),
) -> dict:
    """Run a query of the SQL API on a database holding the data.

    registrations: (id_user, id_service, ISO date) rows of services_users.
    members: rows of users; a registered user not among them is added.
    tabs: notes of the cash register.
    """
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    members = list(members)
    known = {m.id for m in members}
    users = sorted({user for user, _, _ in registrations} - known)
    db.executemany(
        "INSERT INTO users (id, numero, prenom, nom, email) VALUES (?, ?, ?, ?, ?)",
        [(m.id, m.numero, m.prenom, m.nom, m.email) for m in members]
        + [(user, user, "Prénom", "NOM", None) for user in users],
    )
    db.executemany(
        "INSERT INTO services_users (id_user, id_service, paid, date)"
        " VALUES (?, ?, 1, ?)",
        registrations,
    )
    categories = dict(db.execute("SELECT id, name FROM plugin_pos_categories"))
    for number, tab in enumerate(tabs, start=1):
        opened = datetime.fromisoformat(tab.opened)
        added = tab.added or (opened + timedelta(hours=1)).isoformat(" ")
        closed = (opened + timedelta(hours=3)).isoformat(" ")
        db.execute(
            "INSERT INTO plugin_pos_sessions (id, opened, closed) VALUES (?, ?, ?)",
            (number, tab.opened, closed),
        )
        db.execute(
            "INSERT INTO plugin_pos_tabs (id, session, name, user_id, opened, closed)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (number, number, tab.name, tab.user_id, tab.opened, closed),
        )
        db.executemany(
            "INSERT INTO plugin_pos_tabs_items (tab, added, product, qty, price,"
            " total, name, category_name) VALUES (?, ?, ?, ?, 1500, ?, ?, ?)",
            [
                (number, added, 100 + cat, qty, 1500 * qty, name, categories[cat])
                for name, qty, cat in tab.lines
            ],
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
    queried by the SQL API, with `members` (users) and `tabs` (cash register).
    """

    def __init__(self) -> None:
        self.status = 200
        self.error: Exception | None = None
        self.held = False
        self.calls = 0
        self.registrations: list[tuple[int, int, str]] = []
        self.members: list[Member] = []
        self.tabs: list[Tab] = []

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
            body = run_sql(
                request.content.decode(), self.registrations, self.members, self.tabs
            )
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
