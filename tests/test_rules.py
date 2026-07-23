"""Unit tests for normalization and deterministic rule families."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from expense_quality_monitor.config import EXPECTED_COLUMNS
from expense_quality_monitor.normalization import (
    normalize_expenses,
    parse_amount,
    parse_expense_date,
)
from expense_quality_monitor.rules.completeness import check_completeness
from expense_quality_monitor.rules.policy import check_policy
from expense_quality_monitor.rules.statistical import check_statistical
from expense_quality_monitor.rules.uniqueness import check_uniqueness
from expense_quality_monitor.rules.validity import check_validity


def _row(number: int, **changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "source_row_number": number,
        "id_spesa": str(number),
        "data_spesa": "13/07/2026",
        "dipendente": f"Cognome{number} Nome{number}",
        "centro_di_costo": "",
        "categoria": "Vitto",
        "descrizione": "",
        "importo": "10.00",
        "valuta_originale": "",
        "progetto": "PRJ-TEST",
        "approvatore": "",
    }
    row.update(changes)
    return row


def _working(*rows: dict[str, object]) -> pd.DataFrame:
    columns = ("source_row_number", *EXPECTED_COLUMNS)
    return normalize_expenses(pd.DataFrame(rows, columns=columns))


def _rule_ids(findings: pd.DataFrame) -> list[str]:
    return findings["rule_id"].tolist()


def test_normalization_preserves_raw_values_and_creates_decimal_work_value() -> None:
    data = _working(
        _row(
            1,
            dipendente="  ROSSI   Mario ",
            importo="10,50",
            approvatore="   ",
        )
    )

    assert data.loc[0, "dipendente"] == "  ROSSI   Mario "
    assert data.loc[0, "_employee_normalized"] == "rossi mario"
    assert data.loc[0, "_amount_parsed"] == Decimal("10.50")
    assert bool(data.loc[0, "_approver_missing"])


@pytest.mark.parametrize(
    ("value", "valid"),
    [
        ("01/01/2026", True),
        ("1/01/2026", False),
        ("01/1/2026", False),
        ("29/02/2024", True),
        ("29/02/2025", False),
    ],
)
def test_date_parser_enforces_exact_format_and_calendar(value: str, valid: bool) -> None:
    assert (parse_expense_date(value) is not None) is valid


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10,50", Decimal("10.50")),
        ("10.50", Decimal("10.50")),
        ("10,5.0", None),
        ("10.5.0", None),
        ("dieci", None),
    ],
)
def test_amount_parser_accepts_one_decimal_separator_only(
    value: str,
    expected: Decimal | None,
) -> None:
    assert parse_amount(value) == expected


def test_completeness_reports_each_missing_required_field() -> None:
    data = _working(
        _row(
            1,
            id_spesa="",
            data_spesa=" ",
            dipendente="",
            categoria="   ",
            importo="",
            progetto=" ",
        )
    )

    assert set(_rule_ids(check_completeness(data))) == {
        "COMPLETENESS_MISSING_ID_SPESA",
        "COMPLETENESS_MISSING_DATA_SPESA",
        "COMPLETENESS_MISSING_DIPENDENTE",
        "COMPLETENESS_MISSING_CATEGORIA",
        "COMPLETENESS_MISSING_IMPORTO",
        "COMPLETENESS_MISSING_PROGETTO",
    }
    assert check_validity(data).empty


def test_validity_reports_each_invalid_present_value() -> None:
    data = _working(
        _row(1, id_spesa="ABC"),
        _row(2, data_spesa="31/02/2026"),
        _row(3, importo="dieci"),
        _row(4, importo="-1,25"),
        _row(5, categoria="vitto"),
    )

    assert set(_rule_ids(check_validity(data))) == {
        "VALIDITY_NON_NUMERIC_ID",
        "VALIDITY_INVALID_DATE",
        "VALIDITY_NON_NUMERIC_AMOUNT",
        "VALIDITY_NEGATIVE_AMOUNT",
        "VALIDITY_INVALID_CATEGORY",
    }


def test_duplicate_identifier_marks_all_group_members() -> None:
    data = _working(
        _row(1, id_spesa="10"),
        _row(2, id_spesa="10"),
        _row(3, id_spesa="11"),
    )
    findings = check_uniqueness(data)
    duplicate_ids = findings[findings["rule_id"] == "UNIQUENESS_ID_DUPLICATE"]

    assert duplicate_ids["source_row_number"].tolist() == [1, 2]


def test_same_identifier_is_not_automatically_a_logical_duplicate() -> None:
    data = _working(
        _row(1, id_spesa="10", dipendente="Rossi Mario"),
        _row(2, id_spesa="10", dipendente="Rossi Mario"),
    )
    findings = check_uniqueness(data)

    assert _rule_ids(findings).count("UNIQUENESS_ID_DUPLICATE") == 2
    assert "UNIQUENESS_LOGICAL_DUPLICATE" not in _rule_ids(findings)


def test_logical_duplicate_uses_normalized_values_and_different_ids() -> None:
    data = _working(
        _row(
            1,
            id_spesa="10",
            dipendente="  ROSSI   MARIO ",
            importo="15,50",
        ),
        _row(
            2,
            id_spesa="11",
            dipendente="rossi mario",
            importo="15.50",
        ),
    )
    findings = check_uniqueness(data)
    logical = findings[findings["rule_id"] == "UNIQUENESS_LOGICAL_DUPLICATE"]

    assert logical["source_row_number"].tolist() == [1, 2]


def test_distinct_present_non_numeric_ids_can_still_be_logical_duplicates() -> None:
    data = _working(
        _row(1, id_spesa="A", dipendente="Rossi Mario"),
        _row(2, id_spesa="B", dipendente="rossi mario"),
    )

    assert _rule_ids(check_uniqueness(data)).count("UNIQUENESS_LOGICAL_DUPLICATE") == 2
    assert _rule_ids(check_validity(data)).count("VALIDITY_NON_NUMERIC_ID") == 2


def test_invalid_or_missing_values_do_not_create_logical_duplicates() -> None:
    data = _working(
        _row(1, id_spesa="10", dipendente="", importo="non numerico"),
        _row(2, id_spesa="11", dipendente=" ", importo="non numerico"),
        _row(3, id_spesa="12", data_spesa="31/02/2026"),
        _row(4, id_spesa="13", data_spesa="31/02/2026"),
        _row(5, id_spesa="14", categoria="vitto"),
        _row(6, id_spesa="15", categoria="vitto"),
    )

    assert "UNIQUENESS_LOGICAL_DUPLICATE" not in _rule_ids(check_uniqueness(data))


def test_category_with_fewer_than_five_usable_observations_is_not_evaluable() -> None:
    data = _working(
        *[_row(number, categoria="Formazione", importo="100") for number in range(1, 5)]
    )
    findings = check_statistical(data)

    assert _rule_ids(findings) == ["STATISTICAL_NOT_EVALUABLE"] * 4


def test_statistics_exclude_invalid_categories_and_amounts() -> None:
    data = _working(
        *[_row(number, importo="10") for number in range(1, 5)],
        _row(5, importo="-1"),
        _row(6, importo="testo"),
        _row(7, categoria="vitto", importo="10"),
    )
    findings = check_statistical(data)

    assert findings["source_row_number"].tolist() == [1, 2, 3, 4]
    assert _rule_ids(findings) == ["STATISTICAL_NOT_EVALUABLE"] * 4


def test_statistical_threshold_is_strictly_greater_than_three_times_median() -> None:
    equal_limit = _working(
        *[
            _row(number, importo=amount)
            for number, amount in enumerate(
                ["10", "10", "10", "10", "30"],
                start=1,
            )
        ]
    )
    above_limit = _working(
        *[
            _row(number, importo=amount)
            for number, amount in enumerate(
                ["10", "10", "10", "10", "30.01"],
                start=1,
            )
        ]
    )

    assert "STATISTICAL_AMOUNT_ANOMALY" not in _rule_ids(check_statistical(equal_limit))
    assert _rule_ids(check_statistical(above_limit)).count("STATISTICAL_AMOUNT_ANOMALY") == 1


def test_policy_with_approver_requires_approval_without_nonconformity() -> None:
    data = _working(_row(1, importo="80.01", approvatore="Approvatore Demo"))

    assert _rule_ids(check_policy(data)) == ["POLICY_APPROVAL_REQUIRED"]


def test_amount_equal_to_policy_threshold_does_not_require_approval() -> None:
    data = _working(_row(1, importo="80", approvatore=""))

    assert check_policy(data).empty


@pytest.mark.parametrize("approver", [None, "", "   "])
def test_policy_treats_null_empty_and_whitespace_approver_as_absent(
    approver: object,
) -> None:
    data = _working(_row(1, importo="80.01", approvatore=approver))

    assert _rule_ids(check_policy(data)) == [
        "POLICY_APPROVAL_REQUIRED",
        "POLICY_MISSING_APPROVER",
    ]


def test_statistical_anomaly_can_overlap_policy() -> None:
    data = _working(
        *[
            _row(
                number,
                categoria="Materiale",
                importo=amount,
                approvatore="Approvatore Demo",
            )
            for number, amount in enumerate(
                ["30", "30", "30", "30", "160"],
                start=1,
            )
        ]
    )

    combined = pd.concat(
        [check_statistical(data), check_policy(data)],
        ignore_index=True,
    )
    anomaly_row = combined[combined["source_row_number"] == 5]
    assert set(anomaly_row["rule_id"]) == {
        "STATISTICAL_AMOUNT_ANOMALY",
        "POLICY_APPROVAL_REQUIRED",
    }
