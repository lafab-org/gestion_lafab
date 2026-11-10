from datetime import datetime

import httpx
import pytest
from litestar.testing import TestClient

from gestion_lafab.app import create_app
from tests.fakes import ENV, MEMBERSHIP, OTHER_SERVICE, URL, Clock, FakePaheko
from tests.stats_html import Stats, sse_html

NOW = datetime(2026, 11, 10, 14, 32)

# The hand-compiled history, January to December.
HISTORY = {
    2016: [16, 8, 9, 36, 18, 3, 5, 2, 19, 24, 24, 21],
    2017: [10, 17, 17, 25, 9, 22, 10, 9, 23, 26, 24, 20],
    2018: [17, 29, 22, 22, 18, 20, 36, 17, 13, 25, 26, 12],
    2019: [20, 11, 20, 17, 23, 28, 18, 8, 19, 23, 23, 30],
    2020: [21, 31, 10, 1, 9, 31, 22, 6, 47, 43, 14, 40],
    2021: [18, 9, 25, 10, 17, 21, 12, 3, 16, 43, 34, 37],
    2022: [30, 25, 25, 39, 27, 31, 23, 3, 34, 39, 32, 13],
}


def adhesions(*dates: str, user: int | None = None) -> list[tuple[int, int, str]]:
    """Membership registrations, one member each unless `user` is given."""
    rows = []
    for i, date in enumerate(dates):
        rows.append((user if user is not None else 1000 + i, MEMBERSHIP, date))
    return rows


def read(
    paheko: FakePaheko, now: datetime = NOW, env: dict[str, str] | None = None
) -> tuple[httpx.Response, Stats]:
    app = create_app(dict(ENV) if env is None else env, paheko.transport(), Clock(now))
    with TestClient(app) as client:
        response = client.get("/adhesions/lecture")
    assert response.status_code == 200
    return response, Stats(sse_html(response.text))


def month_count(stats: Stats, year: int, month: int) -> str:
    return stats.monthly[year][month - 1]


# /operations/lire-les-adhesions/ok /ui/page-des-adhesions/stats
# /model/statistiques-des-adhesions/paheko
def test_ok_shows_statistics(paheko):
    paheko.registrations = adhesions("2025-03-04", "2025-03-20", "2026-01-15")
    _, stats = read(paheko)
    assert stats.years == list(range(2026, 2015, -1))
    assert month_count(stats, 2025, 3) == "2"
    assert month_count(stats, 2026, 1) == "1"
    assert stats.total[2025] == "2"


# /operations/lire-les-adhesions/ok /ui/page-des-adhesions/stats
def test_ok_replaces_reading(paheko):
    paheko.registrations = adhesions("2025-03-04")
    app = create_app(dict(ENV), paheko.transport(), Clock(NOW))
    with TestClient(app) as client:
        first = Stats(sse_html(client.get("/adhesions/lecture").text))
        paheko.registrations = adhesions("2025-03-04", "2025-03-05")
        second = Stats(sse_html(client.get("/adhesions/lecture").text))
    assert month_count(first, 2025, 3) == "1"
    assert month_count(second, 2025, 3) == "2"


# /operations/lire-les-adhesions/failed
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
    env = dict(ENV)
    setup(paheko, env)
    _, stats = read(paheko, env=env)
    assert message in stats.text
    assert stats.years == []


# /operations/lire-les-adhesions/failed
# (that the reading in memory is kept: see test_ui_membership)
def test_failed_after_success(paheko):
    paheko.registrations = adhesions("2025-03-04")
    app = create_app(dict(ENV), paheko.transport(), Clock(NOW))
    with TestClient(app) as client:
        client.get("/adhesions/lecture")
        paheko.status = 500
        failed = Stats(sse_html(client.get("/adhesions/lecture").text))
    assert f"Réponse inattendue de {URL} : code 500." in failed.text


# /model/statistiques-des-adhesions/historique
def test_history(paheko):
    paheko.registrations = adhesions("2022-05-10", "2021-01-03", "2016-04-01")
    _, stats = read(paheko)
    for year, months in HISTORY.items():
        assert stats.monthly[year] == [str(n) for n in months], year
        assert stats.total[year] == str(sum(months)), year


# /model/statistiques-des-adhesions/paheko
def test_paheko_counts_membership_only(paheko):
    paheko.registrations = adhesions("2024-06-01", "2024-06-30") + [
        (2000, OTHER_SERVICE, "2024-06-15"),
        (2001, OTHER_SERVICE, "2024-07-15"),
    ]
    _, stats = read(paheko)
    assert month_count(stats, 2024, 6) == "2"
    assert month_count(stats, 2024, 7) == "0"
    assert stats.total[2024] == "2"


# /model/statistiques-des-adhesions/paheko
def test_paheko_month_boundaries(paheko):
    paheko.registrations = adhesions(
        "2023-01-01", "2023-01-31", "2023-02-01", "2023-12-31", "2024-01-01"
    )
    _, stats = read(paheko)
    assert stats.monthly[2023] == ["2", "1"] + ["0"] * 9 + ["1"]
    assert month_count(stats, 2024, 1) == "1"
    assert stats.total[2023] == "4"


# /model/statistiques-des-adhesions/paheko
# /model/statistiques-des-adhesions/futur
def test_current_year(paheko):
    paheko.registrations = adhesions("2026-01-10", "2026-11-02", "2026-11-09")
    _, stats = read(paheko)
    assert stats.monthly[2026] == ["1"] + ["0"] * 9 + ["2", ""]
    assert stats.total[2026] == "3"


# /model/statistiques-des-adhesions/futur
def test_future_months_in_other_month(paheko):
    paheko.registrations = adhesions("2026-02-10")
    _, stats = read(paheko, now=datetime(2026, 3, 1, 9, 0))
    assert stats.monthly[2026] == ["0", "1", "0"] + [""] * 9
    assert stats.monthly[2025] == ["0"] * 12


# /model/statistiques-des-adhesions/futur
def test_years_follow_current_year(paheko):
    paheko.registrations = adhesions("2027-01-05")
    _, stats = read(paheko, now=datetime(2027, 1, 20, 10, 0))
    assert stats.years == list(range(2027, 2015, -1))
    assert stats.monthly[2027] == ["1"] + [""] * 11


# /model/adhesion/doublon
def test_doublon_within_30_days(paheko):
    paheko.registrations = adhesions("2025-04-27", "2025-04-28", user=7)
    _, stats = read(paheko)
    assert month_count(stats, 2025, 4) == "1"


# /model/adhesion/doublon
def test_doublon_30_days_is_not(paheko):
    paheko.registrations = adhesions("2025-01-01", "2025-01-31", user=7)
    _, stats = read(paheko)
    assert month_count(stats, 2025, 1) == "2"


# /model/adhesion/doublon
def test_doublon_29_days_across_months(paheko):
    paheko.registrations = adhesions("2025-01-10", "2025-02-08", user=7)
    _, stats = read(paheko)
    assert month_count(stats, 2025, 1) == "1"
    assert month_count(stats, 2025, 2) == "0"


# /model/adhesion/doublon
def test_doublon_measured_from_counted_adhesion(paheko):
    # 01-01 counts; 01-25 is a doublon; 02-15 is 45 days after 01-01: counts,
    # though 21 days after the doublon; 03-01 is 14 days after 02-15: doublon.
    paheko.registrations = adhesions(
        "2025-01-01", "2025-01-25", "2025-02-15", "2025-03-01", user=7
    )
    _, stats = read(paheko)
    assert stats.monthly[2025][:3] == ["1", "1", "0"]


# /model/adhesion/doublon
def test_doublon_other_members_count(paheko):
    paheko.registrations = adhesions("2025-05-30", "2025-05-30", "2025-05-31")
    _, stats = read(paheko)
    assert month_count(stats, 2025, 5) == "3"


# /model/adhesion/doublon
def test_doublon_across_years(paheko):
    paheko.registrations = adhesions("2025-12-20", "2026-01-05", user=7)
    _, stats = read(paheko)
    assert month_count(stats, 2025, 12) == "1"
    assert month_count(stats, 2026, 1) == "0"
    assert stats.total[2026] == "0"


# /model/adhesion/doublon
def test_doublon_unordered_rows(paheko):
    paheko.registrations = adhesions("2025-06-20", user=7) + adhesions(
        "2025-06-01", user=7
    )
    _, stats = read(paheko)
    assert month_count(stats, 2025, 6) == "1"


# /ui/indicateur/text
def test_indicator_increase(paheko):
    paheko.registrations = adhesions(
        "2025-01-10", "2025-06-01", "2025-11-10", "2025-11-11", "2025-12-01",
        "2026-01-05", "2026-02-05", "2026-03-05", "2026-11-10",
    )  # fmt: skip
    _, stats = read(paheko)
    # 2026 to 10/11 inclusive: 4; 2025 to 10/11 inclusive: 3.
    assert (
        "2026 : 4 adhésions au 10 novembre, +33 % par rapport à 2025"
        " à la même date (3)." in stats.text
    )


# /ui/indicateur/text
def test_indicator_decrease(paheko):
    paheko.registrations = adhesions(
        "2025-01-10", "2025-02-10", "2025-03-10", "2025-04-10", "2026-02-01",
        "2026-03-01", "2026-11-11",
    )  # fmt: skip
    _, stats = read(paheko)
    assert (
        "2026 : 2 adhésions au 10 novembre, −50 % par rapport à 2025"
        " à la même date (4)." in stats.text
    )


# /ui/indicateur/text
def test_indicator_equal(paheko):
    paheko.registrations = adhesions("2025-07-14", "2026-03-03")
    _, stats = read(paheko, now=datetime(2026, 7, 14, 18, 5))
    assert (
        "2026 : 1 adhésions au 14 juillet, 0 % par rapport à 2025"
        " à la même date (1)." in stats.text
    )


# /ui/indicateur/text
def test_indicator_excludes_doublons(paheko):
    # 2025 to 10/11: 4 adhésions, the doublon of 05-02 excluded; 2026: 4.
    paheko.registrations = (
        adhesions("2025-02-01", "2025-03-01", "2025-04-01")
        + adhesions("2025-05-01", "2025-05-02", user=7)
        + adhesions("2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04")
    )
    _, stats = read(paheko)
    assert (
        "2026 : 4 adhésions au 10 novembre, 0 % par rapport à 2025"
        " à la même date (4)." in stats.text
    )


# /ui/indicateur/text
def test_indicator_rounds_to_unit(paheko):
    # 7 against 6: +16.7 % rounds to +17 %.
    paheko.registrations = adhesions(*[f"2025-0{m}-01" for m in range(1, 7)]) + (
        adhesions(*[f"2026-0{m}-02" for m in range(1, 8)])
    )
    _, stats = read(paheko)
    assert "+17 % par rapport à 2025 à la même date (6)." in stats.text


# /ui/graphique-du-cumul/hover
def test_cumulative_hover(paheko):
    paheko.registrations = adhesions("2025-01-10", "2025-03-10", "2025-03-11")
    _, stats = read(paheko)
    assert stats.has_hover(2025, 1, 1)
    assert stats.has_hover(2025, 2, 1)
    assert stats.has_hover(2025, 3, 3)
    assert stats.has_hover(2025, 12, 3)
    assert stats.has_hover(2016, 1, 16)
    assert stats.has_hover(2016, 4, 69)
    assert stats.has_hover(2022, 12, 321)


# /ui/graphique-du-cumul/current
def test_cumulative_current_stops(paheko):
    paheko.registrations = adhesions("2026-01-10", "2026-11-09")
    _, stats = read(paheko)
    assert stats.has_hover(2026, 10, 1)
    assert stats.has_hover(2026, 11, 2)
    assert not stats.has_any_hover(2026, 12)


# /ui/graphique-annuel/hover
def test_annual_hover(paheko):
    paheko.registrations = adhesions("2025-01-10", "2025-03-10", "2026-04-01")
    _, stats = read(paheko)
    assert stats.has_bar(2025, 2)
    assert stats.has_bar(2026, 1)
    assert stats.has_bar(2018, 257)


# /ui/tableau-mensuel/cells /ui/tableau-mensuel/total
def test_table(paheko):
    paheko.registrations = adhesions("2024-08-05", "2024-08-06", "2026-06-01")
    _, stats = read(paheko)
    assert stats.years == list(range(2026, 2015, -1))
    assert stats.monthly[2024] == ["0"] * 7 + ["2"] + ["0"] * 4
    assert stats.total[2024] == "2"
    assert stats.monthly[2026][10:] == ["0", ""]
    assert stats.total[2026] == "1"


# /ui/indicateur/no-previous
def test_indicator_no_previous(paheko):
    paheko.registrations = adhesions("2025-12-01", "2026-01-05")
    _, stats = read(paheko)
    assert (
        "2026 : 1 adhésions au 10 novembre, — par rapport à 2025"
        " à la même date (0)." in stats.text
    )
