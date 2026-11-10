import csv
import io
import re
from datetime import datetime

from playwright.sync_api import Locator, Page, expect

from tests.fakes import CASH_INITIATIONS, Tab
from tests.rapprochement_data import (
    ALICE,
    BRUNO,
    HEADER,
    MEMBERS,
    export_bytes,
    ticket,
)
from tests.test_ui_initiations import monthly, text_rgb

TITLE = "Rapprochement des initiations"
RUNNING = "Rapprochement…"
NO_FILE = "Aucun export des tickets envoyé : ventes de la caisse seulement."
NONE_OCTOBER = "Aucune initiation à ajouter pour octobre 2026."
UNKNOWN = "inconnu@example.org"

# Three lines in October 2026: complete, without member, without activity.
TICKETS = [
    ticket("Initiation au soudage TIG", "03/10/2026 18:00", ALICE.email),
    ticket("Initiation à la découpeuse laser", "09/10/2026 18:00", UNKNOWN),
]
TABS = [
    Tab(
        "2026-10-14 18:30:00",
        [("Autre initiation en groupe 3h", 1, CASH_INITIATIONS)],
        name="Bruno MOREAU",
        user_id=BRUNO.id,
    )
]
LINES = [
    [
        "1204",
        "Alice ARNAUD",
        "Initiation soudage TIG",
        "03/10/2026",
        "TiBillet",
        "alice@example.org",
        "Initiation au soudage TIG",
        "",
    ],
    [
        "",
        "",
        "Initiation laser",
        "09/10/2026",
        "TiBillet",
        UNKNOWN,
        "Initiation à la découpeuse laser",
        "",
    ],
    [
        "876",
        "Bruno MOREAU",
        "",
        "14/10/2026",
        "Caisse",
        "",
        "Autre initiation en groupe 3h",
        "",
    ],
]


def open_page(page: Page, server: str) -> None:
    page.goto(f"{server}/initiations/rapprochement")
    expect(page.get_by_role("heading", name=TITLE)).to_be_visible()


def month_input(page: Page) -> Locator:
    return page.locator("input[type=month]")


def file_input(page: Page) -> Locator:
    return page.locator("input[type=file]")


def choose(page: Page, content: bytes, name: str = "Ticket-2026-11-10.json") -> None:
    file_input(page).set_input_files(
        files=[{"name": name, "mimeType": "application/json", "buffer": content}]
    )


def submit(page: Page) -> Locator:
    button = page.get_by_role("button", name="Rapprocher")
    button.click()
    return button


def table_rows(page: Page) -> list[list[str]]:
    rows = page.get_by_role("table").get_by_role("row")
    return [
        [cell.strip() for cell in row.locator("th, td").all_inner_texts()]
        for row in rows.all()
    ]


def setup(paheko) -> None:
    paheko.members = list(MEMBERS)
    paheko.tabs = list(TABS)


# /ui/page-des-initiations/rapprochement-link
def test_link_from_initiations_page(server, paheko, page: Page):
    page.goto(f"{server}/initiations")
    status = page.get_by_text(re.compile(r"^Données Paheko lues le "))
    expect(status).to_be_visible()
    link = page.get_by_role("link", name="Rapprochement")
    y = link.bounding_box()["y"]
    # @dev43:unsure
    assert status.bounding_box()["y"] < y < monthly(page).bounding_box()["y"]
    link.click()
    expect(page).to_have_url(f"{server}/initiations/rapprochement")
    expect(page.get_by_role("heading", name=TITLE)).to_be_visible()


# /ui/page-du-rapprochement-des-initiations/title
def test_title_and_link(server, paheko, page: Page):
    open_page(page, server)
    page.get_by_role("link", name="Initiations", exact=True).click()
    expect(page).to_have_url(f"{server}/initiations")
    expect(page.get_by_role("heading", name="Initiations", exact=True)).to_be_visible()


# /ui/page-du-rapprochement-des-initiations/title
# /ui/page-du-rapprochement-des-initiations/form
def test_form(server, paheko, page: Page):
    open_page(page, server)
    expect(month_input(page)).to_have_value("2026-10")
    expect(file_input(page)).to_have_count(1)
    ys = [
        page.get_by_role("heading", name=TITLE).bounding_box()["y"],
        month_input(page).bounding_box()["y"],
    ]
    assert ys == sorted(ys)
    expect(page.get_by_role("button", name="Rapprocher")).to_be_enabled()


# /ui/page-du-rapprochement-des-initiations/form
def test_default_month_in_january(server, paheko, clock, page: Page):
    clock.value = datetime(2027, 1, 5, 9, 0)
    open_page(page, server)
    expect(month_input(page)).to_have_value("2026-12")


# /ui/page-du-rapprochement-des-initiations/empty
def test_empty_before_any(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    expect(page.get_by_text(re.compile("initiations? à ajouter"))).to_have_count(0)
    expect(page.get_by_role("table")).to_have_count(0)
    expect(page.get_by_text(RUNNING)).to_have_count(0)
    choose(page, export_bytes(TICKETS))
    submit(page)
    expect(page.get_by_role("table")).to_be_visible()
    open_page(page, server)
    expect(page.get_by_text(re.compile("initiations? à ajouter"))).to_have_count(0)
    expect(page.get_by_role("table")).to_have_count(0)
    expect(page.get_by_text(NO_FILE)).to_have_count(0)


# /ui/page-du-rapprochement-des-initiations/running
# /ui/page-du-rapprochement-des-initiations/submit
def test_running(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    paheko.held = True
    choose(page, export_bytes(TICKETS))
    button = submit(page)
    expect(page.get_by_text(RUNNING)).to_be_visible()
    expect(button).to_be_disabled()
    paheko.held = False
    expect(
        page.get_by_text("3 initiations à ajouter pour octobre 2026.")
    ).to_be_visible()
    expect(page.get_by_text(RUNNING)).to_have_count(0)
    expect(button).to_be_enabled()


# /ui/page-du-rapprochement-des-initiations/error
# /ui/page-du-rapprochement-des-initiations/submit
def test_error(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    choose(page, export_bytes(TICKETS))
    submit(page)
    expect(page.get_by_role("table")).to_be_visible()
    choose(page, b"pas du JSON")
    submit(page)
    message = "Export des tickets illisible."
    expect(page.get_by_text(message)).to_be_visible()
    r, g, b = text_rgb(page, message)
    assert r > g + 50 and r > b + 50
    expect(page.get_by_role("table")).to_have_count(0)
    expect(page.get_by_role("button", name="Rapprocher")).to_be_enabled()


# /ui/page-du-rapprochement-des-initiations/error
def test_paheko_error(server, paheko, page: Page):
    setup(paheko)
    paheko.status = 403
    open_page(page, server)
    choose(page, export_bytes(TICKETS))
    submit(page)
    message = "Identifiants refusés par https://lafab.paheko.cloud."
    expect(page.get_by_text(message)).to_be_visible()
    r, g, b = text_rgb(page, message)
    assert r > g + 50 and r > b + 50


# /ui/page-du-rapprochement-des-initiations/none
# /ui/page-du-rapprochement-des-initiations/caisse-seule
def test_none(server, paheko, page: Page):
    open_page(page, server)
    choose(page, export_bytes([ticket("Septembre", "09/09/2026 18:00", UNKNOWN)]))
    submit(page)
    expect(page.get_by_text(NONE_OCTOBER)).to_be_visible()
    expect(page.get_by_text(NO_FILE)).to_have_count(0)
    expect(page.get_by_role("table")).to_have_count(0)
    expect(page.get_by_role("button", name="Télécharger le CSV")).to_have_count(0)


# /ui/page-du-rapprochement-des-initiations/caisse-seule
# /ui/page-du-rapprochement-des-initiations/none
def test_no_file_warning(server, paheko, page: Page):
    open_page(page, server)
    submit(page)
    warning = page.get_by_text(NO_FILE)
    expect(warning).to_be_visible()
    result = page.get_by_text(NONE_OCTOBER)
    expect(result).to_be_visible()
    assert warning.bounding_box()["y"] < result.bounding_box()["y"]


# /ui/page-du-rapprochement-des-initiations/caisse-seule
# /ui/page-du-rapprochement-des-initiations/lines
def test_no_file_warning_with_lines(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    submit(page)
    warning = page.get_by_text(NO_FILE)
    expect(warning).to_be_visible()
    count = page.get_by_text(re.compile(r"^\s*1 initiations? à ajouter"))
    expect(count).to_be_visible()
    assert warning.bounding_box()["y"] < count.bounding_box()["y"]
    # A later reconciliation with a file has no warning.
    choose(page, export_bytes(TICKETS))
    submit(page)
    expect(
        page.get_by_text("3 initiations à ajouter pour octobre 2026.")
    ).to_be_visible()
    expect(page.get_by_text(NO_FILE)).to_have_count(0)


# /ui/page-du-rapprochement-des-initiations/lines
# /ui/page-du-rapprochement-des-initiations/result
def test_lines(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    choose(page, export_bytes(TICKETS))
    submit(page)
    count = page.get_by_text("3 initiations à ajouter pour octobre 2026.")
    expect(count).to_be_visible()
    expect(page.get_by_role("button", name="Télécharger le CSV")).to_be_visible()
    rows = table_rows(page)
    assert rows[0] == [name for name in HEADER if name != "Payé ?"]
    assert rows[1:] == LINES
    form_y = page.get_by_role("button", name="Rapprocher").bounding_box()["y"]
    count_y = count.bounding_box()["y"]
    assert form_y < count_y < page.get_by_role("table").bounding_box()["y"]


# /ui/page-du-rapprochement-des-initiations/submit
def test_chosen_month(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    month_input(page).fill("2026-09")
    choose(page, export_bytes(TICKETS))
    submit(page)
    expect(
        page.get_by_text("Aucune initiation à ajouter pour septembre 2026.")
    ).to_be_visible()


def highlight(row: Locator) -> list:
    """Computed backgrounds and font of a row and its cells."""
    return row.evaluate(
        """r => [r, ...r.children].map(e => {
            const s = getComputedStyle(e);
            return [s.backgroundColor, s.color, s.fontWeight, s.outline];
        })"""
    )


# /ui/page-du-rapprochement-des-initiations/incomplete
def test_incomplete_highlighted(server, paheko, page: Page):
    setup(paheko)
    paheko.tabs = TABS + [
        Tab(
            "2026-10-20 18:30:00",
            [("Initiation couture", 1, CASH_INITIATIONS)],
            name="Bruno MOREAU",
            user_id=BRUNO.id,
        )
    ]
    open_page(page, server)
    choose(page, export_bytes(TICKETS))
    submit(page)
    expect(
        page.get_by_text("4 initiations à ajouter pour octobre 2026.")
    ).to_be_visible()
    body = page.get_by_role("table").get_by_role("row")
    complete = [highlight(body.nth(1)), highlight(body.nth(4))]
    without_member = highlight(body.nth(2))
    without_activity = highlight(body.nth(3))
    assert complete[0] == complete[1]
    assert without_member != complete[0]
    assert without_activity != complete[0]


# /ui/page-du-rapprochement-des-initiations/download
def test_download(server, paheko, page: Page):
    setup(paheko)
    open_page(page, server)
    choose(page, export_bytes(TICKETS))
    submit(page)
    button = page.get_by_role("button", name="Télécharger le CSV")
    with page.expect_download() as info:
        button.click()
    download = info.value
    assert download.suggested_filename == "rapprochement-initiations-2026-10.csv"
    with open(download.path(), encoding="utf-8") as f:
        rows = list(csv.reader(io.StringIO(f.read())))
    assert rows[0] == HEADER
    assert [row[:4] + row[5:] for row in rows[1:]] == LINES
    assert {row[4] for row in rows[1:]} == {"Oui"}
