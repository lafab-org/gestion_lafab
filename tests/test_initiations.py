from datetime import datetime

import httpx
import pytest
from litestar.testing import TestClient

from gestion_lafab.app import create_app
from tests.fakes import (
    DIGITAL,
    ENV,
    METAL,
    NOT_INITIATIONS,
    SOFT,
    URL,
    WOOD,
    Clock,
    FakePaheko,
)
from tests.stats_html import CATEGORIES, InitiationStats, month_label, sse_html

NOW = datetime(2026, 11, 10, 14, 32)
LASER = DIGITAL[0]
ASSEMBLAGE = WOOD[0]
TIG = METAL[1]
COUTURE = SOFT[1]


def initiations(*rows: tuple[int, str]) -> list[tuple[int, int, str]]:
    """Registrations to activities, given as (activity, ISO date), one member
    each."""
    return [(1000 + i, activity, day) for i, (activity, day) in enumerate(rows)]


def read(
    paheko: FakePaheko, now: datetime = NOW, env: dict[str, str] | None = None
) -> InitiationStats:
    app = create_app(dict(ENV) if env is None else env, paheko.transport(), Clock(now))
    with TestClient(app) as client:
        response = client.get("/initiations/lecture")
    assert response.status_code == 200
    return InitiationStats(sse_html(response.text))


def months_down(first: tuple[int, int], last: tuple[int, int]) -> list[str]:
    """Month labels from `first` (year, month) down to `last`, inclusive."""
    (year, month), labels = first, []
    while (year, month) >= last:
        labels.append(month_label(year, month))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    return labels


def row(stats: InitiationStats, year: int, month: int) -> list[str]:
    return stats.cells[month_label(year, month)]


# /operations/lire-les-initiations/ok /ui/page-des-initiations/stats
# /ui/statistiques-des-initiations-affichees/table
def test_ok_shows_statistics(paheko):
    paheko.registrations = initiations(
        (ASSEMBLAGE, "2025-03-04"), (TIG, "2025-03-20"), (LASER, "2026-01-15")
    )
    stats = read(paheko)
    assert stats.months == months_down((2026, 11), (2025, 1))
    assert row(stats, 2025, 3) == ["1", "1", "0", "0", "2"]
    assert row(stats, 2026, 1) == ["0", "0", "0", "1", "1"]


# /operations/lire-les-initiations/ok
def test_ok_replaces_reading(paheko):
    paheko.registrations = initiations((LASER, "2026-03-04"))
    app = create_app(dict(ENV), paheko.transport(), Clock(NOW))
    with TestClient(app) as client:
        first = InitiationStats(sse_html(client.get("/initiations/lecture").text))
        paheko.registrations = initiations((LASER, "2026-03-04"), (LASER, "2026-03-05"))
        second = InitiationStats(sse_html(client.get("/initiations/lecture").text))
    assert row(first, 2026, 3)[3] == "1"
    assert row(second, 2026, 3)[3] == "2"


# /operations/lire-les-initiations/failed /ui/page-des-initiations/stats
@pytest.mark.parametrize(
    ("setup", "message"),
    [
        (
            lambda p, env: env.pop("PAHEKO_API_TOKEN"),
            "Configuration manquante : PAHEKO_API_TOKEN.",
        ),
        (lambda p, env: setattr(p, "status", 403), f"Identifiants refusés par {URL}."),
        (
            lambda p, env: env.update(PAHEKO_API_TOKEN="wrong"),
            f"Identifiants refusés par {URL}.",
        ),
        (
            lambda p, env: setattr(p, "error", httpx.ConnectError("down")),
            f"Impossible de joindre {URL}.",
        ),
        (
            lambda p, env: setattr(p, "error", httpx.ReadTimeout("slow")),
            f"Impossible de joindre {URL}.",
        ),
        (
            lambda p, env: setattr(p, "status", 500),
            f"Réponse inattendue de {URL} : code 500.",
        ),
    ],
)
def test_failed_message(paheko, setup, message):
    paheko.registrations = initiations((LASER, "2026-03-04"))
    env = dict(ENV)
    setup(paheko, env)
    stats = read(paheko, env=env)
    assert message in stats.text
    assert stats.months == []


# /operations/lire-les-initiations/failed
# (that the reading in memory is kept: see test_ui_initiations)
def test_failed_after_success(paheko):
    paheko.registrations = initiations((LASER, "2026-03-04"))
    app = create_app(dict(ENV), paheko.transport(), Clock(NOW))
    with TestClient(app) as client:
        client.get("/initiations/lecture")
        paheko.status = 500
        failed = InitiationStats(sse_html(client.get("/initiations/lecture").text))
    assert f"Réponse inattendue de {URL} : code 500." in failed.text


# /model/categorie-dinitiation /model/initiation
# /model/statistiques-des-initiations
@pytest.mark.parametrize(
    ("activity", "column"),
    [(a, 0) for a in WOOD]
    + [(a, 1) for a in METAL]
    + [(a, 2) for a in SOFT]
    + [(a, 3) for a in DIGITAL],
)
def test_category_of_activity(paheko, activity, column):
    paheko.registrations = initiations((activity, "2026-04-08"))
    stats = read(paheko)
    expected = ["0"] * 4 + ["1"]
    expected[column] = "1"
    assert row(stats, 2026, 4) == expected
    assert stats.has(f"{CATEGORIES[column]}, avril 2026 : 1")
    assert stats.has(f"{CATEGORIES[column]}, 2026 : 1")


# /model/initiation /model/statistiques-des-initiations
def test_other_activities_are_not_initiations(paheko):
    paheko.registrations = initiations(
        *[(activity, "2024-05-02") for activity in NOT_INITIATIONS],
        *[(activity, "2026-05-02") for activity in NOT_INITIATIONS],
    )
    stats = read(paheko)
    # No initiation: the current year only.
    assert stats.months == months_down((2026, 11), (2026, 1))
    assert row(stats, 2026, 5) == ["0"] * 5


# /model/statistiques-des-initiations
def test_no_initiation_current_year_only(paheko):
    stats = read(paheko)
    assert stats.months == months_down((2026, 11), (2026, 1))
    for label in stats.months:
        assert stats.cells[label] == ["0"] * 5


# /model/statistiques-des-initiations
def test_years_from_first_initiation(paheko):
    paheko.registrations = initiations(
        (COUTURE, "2023-06-01"), (LASER, "2026-02-10"), (COUTURE, "2023-08-01")
    )
    stats = read(paheko)
    assert stats.months == months_down((2026, 11), (2023, 1))
    assert row(stats, 2023, 6) == ["0", "0", "1", "0", "1"]
    assert row(stats, 2024, 6) == ["0"] * 5


# /model/lecture-des-initiations
def test_initiations_after_day_excluded(paheko):
    paheko.registrations = initiations(
        (LASER, "2026-11-10"),
        (LASER, "2026-11-11"),
        (TIG, "2026-12-01"),
        (TIG, "2027-01-05"),
    )
    stats = read(paheko)
    assert stats.months[0] == month_label(2026, 11)
    assert row(stats, 2026, 11) == ["0", "0", "0", "1", "1"]
    assert stats.has("numérique, 2026 : 1")
    assert not stats.has("métal, 2026 : 1")


# /model/lecture-des-initiations /model/statistiques-des-initiations
def test_only_future_initiations_means_none(paheko):
    paheko.registrations = initiations((LASER, "2027-02-01"))
    stats = read(paheko)
    assert stats.months == months_down((2026, 11), (2026, 1))


# /model/statistiques-des-initiations
def test_month_boundaries(paheko):
    paheko.registrations = initiations(
        (TIG, "2025-12-31"),
        (TIG, "2026-01-01"),
        (TIG, "2026-01-31"),
        (TIG, "2026-02-01"),
    )
    stats = read(paheko)
    assert row(stats, 2025, 12) == ["0", "1", "0", "0", "1"]
    assert row(stats, 2026, 1) == ["0", "2", "0", "0", "2"]
    assert row(stats, 2026, 2) == ["0", "1", "0", "0", "1"]


# /model/statistiques-des-initiations/futur
# /ui/graphique-mensuel-des-initiations/future
# /ui/tableau-mensuel-des-initiations
def test_future_months(paheko):
    paheko.registrations = initiations((LASER, "2026-02-10"), (TIG, "2025-07-01"))
    stats = read(paheko, now=datetime(2026, 3, 1, 9, 0))
    assert stats.months == months_down((2026, 3), (2025, 1))
    assert stats.has_monthly(2026, 2)
    for month in range(4, 13):
        assert not stats.has_monthly(2026, month), month


# /model/statistiques-des-initiations/futur
# /ui/tableau-mensuel-des-initiations
def test_years_follow_current_year(paheko):
    paheko.registrations = initiations((LASER, "2026-12-20"), (TIG, "2027-01-05"))
    stats = read(paheko, now=datetime(2027, 1, 20, 10, 0))
    assert stats.months == months_down((2027, 1), (2026, 1))
    assert row(stats, 2027, 1) == ["0", "1", "0", "0", "1"]
    assert row(stats, 2026, 12) == ["0", "0", "0", "1", "1"]


# /ui/graphique-mensuel-des-initiations/hover
def test_monthly_hover(paheko):
    paheko.registrations = initiations(
        (ASSEMBLAGE, "2026-03-02"),
        (WOOD[3], "2026-03-20"),
        (TIG, "2026-03-21"),
        (COUTURE, "2026-10-01"),
        (LASER, "2026-11-09"),
    )
    stats = read(paheko)
    assert stats.has("bois, mars 2026 : 2")
    assert stats.has("métal, mars 2026 : 1")
    assert stats.has("souple, octobre 2026 : 1")
    assert stats.has("numérique, novembre 2026 : 1")


# /ui/graphique-mensuel-des-initiations
def test_monthly_chart_current_year_only(paheko):
    paheko.registrations = initiations((ASSEMBLAGE, "2025-03-02"))
    stats = read(paheko)
    assert row(stats, 2025, 3)[0] == "1"
    for month in range(1, 13):
        assert not stats.has_monthly(2025, month), month


# /model/statistiques-des-initiations
# /ui/graphique-annuel-des-initiations/hover
def test_annual_hover(paheko):
    paheko.registrations = initiations(
        (ASSEMBLAGE, "2024-01-15"),
        (WOOD[1], "2024-06-15"),
        (WOOD[6], "2024-12-15"),
        (METAL[2], "2024-12-16"),
        (SOFT[0], "2025-05-05"),
        (DIGITAL[1], "2026-02-02"),
        (LASER, "2026-11-10"),
    )
    stats = read(paheko)
    assert stats.has("bois, 2024 : 3")
    assert stats.has("métal, 2024 : 1")
    assert stats.has("souple, 2025 : 1")
    assert stats.has("numérique, 2026 : 2")


# /ui/tableau-mensuel-des-initiations
# /ui/tableau-mensuel-des-initiations/cells
# /ui/tableau-mensuel-des-initiations/total
def test_table(paheko):
    paheko.registrations = initiations(
        (ASSEMBLAGE, "2026-06-01"),
        (WOOD[2], "2026-06-02"),
        (TIG, "2026-06-03"),
        (COUTURE, "2026-06-04"),
        (LASER, "2026-06-05"),
        (DIGITAL[1], "2026-06-06"),
        (DIGITAL[1], "2026-06-07"),
        (TIG, "2026-07-01"),
    )
    stats = read(paheko)
    assert stats.header == CATEGORIES + ["Total"]
    assert row(stats, 2026, 6) == ["2", "1", "1", "3", "7"]
    assert row(stats, 2026, 7) == ["0", "1", "0", "0", "1"]
    assert row(stats, 2026, 5) == ["0"] * 5
