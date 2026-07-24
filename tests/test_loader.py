"""Tests for CSV loading, schema validation, and raw-value preservation."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import pytest

from expense_quality_monitor.config import EXPECTED_COLUMNS, FINDING_COLUMNS
from expense_quality_monitor.loader import (
    CsvLoadError,
    compare_schema,
    detect_csv_format,
    load_expenses,
    normalize_column_name,
)
from expense_quality_monitor.pipeline import analyze_expenses
from expense_quality_monitor.reporting import findings_to_csv

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "data" / "synthetic_expenses.csv"
VALID_ROW = (
    "100001",
    "13/07/2026",
    "Cognome001 Nome001",
    "CDC-001",
    "Vitto",
    "Spesa sintetica",
    "25.00",
    "",
    "PRJ-2026-001",
    "Approvatore001 Demo",
)


def expense_csv(
    columns: tuple[str, ...] = EXPECTED_COLUMNS,
    row: tuple[str, ...] = VALID_ROW,
    *,
    delimiter: str = ",",
) -> str:
    """Build one deterministic expense CSV for loader tests."""
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerow(columns)
    writer.writerow(row)
    return output.getvalue()


def test_loader_preserves_text_adds_row_numbers_and_accepts_extra_columns() -> None:
    columns = (*EXPECTED_COLUMNS, "colonna_extra_a", "colonna_extra_b")
    row = (*VALID_ROW, "extra-a", "extra-b")

    loaded = load_expenses(StringIO(expense_csv(columns, row)))

    assert loaded.loc[0, "source_row_number"] == 1
    assert loaded.loc[0, "importo"] == "25.00"
    assert loaded.loc[0, "colonna_extra_a"] == "extra-a"
    assert loaded.loc[0, "colonna_extra_b"] == "extra-b"


def test_loader_preserves_extra_column_that_conflicts_with_technical_row_number() -> None:
    columns = (*EXPECTED_COLUMNS, "source_row_number")
    row = (*VALID_ROW, "valore-originale")

    loaded = load_expenses(StringIO(expense_csv(columns, row)))

    assert loaded.loc[0, "source_row_number"] == 1
    assert loaded.loc[0, "source_row_number_input"] == "valore-originale"


def test_compare_schema_orders_missing_canonically_and_extras_alphabetically() -> None:
    comparison = compare_schema([" progetto ", "Zeta", "id_spesa", "alfa"])

    assert comparison.found_columns == ("progetto", "Zeta", "id_spesa", "alfa")
    assert comparison.missing_columns == tuple(
        column for column in EXPECTED_COLUMNS if column not in {"progetto", "id_spesa"}
    )
    assert comparison.extra_columns == ("alfa", "Zeta")
    assert not comparison.is_compatible


@pytest.mark.parametrize(
    ("columns", "expected_first_column"),
    [
        (tuple(f" {column} " for column in EXPECTED_COLUMNS), "id_spesa"),
        (tuple(column.upper() for column in EXPECTED_COLUMNS), "id_spesa"),
        ((f"\ufeff{EXPECTED_COLUMNS[0]}", *EXPECTED_COLUMNS[1:]), "id_spesa"),
    ],
)
def test_loader_normalizes_spaces_case_and_bom_in_headers(
    columns: tuple[str, ...],
    expected_first_column: str,
) -> None:
    loaded = load_expenses(StringIO(expense_csv(columns)))

    assert loaded.columns[1] == expected_first_column
    assert tuple(loaded.columns[1:]) == EXPECTED_COLUMNS


@pytest.mark.parametrize("delimiter", [",", ";"])
def test_loader_detects_supported_delimiters(delimiter: str) -> None:
    content = expense_csv(delimiter=delimiter)

    assert detect_csv_format(content) == delimiter
    loaded = load_expenses(StringIO(content))
    assert tuple(loaded.columns[1:]) == EXPECTED_COLUMNS


def test_loader_accepts_utf8_bytes_with_bom() -> None:
    content = expense_csv().encode("utf-8-sig")

    loaded = load_expenses(BytesIO(content))

    assert tuple(loaded.columns[1:]) == EXPECTED_COLUMNS


def test_loader_exposes_real_schema_details_when_columns_are_missing() -> None:
    content = "sepal_length,sepal_width,species\n5.1,3.5,setosa\n"

    with pytest.raises(CsvLoadError) as captured:
        load_expenses(StringIO(content))

    error = captured.value
    assert error.code == "incompatible_schema"
    assert error.schema is not None
    assert error.schema.missing_columns == EXPECTED_COLUMNS
    assert error.schema.found_columns == ("sepal_length", "sepal_width", "species")
    assert error.schema.extra_columns == ("sepal_length", "sepal_width", "species")


@pytest.mark.parametrize("content", ["", "   \n"])
def test_loader_reports_empty_files(content: str) -> None:
    with pytest.raises(CsvLoadError, match="Il file è vuoto") as captured:
        load_expenses(StringIO(content))

    assert captured.value.code == "empty"


def test_loader_reports_header_without_data_as_empty() -> None:
    with pytest.raises(CsvLoadError, match="Il file è vuoto") as captured:
        load_expenses(StringIO(",".join(EXPECTED_COLUMNS)))

    assert captured.value.code == "empty"


def test_loader_treats_a_data_row_without_header_as_incompatible_schema() -> None:
    with pytest.raises(CsvLoadError) as captured:
        load_expenses(StringIO(",".join(VALID_ROW)))

    assert captured.value.code == "incompatible_schema"
    assert captured.value.schema is not None
    assert captured.value.schema.missing_columns == EXPECTED_COLUMNS


@pytest.mark.parametrize(
    "source",
    [
        BytesIO(b"\xff\xfe\x00"),
        StringIO("id_spesa|data_spesa\n1|13/07/2026\n"),
        StringIO('id_spesa,data_spesa\n"valore non chiuso,13/07/2026\n'),
    ],
)
def test_loader_reports_unreadable_content(source: BytesIO | StringIO) -> None:
    with pytest.raises(CsvLoadError, match="non può essere letto") as captured:
        load_expenses(source)

    assert captured.value.code == "unreadable"


@pytest.mark.parametrize(
    "columns",
    [
        ("id_spesa", "id_spesa", *EXPECTED_COLUMNS[1:]),
        ("id_spesa", " ID_SPESA ", *EXPECTED_COLUMNS[1:]),
    ],
)
def test_loader_rejects_duplicate_columns_after_normalization(
    columns: tuple[str, ...],
) -> None:
    row = ("100001", "100002", *VALID_ROW[1:])

    with pytest.raises(CsvLoadError, match="stesso nome") as captured:
        load_expenses(StringIO(expense_csv(columns, row)))

    assert captured.value.code == "duplicate_columns"


def test_extra_columns_do_not_change_findings_or_export() -> None:
    original = pd.read_csv(EXAMPLE_PATH, dtype=str, keep_default_na=False)
    extended = original.assign(extra_zeta="z", extra_alfa="a")
    extended_csv = StringIO()
    extended.to_csv(extended_csv, index=False)
    extended_csv.seek(0)

    expected = analyze_expenses(EXAMPLE_PATH)
    actual = analyze_expenses(extended_csv)

    pd.testing.assert_frame_equal(actual.findings, expected.findings)
    assert findings_to_csv(actual.findings.loc[:, FINDING_COLUMNS]) == findings_to_csv(
        expected.findings.loc[:, FINDING_COLUMNS]
    )
    assert actual.summary["total_rows"] == 300
    assert actual.summary["rows_with_findings"] == 37
    assert len(actual.findings) == 43
    assert actual.findings["rule_id"].nunique() == 17


def test_semicolon_example_preserves_confirmed_results() -> None:
    original = pd.read_csv(EXAMPLE_PATH, dtype=str, keep_default_na=False)
    converted = StringIO()
    original.to_csv(converted, index=False, sep=";")
    converted.seek(0)

    result = analyze_expenses(converted)

    assert result.summary["total_rows"] == 300
    assert result.summary["rows_with_findings"] == 37
    assert len(result.findings) == 43
    assert result.findings["rule_id"].nunique() == 17


def test_normalize_column_name_only_applies_documented_transformations() -> None:
    assert normalize_column_name("\ufeff ID_SPESA ") == "id_spesa"
    assert normalize_column_name("price") == "price"
