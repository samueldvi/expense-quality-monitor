#!/usr/bin/env python3
"""Generate deterministic synthetic expenses and their row-level ground truth."""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


SEED = 20260713
ROW_COUNT = 300
WEEK_START = date(2026, 7, 13)

EXPENSE_COLUMNS = [
    "id_spesa",
    "data_spesa",
    "dipendente",
    "centro_di_costo",
    "categoria",
    "descrizione",
    "importo",
    "valuta_originale",
    "progetto",
    "approvatore",
]
TRUTH_COLUMNS = [
    "source_row_number",
    "id_spesa",
    "rule_id",
    "anomaly_type",
    "field",
    "expected_status",
    "expected_message",
    "note",
]

CATEGORY_COUNTS = {
    "Vitto": 90,
    "Trasporto": 70,
    "Alloggio": 55,
    "Materiale": 45,
    "Rappresentanza": 36,
    "Formazione": 4,
}
BASE_AMOUNTS = {
    "Vitto": Decimal("18"),
    "Trasporto": Decimal("50"),
    "Alloggio": Decimal("70"),
    "Materiale": Decimal("30"),
    "Rappresentanza": Decimal("80"),
    "Formazione": Decimal("200"),
}
THRESHOLDS = {
    "Vitto": Decimal("80"),
    "Trasporto": Decimal("200"),
    "Alloggio": Decimal("250"),
    "Materiale": Decimal("150"),
    "Rappresentanza": Decimal("300"),
    "Formazione": Decimal("500"),
}
STAT_AMOUNTS = {
    "Vitto": Decimal("70"),
    "Trasporto": Decimal("180"),
    "Alloggio": Decimal("240"),
    "Materiale": Decimal("180"),
    "Rappresentanza": Decimal("350"),
}

# anomaly_type, expected_status, expected_message
RULES = {
    "COMPLETENESS_MISSING_ID_SPESA": (
        "completezza", "incompleta", "campo obbligatorio mancante: id_spesa"
    ),
    "COMPLETENESS_MISSING_DATA_SPESA": (
        "completezza", "incompleta", "campo obbligatorio mancante: data_spesa"
    ),
    "COMPLETENESS_MISSING_DIPENDENTE": (
        "completezza", "incompleta", "campo obbligatorio mancante: dipendente"
    ),
    "COMPLETENESS_MISSING_CATEGORIA": (
        "completezza", "incompleta", "campo obbligatorio mancante: categoria"
    ),
    "COMPLETENESS_MISSING_IMPORTO": (
        "completezza", "incompleta", "campo obbligatorio mancante: importo"
    ),
    "COMPLETENESS_MISSING_PROGETTO": (
        "completezza", "incompleta", "campo obbligatorio mancante: progetto"
    ),
    "UNIQUENESS_ID_DUPLICATE": (
        "unicità", "duplicato", "id_spesa duplicato"
    ),
    "UNIQUENESS_LOGICAL_DUPLICATE": (
        "unicità", "duplicato logico", "duplicato logico rilevato"
    ),
    "VALIDITY_NON_NUMERIC_ID": (
        "validità", "non valido", "id_spesa non numerico"
    ),
    "VALIDITY_INVALID_DATE": (
        "validità", "non valida", "data_spesa non valida"
    ),
    "VALIDITY_NEGATIVE_AMOUNT": (
        "validità", "non valido", "importo negativo"
    ),
    "VALIDITY_NON_NUMERIC_AMOUNT": (
        "validità", "non valido", "importo non numerico"
    ),
    "VALIDITY_INVALID_CATEGORY": (
        "validità", "non valida", "categoria non ammessa"
    ),
    "STATISTICAL_AMOUNT_ANOMALY": (
        "anomalia statistica",
        "anomalia statistica",
        "importo superiore a 3 volte la mediana della categoria",
    ),
    "STATISTICAL_NOT_EVALUABLE": (
        "valutabilità statistica",
        "non valutabile statisticamente",
        "categoria con meno di 5 righe",
    ),
    "POLICY_APPROVAL_REQUIRED": (
        "policy", "richiede approvazione", "richiede approvazione"
    ),
    "POLICY_MISSING_APPROVER": (
        "non conformità",
        "non conforme",
        "non conforme: supera soglia senza approvatore assegnato",
    ),
}
EXPECTED_COUNTS = {
    "COMPLETENESS_MISSING_ID_SPESA": 1,
    "COMPLETENESS_MISSING_DATA_SPESA": 1,
    "COMPLETENESS_MISSING_DIPENDENTE": 1,
    "COMPLETENESS_MISSING_CATEGORIA": 1,
    "COMPLETENESS_MISSING_IMPORTO": 1,
    "COMPLETENESS_MISSING_PROGETTO": 1,
    "UNIQUENESS_ID_DUPLICATE": 6,
    "UNIQUENESS_LOGICAL_DUPLICATE": 6,
    "VALIDITY_NON_NUMERIC_ID": 1,
    "VALIDITY_INVALID_DATE": 3,
    "VALIDITY_NEGATIVE_AMOUNT": 2,
    "VALIDITY_NON_NUMERIC_AMOUNT": 2,
    "VALIDITY_INVALID_CATEGORY": 2,
    "STATISTICAL_AMOUNT_ANOMALY": 5,
    "STATISTICAL_NOT_EVALUABLE": 4,
    "POLICY_APPROVAL_REQUIRED": 4,
    "POLICY_MISSING_APPROVER": 2,
}


def amount_text(value: Decimal, comma: bool) -> str:
    text = f"{value.quantize(Decimal('0.01')):.2f}"
    return text.replace(".", ",") if comma else text


def parse_amount(value: str) -> Decimal | None:
    try:
        return Decimal(value.strip().replace(",", ".")) if value.strip() else None
    except InvalidOperation:
        return None


def normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def generate_valid_rows() -> list[dict[str, str]]:
    rng = random.Random(SEED)
    categories = [
        category
        for category, count in CATEGORY_COUNTS.items()
        if category != "Formazione"
        for _ in range(count)
    ]
    rng.shuffle(categories)
    categories.extend(["Formazione"] * 4)

    rows = []
    for index, category in enumerate(categories):
        day = WEEK_START + timedelta(days=rng.randrange(5))
        amount = BASE_AMOUNTS[category] + Decimal(rng.randrange(-4, 5))
        rows.append({
            "id_spesa": str(100001 + index),
            "data_spesa": day.strftime("%d/%m/%Y"),
            "dipendente": f"Cognome{index + 1:03d} Nome{index + 1:03d}",
            "centro_di_costo": "" if index % 7 == 0 else f"CDC-{index % 24 + 1:03d}",
            "categoria": category,
            "descrizione": "" if index % 5 == 0 else f"Spesa sintetica {index + 1:03d}",
            "importo": amount_text(amount, index % 2 == 0),
            "valuta_originale": "USD" if index % 29 == 0 else "",
            "progetto": f"PRJ-2026-{index % 20 + 1:03d}",
            "approvatore": "",
        })
    return rows


def mark(
    truth: list[dict[str, str]],
    rows: list[dict[str, str]],
    index: int,
    rule_id: str,
    field: str,
    note: str,
) -> None:
    anomaly_type, status, message = RULES[rule_id]
    truth.append({
        "source_row_number": str(index + 1),
        "id_spesa": rows[index]["id_spesa"],
        "rule_id": rule_id,
        "anomaly_type": anomaly_type,
        "field": field,
        "expected_status": status,
        "expected_message": message,
        "note": note,
    })


def add_basic_scenarios(
    rows: list[dict[str, str]], truth: list[dict[str, str]]
) -> None:
    missing = [
        (0, "id_spesa", "", "COMPLETENESS_MISSING_ID_SPESA"),
        (1, "data_spesa", "", "COMPLETENESS_MISSING_DATA_SPESA"),
        (2, "dipendente", "   ", "COMPLETENESS_MISSING_DIPENDENTE"),
        (3, "categoria", "", "COMPLETENESS_MISSING_CATEGORIA"),
        (4, "importo", "", "COMPLETENESS_MISSING_IMPORTO"),
        (5, "progetto", "   ", "COMPLETENESS_MISSING_PROGETTO"),
    ]
    for index, field, value, rule_id in missing:
        rows[index][field] = value
        mark(truth, rows, index, rule_id, field, f"{field} intenzionalmente mancante")

    rows[6]["id_spesa"] = "ID-DEMO"
    mark(truth, rows, 6, "VALIDITY_NON_NUMERIC_ID", "id_spesa", "ID non numerico")

    for index, value in zip(range(7, 10), ["31/02/2026", "15/13/2026", "2026-07-14"]):
        rows[index]["data_spesa"] = value
        mark(truth, rows, index, "VALIDITY_INVALID_DATE", "data_spesa", value)
    for index, value in zip(range(10, 12), ["-12,50", "-7.25"]):
        rows[index]["importo"] = value
        mark(truth, rows, index, "VALIDITY_NEGATIVE_AMOUNT", "importo", value)
    for index, value in zip(range(12, 14), ["non-numerico", "EUR trenta"]):
        rows[index]["importo"] = value
        mark(truth, rows, index, "VALIDITY_NON_NUMERIC_AMOUNT", "importo", value)
    for index, value in zip(range(14, 16), ["CategoriaDemoA", "CategoriaDemoB"]):
        rows[index]["categoria"] = value
        mark(truth, rows, index, "VALIDITY_INVALID_CATEGORY", "categoria", value)


def add_duplicate_scenarios(
    rows: list[dict[str, str]], truth: list[dict[str, str]]
) -> None:
    for first, second in [(16, 17), (18, 19), (20, 21)]:
        rows[second]["id_spesa"] = rows[first]["id_spesa"]
        for index in (first, second):
            mark(truth, rows, index, "UNIQUENESS_ID_DUPLICATE", "id_spesa", "Coppia ID")

    for pair, (first, second) in enumerate([(22, 23), (24, 25), (26, 27)], 1):
        employee = f"Cognome{90 + pair:03d} Nome{90 + pair:03d}"
        value = Decimal("35.50") + pair
        shared = {
            "data_spesa": (WEEK_START + timedelta(days=pair - 1)).strftime("%d/%m/%Y"),
            "categoria": "Vitto",
        }
        rows[first].update(shared | {
            "dipendente": employee,
            "importo": amount_text(value, True),
        })
        rows[second].update(shared | {
            "dipendente": employee,
            "importo": amount_text(value, False),
        })
        if pair == 1:
            rows[first]["dipendente"] = f"  {employee.upper()} "
            rows[second]["dipendente"] = employee.lower()
        for index in (first, second):
            mark(truth, rows, index, "UNIQUENESS_LOGICAL_DUPLICATE", "", f"Coppia {pair}")


def available_row(rows: list[dict[str, str]], category: str, used: set[int]) -> int:
    return next(
        index for index in range(28, 296)
        if index not in used and rows[index]["categoria"] == category
    )


def add_statistical_and_policy_scenarios(
    rows: list[dict[str, str]], truth: list[dict[str, str]]
) -> None:
    used = set(range(28))
    for category, value in STAT_AMOUNTS.items():
        index = available_row(rows, category, used)
        used.add(index)
        rows[index]["importo"] = amount_text(value, index % 2 == 0)
        if category == "Materiale":
            rows[index]["approvatore"] = "Approvatore001 Demo"
        mark(truth, rows, index, "STATISTICAL_AMOUNT_ANOMALY", "importo", category)
        if value > THRESHOLDS[category]:
            mark(truth, rows, index, "POLICY_APPROVAL_REQUIRED", "importo", category)
            if not rows[index]["approvatore"]:
                mark(truth, rows, index, "POLICY_MISSING_APPROVER", "approvatore", category)

    formation = list(range(296, 300))
    formation_values = [Decimal("550"), Decimal("600"), Decimal("200"), Decimal("250")]
    for position, (index, value) in enumerate(zip(formation, formation_values)):
        rows[index]["importo"] = amount_text(value, position % 2 == 0)
        rows[index]["approvatore"] = "Approvatore002 Demo" if position == 0 else ""
        mark(truth, rows, index, "STATISTICAL_NOT_EVALUABLE", "categoria", "Formazione")
        if value > THRESHOLDS["Formazione"]:
            mark(truth, rows, index, "POLICY_APPROVAL_REQUIRED", "importo", "Formazione")
            if not rows[index]["approvatore"]:
                mark(
                    truth, rows, index, "POLICY_MISSING_APPROVER",
                    "approvatore", "Formazione"
                )


def category_medians(rows: list[dict[str, str]]) -> dict[str, Decimal]:
    values: dict[str, list[Decimal]] = defaultdict(list)
    for row in rows:
        amount = parse_amount(row["importo"])
        if row["categoria"] in CATEGORY_COUNTS and amount is not None and amount >= 0:
            values[row["categoria"]].append(amount)
    medians = {}
    for category, items in values.items():
        ordered = sorted(items)
        middle = len(ordered) // 2
        medians[category] = (
            ordered[middle] if len(ordered) % 2
            else (ordered[middle - 1] + ordered[middle]) / 2
        )
    return medians


def validate(
    rows: list[dict[str, str]], truth: list[dict[str, str]]
) -> None:
    if len(rows) != ROW_COUNT or any(list(row) != EXPENSE_COLUMNS for row in rows):
        raise ValueError("Dataset non conforme per numero di righe o schema")
    if Counter(row["categoria"] for row in rows)["Formazione"] != 4:
        raise ValueError("Formazione non contiene esattamente 4 righe")
    if Counter(item["rule_id"] for item in truth) != Counter(EXPECTED_COUNTS):
        raise ValueError("Conteggi rule_id non conformi")
    if any(not 1 <= int(item["source_row_number"]) <= ROW_COUNT for item in truth):
        raise ValueError("source_row_number fuori intervallo")
    signatures = {tuple(item[column] for column in TRUTH_COLUMNS) for item in truth}
    if len(signatures) != len(truth):
        raise ValueError("Record ground truth identici")

    invalid_categories = [
        row for row in rows if row["categoria"] and row["categoria"] not in CATEGORY_COUNTS
    ]
    if len(invalid_categories) != 2:
        raise ValueError("Categorie grezze non valide diverse da 2")

    id_groups: dict[str, int] = Counter(
        row["id_spesa"] for row in rows if row["id_spesa"]
    )
    if sorted(id_groups.values()).count(2) != 3 or max(id_groups.values()) != 2:
        raise ValueError("Coppie con id_spesa duplicato non conformi")

    logical: dict[tuple[str, str, Decimal, str], list[str]] = defaultdict(list)
    for row in rows:
        amount = parse_amount(row["importo"])
        if (
            row["dipendente"].strip() and row["data_spesa"].strip()
            and amount is not None and amount >= 0
            and row["categoria"] in CATEGORY_COUNTS
        ):
            key = (
                normalize(row["dipendente"]), row["data_spesa"],
                amount, normalize(row["categoria"])
            )
            logical[key].append(row["id_spesa"])
    logical_pairs = [
        ids for ids in logical.values() if len(ids) == 2 and len(set(ids)) == 2
    ]
    if len(logical_pairs) != 3:
        raise ValueError("Coppie di duplicati logici diverse da 3")

    medians = category_medians(rows)
    statistical_rows = [
        index for index, row in enumerate(rows)
        if row["categoria"] != "Formazione"
        and row["categoria"] in CATEGORY_COUNTS
        and (value := parse_amount(row["importo"])) is not None
        and value >= 0 and value > medians[row["categoria"]] * 3
    ]
    policy_rows = [
        index for index, row in enumerate(rows)
        if row["categoria"] in CATEGORY_COUNTS
        and (value := parse_amount(row["importo"])) is not None
        and value > THRESHOLDS[row["categoria"]]
    ]
    missing_approvers = [
        index for index in policy_rows if not rows[index]["approvatore"].strip()
    ]
    if (len(statistical_rows), len(policy_rows), len(missing_approvers)) != (5, 4, 2):
        raise ValueError("Conteggi statistici o policy non conformi")

    error_rows = {int(item["source_row_number"]) - 1 for item in truth}
    if (ROW_COUNT - len(error_rows)) / ROW_COUNT < 0.80:
        raise ValueError("Meno dell'80% delle righe è senza errori intenzionali")


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = generate_valid_rows()
    truth: list[dict[str, str]] = []
    add_basic_scenarios(rows, truth)
    add_duplicate_scenarios(rows, truth)
    add_statistical_and_policy_scenarios(rows, truth)
    truth.sort(key=lambda item: (int(item["source_row_number"]), item["rule_id"]))
    validate(rows, truth)
    write_csv(root / "data/synthetic_expenses.csv", EXPENSE_COLUMNS, rows)
    write_csv(root / "data/expected_anomalies.csv", TRUTH_COLUMNS, truth)
    error_rows = {item["source_row_number"] for item in truth}
    print(
        f"Generazione completata: {len(rows)} spese, {len(truth)} segnalazioni, "
        f"{len(rows) - len(error_rows)} righe senza errori intenzionali."
    )


if __name__ == "__main__":
    main()
