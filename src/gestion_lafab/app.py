from collections.abc import Mapping

import httpx
from litestar import Litestar


def create_app(
    env: Mapping[str, str] | None = None,
    paheko_transport: httpx.AsyncBaseTransport | None = None,
) -> Litestar:
    """Build the application.

    env: configuration variables; read from `.env` and the environment when None.
    paheko_transport: transport for Paheko API calls; the network when None.
    """
    return Litestar(route_handlers=[])
