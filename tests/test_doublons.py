from datetime import datetime
from html.parser import HTMLParser

from litestar.testing import TestClient

from gestion_lafab.app import create_app
from tests.fakes import (
    DIGITAL,
    ENV,
    MEMBERSHIP,
    METAL,
    NOT_INITIATIONS,
    SOFT,
    WOOD,
    Clock,
    FakePaheko,
    Member,
)
from tests.stats_html import normalize, sse_html

NOW = datetime(2026, 11, 10, 14, 32)
LASER = DIGITAL[0]
TIG = METAL[1]
COUTURE = SOFT[1]
PORTATIF = WOOD[5]
PORTATIF_NV2 = WOOD[6]
OTHER = NOT_INITIATIONS[1]

ALICE = Member(11, 1204, "Alice", "ARNAUD")
BRUNO = Member(12, 876, "Bruno", "MOREAU")
HEADER = ["Membre", "Activité", "Première", "Seconde"]


class _Rows(HTMLParser):
    """The rows of the table that follows the `Doublons` title, and the text
    shown after that title."""

    def __init__(self) -> None:
        super().__init__()
        self.after_title = False
        self.headings: list[str] = []
        self._heading: list[str] | None = None
        self.rows: list[list[str]] = []
        self.texts: list[str] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "h4"):
            self._heading = []
        elif tag == "tr" and self.after_title:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4") and self._heading is not None:
            heading = normalize("".join(self._heading)).strip()
            self.headings.append(heading)
            self.after_title = heading == "Doublons"
            self._heading = None
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(normalize("".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._heading is not None:
            self._heading.append(data)
        elif self.after_title:
            self.texts.append(data)
            if self._cell is not None:
                self._cell.append(data)


class Duplicates:
    """What the reading shows of the duplicates: whether the title is there,
    the header and the lines of the table, and the text after the title."""

    def __init__(self, html: str) -> None:
        parser = _Rows()
        parser.feed(html)
        self.titled = "Doublons" in parser.headings
        rows = parser.rows
        self.header = rows[0] if rows and rows[0] == HEADER else []
        self.lines = rows[1:] if self.header else rows
        self.text = normalize(" ".join(parser.texts))


def read(paheko: FakePaheko, now: datetime = NOW) -> Duplicates:
    app = create_app(dict(ENV), paheko.transport(), Clock(now))
    with TestClient(app) as client:
        response = client.get("/initiations/lecture")
    assert response.status_code == 200
    return Duplicates(sse_html(response.text))


def setup(paheko: FakePaheko, *rows: tuple[Member, int, str]) -> None:
    """Registrations given as (member, activity, ISO date)."""
    paheko.members = [ALICE, BRUNO]
    paheko.registrations = [(m.id, activity, day) for m, activity, day in rows]


def pairs(duplicates: Duplicates) -> list[tuple[str, str]]:
    return [(line[2], line[3]) for line in duplicates.lines]


# /model/doublons-dinitiation/ecart /ui/tableau-des-doublons-dinitiation
# /ui/tableau-des-doublons-dinitiation/dates
def test_same_date_is_duplicate(paheko):
    setup(paheko, (ALICE, LASER, "2026-10-14"), (ALICE, LASER, "2026-10-14"))
    duplicates = read(paheko)
    assert duplicates.header == HEADER
    assert pairs(duplicates) == [("14/10/2026", "14/10/2026")]


# /model/doublons-dinitiation/ecart /ui/tableau-des-doublons-dinitiation/dates
def test_day_before_anniversary_is_duplicate(paheko):
    setup(paheko, (ALICE, TIG, "2026-03-09"), (ALICE, TIG, "2025-03-10"))
    assert pairs(read(paheko)) == [("10/03/2025", "09/03/2026")]


# /model/doublons-dinitiation/ecart /ui/tableau-des-doublons-dinitiation/aucun
def test_anniversary_is_not_duplicate(paheko):
    setup(paheko, (ALICE, TIG, "2025-03-10"), (ALICE, TIG, "2026-03-10"))
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []
    assert "Aucun doublon." in duplicates.text


# /model/doublons-dinitiation/ecart
def test_more_than_a_year_is_not_duplicate(paheko):
    setup(paheko, (ALICE, TIG, "2024-01-05"), (ALICE, TIG, "2026-06-20"))
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []


# /model/doublons-dinitiation/ecart
def test_other_activity_is_not_duplicate(paheko):
    setup(
        paheko,
        (ALICE, PORTATIF, "2026-02-01"),
        (ALICE, PORTATIF_NV2, "2026-02-01"),
        (ALICE, LASER, "2026-04-01"),
    )
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []


# /model/doublons-dinitiation/ecart
def test_other_member_is_not_duplicate(paheko):
    setup(paheko, (ALICE, LASER, "2026-02-01"), (BRUNO, LASER, "2026-02-01"))
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []


# /model/doublons-dinitiation /model/lecture-des-initiations
def test_initiation_after_day_not_counted(paheko):
    setup(paheko, (ALICE, LASER, "2026-11-10"), (ALICE, LASER, "2026-11-11"))
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []


# /model/doublons-dinitiation/paires /ui/tableau-des-doublons-dinitiation/ordre
def test_each_pair_is_a_duplicate(paheko):
    setup(
        paheko,
        (ALICE, COUTURE, "2026-01-10"),
        (ALICE, COUTURE, "2026-02-10"),
        (ALICE, COUTURE, "2026-03-10"),
    )
    found = pairs(read(paheko))
    assert sorted(found) == sorted(
        [
            ("10/01/2026", "10/02/2026"),
            ("10/02/2026", "10/03/2026"),
            ("10/01/2026", "10/03/2026"),
        ]
    )
    assert found[0][1] == "10/03/2026"
    assert found[2][1] == "10/02/2026"


# /model/doublons-dinitiation/paires
def test_pairs_only_within_a_year(paheko):
    setup(
        paheko,
        (ALICE, COUTURE, "2025-01-10"),
        (ALICE, COUTURE, "2025-09-10"),
        (ALICE, COUTURE, "2026-03-10"),
    )
    assert sorted(pairs(read(paheko))) == sorted(
        [("10/01/2025", "10/09/2025"), ("10/09/2025", "10/03/2026")]
    )


# /ui/tableau-des-doublons-dinitiation/ordre
def test_order_most_recent_second_first(paheko):
    setup(
        paheko,
        (BRUNO, TIG, "2025-12-03"),
        (BRUNO, TIG, "2026-06-21"),
        (ALICE, LASER, "2026-02-14"),
        (ALICE, LASER, "2026-10-14"),
        (ALICE, COUTURE, "2026-03-01"),
        (ALICE, COUTURE, "2026-03-05"),
    )
    assert [(line[2], line[3]) for line in read(paheko).lines] == [
        ("14/02/2026", "14/10/2026"),
        ("03/12/2025", "21/06/2026"),
        ("01/03/2026", "05/03/2026"),
    ]


# /model/doublons-dinitiation /model/initiation
def test_other_activities_are_not_counted(paheko):
    setup(
        paheko,
        (ALICE, MEMBERSHIP, "2026-02-01"),
        (ALICE, MEMBERSHIP, "2026-02-01"),
        (BRUNO, OTHER, "2026-04-01"),
        (BRUNO, OTHER, "2026-04-01"),
    )
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []


# /ui/tableau-des-doublons-dinitiation/membre
# /ui/tableau-des-doublons-dinitiation/activite
def test_member_and_activity(paheko):
    setup(
        paheko,
        (BRUNO, TIG, "2026-02-03"),
        (BRUNO, TIG, "2026-06-21"),
        (ALICE, LASER, "2026-10-14"),
        (ALICE, LASER, "2026-10-14"),
    )
    assert [line[:2] for line in read(paheko).lines] == [
        ["1204 Alice ARNAUD", "Initiation laser"],
        ["876 Bruno MOREAU", "Initiation soudage TIG"],
    ]


# /ui/tableau-des-doublons-dinitiation/activite /model/lecture-des-initiations
def test_activity_label_read_from_paheko(paheko):
    setup(paheko, (ALICE, LASER, "2026-10-14"), (ALICE, LASER, "2026-10-14"))
    paheko.labels = {LASER: "Découpe laser (initiation)"}
    assert read(paheko).lines[0][1] == "Découpe laser (initiation)"


# /ui/tableau-des-doublons-dinitiation/activite
def test_activity_without_label_is_empty(paheko):
    setup(paheko, (ALICE, LASER, "2026-10-14"), (ALICE, LASER, "2026-10-14"))
    paheko.labels = {LASER: None}
    lines = read(paheko).lines
    assert [line[0] for line in lines] == ["1204 Alice ARNAUD"]
    assert lines[0][1] == ""


# /ui/tableau-des-doublons-dinitiation/aucun
def test_no_duplicate_message(paheko):
    setup(paheko, (ALICE, LASER, "2026-10-14"), (BRUNO, TIG, "2026-10-14"))
    duplicates = read(paheko)
    assert duplicates.titled
    assert duplicates.lines == []
    assert "Aucun doublon." in duplicates.text


# /ui/tableau-des-doublons-dinitiation/aucun
def test_no_message_with_duplicates(paheko):
    setup(paheko, (ALICE, LASER, "2026-10-14"), (ALICE, LASER, "2026-10-14"))
    duplicates = read(paheko)
    assert duplicates.titled
    assert "Aucun doublon." not in duplicates.text
