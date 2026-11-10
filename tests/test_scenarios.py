import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from tests.fakes import API_ID, API_TOKEN, basic_auth

REPO = Path(__file__).resolve().parent.parent


class PahekoServer:
    """Simulated Paheko over real HTTP; requests wait while `gate` is clear."""

    def __init__(self) -> None:
        self.gate = threading.Event()
        self.gate.set()
        gate = self.gate

        class Handler(BaseHTTPRequestHandler):
            def answer(self) -> None:
                gate.wait(timeout=30)
                ok = self.headers.get("authorization") == basic_auth(API_ID, API_TOKEN)
                body = b'{"count": 1, "results": []}' if ok else b"{}"
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


# /scenarios/premier-lancement
def test_first_launch(tmp_path, paheko_server, page: Page):
    (tmp_path / ".env").write_text(
        f"PAHEKO_URL={paheko_server.url}\n"
        f"PAHEKO_API_ID={API_ID}\n"
        f"PAHEKO_API_TOKEN={API_TOKEN}\n"
    )
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
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
