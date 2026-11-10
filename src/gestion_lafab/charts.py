"""Geometry of the charts, drawn as SVG by the templates."""

import math
from dataclasses import dataclass

from gestion_lafab.initiations import CATEGORIES
from gestion_lafab.initiations import Statistics as InitiationStatistics
from gestion_lafab.membership import MONTHS, Statistics

WIDTH = 720
LEFT, RIGHT, TOP, BOTTOM = 44, 64, 16, 32
CUMULATIVE_HEIGHT = 320
ANNUAL_HEIGHT = 220
MONTH_TICKS = [
    "Janv.",
    "Févr.",
    "Mars",
    "Avr.",
    "Mai",
    "Juin",
    "Juil.",
    "Août",
    "Sept.",
    "Oct.",
    "Nov.",
    "Déc.",
]


@dataclass(frozen=True)
class Tick:
    value: str
    x: float
    y: float


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    hover: str


@dataclass(frozen=True)
class Curve:
    year: int
    role: str  # current, previous or older
    points: str  # polyline points
    marks: list[Point]


@dataclass(frozen=True)
class Bar:
    year: int
    x: float
    width: float
    y: float
    bottom: float
    partial: bool
    hover: str
    value: str


@dataclass(frozen=True)
class Chart:
    width: int
    height: int
    left: float
    right: float
    grid: list[Tick]  # horizontal grid lines, labelled on the left
    ticks: list[Tick]  # horizontal axis labels


def nice_max(value: int, step: int) -> int:
    return max(step, math.ceil(value / step) * step)


def scale(top: float, bottom: float, maximum: int):
    return lambda v: bottom - (bottom - top) * v / maximum


def cumulative_chart(stats: Statistics) -> tuple[Chart, list[Curve]]:
    height = CUMULATIVE_HEIGHT
    top, bottom = TOP, height - BOTTOM
    maximum = nice_max(max(stats.total.values()), 50)
    y = scale(top, bottom, maximum)

    def x(month_index: int) -> float:
        return LEFT + (WIDTH - LEFT - RIGHT) * month_index / 11

    grid = [Tick(str(v), LEFT - 6, y(v)) for v in range(0, maximum + 1, 50)]
    ticks = [Tick(label, x(i), height - 10) for i, label in enumerate(MONTH_TICKS)]
    chart = Chart(WIDTH, height, LEFT, WIDTH - RIGHT, grid, ticks)

    def role(year: int) -> str:
        if year == stats.current_year:
            return "current"
        if year == stats.current_year - 1:
            return "previous"
        return "older"

    # Older years first, so that the highlighted curves are drawn on top.
    rank = {"older": 0, "previous": 1, "current": 2}
    order = sorted(stats.years, key=lambda yr: (rank[role(yr)], yr))
    curves = []
    for year in order:
        marks = [
            Point(x(i), y(v), f"{year}, {MONTHS[i]} : {v}")
            for i, v in enumerate(stats.cumulative[year])
            if v is not None
        ]
        points = " ".join(f"{m.x:.1f},{m.y:.1f}" for m in marks)
        curves.append(Curve(year, role(year), points, marks))
    return chart, curves


def annual_chart(stats: Statistics) -> tuple[Chart, list[Bar]]:
    height = ANNUAL_HEIGHT
    top, bottom = TOP + 8, height - BOTTOM + 4
    maximum = nice_max(max(stats.total.values()), 100)
    y = scale(top, bottom, maximum)
    right = WIDTH - 16
    slot = (right - LEFT) / len(stats.years)
    grid = [Tick(str(v), LEFT - 6, y(v)) for v in range(0, maximum + 1, 100)]
    bars = []
    ticks = []
    for k, year in enumerate(stats.years):
        x = LEFT + k * slot + 4
        width = slot - 8
        total = stats.total[year]
        partial = year == stats.current_year
        bars.append(
            Bar(
                year, x, width, y(total), y(0), partial, f"{year} : {total}", str(total)
            )
        )
        ticks.append(Tick(str(year), x + width / 2, height - 10))
    return Chart(WIDTH, height, LEFT, right, grid, ticks), bars


# Initiation charts: bars stacking the categories, bois at the bottom.

INITIATION_HEIGHT = 260


@dataclass(frozen=True)
class Segment:
    category: str
    y: float
    height: float
    hover: str


@dataclass(frozen=True)
class StackedBar:
    x: float
    width: float
    top: float  # y of the top of the bar
    bottom: float
    partial: bool
    value: str
    segments: list[Segment]


def grid_step(maximum: int) -> int:
    """A round step giving at most five grid lines above 0."""
    for step in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000):
        if maximum <= 5 * step:
            return step
    return 10 ** len(str(maximum))


def stacked_chart(
    bars: list[tuple[str, list[int] | None, list[str], bool]],
) -> tuple[Chart, list[StackedBar]]:
    """bars: (axis label, counts by category or None for no bar, hover texts
    by category, partial), in order from left to right."""
    height = INITIATION_HEIGHT
    top, bottom = TOP + 8, height - BOTTOM + 4
    largest = max((sum(c) for _, c, _, _ in bars if c is not None), default=0)
    step = grid_step(largest)
    maximum = nice_max(largest, step)
    y = scale(top, bottom, maximum)
    right = WIDTH - 16
    slot = (right - LEFT) / len(bars)
    grid = [Tick(str(v), LEFT - 6, y(v)) for v in range(0, maximum + 1, step)]
    ticks = []
    drawn = []
    for k, (label, counts, hovers, partial) in enumerate(bars):
        width = min(slot * 0.7, 60)
        x = LEFT + k * slot + (slot - width) / 2
        ticks.append(Tick(label, x + width / 2, height - 10))
        if counts is None:
            continue
        segments = []
        base = 0
        for category, n, hover in zip(CATEGORIES, counts, hovers):
            if n:
                segments.append(
                    Segment(category, y(base + n), y(base) - y(base + n), hover)
                )
            base += n
        drawn.append(StackedBar(x, width, y(base), y(0), partial, str(base), segments))
    return Chart(WIDTH, height, LEFT, right, grid, ticks), drawn


def monthly_initiation_chart(
    stats: InitiationStatistics,
) -> tuple[Chart, list[StackedBar]]:
    """One bar per month of the current year."""
    rows = {row.month: row for row in stats.monthly[stats.current_year]}
    bars = []
    for month in range(1, 13):
        row = rows.get(month)
        hovers = (
            [f"{c}, {row.label} : {n}" for c, n in zip(CATEGORIES, row.counts)]
            if row
            else []
        )
        bars.append(
            (MONTH_TICKS[month - 1], row.counts if row else None, hovers, False)
        )
    return stacked_chart(bars)


def annual_initiation_chart(
    stats: InitiationStatistics,
) -> tuple[Chart, list[StackedBar]]:
    """One bar per year, chronologically."""
    bars = []
    for year in stats.years:
        counts = stats.total[year]
        hovers = [f"{c}, {year} : {n}" for c, n in zip(CATEGORIES, counts)]
        bars.append((str(year), counts, hovers, year == stats.current_year))
    return stacked_chart(bars)
