from collections.abc import Mapping
from dataclasses import dataclass, field

import httpx

from gestion_lafab.config import missing_variables

TIMEOUT = 10.0


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    message: str


@dataclass(frozen=True)
class SqlResult:
    """Rows of a query, or the message explaining why there are none."""

    ok: bool
    message: str = ""
    rows: list[dict] = field(default_factory=list)
    answered: bool = False  # the API accepted the query (status 200)


async def run_sql(
    env: Mapping[str, str], transport: httpx.AsyncBaseTransport | None, query: str
) -> SqlResult:
    """Run a read-only query through the SQL API of Paheko."""
    missing = missing_variables(env)
    if missing:
        return SqlResult(False, f"Configuration manquante : {', '.join(missing)}.")
    url = env["PAHEKO_URL"]
    try:
        async with httpx.AsyncClient(
            base_url=url,
            auth=(env["PAHEKO_API_ID"], env["PAHEKO_API_TOKEN"]),
            transport=transport,
            timeout=TIMEOUT,
        ) as client:
            response = await client.post("/api/sql/", content=query)
    except (httpx.TransportError, httpx.InvalidURL):
        return SqlResult(False, f"Impossible de joindre {url}.")
    if response.status_code in (401, 403):
        return SqlResult(False, f"Identifiants refusés par {url}.")
    if response.status_code != 200:
        return SqlResult(
            False, f"Réponse inattendue de {url} : code {response.status_code}."
        )
    try:
        rows = response.json()["results"]
        if not isinstance(rows, list):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        return SqlResult(
            False, f"Réponse inattendue de {url} : code 200.", answered=True
        )
    return SqlResult(True, rows=rows, answered=True)


async def check_connection(
    env: Mapping[str, str], transport: httpx.AsyncBaseTransport | None
) -> CheckResult:
    """Run a trivial read-only query against the Paheko API."""
    result = await run_sql(env, transport, "SELECT 1;")
    if result.answered:
        return CheckResult(True, f"Connecté à {env['PAHEKO_URL']}.")
    return CheckResult(False, result.message)
