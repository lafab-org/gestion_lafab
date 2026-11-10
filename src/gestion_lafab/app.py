from collections.abc import AsyncIterator, Callable, Mapping
from datetime import datetime
from html import escape
from pathlib import Path

import httpx
from datastar_py.litestar import DatastarResponse
from datastar_py.litestar import ServerSentEventGenerator as SSE
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import Litestar, MediaType, Response, get
from litestar.plugins.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

from gestion_lafab.charts import MONTH_TICKS, annual_chart, cumulative_chart
from gestion_lafab.config import read_env
from gestion_lafab.membership import (
    Reading,
    indicator_text,
    instant_text,
    load_history,
    read_memberships,
    statistics,
)
from gestion_lafab.paheko import check_connection

PACKAGE_DIR = Path(__file__).parent
CHECKING = "Test en cours…"
READING = "Lecture de Paheko…"


def status_html(message: str, css_class: str) -> str:
    return (
        f'<p id="connection-status" class="{css_class}">'
        f"{escape(message, quote=False)}</p>"
    )


def reading_status_html(message: str, css_class: str) -> str:
    return (
        f'<p id="reading-status" class="{css_class}">{escape(message, quote=False)}</p>'
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
    templates = Environment(
        loader=FileSystemLoader(PACKAGE_DIR / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    history = load_history()
    # The Lecture Paheko kept in memory while the application runs.
    memory: dict[str, Reading] = {}

    def current_env() -> Mapping[str, str]:
        return env if env is not None else read_env()

    def stats_html() -> str:
        reading = memory.get("reading")
        context: dict = {"stats": None}
        if reading is not None:
            stats = statistics(history, reading)
            cumul_chart, curves = cumulative_chart(stats)
            annual, bars = annual_chart(stats)
            context = {
                "stats": stats,
                "indicator": indicator_text(stats),
                "cumul_chart": cumul_chart,
                "curves": curves,
                "annual_chart": annual,
                "bars": bars,
                "month_ticks": MONTH_TICKS,
            }
        return templates.get_template("membership_stats.html").render(context)

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

    @get("/adhesions", media_type=MediaType.HTML)
    async def adhesions() -> Response[str]:
        reading = memory.get("reading")
        if reading is None:
            status = reading_status_html(READING, "")
        else:
            status = reading_status_html(instant_text(reading.instant), "read")
        page = templates.get_template("membership.html").render(
            init=reading is None, status=status, stats=stats_html()
        )
        return Response(page, media_type=MediaType.HTML)

    @get("/adhesions/lecture")
    async def adhesions_lecture() -> DatastarResponse:
        async def events() -> AsyncIterator[str]:
            yield SSE.patch_signals({"reading": True})
            yield SSE.patch_elements(reading_status_html(READING, ""))
            result = await read_memberships(
                current_env(), paheko_transport, now(), max(history) + 1
            )
            if result.ok and result.reading is not None:
                memory["reading"] = result.reading
                yield SSE.patch_elements(
                    reading_status_html(instant_text(result.reading.instant), "read")
                )
                yield SSE.patch_elements(stats_html())
            else:
                yield SSE.patch_elements(reading_status_html(result.message, "error"))
            yield SSE.patch_signals({"reading": False})

        return DatastarResponse(events())

    return Litestar(
        route_handlers=[
            home,
            connexion,
            adhesions,
            adhesions_lecture,
            create_static_files_router(
                path="/static", directories=[PACKAGE_DIR / "static"]
            ),
        ],
        template_config=TemplateConfig(
            directory=PACKAGE_DIR / "templates", engine=JinjaTemplateEngine
        ),
    )
