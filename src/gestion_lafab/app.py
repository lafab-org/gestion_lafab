from collections.abc import AsyncIterator, Callable, Mapping
from datetime import datetime
from html import escape
from pathlib import Path

import httpx
from datastar_py.litestar import DatastarResponse
from datastar_py.litestar import ServerSentEventGenerator as SSE
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar import Litestar, MediaType, Request, Response, get, post
from litestar.exceptions import NotFoundException
from litestar.plugins.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

from gestion_lafab import initiations, reconciliation
from gestion_lafab.charts import (
    MONTH_TICKS,
    annual_chart,
    annual_initiation_chart,
    cumulative_chart,
    monthly_initiation_chart,
)
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
RECONCILING = "Rapprochement…"
NO_EXPORT = "Aucun export des tickets envoyé : ventes de la caisse seulement."


def previous_month(day: datetime) -> tuple[int, int]:
    return (day.year, day.month - 1) if day.month > 1 else (day.year - 1, 12)


def parse_month(value: object, default: tuple[int, int]) -> tuple[int, int]:
    """`AAAA-MM` from the month input; the default if it is not one."""
    try:
        year, month = (int(part) for part in str(value).split("-"))
    except ValueError:
        return default
    return (year, month) if 1 <= month <= 12 and 1 <= year <= 9999 else default


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
    # The Lecture des initiations, likewise.
    initiation_memory: dict[str, initiations.Reading] = {}
    # The Rapprochement des initiations, likewise.
    reconciliation_memory: dict[str, reconciliation.Reconciliation] = {}

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

    def initiations_stats_html() -> str:
        reading = initiation_memory.get("reading")
        context: dict = {"stats": None, "categories": initiations.CATEGORIES}
        if reading is not None:
            stats = initiations.statistics(reading)
            monthly_chart, monthly_bars = monthly_initiation_chart(stats)
            annual, annual_bars = annual_initiation_chart(stats)
            context.update(
                stats=stats,
                monthly_chart=monthly_chart,
                monthly_bars=monthly_bars,
                annual_chart=annual,
                annual_bars=annual_bars,
            )
        return templates.get_template("initiations_stats.html").render(context)

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

    @get("/initiations", media_type=MediaType.HTML)
    async def initiations_page() -> Response[str]:
        reading = initiation_memory.get("reading")
        if reading is None:
            status = reading_status_html(READING, "")
        else:
            status = reading_status_html(instant_text(reading.instant), "read")
        page = templates.get_template("initiations.html").render(
            init=reading is None, status=status, stats=initiations_stats_html()
        )
        return Response(page, media_type=MediaType.HTML)

    @get("/initiations/lecture")
    async def initiations_lecture() -> DatastarResponse:
        async def events() -> AsyncIterator[str]:
            yield SSE.patch_signals({"reading": True})
            yield SSE.patch_elements(reading_status_html(READING, ""))
            result = await initiations.read_initiations(
                current_env(), paheko_transport, now()
            )
            if result.ok and result.reading is not None:
                initiation_memory["reading"] = result.reading
                yield SSE.patch_elements(
                    reading_status_html(instant_text(result.reading.instant), "read")
                )
                yield SSE.patch_elements(initiations_stats_html())
            else:
                yield SSE.patch_elements(reading_status_html(result.message, "error"))
            yield SSE.patch_signals({"reading": False})

        return DatastarResponse(events())

    def reconciliation_html(
        message: str = "",
        css_class: str = "",
        result: reconciliation.Reconciliation | None = None,
        no_export: bool = False,
    ) -> str:
        return templates.get_template("reconciliation_result.html").render(
            message=message,
            css_class=css_class,
            result=result,
            lines=list(zip(result.lines, result.rows())) if result else [],
            no_export=no_export,
            no_export_text=NO_EXPORT,
        )

    @get("/initiations/rapprochement", media_type=MediaType.HTML)
    async def reconciliation_page() -> Response[str]:
        year, month = previous_month(now())
        page = templates.get_template("reconciliation.html").render(
            month=f"{year:04d}-{month:02d}", result=reconciliation_html()
        )
        return Response(page, media_type=MediaType.HTML)

    @post("/initiations/rapprochement", status_code=200)
    async def reconciliation_run(request: Request) -> DatastarResponse:
        # Parsed in memory: the export is never written to disk.
        form = reconciliation.read_form(
            request.headers.get("content-type", ""), await request.body()
        )
        month_field = form.get("mois", (None, b""))[1].decode("utf-8", "replace")
        year, month = parse_month(month_field, previous_month(now()))
        filename, content = form.get("export", (None, b""))
        sent = bool(filename) or bool(content)

        async def events() -> AsyncIterator[str]:
            try:
                async for event in reconcile_events():
                    yield event
            except Exception:
                yield SSE.patch_elements(reconciliation_html())
                yield SSE.patch_signals({"running": False})
                raise

        async def reconcile_events() -> AsyncIterator[str]:
            yield SSE.patch_signals({"running": True})
            yield SSE.patch_elements(reconciliation_html(RECONCILING, "muted"))
            tickets = reconciliation.parse_export(content) if sent else None
            if sent and tickets is None:
                yield SSE.patch_elements(
                    reconciliation_html(reconciliation.UNREADABLE, "error")
                )
            else:
                result = await reconciliation.reconcile(
                    current_env(), paheko_transport, year, month, tickets
                )
                if result.ok and result.reconciliation is not None:
                    reconciliation_memory["last"] = result.reconciliation
                    yield SSE.patch_elements(
                        reconciliation_html(
                            result=result.reconciliation, no_export=not sent
                        )
                    )
                else:
                    yield SSE.patch_elements(
                        reconciliation_html(result.message, "error")
                    )
            yield SSE.patch_signals({"running": False})

        return DatastarResponse(events())

    @get("/initiations/rapprochement.csv")
    async def reconciliation_csv() -> Response[bytes]:
        last = reconciliation_memory.get("last")
        if last is None:
            raise NotFoundException()
        return Response(
            last.csv().encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{last.filename}"'},
        )

    return Litestar(
        route_handlers=[
            home,
            connexion,
            adhesions,
            adhesions_lecture,
            initiations_page,
            initiations_lecture,
            reconciliation_page,
            reconciliation_run,
            reconciliation_csv,
            create_static_files_router(
                path="/static", directories=[PACKAGE_DIR / "static"]
            ),
        ],
        template_config=TemplateConfig(
            directory=PACKAGE_DIR / "templates", engine=JinjaTemplateEngine
        ),
    )
