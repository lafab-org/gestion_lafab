"""Geometry of the membership charts, drawn as SVG by the templates."""

import math
from dataclasses import dataclass

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
