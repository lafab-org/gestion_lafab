import httpx
import pytest
from litestar.testing import TestClient

from gestion_lafab.app import create_app
from tests.fakes import ENV, URL, FakePaheko


def check(env: dict[str, str], paheko: FakePaheko) -> httpx.Response:
    app = create_app(env, paheko.transport())
    with TestClient(app) as client:
        response = client.get("/connexion")
    assert response.status_code == 200
    return response


# /operations/tester-la-connexion/ok
def test_ok(paheko):
    response = check(dict(ENV), paheko)
    assert f"Connecté à {URL}." in response.text
    assert paheko.calls >= 1


# /operations/tester-la-connexion/ok
def test_ok_with_other_url(paheko):
    env = dict(ENV, PAHEKO_URL="https://autre.paheko.cloud")
    response = check(env, paheko)
    assert "Connecté à https://autre.paheko.cloud." in response.text


# /operations/tester-la-connexion/config
@pytest.mark.parametrize(
    ("absent", "listed"),
    [
        (["PAHEKO_URL"], "PAHEKO_URL"),
        (["PAHEKO_API_ID"], "PAHEKO_API_ID"),
        (["PAHEKO_API_TOKEN"], "PAHEKO_API_TOKEN"),
        (["PAHEKO_API_TOKEN", "PAHEKO_URL"], "PAHEKO_URL, PAHEKO_API_TOKEN"),
        (
            ["PAHEKO_URL", "PAHEKO_API_ID", "PAHEKO_API_TOKEN"],
            "PAHEKO_URL, PAHEKO_API_ID, PAHEKO_API_TOKEN",
        ),
    ],
)
def test_config_absent(paheko, absent, listed):
    env = {k: v for k, v in ENV.items() if k not in absent}
    response = check(env, paheko)
    assert f"Configuration manquante : {listed}." in response.text
    assert "Connecté" not in response.text


# /operations/tester-la-connexion/config
def test_config_empty(paheko):
    env = dict(ENV, PAHEKO_API_ID="")
    response = check(env, paheko)
    assert "Configuration manquante : PAHEKO_API_ID." in response.text


# /operations/tester-la-connexion/refused
def test_refused_wrong_credentials(paheko):
    env = dict(ENV, PAHEKO_API_TOKEN="wrong")
    response = check(env, paheko)
    assert f"Identifiants refusés par {URL}." in response.text
    assert "Connecté" not in response.text


# /operations/tester-la-connexion/refused
@pytest.mark.parametrize("status", [401, 403])
def test_refused_status(paheko, status):
    paheko.status = status
    response = check(dict(ENV), paheko)
    assert f"Identifiants refusés par {URL}." in response.text


# /operations/tester-la-connexion/unreachable
@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("network down"),
        httpx.ConnectError("[Errno -2] Name or service not known"),
        httpx.ConnectTimeout("timed out"),
        httpx.ReadTimeout("timed out"),
    ],
)
def test_unreachable(paheko, error):
    paheko.error = error
    response = check(dict(ENV), paheko)
    assert f"Impossible de joindre {URL}." in response.text
    assert "Connecté" not in response.text


# /operations/tester-la-connexion/unexpected
@pytest.mark.parametrize("status", [302, 404, 500, 502])
def test_unexpected(paheko, status):
    paheko.status = status
    response = check(dict(ENV), paheko)
    assert f"Réponse inattendue de {URL} : code {status}." in response.text
    assert "Connecté" not in response.text


# /operations/etat-initial/vide
def test_initial_state_nothing_in_memory(paheko):
    paheko.registrations = [(7, 1, "2026-03-04"), (8, 23, "2026-03-04")]
    app = create_app(dict(ENV), paheko.transport())
    with TestClient(app) as client:
        adhesions = client.get("/adhesions").text
        initiations = client.get("/initiations").text
        csv = client.get("/initiations/rapprochement.csv")
    assert "Données Paheko lues le" not in adhesions
    assert "Cumul mensuel" not in adhesions
    assert "Données Paheko lues le" not in initiations
    assert "Initiations par année" not in initiations
    assert csv.status_code == 404
