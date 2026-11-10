from collections.abc import Mapping
from dataclasses import dataclass

import httpx

from gestion_lafab.config import missing_variables

TIMEOUT = 10.0


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    message: str


async def check_connection(
    env: Mapping[str, str], transport: httpx.AsyncBaseTransport | None
) -> CheckResult:
    """Run a trivial read-only query against the Paheko API."""
    missing = missing_variables(env)
    if missing:
        return CheckResult(False, f"Configuration manquante : {', '.join(missing)}.")
    url = env["PAHEKO_URL"]
    try:
        async with httpx.AsyncClient(
            base_url=url,
            auth=(env["PAHEKO_API_ID"], env["PAHEKO_API_TOKEN"]),
            transport=transport,
            timeout=TIMEOUT,
        ) as client:
            response = await client.post("/api/sql/", content="SELECT 1;")
    except (httpx.TransportError, httpx.InvalidURL):
        return CheckResult(False, f"Impossible de joindre {url}.")
    if response.status_code == 200:
        return CheckResult(True, f"Connecté à {url}.")
    if response.status_code in (401, 403):
        return CheckResult(False, f"Identifiants refusés par {url}.")
    return CheckResult(
        False, f"Réponse inattendue de {url} : code {response.status_code}."
    )
