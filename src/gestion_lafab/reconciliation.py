"""Rapprochement des initiations: initiation sales of a month missing in Paheko."""

import csv
import email.policy
import io
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from email.parser import BytesParser
from urllib.parse import parse_qsl

import httpx

from gestion_lafab.initiations import CATEGORY_OF_ACTIVITY
from gestion_lafab.membership import MONTHS
from gestion_lafab.paheko import run_sql

UNREADABLE = "Export des tickets illisible."
CASH_CATEGORY = 5
CASH_CATEGORY_NAME = "D - Initiations"
TICKET_FIELDS = ("event_name", "event_datetime", "email", "product_name")
TICKET_DATETIME = "%d/%m/%Y %H:%M"
TICKET_DATETIME_SHAPE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}")

# Keywords of each activity of initiation, as written in a sale's label.
KEYWORDS = {
    27: ["électrode"],
    30: ["tig"],
    34: ["semi-auto"],
    23: ["laser"],
    31: ["impression 3d"],
    22: ["dégau"],
    25: ["scie"],
    28: ["tour"],
    29: ["électroportatif", "électro-portatif"],
    33: ["tock", "nv2"],
    24: ["cordonnerie"],
    32: ["couture"],
}

CSV_HEADER = [
    "Numéro de membre",
    "Membre",
    "Activité",
    "Date d'inscription",
    "Payé ?",
    "Source",
    "E-mail",
    "Libellé",
    "Remarque",
]


def fold(text: str) -> str:
    """Lowercase, accents removed."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


FOLDED_KEYWORDS = {
    activity: [fold(k) for k in words] for activity, words in KEYWORDS.items()
}


def activity_of(label: str) -> int | None:
    """The activity whose keyword is in the label; None if none or several."""
    folded = fold(label)
    found = {
        activity
        for activity, words in FOLDED_KEYWORDS.items()
        if any(word in folded for word in words)
    }
    return found.pop() if len(found) == 1 else None


@dataclass(frozen=True)
class Member:
    id: int
    numero: str
    name: str


@dataclass(frozen=True)
class Ticket:
    event: str
    day: date
    email: str
    product: str


@dataclass(frozen=True)
class Sale:
    """A Vente d'initiation."""

    source: str  # "TiBillet" or "Caisse"
    label: str
    day: date
    email: str
    member: Member | None
    note: str
    activity: int | None
    remark: str = ""

    @property
    def incomplete(self) -> bool:
        return self.member is None or self.activity is None


@dataclass(frozen=True)
class Reconciliation:
    year: int
    month: int
    lines: list[Sale]
    labels: dict[int, str]  # Paheko label of each activity

    @property
    def month_label(self) -> str:
        return f"{MONTHS[self.month - 1]} {self.year}"

    @property
    def filename(self) -> str:
        return f"rapprochement-initiations-{self.year}-{self.month:02d}.csv"

    def rows(self) -> list[list[str]]:
        """The CSV rows of the lines, header excluded."""
        return [
            [
                line.member.numero if line.member else "",
                line.member.name if line.member else line.note,
                self.labels.get(line.activity, "") if line.activity else "",
                line.day.strftime("%d/%m/%Y"),
                "Oui",
                line.source,
                line.email,
                line.label,
                line.remark,
            ]
            for line in self.lines
        ]

    def csv(self) -> str:
        out = io.StringIO()
        writer = csv.writer(out, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        writer.writerow(CSV_HEADER)
        writer.writerows(self.rows())
        return out.getvalue()


@dataclass(frozen=True)
class Result:
    ok: bool
    message: str = ""
    reconciliation: Reconciliation | None = None


def read_form(content_type: str, body: bytes) -> dict[str, tuple[str | None, bytes]]:
    """The fields of a form body, in memory: by name, (file name or None,
    content)."""
    if content_type.startswith("application/x-www-form-urlencoded"):
        return {
            name: (None, value.encode())
            for name, value in parse_qsl(body.decode("utf-8", "replace"))
        }
    if not content_type.startswith("multipart/form-data"):
        return {}
    message = BytesParser(policy=email.policy.HTTP).parsebytes(
        b"Content-Type: " + content_type.encode("latin-1") + b"\r\n\r\n" + body
    )
    fields: dict[str, tuple[str | None, bytes]] = {}
    if not message.is_multipart():
        return fields
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if name is None:
            continue
        payload = part.get_payload(decode=True) or b""
        fields[str(name)] = (part.get_filename(), payload)
    return fields


def parse_export(content: bytes) -> list[Ticket] | None:
    """The tickets of a TiBillet export; None if it is unreadable."""
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, list):
        return None
    tickets = []
    for item in data:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(f), str) for f in TICKET_FIELDS
        ):
            return None
        if not TICKET_DATETIME_SHAPE.fullmatch(item["event_datetime"]):
            return None
        try:
            when = datetime.strptime(item["event_datetime"], TICKET_DATETIME)
        except ValueError:
            return None
        tickets.append(
            Ticket(
                item["event_name"],
                when.date(),
                item["email"].strip(),
                item["product_name"],
            )
        )
    return tickets


def member_name(row: Mapping) -> str:
    return " ".join(str(row[k]) for k in ("prenom", "nom") if row.get(k)).strip()


def to_member(row: Mapping, id_key: str = "id") -> Member:
    numero = row.get("numero")
    return Member(
        int(row[id_key]), "" if numero is None else str(numero), member_name(row)
    )


def month_bounds(year: int, month: int) -> tuple[str, str]:
    """ISO dates of the first day of the month and of the next month."""
    following = (year + 1, 1) if month == 12 else (year, month + 1)
    return f"{year:04d}-{month:02d}-01", f"{following[0]:04d}-{following[1]:02d}-01"


async def reconcile(
    env: Mapping[str, str],
    transport: httpx.AsyncBaseTransport | None,
    year: int,
    month: int,
    tickets: list[Ticket] | None,
) -> Result:
    """The Rapprochement des initiations of the month; `tickets` None when no
    export was sent."""
    start, end = month_bounds(year, month)
    activities = ", ".join(str(a) for a in sorted(CATEGORY_OF_ACTIVITY))
    # Queries are built from constants and validated integers only.
    queries = {
        "labels": f"SELECT id, label FROM services WHERE id IN ({activities});",
        "registrations": (
            "SELECT id_user, id_service, date FROM services_users"
            f" WHERE id_service IN ({activities})"
            f" AND date >= '{start}' AND date < '{end}';"
        ),
        "cash": (
            "SELECT i.name AS libelle, i.qty AS quantite, t.opened AS ouverture,"
            " t.name AS note, t.user_id, u.numero, u.prenom, u.nom"
            " FROM plugin_pos_tabs_items i"
            " JOIN plugin_pos_tabs t ON t.id = i.tab"
            " LEFT JOIN plugin_pos_products p ON p.id = i.product"
            " LEFT JOIN users u ON u.id = t.user_id"
            f" WHERE (p.category = {CASH_CATEGORY}"
            f" OR (p.id IS NULL AND i.category_name = '{CASH_CATEGORY_NAME}'))"
            f" AND t.opened >= '{start}' AND t.opened < '{end}'"
            " ORDER BY t.opened, i.id;"
        ),
    }
    if tickets is not None:
        queries["members"] = (
            "SELECT id, numero, prenom, nom, email FROM users"
            " WHERE email IS NOT NULL AND email != '';"
        )
    rows = {}
    for key, query in queries.items():
        result = await run_sql(env, transport, query)
        if not result.ok:
            return Result(False, result.message)
        rows[key] = result.rows

    labels = {int(r["id"]): str(r["label"]) for r in rows["labels"]}
    sales: list[Sale] = []

    if tickets is not None:
        by_email: dict[str, list[Member]] = {}
        for r in rows["members"]:
            key = str(r["email"]).strip().casefold()
            if key:
                by_email.setdefault(key, []).append(to_member(r))
        for t in tickets:
            if not t.product.startswith("Initiation"):
                continue
            if (t.day.year, t.day.month) != (year, month):
                continue
            found = by_email.get(t.email.casefold(), [])
            sales.append(
                Sale(
                    "TiBillet",
                    t.event,
                    t.day,
                    t.email,
                    found[0] if len(found) == 1 else None,
                    "",
                    activity_of(t.event),
                )
            )

    for r in rows["cash"]:
        label = str(r["libelle"])
        day = date.fromisoformat(str(r["ouverture"])[:10])
        note = "" if r["note"] is None else str(r["note"])
        member = to_member(r, "user_id") if r["user_id"] is not None else None
        activity = activity_of(label)
        quantity = int(r["quantite"])
        if quantity <= 0:  # refunds and corrections
            continue
        remark = ""
        if quantity > 1:
            # A note without a name: the quantity only.
            remark = (
                f"Quantité {quantity}, payée par {note}."
                if note.strip()
                else f"Quantité {quantity}."
            )
        sales.append(Sale("Caisse", label, day, "", member, note, activity, remark))
        for _ in range(quantity - 1):
            sales.append(Sale("Caisse", label, day, "", None, "", activity, remark))

    registered = {
        (int(r["id_user"]), int(r["id_service"]), str(r["date"])[:10])
        for r in rows["registrations"]
    }
    lines = [
        s
        for s in sales
        if not (
            s.member is not None
            and s.activity is not None
            and (s.member.id, s.activity, s.day.isoformat()) in registered
        )
    ]
    lines.sort(
        key=lambda s: (
            s.day,
            s.member is None,
            fold(s.member.name) if s.member else "",
            s.label,
        )
    )
    return Result(True, reconciliation=Reconciliation(year, month, lines, labels))
