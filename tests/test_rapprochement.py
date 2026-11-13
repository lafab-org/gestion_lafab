import json
from collections import Counter
from datetime import datetime

import httpx
import pytest
from litestar.testing import TestClient

from gestion_lafab.app import create_app
from tests.fakes import (
    CASH_COACHING,
    CASH_INITIATIONS,
    CASH_METAL_SUPPLIES,
    CASH_TICKETS,
    ENV,
    URL,
    Clock,
    FakePaheko,
    Member,
    Tab,
)
from tests.rapprochement_data import (
    ALICE,
    BRUNO,
    FORM_EXPORT,
    FORM_MONTH,
    HEADER,
    LABELS,
    MEMBERS,
    csv_rows,
    download,
    reconcile,
    ticket,
)
from tests.stats_html import normalize, sse_html

NOW = datetime(2026, 11, 10, 14, 32)
LASER, TIG, COUTURE = 23, 30, 32
UNKNOWN = "inconnu@example.org"


@pytest.fixture
def paheko() -> FakePaheko:
    fake = FakePaheko()
    fake.members = list(MEMBERS)
    return fake


@pytest.fixture
def client(paheko):
    app = create_app(dict(ENV), paheko.transport(), Clock(NOW))
    with TestClient(app) as c:
        yield c


def text(response) -> str:
    return normalize(sse_html(response.text))


def libelles(rows: list[list[str]]) -> list[str]:
    return [row[7] for row in rows]


# /operations/telecharger-le-rapprochement/none /operations/etat-initial/vide
def test_download_without_reconciliation(client):
    assert download(client).status_code == 404


# /operations/rapprocher-les-initiations/ok
# /operations/rapprocher-les-initiations/billet
# /operations/telecharger-le-rapprochement/csv /model/billet /model/membre
# /model/vente-dinitiation /operations/rapprocher-les-initiations/remarque-billet
def test_ticket_line(client):
    reconcile(
        client,
        export=[
            ticket("Initiation à la découpeuse laser", "09/10/2026 18:00", ALICE.email)
        ],
    )
    assert csv_rows(client) == [
        [
            "1204",
            "Alice ARNAUD",
            "Initiation laser",
            "09/10/2026",
            "Oui",
            "TiBillet",
            "alice@example.org",
            "Initiation à la découpeuse laser",
            "",
        ]
    ]


# /operations/rapprocher-les-initiations/billet /model/billet
# /model/export-des-tickets
def test_ticket_selection(client):
    reconcile(
        client,
        export=[
            ticket("A produit Initiation", "15/10/2026 10:00", UNKNOWN),
            ticket(
                "B produit Initiation tock",
                "15/10/2026 10:00",
                UNKNOWN,
                "Initiation tock",
            ),
            ticket("C début du mois", "01/10/2026 00:00", UNKNOWN),
            ticket("D fin du mois", "31/10/2026 23:30", UNKNOWN),
            ticket(
                "Réservation gratuite",
                "15/10/2026 10:00",
                UNKNOWN,
                "Réservation gratuite",
            ),
            ticket(
                "Produit qui ne commence pas",
                "15/10/2026 10:00",
                UNKNOWN,
                "Atelier Initiation",
            ),
            ticket("Mois précédent", "30/09/2026 23:59", UNKNOWN),
            ticket("Mois suivant", "01/11/2026 00:00", UNKNOWN),
            ticket("Année précédente", "15/10/2025 10:00", UNKNOWN),
        ],
    )
    rows = csv_rows(client)
    assert sorted(libelles(rows)) == [
        "A produit Initiation",
        "B produit Initiation tock",
        "C début du mois",
        "D fin du mois",
    ]
    dates = {row[7]: row[3] for row in rows}
    assert dates["C début du mois"] == "01/10/2026"
    assert dates["D fin du mois"] == "31/10/2026"


# /operations/rapprocher-les-initiations/produit
# /operations/rapprocher-les-initiations/billet
def test_free_ticket_selection(client):
    free = "Réservation gratuite"
    reconcile(
        client,
        export=[
            ticket(
                "Réservée étudiants ENSAS - Initiation laser - Yoann",
                "16/10/2026 20:00",
                UNKNOWN,
                free,
            ),
            ticket("Gratuit INITIATION soudure", "15/10/2026 10:00", UNKNOWN, free),
            ticket("Gratuit réinitiation", "15/10/2026 10:00", UNKNOWN, free),
            ticket("Adieu Windows", "22/10/2026 19:00", UNKNOWN, free),
            ticket(
                "Initiation hors produit gratuit",
                "15/10/2026 10:00",
                UNKNOWN,
                "réservation gratuite",
            ),
            ticket(
                "Initiation gratuite autre produit",
                "15/10/2026 10:00",
                UNKNOWN,
                "Réservation",
            ),
            ticket(
                "Initiation gratuite mois suivant", "01/11/2026 00:00", UNKNOWN, free
            ),
            ticket(
                "Initiation gratuite mois précédent", "30/09/2026 23:59", UNKNOWN, free
            ),
        ],
    )
    assert sorted(libelles(csv_rows(client))) == [
        "Gratuit INITIATION soudure",
        "Gratuit réinitiation",
        "Réservée étudiants ENSAS - Initiation laser - Yoann",
    ]


# /operations/rapprocher-les-initiations/produit
# /operations/rapprocher-les-initiations/billet
# /operations/telecharger-le-rapprochement/csv
# /operations/rapprocher-les-initiations/activite
def test_free_ticket_line(client):
    reconcile(
        client,
        export=[
            ticket(
                "Réservée étudiants ENSAS - Initiation laser - Yoann",
                "16/10/2026 20:00",
                ALICE.email,
                "Réservation gratuite",
            )
        ],
    )
    assert csv_rows(client) == [
        [
            "1204",
            "Alice ARNAUD",
            "Initiation laser",
            "16/10/2026",
            "Oui",
            "TiBillet",
            "alice@example.org",
            "Réservée étudiants ENSAS - Initiation laser - Yoann",
            "",
        ]
    ]


# /operations/rapprocher-les-initiations/membre-vide
@pytest.mark.parametrize("email", [UNKNOWN, "famille@example.org"])
def test_ticket_without_member(client, email):
    reconcile(client, export=[ticket("Initiation laser", "09/10/2026 18:00", email)])
    assert csv_rows(client) == [
        [
            "",
            "",
            "Initiation laser",
            "09/10/2026",
            "Oui",
            "TiBillet",
            email,
            "Initiation laser",
            "",
        ]
    ]


# /operations/rapprocher-les-initiations/caisse /model/ligne-de-caisse
# /operations/telecharger-le-rapprochement/csv
# /operations/rapprocher-les-initiations/remarque-vide
def test_cash_lines(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-14 18:30:00",
            [("Initiation métal TIG 3h", 1, CASH_INITIATIONS)],
            name="Bruno au comptoir",
            user_id=BRUNO.id,
        ),
        Tab(
            "2026-10-20 09:00:00",
            [("Initiation couture", 1, CASH_INITIATIONS)],
            name="Groupe lycée",
        ),
    ]
    reconcile(client)
    assert csv_rows(client) == [
        [
            "876",
            "Bruno MOREAU",
            "Initiation soudage TIG",
            "14/10/2026",
            "Oui",
            "Caisse",
            "",
            "Initiation métal TIG 3h",
            "",
        ],
        [
            "",
            "Groupe lycée",
            "Initiation couture",
            "20/10/2026",
            "Oui",
            "Caisse",
            "",
            "Initiation couture",
            "",
        ],
    ]


# /operations/rapprocher-les-initiations/billet
# /operations/rapprocher-les-initiations/membre-vide
@pytest.mark.parametrize(
    ("ticket_email", "member_email"),
    [
        (" ALICE@Example.ORG ", ALICE.email),
        ("eve@example.org", " Eve@Example.org "),
    ],
)
def test_ticket_email_case_and_spaces(client, paheko, ticket_email, member_email):
    paheko.members = [
        Member(ALICE.id, 1204, "Alice", "ARNAUD", member_email),
        BRUNO,
    ]
    reconcile(
        client, export=[ticket("Initiation laser", "09/10/2026 18:00", ticket_email)]
    )
    rows = csv_rows(client)
    assert [row[:2] for row in rows] == [["1204", "Alice ARNAUD"]]
    assert rows[0][6] == ticket_email.strip()


# /operations/rapprocher-les-initiations/membre-vide
@pytest.mark.parametrize("email", ["", "   "])
def test_ticket_without_email(client, paheko, email):
    paheko.members = [
        ALICE,
        Member(15, 700, "Sans", "COURRIEL", ""),
        Member(16, 701, "Sans", "ADRESSE", None),
    ]
    reconcile(client, export=[ticket("Initiation laser", "09/10/2026 18:00", email)])
    rows = csv_rows(client)
    assert [row[:2] for row in rows] == [["", ""]]
    assert rows[0][6] == ""


# /operations/rapprocher-les-initiations/caisse /model/ligne-de-caisse
def test_cash_selection(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-05 10:00:00",
            [
                ("A initiation", 1, CASH_INITIATIONS),
                ("Initiation laser accompagnement", 1, CASH_COACHING),
                ("Initiation laser ticket", 1, CASH_TICKETS),
                ("Initiation électrode fournitures", 1, CASH_METAL_SUPPLIES),
            ],
            name="Note",
        ),
        Tab("2026-10-01 00:00:00", [("B début du mois", 1, CASH_INITIATIONS)]),
        # Opened in October, its line added in November.
        Tab(
            "2026-10-31 23:30:00",
            [("C ouverte fin du mois", 1, CASH_INITIATIONS)],
            added="2026-11-01 00:30:00",
        ),
        # Opened in September, its line added in October.
        Tab(
            "2026-09-30 22:00:00",
            [("Ouverte en septembre", 1, CASH_INITIATIONS)],
            added="2026-10-01 01:00:00",
        ),
        Tab("2026-09-30 23:59:59", [("Mois précédent", 1, CASH_INITIATIONS)]),
        Tab("2026-11-01 00:00:00", [("Mois suivant", 1, CASH_INITIATIONS)]),
        Tab("2025-10-15 10:00:00", [("Année précédente", 1, CASH_INITIATIONS)]),
    ]
    reconcile(client)
    rows = csv_rows(client)
    assert sorted(libelles(rows)) == [
        "A initiation",
        "B début du mois",
        "C ouverte fin du mois",
    ]
    dates = {row[7]: row[3] for row in rows}
    assert dates["B début du mois"] == "01/10/2026"
    assert dates["C ouverte fin du mois"] == "31/10/2026"


# /operations/rapprocher-les-initiations/caisse /model/ligne-de-caisse
# /technical/pile
def test_cash_category_of_line(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-05 10:00:00",
            [
                # Products that no longer exist: the recorded category.
                ("A produit supprimé", 1, None, "D - Initiations"),
                ("Produit supprimé ailleurs", 1, None, "D - Accompagnement"),
                # Existing products: their current category.
                ("B produit déplacé ici", 1, CASH_INITIATIONS, "B - Tickets"),
                ("Produit déplacé ailleurs", 1, CASH_COACHING, "D - Initiations"),
            ],
            name="Note",
        )
    ]
    reconcile(client)
    assert sorted(libelles(csv_rows(client))) == [
        "A produit supprimé",
        "B produit déplacé ici",
    ]


# /operations/rapprocher-les-initiations/quantite
def test_quantity_with_member(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-21 18:00:00",
            [("Initiation métal TIG 3h", 2, CASH_INITIATIONS)],
            name="Bruno (2 places)",
            user_id=BRUNO.id,
        )
    ]
    reconcile(client)
    remark = "Quantité 2, payée par Bruno (2 places)."
    common = ["Initiation soudage TIG", "21/10/2026", "Oui", "Caisse", ""]
    assert csv_rows(client) == [
        ["876", "Bruno MOREAU", *common, "Initiation métal TIG 3h", remark],
        ["", "", *common, "Initiation métal TIG 3h", remark],
    ]


# /operations/rapprocher-les-initiations/quantite
# /operations/rapprocher-les-initiations/sans-nom
@pytest.mark.parametrize("name", [None, ""])
def test_quantity_note_without_name(client, paheko, name):
    paheko.tabs = [
        Tab(
            "2026-10-21 18:00:00",
            [("Initiation couture", 2, CASH_INITIATIONS)],
            name=name,
        )
    ]
    reconcile(client)
    rows = csv_rows(client)
    assert [row[8] for row in rows] == ["Quantité 2.", "Quantité 2."]
    assert [row[:2] for row in rows] == [["", ""], ["", ""]]


# /operations/rapprocher-les-initiations/remarque-vide
# /operations/rapprocher-les-initiations/remarque-billet
def test_remarks_empty(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-21 18:00:00",
            [
                ("Initiation couture seule", 1, CASH_INITIATIONS),
                ("Initiation laser à deux", 2, CASH_INITIATIONS),
            ],
            name="Bruno MOREAU",
            user_id=BRUNO.id,
        )
    ]
    reconcile(
        client, export=[ticket("Initiation TIG", "21/10/2026 10:00", ALICE.email)]
    )
    remarks = {row[7]: row[8] for row in csv_rows(client)}
    assert remarks["Initiation couture seule"] == ""
    assert remarks["Initiation TIG"] == ""
    assert remarks["Initiation laser à deux"] == "Quantité 2, payée par Bruno MOREAU."


# /operations/rapprocher-les-initiations/quantite-nulle
def test_quantity_zero_or_negative(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-21 18:00:00",
            [
                ("Initiation couture vendue", 1, CASH_INITIATIONS),
                ("Initiation couture annulée", 0, CASH_INITIATIONS),
                ("Initiation couture remboursée", -1, CASH_INITIATIONS),
                ("Initiation laser remboursées", -2, CASH_INITIATIONS),
            ],
            name="Bruno MOREAU",
            user_id=BRUNO.id,
        )
    ]
    reconcile(client)
    assert libelles(csv_rows(client)) == ["Initiation couture vendue"]


# /operations/rapprocher-les-initiations/quantite
def test_quantity_without_member(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-21 18:00:00",
            [("Initiation couture", 3, CASH_INITIATIONS)],
            name="Groupe lycée",
        )
    ]
    reconcile(client)
    remark = "Quantité 3, payée par Groupe lycée."
    common = ["Initiation couture", "21/10/2026", "Oui", "Caisse", ""]
    line = ["", "Groupe lycée", *common, "Initiation couture", remark]
    other = ["", "", *common, "Initiation couture", remark]
    assert Counter(map(tuple, csv_rows(client))) == Counter(
        [tuple(line), tuple(other), tuple(other)]
    )


# /operations/rapprocher-les-initiations/nofile
def test_no_file_cash_only(client, paheko):
    paheko.tabs = [
        Tab("2026-10-14 18:30:00", [("Initiation laser", 1, CASH_INITIATIONS)])
    ]
    reconcile(client)
    assert libelles(csv_rows(client)) == ["Initiation laser"]


# /operations/rapprocher-les-initiations/ok
# /operations/rapprocher-les-initiations/caisse
# /operations/rapprocher-les-initiations/billet
def test_tickets_and_cash(client, paheko):
    paheko.tabs = [Tab("2026-10-14 18:30:00", [("Caisse laser", 1, CASH_INITIATIONS)])]
    reconcile(client, export=[ticket("Billet laser", "15/10/2026 18:00", UNKNOWN)])
    rows = csv_rows(client)
    assert [(row[5], row[7]) for row in rows] == [
        ("Caisse", "Caisse laser"),
        ("TiBillet", "Billet laser"),
    ]


# /operations/rapprocher-les-initiations/activite /model/mot-cle-dactivite
@pytest.mark.parametrize(
    ("libelle", "activity"),
    [
        ("Initiation au soudage à l'ELECTRODE enrobée", 27),
        ("Soudage TIG", 30),
        ("Soudage au poste Semi-Auto", 34),
        ("Découpeuse LASER", 23),
        ("Impression 3D débutants", 31),
        ("Degauchisseuse", 22),
        ("Scie à format", 25),
        ("Tour à bois", 28),
        ("Electroportatif", 29),
        ("Électro-portatif", 29),
        ("Tock", 33),
        ("Cordonnerie", 24),
        ("Couture", 32),
    ],
)
def test_activity_keywords(client, libelle, activity):
    reconcile(client, export=[ticket(libelle, "09/10/2026 18:00", UNKNOWN)])
    assert csv_rows(client)[0][2] == LABELS[activity]


# /operations/rapprocher-les-initiations/activite
# /operations/rapprocher-les-initiations/activite-vide
@pytest.mark.parametrize(
    ("libelle", "label"),
    [
        ("Autre initiation en groupe 3h", ""),
        ("Initiation laser et impression 3D", ""),
        ("Électroportatif ou électro-portatif", LABELS[29]),
        ("TIG, encore du tig", LABELS[30]),
    ],
)
def test_activity_none_or_several(client, libelle, label):
    reconcile(client, export=[ticket(libelle, "09/10/2026 18:00", UNKNOWN)])
    assert csv_rows(client)[0][2] == label


# /operations/rapprocher-les-initiations/activite
# /operations/rapprocher-les-initiations/activite-vide /model/mot-cle-dactivite
@pytest.mark.parametrize(
    ("libelle", "label"),
    [
        ("Initiation électro-portatif bois NV2", ""),
        ("Initiation tock nv2", LABELS[33]),
        ("Initiation bois Nv2", LABELS[33]),
    ],
)
def test_activity_nv2(client, libelle, label):
    reconcile(client, export=[ticket(libelle, "09/10/2026 18:00", UNKNOWN)])
    assert csv_rows(client)[0][2] == label


# /operations/rapprocher-les-initiations/activite
def test_cash_activity_keyword(client, paheko):
    paheko.tabs = [
        Tab("2026-10-14 18:30:00", [("Initiation COUTURE 3h", 1, CASH_INITIATIONS)])
    ]
    reconcile(client)
    assert csv_rows(client)[0][2] == LABELS[COUTURE]


# /operations/rapprocher-les-initiations/deja-inscrit /model/initiation
def test_already_registered(client, paheko):
    paheko.registrations = [
        (ALICE.id, LASER, "2026-10-09"),
        (BRUNO.id, LASER, "2026-10-14"),
        (BRUNO.id, TIG, "2026-10-14"),
    ]
    paheko.tabs = [
        Tab(
            "2026-10-14 18:30:00",
            [
                ("Bruno laser inscrit", 1, CASH_INITIATIONS),
                ("Bruno sans activité", 1, CASH_INITIATIONS),
            ],
            name="Bruno MOREAU",
            user_id=BRUNO.id,
        ),
        Tab(
            "2026-10-14 19:00:00",
            [("Laser pour deux", 2, CASH_INITIATIONS)],
            name="Bruno MOREAU",
            user_id=BRUNO.id,
        ),
    ]
    reconcile(
        client,
        export=[
            ticket("Alice laser inscrite", "09/10/2026 18:00", ALICE.email),
            ticket("Alice laser autre jour", "16/10/2026 18:00", ALICE.email),
            ticket("Alice TIG même jour", "09/10/2026 18:00", ALICE.email),
            ticket("Inconnu laser", "09/10/2026 18:00", UNKNOWN),
        ],
    )
    rows = csv_rows(client)
    assert sorted(libelles(rows)) == [
        "Alice TIG même jour",
        "Alice laser autre jour",
        "Bruno sans activité",
        "Inconnu laser",
        "Laser pour deux",
    ]
    second_place = next(row for row in rows if row[7] == "Laser pour deux")
    assert second_place[:2] == ["", ""]


# /operations/rapprocher-les-initiations/deja-inscrit /model/initiation
def test_already_registered_read_at_reconciliation(client, paheko):
    # The Lecture des initiations is made before the registrations change.
    paheko.registrations = [(BRUNO.id, LASER, "2026-10-09")]
    assert client.get("/initiations/lecture").status_code == 200
    paheko.registrations = [(ALICE.id, LASER, "2026-10-09")]
    reconcile(
        client,
        export=[
            ticket("Alice laser", "09/10/2026 18:00", ALICE.email),
            ticket("Bruno laser", "09/10/2026 18:00", BRUNO.email),
        ],
    )
    assert libelles(csv_rows(client)) == ["Bruno laser"]


# /operations/rapprocher-les-initiations/ordre
def test_order_member_name_ignores_case_and_accents(client, paheko):
    paheko.members = [
        Member(18, 801, "élodie", "Z", "elodie@example.org"),
        Member(19, 802, "Eric", "A", "eric@example.org"),
        Member(20, 803, "agathe", "B", "agathe@example.org"),
    ]
    reconcile(
        client,
        export=[
            ticket("Eric", "05/10/2026 09:00", "eric@example.org"),
            ticket("élodie", "05/10/2026 09:00", "elodie@example.org"),
            ticket("agathe", "05/10/2026 09:00", "agathe@example.org"),
        ],
    )
    assert libelles(csv_rows(client)) == ["agathe", "élodie", "Eric"]


# /operations/rapprocher-les-initiations/ordre
def test_order_libelle(client):
    reconcile(
        client,
        export=[
            ticket("Initiation couture", "05/10/2026 09:00", UNKNOWN),
            ticket("Initiation bois", "05/10/2026 09:00", UNKNOWN),
            ticket("Initiation laser", "05/10/2026 09:00", UNKNOWN),
        ],
    )
    assert libelles(csv_rows(client)) == [
        "Initiation bois",
        "Initiation couture",
        "Initiation laser",
    ]


# /operations/rapprocher-les-initiations/libelles
# /operations/telecharger-le-rapprochement/csv /model/libelle-dactivite
def test_activity_label_read_from_paheko(client, paheko):
    paheko.labels = {LASER: "Découpe laser (initiation)", TIG: None}
    reconcile(
        client,
        export=[
            ticket("Initiation laser", "09/10/2026 18:00", UNKNOWN),
            ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN),
            ticket("Initiation couture", "11/10/2026 18:00", UNKNOWN),
        ],
    )
    assert {row[7]: row[2] for row in csv_rows(client)} == {
        "Initiation laser": "Découpe laser (initiation)",
        "Initiation TIG": "",
        "Initiation couture": LABELS[COUTURE],
    }


def post_month(client, fields: dict):
    response = client.post(
        "/initiations/rapprochement",
        data=fields,
        files={FORM_EXPORT: ("", b"", "application/octet-stream")},
    )
    assert response.status_code == 200
    return response


# /operations/rapprocher-les-initiations/mois-invalide
@pytest.mark.parametrize(
    "fields",
    [{}, {FORM_MONTH: ""}, {FORM_MONTH: "2026-13"}, {FORM_MONTH: "octobre"}],
)
def test_invalid_month_is_previous_month(client, paheko, fields):
    paheko.tabs = [
        Tab("2026-10-14 18:30:00", [("Octobre", 1, CASH_INITIATIONS)]),
        Tab("2026-11-02 18:30:00", [("Novembre", 1, CASH_INITIATIONS)]),
    ]
    post_month(client, fields)
    assert libelles(csv_rows(client)) == ["Octobre"]
    disposition = download(client).headers["content-disposition"]
    assert "rapprochement-initiations-2026-10.csv" in disposition


# /operations/rapprocher-les-initiations/ordre
def test_order(client, paheko):
    paheko.tabs = [
        Tab(
            "2026-10-05 10:00:00",
            [("Y caisse Alice", 1, CASH_INITIATIONS)],
            name="Alice ARNAUD",
            user_id=ALICE.id,
        ),
        Tab(
            "2026-10-05 11:00:00",
            [("A caisse sans membre", 1, CASH_INITIATIONS)],
            name="Zoé",
        ),
        Tab(
            "2026-10-04 11:00:00",
            [("Z caisse sans membre", 1, CASH_INITIATIONS)],
            name="Zoé",
        ),
    ]
    reconcile(
        client,
        export=[
            ticket("B billet sans membre", "05/10/2026 09:00", UNKNOWN),
            ticket("Z billet Bruno", "05/10/2026 09:00", BRUNO.email),
            ticket("A billet Bruno", "05/10/2026 20:00", BRUNO.email),
            ticket("Z billet Alice", "06/10/2026 09:00", ALICE.email),
        ],
    )
    assert libelles(csv_rows(client)) == [
        "Z caisse sans membre",
        "Y caisse Alice",
        "A billet Bruno",
        "Z billet Bruno",
        "A caisse sans membre",
        "B billet sans membre",
        "Z billet Alice",
    ]


# /operations/rapprocher-les-initiations/ok
# /operations/telecharger-le-rapprochement/csv
def test_replaces_reconciliation(client):
    export = [
        ticket("Octobre", "09/10/2026 18:00", UNKNOWN),
        ticket("Septembre", "09/09/2026 18:00", UNKNOWN),
    ]
    reconcile(client, "2026-10", export)
    assert libelles(csv_rows(client)) == ["Octobre"]
    reconcile(client, "2026-09", export)
    assert libelles(csv_rows(client)) == ["Septembre"]
    disposition = download(client).headers["content-disposition"]
    assert "rapprochement-initiations-2026-09.csv" in disposition


# /operations/telecharger-le-rapprochement/csv /technical/pile
def test_csv_file(client):
    reconcile(
        client, export=[ticket("Initiation laser", "09/10/2026 18:00", ALICE.email)]
    )
    response = download(client)
    assert "attachment" in response.headers["content-disposition"]
    assert (
        "rapprochement-initiations-2026-10.csv"
        in (response.headers["content-disposition"])
    )
    body = response.content.decode("utf-8")
    lines = body.split("\r\n")
    assert lines[-1] == ""
    assert lines[0] == ",".join(f'"{name}"' for name in HEADER)
    assert lines[1] == (
        '"1204","Alice ARNAUD","Initiation laser","09/10/2026","Oui",'
        '"TiBillet","alice@example.org","Initiation laser",""'
    )
    assert len(lines) == 3


# /operations/telecharger-le-rapprochement/csv
def test_csv_without_lines(client):
    reconcile(client, "2026-08")
    assert csv_rows(client) == []
    disposition = download(client).headers["content-disposition"]
    assert "rapprochement-initiations-2026-08.csv" in disposition


UNREADABLE = [
    b"ceci n'est pas du JSON",
    b'[{"event_name": "Initiation laser"',
    # JSON that is not a list of tickets.
    json.dumps(ticket("Initiation laser", "09/10/2026 18:00", UNKNOWN)).encode(),
    json.dumps({"tickets": []}).encode(),
    json.dumps(
        [ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN), "Initiation laser"]
    ).encode(),
    json.dumps([ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN), 42]).encode(),
    json.dumps([ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN), None]).encode(),
]
# Tickets with a field that is not a text.
for field, value in [
    ("event_name", 42),
    ("event_datetime", None),
    ("email", ["alice@example.org"]),
    ("product_name", {"name": "Initiation"}),
]:
    wrong = ticket("Initiation laser", "09/10/2026 18:00", UNKNOWN)
    wrong[field] = value
    UNREADABLE.append(
        json.dumps(
            [ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN), wrong]
        ).encode()
    )
# Tickets whose date is not a valid date and time as JJ/MM/AAAA HH:MM.
for when in [
    "31/02/2026 10:00",
    "09/10/2026 25:00",
    "09/13/2026 10:00",
    "2026-10-09 18:00",
    "09/10/2026",
    "",
]:
    UNREADABLE.append(
        json.dumps(
            [
                ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN),
                ticket("Initiation laser", when, UNKNOWN),
            ]
        ).encode()
    )
INCOMPLETE = [
    (field, ticket("Initiation laser", "09/10/2026 18:00", UNKNOWN))
    for field in ["event_name", "event_datetime", "email", "product_name"]
] + [
    # Tickets the month or the product would leave out.
    ("email", ticket("Initiation laser", "09/09/2026 18:00", UNKNOWN)),
    (
        "event_name",
        ticket("Réservation", "09/10/2026 18:00", UNKNOWN, "Réservation gratuite"),
    ),
]
for missing, incomplete in INCOMPLETE:
    del incomplete[missing]
    UNREADABLE.append(
        json.dumps(
            [ticket("Initiation TIG", "10/10/2026 18:00", UNKNOWN), incomplete]
        ).encode()
    )


# /operations/rapprocher-les-initiations/export
@pytest.mark.parametrize("content", UNREADABLE)
def test_unreadable_export(client, content):
    reconcile(client, export=[ticket("Avant", "09/10/2026 18:00", UNKNOWN)])
    response = reconcile(client, export=content)
    assert "Export des tickets illisible." in text(response)
    assert libelles(csv_rows(client)) == ["Avant"]


# /operations/rapprocher-les-initiations/export
def test_unreadable_export_first(client):
    response = reconcile(client, export=b"pas du JSON")
    assert "Export des tickets illisible." in text(response)
    assert download(client).status_code == 404


# /operations/rapprocher-les-initiations/export
# /operations/rapprocher-les-initiations/failed
def test_unreadable_export_and_paheko_failing(client, paheko):
    paheko.status = 500
    response = reconcile(client, export=b"pas du JSON")
    assert "Export des tickets illisible." in text(response)


FAILURES = [
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
        lambda p, env: setattr(p, "status", 500),
        f"Réponse inattendue de {URL} : code 500.",
    ),
    (
        lambda p, env: setattr(p, "body", b"pas du JSON"),
        f"Réponse inattendue de {URL} : code 200.",
    ),
    (
        lambda p, env: setattr(p, "body", b'{"results": "aucun"}'),
        f"Réponse inattendue de {URL} : code 200.",
    ),
]


# /operations/rapprocher-les-initiations/failed
@pytest.mark.parametrize(("setup", "message"), FAILURES)
@pytest.mark.parametrize("with_file", [True, False])
def test_paheko_failed(paheko, setup, message, with_file):
    env = dict(ENV)
    app = create_app(env, paheko.transport(), Clock(NOW))
    export = [ticket("Avant", "09/10/2026 18:00", UNKNOWN)]
    with TestClient(app) as client:
        reconcile(client, export=export)
        setup(paheko, env)
        response = reconcile(client, export=export if with_file else None)
        assert message in text(response)
        paheko.status, paheko.error, paheko.body = 200, None, None
        env.update(ENV)
        assert libelles(csv_rows(client)) == ["Avant"]


# /operations/rapprocher-les-initiations/failed
def test_paheko_failed_first(client, paheko):
    paheko.status = 500
    response = reconcile(client)
    assert f"Réponse inattendue de {URL} : code 500." in text(response)
    paheko.status = 200
    assert download(client).status_code == 404


# /ui/page-du-rapprochement-des-initiations/caisse-seule
# /ui/page-du-rapprochement-des-initiations/error
def test_no_file_warning_not_after_refusal(client, paheko):
    paheko.status = 500
    response = reconcile(client)
    assert f"Réponse inattendue de {URL} : code 500." in text(response)
    assert "Aucun export des tickets envoyé" not in text(response)
