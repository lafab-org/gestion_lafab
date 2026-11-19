"""Initiation statistics: Paheko registrations to initiation activities."""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from itertools import combinations

import httpx

from gestion_lafab.membership import MONTHS
from gestion_lafab.paheko import Member, run_sql, to_member

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
    activity: int = 0
    member: Member | None = None
    id: int = 0  # of the registration in Paheko


@dataclass(frozen=True)
class Reading:
    """Initiations read from Paheko, dated up to the day of the reading."""

    initiations: list[Initiation]
    instant: datetime
    labels: dict[int, str] = field(default_factory=dict)  # by activity

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
        "SELECT su.id, su.id_user, su.id_service, su.date, s.label,"
        " u.numero, u.prenom, u.nom"
        " FROM services_users su"
        " LEFT JOIN services s ON s.id = su.id_service"
        " LEFT JOIN users u ON u.id = su.id_user"
        f" WHERE su.id_service IN ({activities});"
    )
    result = await run_sql(env, transport, query)
    if not result.ok:
        return ReadResult(False, result.message)
    initiations = []
    labels: dict[int, str] = {}
    members: dict[int, Member] = {}
    for row in result.rows:
        activity = int(row["id_service"])
        category = CATEGORY_OF_ACTIVITY.get(activity)
        day = date.fromisoformat(str(row["date"])[:10])
        if category is None or day > now.date():
            continue
        if row.get("label"):
            labels[activity] = str(row["label"])
        user = int(row["id_user"])
        if user not in members:
            members[user] = to_member(row, "id_user")
        initiations.append(
            Initiation(day, category, activity, members[user], int(row["id"]))
        )
    return ReadResult(True, reading=Reading(initiations, now, labels))


@dataclass(frozen=True)
class Duplicate:
    member: Member
    activity: int
    first: Initiation
    second: Initiation


def one_year_after(day: date) -> date:
    try:
        return day.replace(year=day.year + 1)
    except ValueError:  # 29 February
        return date(day.year + 1, 3, 1)


def duplicates(reading: Reading) -> list[Duplicate]:
    """Pairs of initiations of a member to an activity less than a year
    apart, the most recent second first."""
    groups: dict[tuple[Member, int], list[Initiation]] = defaultdict(list)
    for i in reading.initiations:
        if i.member is not None:
            groups[(i.member, i.activity)].append(i)
    found = [
        Duplicate(member, activity, first, second)
        for (member, activity), group in groups.items()
        for first, second in combinations(sorted(group, key=lambda i: i.day), 2)
        if second.day < one_year_after(first.day)
    ]
    return sorted(found, key=lambda d: (d.second.day, d.first.day), reverse=True)


@dataclass(frozen=True)
class MemberCount:
    member: Member
    activities: list[int]  # distinct activities, by category, in CATEGORIES order

    @property
    def total(self) -> int:
        return sum(self.activities)


def by_member(reading: Reading) -> list[MemberCount]:
    """Members with at least one initiation, the most distinct activities
    first."""
    activities: dict[Member, set[tuple[str, int]]] = defaultdict(set)
    for i in reading.initiations:
        if i.member is not None:
            activities[i.member].add((i.category, i.activity))
    counts = [
        MemberCount(
            member,
            [sum(1 for c, _ in found if c == category) for category in CATEGORIES],
        )
        for member, found in activities.items()
    ]
    return sorted(counts, key=lambda c: c.total, reverse=True)


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
