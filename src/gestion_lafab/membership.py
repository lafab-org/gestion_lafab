"""Membership statistics: Paheko registrations and the hand-compiled history."""

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import httpx

from gestion_lafab.paheko import run_sql

MEMBERSHIP_SERVICE = 1
DOUBLON_DAYS = 30
HISTORY_FILE = Path(__file__).parent / "data" / "historique_adhesions.csv"

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


def load_history(path: Path = HISTORY_FILE) -> dict[int, list[int]]:
    """Monthly counts by year: one line per year, the year then 12 numbers."""
    history = {}
    with path.open(newline="") as f:
        for row in csv.reader(f):
            if row:
                history[int(row[0])] = [int(n) for n in row[1:13]]
    return history


@dataclass(frozen=True)
class Reading:
    """Membership registrations read from Paheko, doublons excluded."""

    dates: list[date]
    instant: datetime

    @property
    def day(self) -> date:
        return self.instant.date()


@dataclass(frozen=True)
class ReadResult:
    ok: bool
    message: str = ""
    reading: Reading | None = None


def without_doublons(registrations: list[tuple[int, date]]) -> list[date]:
    """Dates of the registrations that are not doublons."""
    last: dict[int, date] = {}
    kept = []
    for user, day in sorted(registrations, key=lambda r: (r[1], r[0])):
        previous = last.get(user)
        if previous is not None and (day - previous).days < DOUBLON_DAYS:
            continue
        last[user] = day
        kept.append(day)
    return kept


async def read_memberships(
    env: Mapping[str, str],
    transport: httpx.AsyncBaseTransport | None,
    now: datetime,
    since_year: int,
) -> ReadResult:
    """Read the membership registrations dated from 1 January of since_year."""
    query = (
        "SELECT id_user, date FROM services_users"
        f" WHERE id_service = {MEMBERSHIP_SERVICE}"
        f" AND date >= '{since_year:04d}-01-01';"
    )
    result = await run_sql(env, transport, query)
    if not result.ok:
        return ReadResult(False, result.message)
    registrations = [
        (int(row["id_user"]), date.fromisoformat(row["date"][:10]))
        for row in result.rows
    ]
    return ReadResult(True, reading=Reading(without_doublons(registrations), now))


@dataclass(frozen=True)
class Statistics:
    current_year: int
    years: list[int]  # chronological
    monthly: dict[int, list[int | None]]  # None: month without a number
    cumulative: dict[int, list[int | None]]
    total: dict[int, int]
    day: date
    to_date: int
    previous_to_date: int


def statistics(history: Mapping[int, list[int]], reading: Reading) -> Statistics:
    day = reading.day
    current = day.year
    years = list(range(min(history), current + 1))
    monthly: dict[int, list[int | None]] = {}
    for year in years:
        if year in history:
            monthly[year] = list(history[year])
            continue
        counts: list[int | None] = [0] * 12
        for d in reading.dates:
            if d.year == year:
                counts[d.month - 1] += 1
        if year == current:
            counts[day.month :] = [None] * (12 - day.month)
        monthly[year] = counts
    cumulative: dict[int, list[int | None]] = {}
    total = {}
    for year, counts in monthly.items():
        running = 0
        cumul: list[int | None] = []
        for n in counts:
            if n is None:
                cumul.append(None)
            else:
                running += n
                cumul.append(running)
        cumulative[year] = cumul
        total[year] = running
    to_date = sum(1 for d in reading.dates if d.year == current and d <= day)
    previous_to_date = sum(
        1
        for d in reading.dates
        if d.year == current - 1 and (d.month, d.day) <= (day.month, day.day)
    )
    return Statistics(
        current, years, monthly, cumulative, total, day, to_date, previous_to_date
    )


def change_text(new: int, old: int) -> str:
    """Variation from old to new, in percent rounded to the unit."""
    if old == 0:
        return "—"
    percent = Decimal(abs(new - old) * 100) / Decimal(old)
    rounded = int(percent.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if rounded == 0:
        return "0 %"
    return f"{'+' if new > old else '−'}{rounded} %"


def indicator_text(stats: Statistics) -> str:
    year = stats.current_year
    return (
        f"{year} : {stats.to_date} adhésions au {stats.day.day}"
        f" {MONTHS[stats.day.month - 1]},"
        f" {change_text(stats.to_date, stats.previous_to_date)}"
        f" par rapport à {year - 1} à la même date ({stats.previous_to_date})."
    )


def instant_text(instant: datetime) -> str:
    return f"Données Paheko lues le {instant:%d/%m/%Y} à {instant:%H} h {instant:%M}."
