import re
import time
from datetime import datetime

from playwright.sync_api import Locator, Page, expect

from tests.fakes import DIGITAL, MEMBERSHIP, METAL, SOFT, URL, WOOD

READ = "Données Paheko lues le 10/11/2026 à 14 h 32."
READING = "Lecture de Paheko…"
CATEGORIES = ["bois", "métal", "souple", "numérique"]

# Each category in March 2026 and in 2025; bois also in January 2026.
REGISTRATIONS = [
    (1, WOOD[0], "2026-03-02"),
    (2, WOOD[1], "2026-03-03"),
    (3, METAL[0], "2026-03-04"),
    (4, SOFT[0], "2026-03-05"),
    (5, DIGITAL[0], "2026-03-06"),
    (6, WOOD[2], "2026-01-06"),
    (7, WOOD[0], "2025-04-02"),
    (8, METAL[1], "2025-04-03"),
    (9, SOFT[1], "2025-04-04"),
    (10, DIGITAL[1], "2025-04-05"),
]
CURRENT_MONTH = "novembre 2026"


def wait_calls(paheko, expected: int, timeout: float = 5) -> None:
    deadline = time.monotonic() + timeout
    while paheko.calls < expected and time.monotonic() < deadline:
        time.sleep(0.01)
    assert paheko.calls == expected


def open_page(page: Page, server: str) -> None:
    page.goto(f"{server}/initiations")


def svg_with_title(page: Page, pattern: str) -> Locator:
    return page.locator("svg").filter(
        has=page.locator("title", has_text=re.compile(pattern))
    )


def monthly(page: Page) -> Locator:
    return svg_with_title(page, r"^\S+, mars 2026 : \d+$")


def annual(page: Page) -> Locator:
    return svg_with_title(page, r"^\S+, 2025 : \d+$")


def segment(page: Page, hover: str) -> Locator:
    """The chart mark carrying the hover text."""
    return page.locator("svg title", has_text=re.compile(rf"^{hover}$")).locator("..")


def fill_rgb(mark: Locator) -> tuple[int, int, int]:
    paint = mark.evaluate("e => getComputedStyle(e).fill")
    r, g, b = (int(x) for x in re.findall(r"\d+", paint)[:3])
    return r, g, b


def styles(mark: Locator) -> dict:
    """Computed style of a mark and of its parent."""
    return mark.evaluate(
        """e => [e, e.parentElement].map(x => {
            const s = getComputedStyle(x);
            return [s.fill, s.stroke, s.fillOpacity, s.opacity, s.strokeDasharray];
        })"""
    )


def distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum(abs(x - y) for x, y in zip(a, b))


def text_rgb(page: Page, text: str) -> tuple[int, int, int]:
    color = page.get_by_text(text).evaluate("e => getComputedStyle(e).color")
    r, g, b = (int(x) for x in re.findall(r"\d+", color)[:3])
    return r, g, b


def table_row(page: Page, label: str) -> Locator:
    return page.get_by_role("row").filter(has_text=re.compile(rf"^\s*{label}\b"))


def total_cell(page: Page, label: str) -> Locator:
    return table_row(page, label).locator("td, th").last


# /ui/page-daccueil/initiations-link /ui/page-daccueil/adhesions-link
def test_home_link(server, paheko, page: Page):
    page.goto(server)
    adhesions = page.get_by_role("link", name="Adhésions").bounding_box()
    link = page.get_by_role("link", name="Initiations")
    assert adhesions["y"] < link.bounding_box()["y"]
    link.click()
    expect(page).to_have_url(f"{server}/initiations")
    expect(page.get_by_role("heading", name="Initiations", exact=True)).to_be_visible()


# /ui/page-des-initiations/title
def test_title_and_home_link(server, paheko, page: Page):
    open_page(page, server)
    expect(page.get_by_role("heading", name="Initiations", exact=True)).to_be_visible()
    page.get_by_role("link", name="Accueil").click()
    expect(page).to_have_url(f"{server}/")
    expect(page.get_by_role("heading", name="Gestion La Fabrique")).to_be_visible()


# /ui/page-des-initiations/title /ui/page-des-initiations/reading
# /ui/page-des-initiations/refresh /ui/page-des-initiations/stats
# /ui/statistiques-des-initiations-affichees/monthly
# /ui/statistiques-des-initiations-affichees/annual
# /ui/statistiques-des-initiations-affichees/table
def test_layout_order(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    boxes = [
        page.get_by_role("heading", name="Initiations", exact=True).bounding_box(),
        page.get_by_text(READ).bounding_box(),
        page.get_by_role("button", name="Actualiser").bounding_box(),
        monthly(page).bounding_box(),
        annual(page).bounding_box(),
        page.get_by_role("table").bounding_box(),
    ]
    ys = [box["y"] for box in boxes]
    assert ys == sorted(ys)
    assert len(set(ys)) == len(ys)


# /ui/statut-de-lecture/reading /ui/statut-de-lecture/opened
# /ui/page-des-initiations/refresh-click
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
# /ui/page-des-initiations/stats
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
    expect(total_cell(page, "mars 2026")).to_have_text("5")
    time.sleep(0.3)
    wait_calls(paheko, 1 + 1)  # the connection test of the home page only


# /ui/statut-de-lecture /ui/statut-de-lecture/opened
# /ui/statut-de-lecture/read
def test_each_page_has_its_reading(server, paheko, clock, page: Page):
    paheko.registrations = REGISTRATIONS + [(20, MEMBERSHIP, "2026-01-05")]
    page.goto(f"{server}/adhesions")
    expect(page.get_by_text(READ)).to_be_visible()
    wait_calls(paheko, 1)

    clock.value = datetime(2026, 11, 10, 15, 0)
    open_page(page, server)
    initiations_read = page.get_by_text("Données Paheko lues le 10/11/2026 à 15 h 00.")
    expect(initiations_read).to_be_visible()
    wait_calls(paheko, 2)
    expect(total_cell(page, "mars 2026")).to_have_text("5")

    page.goto(f"{server}/adhesions")
    expect(page.get_by_text(READ)).to_be_visible()
    open_page(page, server)
    expect(initiations_read).to_be_visible()
    time.sleep(0.3)
    wait_calls(paheko, 2)


# /ui/page-des-initiations/refresh-click /ui/statut-de-lecture/reading
# /ui/statut-de-lecture/read
def test_refresh(server, paheko, clock, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(page.get_by_text(READ)).to_be_visible()
    expect(total_cell(page, CURRENT_MONTH)).to_have_text("0")
    calls = paheko.calls
    clock.value = datetime(2026, 11, 10, 15, 45)
    paheko.registrations = REGISTRATIONS + [(30, METAL[2], "2026-11-02")]
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
    expect(total_cell(page, CURRENT_MONTH)).to_have_text("1")


# /ui/statut-de-lecture/failed /ui/page-des-initiations/stats
def test_failed_on_open(server, paheko, page: Page):
    paheko.status = 403
    open_page(page, server)
    message = f"Identifiants refusés par {URL}."
    expect(page.get_by_text(message)).to_be_visible()
    r, g, b = text_rgb(page, message)
    assert r > g and r > b
    expect(page.get_by_role("table")).to_have_count(0)
    expect(page.locator("svg title")).to_have_count(0)
    expect(page.get_by_role("button", name="Actualiser")).to_be_enabled()


# /ui/statut-de-lecture/failed /operations/lire-les-initiations/failed
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
    expect(total_cell(page, "mars 2026")).to_have_text("5")
    expect(monthly(page)).to_be_visible()
    page.reload()
    expect(page.get_by_text(READ)).to_be_visible()
    expect(total_cell(page, "mars 2026")).to_have_text("5")


# /ui/statistiques-des-initiations-affichees/colors
def test_category_colors(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(monthly(page)).to_be_visible()
    colors = [fill_rgb(segment(page, f"{c}, mars 2026 : \\d+")) for c in CATEGORIES]
    for i, a in enumerate(colors):
        for b in colors[i + 1 :]:
            assert distance(a, b) > 60
    for category, color in zip(CATEGORIES, colors):
        # @dev43:unsure
        assert fill_rgb(segment(page, f"{category}, janvier 2026 : \\d+")) == color
        assert fill_rgb(segment(page, f"{category}, 2025 : \\d+")) == color


# /ui/statistiques-des-initiations-affichees/colors
def test_legend(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(monthly(page)).to_be_visible()
    painted = page.evaluate(
        """() => [...document.querySelectorAll("body *")]
            .filter(e => e.tagName !== "title" && !e.querySelector(":scope > title"))
            .flatMap(e => {
                const s = getComputedStyle(e);
                return [s.backgroundColor, s.fill, s.color, s.stroke];
            })"""
    )
    painted = {
        tuple(int(x) for x in re.findall(r"\d+", p)[:3])
        for p in painted
        if p.startswith("rgb")
    }
    for category in CATEGORIES:
        expect(page.get_by_text(category, exact=True).first).to_be_visible()
        assert fill_rgb(segment(page, f"{category}, 2025 : \\d+")) in painted


# /ui/statistiques-des-initiations-affichees/colors
def test_stacking_order(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(monthly(page)).to_be_visible()
    for hover in ("{}, mars 2026 : \\d+", "{}, 2025 : \\d+"):
        boxes = [segment(page, hover.format(c)).bounding_box() for c in CATEGORIES]
        bottoms = [box["y"] + box["height"] for box in boxes]
        assert bottoms == sorted(bottoms, reverse=True), hover
        assert len({round(b) for b in bottoms}) == len(bottoms), hover


# /ui/graphique-mensuel-des-initiations
def test_monthly_bars_in_order(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS
    open_page(page, server)
    expect(monthly(page)).to_be_visible()
    january = segment(page, "bois, janvier 2026 : \\d+").bounding_box()
    march = segment(page, "bois, mars 2026 : \\d+").bounding_box()
    assert january["x"] < march["x"]


# /ui/graphique-annuel-des-initiations
def test_annual_bars_in_order(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS + [(40, METAL[0], "2023-05-05")]
    open_page(page, server)
    expect(annual(page)).to_be_visible()
    xs = [
        segment(page, f"métal, {year} : \\d+").bounding_box()["x"]
        for year in (2023, 2025, 2026)
    ]
    assert xs == sorted(xs)
    assert len(set(xs)) == len(xs)


# /ui/graphique-annuel-des-initiations/partial
def test_annual_partial(server, paheko, page: Page):
    paheko.registrations = REGISTRATIONS + [(40, WOOD[0], "2024-05-05")]
    open_page(page, server)
    expect(annual(page)).to_be_visible()
    current = styles(segment(page, "bois, 2026 : \\d+"))
    previous = styles(segment(page, "bois, 2025 : \\d+"))
    older = styles(segment(page, "bois, 2024 : \\d+"))
    assert current != previous
    assert current != older
