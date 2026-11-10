from collections.abc import AsyncIterator, Callable, Mapping
from datetime import datetime
from html import escape
from pathlib import Path

import httpx
from datastar_py.litestar import DatastarResponse
from datastar_py.litestar import ServerSentEventGenerator as SSE
from litestar import Litestar, get
from litestar.plugins.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

from gestion_lafab.config import read_env
from gestion_lafab.paheko import check_connection

PACKAGE_DIR = Path(__file__).parent
CHECKING = "Test en cours…"


def status_html(message: str, css_class: str) -> str:
    return (
        f'<p id="connection-status" class="{css_class}">'
        f"{escape(message, quote=False)}</p>"
    )


def create_app(
    env: Mapping[str, str] | None = None,
    paheko_transport: httpx.AsyncBaseTransport | None = None,
    now: Callable[[], datetime] = datetime.now,
) -> Litestar:
    """Build the application.

    env: configuration variables; read from `.env` and the environment when None.
    paheko_transport: transport for Paheko API calls; the network when None.
    now: the current local date and time.
    """

    def current_env() -> Mapping[str, str]:
        return env if env is not None else read_env()

    @get("/")
    async def home() -> Template:
        return Template(
            template_name="home.html", context={"status": status_html(CHECKING, "")}
        )

    @get("/connexion")
    async def connexion() -> DatastarResponse:
        async def events() -> AsyncIterator[str]:
            yield SSE.patch_signals({"checking": True})
            yield SSE.patch_elements(status_html(CHECKING, ""))
            result = await check_connection(current_env(), paheko_transport)
            yield SSE.patch_elements(
                status_html(result.message, "ok" if result.ok else "error")
            )
            yield SSE.patch_signals({"checking": False})

        return DatastarResponse(events())

    return Litestar(
        route_handlers=[
            home,
            connexion,
            create_static_files_router(
                path="/static", directories=[PACKAGE_DIR / "static"]
            ),
        ],
        template_config=TemplateConfig(
            directory=PACKAGE_DIR / "templates", engine=JinjaTemplateEngine
        ),
    )
