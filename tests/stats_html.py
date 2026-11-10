"""Reading the statistics out of HTML answers."""

import re
from html.parser import HTMLParser

MONTHS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def normalize(text: str) -> str:
    """Collapse whitespace, non-breaking spaces included."""
    return re.sub(r"\s+", " ", text.replace(" ", " ").replace(" ", " "))


def sse_html(body: str) -> str:
    """The HTML carried by the element patches of a Datastar event stream."""
    prefix = "data: elements "
    return "\n".join(
        line[len(prefix) :] for line in body.splitlines() if line.startswith(prefix)
    )


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.texts: list[str] = []
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(normalize("".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        self.texts.append(data)
        if self._cell is not None:
            self._cell.append(data)


class Stats:
    """What an HTML fragment shows: its text, and its table rows by year."""

    def __init__(self, html: str) -> None:
        parser = _Parser()
        parser.feed(html)
        self.text = normalize(" ".join(parser.texts))
        self.years: list[int] = []
        self.monthly: dict[int, list[str]] = {}
        self.total: dict[int, str] = {}
        for row in parser.rows:
            if len(row) == 14 and re.fullmatch(r"\d{4}", row[0]):
                year = int(row[0])
                self.years.append(year)
                self.monthly[year] = row[1:13]
                self.total[year] = row[13]

    def has_hover(self, year: int, month: int, value: int) -> bool:
        pattern = rf"\b{year}, {MONTHS[month - 1]} : {value}\b"
        return re.search(pattern, self.text) is not None

    def has_any_hover(self, year: int, month: int) -> bool:
        return re.search(rf"\b{year}, {MONTHS[month - 1]} : \d+", self.text) is not None

    def has_bar(self, year: int, total: int) -> bool:
        return re.search(rf"\b{year} : {total}\b(?! adhésions)", self.text) is not None
