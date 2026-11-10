import re
import time
from datetime import datetime

from playwright.sync_api import Locator, Page, expect

from tests.fakes import MEMBERSHIP, URL

READ = "Données Paheko lues le 10/11/2026 à 14 h 32."
READING = "Lecture de Paheko…"
INDICATOR = re.compile(r"^2026 : \d+ adhésions au 10 novembre")

REGISTRATIONS = [
    (1, MEMBERSHIP, "2025-01-10"),
    (2, MEMBERSHIP, "2025-03-10"),
    (3, MEMBERSHIP, "2026-01-12"),
    (4, MEMBERSHIP, "2026-02-12"),
]


def wait_calls(paheko, expected: int, timeout: float = 5) -> None:
    deadline = time.monotonic() + timeout
    while paheko.calls < expected and time.monotonic() < deadline:
        time.sleep(0.01)
    assert paheko.calls == expected


def open_page(page: Page, server: str) -> None:
    page.goto(f"{server}/adhesions")


def svg_with_title(page: Page, pattern: str) -> Locator:
    return page.locator("svg").filter(
        has=page.locator("title", has_text=re.compile(pattern))
    )


def cumulative(page: Page) -> Locator:
    return svg_with_title(page, r"^2025, janvier : \d+$")


def annual(page: Page) -> Locator:
    return svg_with_title(page, r"^2025 : \d+$")


def mark_style(page: Page, pattern: str) -> dict:
    """Computed style of the chart mark carrying the hover text."""
    title = page.locator("svg title", has_text=re.compile(pattern)).first
    return title.evaluate(
        """t => {
            const s = getComputedStyle(t.parentElement);
            return {fill: s.fill, stroke: s.stroke, fillOpacity: s.fillOpacity,
                    opacity: s.opacity, dash: s.strokeDasharray};
        }"""
    )


def mark_rgb(page: Page, pattern: str) -> tuple[int, int, int]:
    """Colour of the mark carrying the hover text; for a transparent hit
    target, of the first painted line of its group."""
    title = page.locator("svg title", has_text=re.compile(pattern)).first
    paint = title.evaluate(
        """t => {
            const painted = e => {
                const s = getComputedStyle(e);
                if (s.opacity === "0") return null;
                const paints = [[s.fill, s.fillOpacity], [s.stroke, s.strokeOpacity]];
                for (const [p, o] of paints) {
                    if (p.startsWith("rgb(") && o !== "0") return p;
                }
                return null;
            };
            const mark = t.parentElement;
            const own = painted(mark);
            if (own) return own;
            for (const e of mark.parentElement.querySelectorAll(
                    "polyline, path, line")) {
                const p = painted(e);
                if (p) return p;
            }
            return "";
        }"""
    )
    r, g, b = (int(x) for x in re.findall(r"\d+", paint)[:3])
    return r, g, b


def text_rgb(page: Page, text: str) -> tuple[int, int, int]:
    color = page.get_by_text(text).evaluate("e => getComputedStyle(e).color")
    r, g, b = (int(x) for x in re.findall(r"\d+", color)[:3])
    return r, g, b


# /ui/page-daccueil/adhesions-link
def test_home_link(server, paheko, page: Page):
    page.goto(server)
    page.get_by_role("link", name="Adhésions").click()
    expect(page).to_have_url(f"{server}/adhesions")
    expect(page.get_by_role("heading", name="Adhésions", exact=True)).to_be_visible()


# /ui/page-des-adhesions/title
def test_title_and_home_link(server, paheko, page: Page):
    open_page(page, server)
    expect(page.get_by_role("heading", name="Adhésions", exact=True)).to_be_visible()
    page.get_by_role("link", name="Accueil").click()
    expect(page).to_have_url(f"{server}/")
    expect(page.get_by_role("heading", name="Gestion La Fabrique")).to_be_visible()


# /ui/page-des-adhesions/title /ui/page-des-adhesions/reading
# /ui/page-des-adhesions/refresh /ui/page-des-adhesions/stats
# /ui/statistiques-affichees/indicator /ui/statistiques-affichees/cumulative
# /ui/statistiques-affichees/annual /ui/statistiques-affichees/table
def test_layout_order(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    boxes = [
        page.get_by_role("heading", name="Adhésions", exact=True).bounding_box(),
        page.get_by_text(READ).bounding_box(),
        page.get_by_role("button", name="Actualiser").bounding_box(),
        page.get_by_text(INDICATOR).bounding_box(),
        cumulative(page).bounding_box(),
        annual(page).bounding_box(),
        page.get_by_role("table").bounding_box(),
    ]
    ys = [box["y"] for box in boxes]
    assert ys == sorted(ys)
    assert len(set(ys)) == len(ys)


# /ui/statut-de-lecture/reading /ui/statut-de-lecture/opened
# /ui/page-des-adhesions/refresh-click
def test_reading_on_open(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    paheko.held = True
    open_page(page, server)
    expect(page.get_by_text(READING)).to_be_visible()
    wait_calls(paheko, 1)
    expect(page.get_by_role("button", name="Actualiser")).to_be_disabled()
    paheko.held = False
    expect(page.get_by_text(READ)).to_be_visible()
    expect(page.get_by_text(READING)).to_have_count(0)
    expect(page.get_by_role("button", name="Actualiser")).to_be_enabled()
    expect(page.get_by_role("table")).to_be_visible()


# /ui/statut-de-lecture/read
def test_read_instant(server, paheko, clock, page: Page):
    clock.value = datetime(2026, 3, 5, 18, 7)
    open_page(page, server)
    expect(
        page.get_by_text("Données Paheko lues le 05/03/2026 à 18 h 07.")
    ).to_be_visible()


# /ui/statut-de-lecture/opened /ui/statut-de-lecture/read
# /ui/page-des-adhesions/stats
def test_reading_kept_in_memory(server, paheko, clock, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    wait_calls(paheko, 1)
    clock.value = datetime(2026, 11, 10, 16, 0)
    paheko.registrations = []
    page.goto(server)
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    expect(page.get_by_text(INDICATOR)).to_be_visible()
    expect(page.get_by_role("table")).to_be_visible()
    time.sleep(0.3)
    wait_calls(paheko, 1 + 1)  # the connection test of the home page only


# /ui/page-des-adhesions/refresh-click /ui/statut-de-lecture/reading
# /ui/statut-de-lecture/read
def test_refresh(server, paheko, clock, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    expect(page.get_by_text(INDICATOR)).to_have_text(re.compile(r"^2026 : 2 "))
    calls = paheko.calls
    clock.value = datetime(2026, 11, 10, 15, 45)
    paheko.registrations = REGISTRATIONS + [(5, MEMBERSHIP, "2026-03-12")]
    paheko.held = True
    button = page.get_by_role("button", name="Actualiser")
    button.click()
    expect(page.get_by_text(READING)).to_be_visible()
    expect(button).to_be_disabled()
    wait_calls(paheko, calls + 1)
    paheko.held = False
    expect(
        page.get_by_text("Données Paheko lues le 10/11/2026 à 15 h 45.")
    ).to_be_visible()
    expect(button).to_be_enabled()
    expect(page.get_by_text(INDICATOR)).to_have_text(re.compile(r"^2026 : 3 "))


# /ui/statut-de-lecture/failed /ui/page-des-adhesions/stats
def test_failed_on_open(server, paheko, page: Page):
    paheko.status = 403
    open_page(page, server)
    message = f"Identifiants refusés par {URL}."
    expect(page.get_by_text(message)).to_be_visible()
    r, g, b = text_rgb(page, message)
    assert r > g and r > b
    expect(page.get_by_role("table")).to_have_count(0)
    expect(page.get_by_text(INDICATOR)).to_have_count(0)
    expect(page.get_by_role("button", name="Actualiser")).to_be_enabled()


# /ui/statut-de-lecture/failed /operations/lire-les-adhesions/failed
# /ui/statut-de-lecture/read
def test_failed_refresh_keeps_statistics(server, paheko, clock, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    clock.value = datetime(2026, 11, 10, 15, 45)
    paheko.status = 500
    page.get_by_role("button", name="Actualiser").click()
    message = f"Réponse inattendue de {URL} : code 500."
    expect(page.get_by_text(message)).to_be_visible()
    r, g, b = text_rgb(page, message)
    assert r > g and r > b
    expect(page.get_by_text(INDICATOR)).to_have_text(re.compile(r"^2026 : 2 "))
    expect(page.get_by_role("table")).to_be_visible()
    page.reload()
    expect(page.get_by_text(READ)).to_be_visible()
    expect(page.get_by_text(INDICATOR)).to_have_text(re.compile(r"^2026 : 2 "))


# /ui/graphique-du-cumul/current /ui/graphique-du-cumul/previous
# /ui/graphique-du-cumul/older
def test_cumulative_colors(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(cumulative(page)).to_be_visible()
    current = mark_rgb(page, r"^2026, janvier : \d+$")
    previous = mark_rgb(page, r"^2025, janvier : \d+$")
    older = [mark_rgb(page, rf"^{year}, janvier : \d+$") for year in range(2016, 2025)]
    assert max(current) - min(current) > 60
    assert max(previous) - min(previous) > 60
    assert sum(abs(c - p) for c, p in zip(current, previous)) > 60
    for color in older:
        assert max(color) - min(color) < 25
        assert sum(color) / 3 > 150


# /ui/graphique-annuel/partial
def test_annual_partial(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(annual(page)).to_be_visible()
    current = mark_style(page, r"^2026 : \d+$")
    previous = mark_style(page, r"^2025 : \d+$")
    older = mark_style(page, r"^2018 : \d+$")
    assert current != previous
    assert current != older
