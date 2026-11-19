from datetime import datetime
from html.parser import HTMLParser

from litestar.testing import TestClient

from gestion_lafab.app import create_app
from tests.fakes import DIGITAL, ENV, METAL, URL, Clock, FakePaheko, Member
from tests.stats_html import normalize, sse_html

NOW = datetime(2026, 11, 10, 14, 32)
LASER = DIGITAL[0]
TIG = METAL[1]
ALICE = Member(11, 1204, "Alice", "ARNAUD")
BRUNO = Member(12, 876, "Bruno", "MOREAU")


class _Links(HTMLParser):
    """The links in the data cells (`td`) of the table rows after the
    `Doublons` title, by row: (text, href, target) of each."""

    def __init__(self) -> None:
        super().__init__()
        self.after_title = False
        self._heading: list[str] | None = None
        self.rows: list[list[tuple[str, str, str]]] = []
        self._row: list[tuple[str, str, str]] | None = None
        self._link: tuple[list[str], str, str] | None = None
        self._in_td = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4"):
            self._heading = []
        elif tag == "tr" and self.after_title:
            self._row = []
        elif tag == "td" and self._row is not None:
            self._in_td = True
        elif tag == "a" and self._row is not None and self._in_td:
            self._link = ([], attrs.get("href") or "", attrs.get("target") or "")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4") and self._heading is not None:
            heading = normalize("".join(self._heading)).strip()
            self.after_title = heading == "Doublons"
            self._heading = None
        elif tag == "td":
            self._in_td = False
        elif tag == "a" and self._link is not None and self._row is not None:
            text, href, target = self._link
            self._row.append((normalize("".join(text)).strip(), href, target))
            self._link = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._heading is not None:
            self._heading.append(data)
        elif self._link is not None:
            self._link[0].append(data)


def links(paheko: FakePaheko, env: dict[str, str] | None = None):
    app = create_app(dict(ENV) if env is None else env, paheko.transport(), Clock(NOW))
    with TestClient(app) as client:
        response = client.get("/initiations/lecture")
    assert response.status_code == 200
    parser = _Links()
    parser.feed(sse_html(response.text))
    return parser.rows


def setup(paheko: FakePaheko, *rows: tuple[Member, int, str]) -> None:
    """Registrations given as (member, activity, ISO date); the simulated
    Paheko numbers them 1, 2, … in this order."""
    paheko.members = [ALICE, BRUNO]
    paheko.registrations = [(m.id, activity, day) for m, activity, day in rows]


def delete_url(registration: int, url: str = URL) -> str:
    return f"{url}/admin/services/user/delete.php?id={registration}"


# /ui/tableau-des-doublons-dinitiation/suppression /model/initiation
# /ui/tableau-des-doublons-dinitiation/dates
def test_each_date_links_to_its_registration(paheko):
    setup(
        paheko,
        (BRUNO, LASER, "2026-05-01"),
        (ALICE, TIG, "2026-06-21"),
        (ALICE, TIG, "2026-02-03"),
    )
    assert [(text, href) for text, href, _ in links(paheko)[0]] == [
        ("03/02/2026", delete_url(3)),
        ("21/06/2026", delete_url(2)),
    ]


# /ui/tableau-des-doublons-dinitiation/suppression
def test_links_of_each_duplicate(paheko):
    setup(
        paheko,
        (ALICE, LASER, "2026-10-14"),
        (BRUNO, TIG, "2026-02-03"),
        (ALICE, LASER, "2026-10-14"),
        (BRUNO, TIG, "2026-06-21"),
    )
    rows = links(paheko)
    assert len(rows) == 2
    assert sorted(href for _, href, _ in rows[0]) == [delete_url(1), delete_url(3)]
    assert [href for _, href, _ in rows[1]] == [delete_url(2), delete_url(4)]


# /ui/tableau-des-doublons-dinitiation/suppression
def test_links_use_configured_url(paheko):
    setup(paheko, (ALICE, LASER, "2026-03-01"), (ALICE, LASER, "2026-03-02"))
    other = "https://autre.paheko.cloud"
    rows = links(paheko, dict(ENV, PAHEKO_URL=other))
    assert [href for _, href, _ in rows[0]] == [
        delete_url(1, other),
        delete_url(2, other),
    ]


# /ui/tableau-des-doublons-dinitiation/suppression
def test_links_open_in_new_tab(paheko):
    setup(paheko, (ALICE, LASER, "2026-03-01"), (ALICE, LASER, "2026-03-02"))
    assert [target for _, _, target in links(paheko)[0]] == ["_blank", "_blank"]
