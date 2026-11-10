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


CATEGORIES = ["bois", "métal", "souple", "numérique"]


def month_label(year: int, month: int) -> str:
    return f"{MONTHS[month - 1]} {year}"


class InitiationStats:
    """What an HTML fragment of the initiations shows: its text, the header
    of its table, and its table rows by month label (`<mois> <année>`)."""

    def __init__(self, html: str) -> None:
        parser = _Parser()
        parser.feed(html)
        self.text = normalize(" ".join(parser.texts))
        self.header: list[str] = []
        self.months: list[str] = []
        self.cells: dict[str, list[str]] = {}
        label = re.compile(rf"(?:{'|'.join(MONTHS)}) \d{{4}}")
        for row in parser.rows:
            if len(row) == 6 and label.fullmatch(row[0]):
                self.months.append(row[0])
                self.cells[row[0]] = row[1:]
            elif len(row) == 6 and row[5] == "Total" and not self.header:
                self.header = row[1:]

    def has(self, hover: str) -> bool:
        """Whether the exact hover text appears, its number not prolonged."""
        return re.search(re.escape(hover) + r"(?!\d)", self.text) is not None

    def has_monthly(self, year: int, month: int) -> bool:
        """Whether any segment of the monthly chart is shown for that month."""
        pattern = rf"(?:{'|'.join(CATEGORIES)}), {month_label(year, month)} : \d+"
        return re.search(pattern, self.text) is not None
