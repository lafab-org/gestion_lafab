import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from tests.fakes import (
    API_ID,
    API_TOKEN,
    DIGITAL,
    MEMBERSHIP,
    WOOD,
    basic_auth,
    run_sql,
)
from tests.stats_html import month_label

REPO = Path(__file__).resolve().parent.parent


class PahekoServer:
    """Simulated Paheko over real HTTP; requests wait while `gate` is clear.

    registrations: (id_user, id_service, ISO date) rows queried by the SQL API.
    queries: the SQL queries received.
    """

    def __init__(self) -> None:
        self.gate = threading.Event()
        self.gate.set()
        self.registrations: list[tuple[int, int, str]] = []
        self.queries: list[str] = []
        gate = self.gate
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def answer(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                query = self.rfile.read(length).decode()
                fake.queries.append(query)
                gate.wait(timeout=30)
                ok = self.headers.get("authorization") == basic_auth(API_ID, API_TOKEN)
                body = (
                    json.dumps(run_sql(query, fake.registrations)).encode()
                    if ok
                    else b"{}"
                )
                self.send_response(200 if ok else 401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = do_POST = answer

            def log_message(self, *args) -> None:
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.gate.set()
        self.httpd.shutdown()


@pytest.fixture
def paheko_server():
    srv = PahekoServer()
    yield srv
    srv.close()


def wait_for(path: Path, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and path.read_text().strip():
            return path.read_text().strip()
        time.sleep(0.1)
    raise AssertionError("the browser was not opened")


def goto_when_up(page: Page, url: str, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            page.goto(url)
            return
        except Exception:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.2)


def write_env(tmp_path: Path, paheko_url: str) -> None:
    (tmp_path / ".env").write_text(
        f"PAHEKO_URL={paheko_url}\n"
        f"PAHEKO_API_ID={API_ID}\n"
        f"PAHEKO_API_TOKEN={API_TOKEN}\n"
    )


def launch(tmp_path: Path) -> tuple[subprocess.Popen, Path]:
    """Run `uv run gestion-lafab`; returns the process and where the browser
    records the opened URL."""
    opened = tmp_path / "opened-url"
    browser = tmp_path / "record-browser"
    browser.write_text(
        f'#!{sys.executable}\nimport sys\nopen("{opened}", "w").write(sys.argv[1])\n'
    )
    browser.chmod(0o755)
    env = dict(os.environ, BROWSER=str(browser))
    env = {k: v for k, v in env.items() if not k.startswith("PAHEKO_")}
    process = subprocess.Popen(
        ["uv", "run", "--project", str(REPO), "gestion-lafab"],
        cwd=tmp_path,
        env=env,
        start_new_session=True,
    )
    return process, opened


def stop(process: subprocess.Popen) -> None:
    os.killpg(process.pid, signal.SIGTERM)
    process.wait(timeout=10)


# /scenarios/premier-lancement
def test_first_launch(tmp_path, paheko_server, page: Page):
    write_env(tmp_path, paheko_server.url)
    process, opened = launch(tmp_path)
    try:
        url = wait_for(opened, timeout=30)
        assert url.startswith("http://127.0.0.1:8000")
        goto_when_up(page, url)
        connected = f"Connecté à {paheko_server.url}."
        expect(page.get_by_text(connected)).to_be_visible()

        paheko_server.gate.clear()
        page.get_by_role("button", name="Tester à nouveau").click()
        expect(page.get_by_text("Test en cours…")).to_be_visible()
        paheko_server.gate.set()
        expect(page.get_by_text(connected)).to_be_visible()
    finally:
        stop(process)


def read_text(at: datetime) -> str:
    return f"Données Paheko lues le {at:%d/%m/%Y} à {at:%H} h {at:%M}."


# /scenarios/consulter-les-adhesions
def test_consult_memberships(tmp_path, paheko_server, page: Page):
    today = date.today()
    paheko_server.registrations = [
        (1, MEMBERSHIP, today.isoformat()),
        (2, MEMBERSHIP, today.replace(month=1, day=1).isoformat()),
        (3, MEMBERSHIP, f"{today.year - 1}-01-01"),
    ]
    write_env(tmp_path, paheko_server.url)
    process, opened = launch(tmp_path)
    try:
        goto_when_up(page, wait_for(opened, timeout=30))

        def readings() -> int:
            return sum("SELECT 1" not in q for q in paheko_server.queries)

        paheko_server.gate.clear()
        page.get_by_role("link", name="Adhésions").click()
        expect(page.get_by_text("Lecture de Paheko…")).to_be_visible()
        before = datetime.now().replace(second=0, microsecond=0)
        paheko_server.gate.set()
        status = page.get_by_text(re.compile(r"^Données Paheko lues le "))
        expect(status).to_be_visible()
        after = datetime.now()
        first = status.text_content()
        assert first in {read_text(before), read_text(after)}
        expect(
            page.get_by_text(re.compile(rf"^{today.year} : \d+ adhésions au "))
        ).to_be_visible()
        expect(page.locator("svg").filter(has=page.locator("title"))).to_have_count(2)
        rows = page.get_by_role("table").get_by_role("row")
        years = [
            int(m.group(0))
            for m in (re.match(r"\d{4}", t.strip()) for t in rows.all_inner_texts())
            if m
        ]
        assert years == list(range(today.year, 2015, -1))
        assert readings() == 1

        page.get_by_role("link", name="Accueil").click()
        page.get_by_role("link", name="Adhésions").click()
        expect(status).to_have_text(first)
        assert readings() == 1

        before = datetime.now()
        button = page.get_by_role("button", name="Actualiser")
        button.click()
        deadline = time.monotonic() + 10
        while readings() < 2 and time.monotonic() < deadline:
            time.sleep(0.05)
        expect(button).to_be_enabled()
        expect(status).to_be_visible()
        after = datetime.now()
        assert status.text_content() in {read_text(before), read_text(after)}
        assert readings() == 2
    finally:
        stop(process)


# /scenarios/consulter-les-initiations
def test_consult_initiations(tmp_path, paheko_server, page: Page):
    today = date.today()
    paheko_server.registrations = [
        (1, DIGITAL[0], today.isoformat()),
        (2, WOOD[0], today.replace(month=1, day=1).isoformat()),
    ]
    write_env(tmp_path, paheko_server.url)
    process, opened = launch(tmp_path)
    try:
        goto_when_up(page, wait_for(opened, timeout=30))

        def readings() -> int:
            return sum("SELECT 1" not in q for q in paheko_server.queries)

        paheko_server.gate.clear()
        page.get_by_role("link", name="Initiations").click()
        expect(page.get_by_text("Lecture de Paheko…")).to_be_visible()
        before = datetime.now().replace(second=0, microsecond=0)
        paheko_server.gate.set()
        status = page.get_by_text(re.compile(r"^Données Paheko lues le "))
        expect(status).to_be_visible()
        after = datetime.now()
        assert status.text_content() in {read_text(before), read_text(after)}
        expect(page.locator("svg").filter(has=page.locator("title"))).to_have_count(2)
        rows = page.get_by_role("table").get_by_role("row")
        labels = [
            m.group(0)
            for m in (re.match(r"\S+ \d{4}", t.strip()) for t in rows.all_inner_texts())
            if m
        ]
        assert labels == [
            month_label(today.year, month) for month in range(today.month, 0, -1)
        ]
        assert readings() == 1

        before = datetime.now()
        button = page.get_by_role("button", name="Actualiser")
        button.click()
        deadline = time.monotonic() + 10
        while readings() < 2 and time.monotonic() < deadline:
            time.sleep(0.05)
        expect(button).to_be_enabled()
        expect(status).to_be_visible()
        after = datetime.now()
        assert status.text_content() in {read_text(before), read_text(after)}
        assert readings() == 2
    finally:
        stop(process)
