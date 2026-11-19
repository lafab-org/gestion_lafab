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
TITLE = "Initiations par membre"
HEADER = ["Membre", "bois", "métal", "souple", "numérique", "Total"]

ALICE = Member(11, 1204, "Alice", "ARNAUD")
BRUNO = Member(12, 876, "Bruno", "MOREAU")
CAMILLE = Member(13, 412, "Camille", "MARTIN")


class _Section(HTMLParser):
    """The rows of the table after the title `TITLE`, the text after it,
    and every heading."""

    def __init__(self) -> None:
        super().__init__()
        self.after_title = False
        self.headings: list[str] = []
        self.rows: list[list[str]] = []
        self.texts: list[str] = []
        self._heading: list[str] | None = None
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
            self.after_title = heading == TITLE
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


class ByMember:
    def __init__(self, html: str) -> None:
        parser = _Section()
        parser.feed(html)
        self.headings = parser.headings
        rows = parser.rows
        self.header = rows[0] if rows and rows[0] == HEADER else []
        self.lines = rows[1:] if self.header else rows
        self.text = normalize(" ".join(parser.texts))

    def line(self, member: str) -> list[str]:
        (found,) = [line[1:] for line in self.lines if line[0] == member]
        return found


def read(paheko: FakePaheko, now: datetime = NOW) -> ByMember:
    app = create_app(dict(ENV), paheko.transport(), Clock(now))
    with TestClient(app) as client:
        response = client.get("/initiations/lecture")
    assert response.status_code == 200
    return ByMember(sse_html(response.text))


def setup(paheko: FakePaheko, *rows: tuple[Member, int, str]) -> None:
    """Registrations given as (member, activity, ISO date)."""
    paheko.members = [ALICE, BRUNO, CAMILLE]
    paheko.registrations = [(m.id, activity, day) for m, activity, day in rows]


# /model/initiations-par-membre /ui/tableau-des-initiations-par-membre
# /ui/tableau-des-initiations-par-membre/cells
# /ui/tableau-des-initiations-par-membre/total
def test_distinct_activities_counted_once(paheko):
    setup(
        paheko,
        (ALICE, DIGITAL[0], "2026-01-10"),
        (ALICE, DIGITAL[0], "2026-01-10"),
        (ALICE, DIGITAL[0], "2024-05-02"),
        (ALICE, DIGITAL[1], "2026-03-01"),
        (ALICE, METAL[1], "2025-06-01"),
    )
    by_member = read(paheko)
    assert by_member.header == HEADER
    assert by_member.line("1204 Alice ARNAUD") == ["0", "1", "0", "2", "3"]


# /model/initiations-par-membre /ui/tableau-des-initiations-par-membre/cells
# /ui/tableau-des-initiations-par-membre/total
def test_each_category_in_its_column(paheko):
    setup(
        paheko,
        (BRUNO, WOOD[0], "2026-01-10"),
        (BRUNO, WOOD[5], "2026-01-11"),
        (BRUNO, WOOD[6], "2026-01-12"),
        (BRUNO, METAL[0], "2026-02-01"),
        (BRUNO, METAL[2], "2026-02-02"),
        (BRUNO, SOFT[0], "2026-03-01"),
        (BRUNO, DIGITAL[1], "2026-04-01"),
    )
    assert read(paheko).line("876 Bruno MOREAU") == ["3", "2", "1", "1", "7"]


# /model/initiations-par-membre
def test_only_members_with_an_initiation(paheko):
    setup(
        paheko,
        (ALICE, DIGITAL[0], "2026-01-10"),
        (BRUNO, MEMBERSHIP, "2026-01-10"),
        (BRUNO, NOT_INITIATIONS[1], "2026-01-11"),
    )
    assert [line[0] for line in read(paheko).lines] == ["1204 Alice ARNAUD"]


# /model/initiations-par-membre /model/lecture-des-initiations
def test_initiations_after_day_not_counted(paheko):
    setup(
        paheko,
        (ALICE, DIGITAL[0], "2026-11-10"),
        (ALICE, DIGITAL[1], "2026-11-11"),
        (BRUNO, METAL[0], "2026-12-01"),
    )
    by_member = read(paheko)
    assert [line[0] for line in by_member.lines] == ["1204 Alice ARNAUD"]
    assert by_member.line("1204 Alice ARNAUD") == ["0", "0", "0", "1", "1"]


# /ui/tableau-des-initiations-par-membre/ordre
# /ui/tableau-des-initiations-par-membre/membre
def test_order_by_total(paheko):
    setup(
        paheko,
        (ALICE, DIGITAL[0], "2026-01-10"),
        (BRUNO, WOOD[0], "2026-01-10"),
        (BRUNO, WOOD[1], "2026-01-10"),
        (BRUNO, METAL[0], "2026-01-10"),
        (CAMILLE, SOFT[0], "2026-01-10"),
        (CAMILLE, SOFT[1], "2026-01-10"),
        (CAMILLE, SOFT[1], "2026-02-10"),
        (CAMILLE, SOFT[1], "2026-03-10"),
    )
    lines = read(paheko).lines
    assert [line[0] for line in lines] == [
        "876 Bruno MOREAU",
        "412 Camille MARTIN",
        "1204 Alice ARNAUD",
    ]
    assert [line[5] for line in lines] == ["3", "2", "1"]


# /ui/tableau-des-initiations-par-membre/ordre
def test_ties_listed_after_higher_totals(paheko):
    setup(
        paheko,
        (ALICE, DIGITAL[0], "2026-01-10"),
        (BRUNO, METAL[0], "2026-01-10"),
        (CAMILLE, SOFT[0], "2026-01-10"),
        (CAMILLE, SOFT[1], "2026-01-10"),
    )
    lines = read(paheko).lines
    assert lines[0][0] == "412 Camille MARTIN"
    assert sorted(line[0] for line in lines[1:]) == [
        "1204 Alice ARNAUD",
        "876 Bruno MOREAU",
    ]


# /ui/tableau-des-initiations-par-membre/aucun
def test_no_initiation_message(paheko):
    setup(paheko, (ALICE, MEMBERSHIP, "2026-01-10"))
    by_member = read(paheko)
    assert TITLE in by_member.headings
    assert by_member.lines == []
    assert "Aucune initiation." in by_member.text


# /ui/tableau-des-initiations-par-membre/aucun
def test_no_message_with_members(paheko):
    setup(paheko, (ALICE, DIGITAL[0], "2026-01-10"))
    by_member = read(paheko)
    assert TITLE in by_member.headings
    assert "Aucune initiation." not in by_member.text


# /ui/page-des-initiations/par-membre
def test_section_comes_last(paheko):
    setup(
        paheko,
        (ALICE, DIGITAL[0], "2026-01-10"),
        (ALICE, DIGITAL[0], "2026-01-10"),
    )
    by_member = read(paheko)
    assert by_member.headings[-1] == TITLE
    assert by_member.headings.index("Doublons") < by_member.headings.index(TITLE)
