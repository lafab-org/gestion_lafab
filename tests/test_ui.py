import re
import time

from playwright.sync_api import Page, expect

from tests.fakes import URL

CONNECTED = f"Connecté à {URL}."
CHECKING = "Test en cours…"


def wait_calls(paheko, expected: int, timeout: float = 5) -> None:
    deadline = time.monotonic() + timeout
    while paheko.calls < expected and time.monotonic() < deadline:
        time.sleep(0.01)
    assert paheko.calls == expected


def rgb(page: Page, text: str) -> tuple[int, int, int]:
    color = page.get_by_text(text).evaluate("e => getComputedStyle(e).color")
    r, g, b = (int(x) for x in re.findall(r"\d+", color)[:3])
    return r, g, b


# /ui/page-daccueil/title
def test_title(server, page: Page):
    page.goto(server)
    expect(page.get_by_role("heading", name="Gestion La Fabrique")).to_be_visible()


# /ui/page-daccueil/status /ui/page-daccueil/recheck
def test_layout_order(server, page: Page):
    page.goto(server)
    expect(page.get_by_text(CONNECTED)).to_be_visible()
    title = page.get_by_role("heading", name="Gestion La Fabrique").bounding_box()
    status = page.get_by_text(CONNECTED).bounding_box()
    button = page.get_by_role("button", name="Tester à nouveau").bounding_box()
    assert title["y"] < status["y"] < button["y"]


# /ui/statut-de-connexion/checking /ui/statut-de-connexion/opened
# /ui/page-daccueil/recheck-click
def test_checking_on_open(server, paheko, page: Page):
    paheko.held = True
    page.goto(server)
    expect(page.get_by_text(CHECKING)).to_be_visible()
    wait_calls(paheko, 1)
    expect(page.get_by_role("button", name="Tester à nouveau")).to_be_disabled()
    paheko.held = False
    expect(page.get_by_text(CONNECTED)).to_be_visible()
    expect(page.get_by_text(CHECKING)).to_have_count(0)


# /ui/statut-de-connexion/connected
def test_connected_green(server, page: Page):
    page.goto(server)
    expect(page.get_by_text(CONNECTED)).to_be_visible()
    r, g, b = rgb(page, CONNECTED)
    assert g > r and g > b


# /ui/statut-de-connexion/failed
def test_failed_red(server, paheko, page: Page):
    paheko.status = 403
    page.goto(server)
    message = f"Identifiants refusés par {URL}."
    expect(page.get_by_text(message)).to_be_visible()
    r, g, b = rgb(page, message)
    assert r > g and r > b


# /ui/page-daccueil/recheck-click /ui/statut-de-connexion/checking
def test_recheck(server, paheko, page: Page):
    page.goto(server)
    expect(page.get_by_text(CONNECTED)).to_be_visible()
    button = page.get_by_role("button", name="Tester à nouveau")
    expect(button).to_be_enabled()
    calls = paheko.calls
    paheko.held = True
    button.click()
    expect(page.get_by_text(CHECKING)).to_be_visible()
    expect(button).to_be_disabled()
    wait_calls(paheko, calls + 1)
    paheko.held = False
    expect(page.get_by_text(CONNECTED)).to_be_visible()
    expect(button).to_be_enabled()


# /ui/page-daccueil/recheck-click
def test_recheck_shows_new_result(server, paheko, page: Page):
    page.goto(server)
    expect(page.get_by_text(CONNECTED)).to_be_visible()
    paheko.status = 500
    page.get_by_role("button", name="Tester à nouveau").click()
    expect(page.get_by_text(f"Réponse inattendue de {URL} : code 500.")).to_be_visible()
    expect(page.get_by_text(CONNECTED)).to_have_count(0)
