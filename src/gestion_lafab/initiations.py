"""Initiation statistics: Paheko registrations to initiation activities."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

import httpx

from gestion_lafab.membership import MONTHS
from gestion_lafab.paheko import run_sql

CATEGORIES = ["bois", "métal", "souple", "numérique"]
# Category of each Paheko activity of initiation, by activity id.
CATEGORY_OF_ACTIVITY = {
    **dict.fromkeys([20, 21, 22, 25, 28, 29, 33], "bois"),
    **dict.fromkeys([27, 30, 34], "métal"),
    **dict.fromkeys([24, 32], "souple"),
    **dict.fromkeys([23, 31], "numérique"),
}


@dataclass(frozen=True)
class Initiation:
    day: date
    category: str


@dataclass(frozen=True)
class Reading:
    """Initiations read from Paheko, dated up to the day of the reading."""

    initiations: list[Initiation]
    instant: datetime

    @property
    def day(self) -> date:
        return self.instant.date()


@dataclass(frozen=True)
class ReadResult:
    ok: bool
    message: str = ""
    reading: Reading | None = None


async def read_initiations(
    env: Mapping[str, str], transport: httpx.AsyncBaseTransport | None, now: datetime
) -> ReadResult:
    activities = ", ".join(str(a) for a in sorted(CATEGORY_OF_ACTIVITY))
    query = (
        "SELECT id_service, date FROM services_users"
        f" WHERE id_service IN ({activities});"
    )
    result = await run_sql(env, transport, query)
    if not result.ok:
        return ReadResult(False, result.message)
    initiations = []
    for row in result.rows:
        category = CATEGORY_OF_ACTIVITY.get(int(row["id_service"]))
        day = date.fromisoformat(str(row["date"])[:10])
        if category is not None and day <= now.date():
            initiations.append(Initiation(day, category))
    return ReadResult(True, reading=Reading(initiations, now))


@dataclass(frozen=True)
class MonthRow:
    year: int
    month: int
    counts: list[int]  # by category, in the order of CATEGORIES

    @property
    def label(self) -> str:
        return f"{MONTHS[self.month - 1]} {self.year}"

    @property
    def total(self) -> int:
        return sum(self.counts)


@dataclass(frozen=True)
class Statistics:
    current_year: int
    day: date
    years: list[int]  # chronological
    # By year, the months that have numbers, January first.
    monthly: dict[int, list[MonthRow]]
    total: dict[int, list[int]]  # by year, by category

    def table_rows(self) -> list[MonthRow]:
        """Months from the month of the reading down to the first January."""
        return [
            row for year in reversed(self.years) for row in self.monthly[year][::-1]
        ]


def statistics(reading: Reading) -> Statistics:
    day = reading.day
    current = day.year
    first = min((i.day.year for i in reading.initiations), default=current)
    years = list(range(first, current + 1))
    counts = {
        (year, month): [0] * len(CATEGORIES) for year in years for month in range(1, 13)
    }
    for i in reading.initiations:
        counts[(i.day.year, i.day.month)][CATEGORIES.index(i.category)] += 1
    monthly = {}
    total = {}
    for year in years:
        last = day.month if year == current else 12
        monthly[year] = [
            MonthRow(year, month, counts[(year, month)]) for month in range(1, last + 1)
        ]
        total[year] = [
            sum(row.counts[k] for row in monthly[year]) for k in range(len(CATEGORIES))
        ]
    return Statistics(current, day, years, monthly, total)
