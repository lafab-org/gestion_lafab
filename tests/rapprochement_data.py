"""Helpers for the Rapprochement des initiations: TiBillet exports, requests."""

import csv
import io
import json

from tests.fakes import Member

# Fields of the form sent to /initiations/rapprochement.
FORM_MONTH, FORM_EXPORT = "mois", "export"

HEADER = [
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

ALICE = Member(11, 1204, "Alice", "ARNAUD", "alice@example.org")
BRUNO = Member(12, 876, "Bruno", "MOREAU", "bruno@example.org")
# Two members sharing an e-mail.
TWIN_1 = Member(13, 501, "Chris", "LEROY", "famille@example.org")
TWIN_2 = Member(14, 502, "Dana", "LEROY", "famille@example.org")
MEMBERS = [ALICE, BRUNO, TWIN_1, TWIN_2]

LABELS = {
    20: "Initiation assemblage bois",
    21: "Initiation assemblage main",
    22: "Initiation dégau-rabo",
    23: "Initiation laser",
    24: "Initiation projet cordonnerie",
    25: "Initiation scie à format",
    27: "Initiation soudage électrode enrobée",
    28: "Initiation tour à bois",
    29: "Initiation électro-portatif bois",
    30: "Initiation soudage TIG",
    31: "Initiation impression 3D",
    32: "Initiation couture",
    33: "Initiation électro-portatif bois NV2",
    34: "Initiation soudage semi-auto",
}


def ticket(event: str, when: str, email: str, product: str = "Initiation") -> dict:
    """A ticket of the TiBillet export; `when` is `JJ/MM/AAAA HH:MM`."""
    return {
        "event_name": event,
        "event_datetime": when,
        "email": email,
        "userId": "00000000-0000-0000-0000-000000000000",
        "reservation_uuid": "00000000",
        "numero_uuid": "00000000",
        "status": "Valide et non scanné",
        "price_name": "Tarif normal",
        "product_name": product,
        "options": "",
        "reservation_datetime": "01/09/2026 10:00",
        "payment_method": "",
    }


def export_bytes(tickets: list[dict]) -> bytes:
    return json.dumps(tickets, ensure_ascii=False, indent=2).encode()


def reconcile(client, month: str = "2026-10", export: list[dict] | bytes | None = None):
    """POST the form; `export` None sends the file field empty, as a browser
    does when no file is chosen."""
    if export is None:
        part = ("", b"", "application/octet-stream")
    else:
        content = export if isinstance(export, bytes) else export_bytes(export)
        part = ("Ticket-2026-11-10.json", content, "application/json")
    response = client.post(
        "/initiations/rapprochement",
        data={FORM_MONTH: month},
        files={FORM_EXPORT: part},
    )
    assert response.status_code == 200
    return response


def download(client):
    return client.get("/initiations/rapprochement.csv")


def csv_rows(client) -> list[list[str]]:
    """The lines of the downloaded CSV, header excluded."""
    response = download(client)
    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
    assert rows[0] == HEADER
    return rows[1:]
