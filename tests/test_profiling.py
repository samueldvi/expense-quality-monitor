"""Tests for deterministic dataset profiling and canonical column metadata."""

from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from expense_quality_monitor.config import (
    COLUMN_METADATA,
    EXPECTED_COLUMNS,
    QUALITY_DIMENSIONS,
    REQUIRED_FIELDS,
    RULE_CATALOG,
    RULE_TARGET_FIELDS,
)
from expense_quality_monitor.profiling import (
    build_column_profile,
    build_data_dictionary,
    build_data_profile,
)


def source_frame() -> pd.DataFrame:
    """Return a small source with valid, invalid, missing, and extra values."""
    return pd.DataFrame(
        {
            "source_row_number": [2, 3, 4, 5],
            "id_spesa": ["100", "101", None, "103"],
            "data_spesa": ["01/01/2026", "29/02/2025", "31/12/2026", "  "],
            "dipendente": ["Cognome001 Nome001", "", "Cognome003 Nome003", pd.NA],
            "centro_di_costo": ["CDC-001", "CDC-001", None, " "],
            "categoria": ["Vitto", "Vitto", "Trasporto", "Materiale"],
            "descrizione": ["Pranzo", "Pranzo", "", float("nan")],
            "importo": ["10,50", "-2", "testo", "20.00"],
            "valuta_originale": ["EUR", "EUR", None, ""],
            "progetto": ["PRJ-2026-001", "PRJ-2026-001", "PRJ-2026-002", " "],
            "approvatore": ["Cognome010 Nome010", None, "", "Cognome011 Nome011"],
            "extra_note": ["A", "A", "", "B"],
        }
    )


def findings_frame() -> pd.DataFrame:
    """Return explicit findings covering direct and multi-field associations."""
    return pd.DataFrame(
        [
            {
                "source_row_number": 2,
                "rule_id": "VALIDITY_NON_NUMERIC_ID",
                "field": "id_spesa",
            },
            {
                "source_row_number": 2,
                "rule_id": "UNIQUENESS_ID_DUPLICATE",
                "field": "id_spesa",
            },
            {
                "source_row_number": 3,
                "rule_id": "UNIQUENESS_ID_DUPLICATE",
                "field": "id_spesa",
            },
            {
                "source_row_number": 2,
                "rule_id": "UNIQUENESS_LOGICAL_DUPLICATE",
                "field": "",
            },
            {
                "source_row_number": 3,
                "rule_id": "UNIQUENESS_LOGICAL_DUPLICATE",
                "field": "",
            },
            {
                "source_row_number": 4,
                "rule_id": "VALIDITY_NON_NUMERIC_AMOUNT",
                "field": "importo",
            },
        ]
    )


def test_data_profile_keeps_structure_and_rule_results_distinct() -> None:
    profile = build_data_profile(source_frame(), findings_frame())

    assert profile.row_count == 4
    assert profile.source_column_count == 11
    assert profile.canonical_column_count == 10
    assert profile.extra_columns == ("extra_note",)
    assert profile.rows_with_findings == 3
    assert profile.finding_count == 6
    assert profile.duplicate_id_rows == 2
    assert profile.logical_duplicate_rows == 2
    assert profile.validity_finding_count == 2


def test_data_profile_is_deeply_immutable_for_its_declared_fields() -> None:
    profile = build_data_profile(source_frame(), findings_frame())

    assert isinstance(profile.extra_columns, tuple)
    with pytest.raises(FrozenInstanceError):
        setattr(profile, "row_count", 5)


def test_data_profile_ignores_findings_without_a_valid_source_row() -> None:
    findings = pd.concat(
        [
            findings_frame(),
            pd.DataFrame(
                [
                    {
                        "source_row_number": 999,
                        "rule_id": "UNIQUENESS_ID_DUPLICATE",
                        "field": "id_spesa",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    profile = build_data_profile(source_frame(), findings)
    columns = build_column_profile(source_frame(), findings).set_index("technical_name")

    assert profile.finding_count == 7
    assert profile.rows_with_findings == 3
    assert profile.duplicate_id_rows == 2
    assert columns.loc["id_spesa", "related_findings"] == 3


def test_column_profile_uses_canonical_then_source_extra_order() -> None:
    profile = build_column_profile(source_frame(), findings_frame())

    assert profile["technical_name"].tolist() == [
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
        "extra_note",
    ]
    assert profile["column_kind"].tolist() == ["canonical"] * 10 + ["extra"]


def test_missing_values_include_null_nan_empty_and_whitespace() -> None:
    profile = build_column_profile(source_frame(), findings_frame()).set_index("technical_name")

    assert profile.loc["dipendente", "missing_values"] == 2
    assert profile.loc["descrizione", "missing_values"] == 2
    assert profile.loc["valuta_originale", "missing_values"] == 2
    assert profile.loc["approvatore", "missing_values"] == 2
    assert profile.loc["dipendente", "completeness_percentage"] == 50.0


def test_zero_and_false_are_present_values() -> None:
    source = pd.DataFrame(
        {
            "source_row_number": [2, 3],
            "zero_value": [0, None],
            "boolean_value": [False, " "],
        }
    )

    profile = build_column_profile(source, pd.DataFrame()).set_index("technical_name")

    assert profile.loc["zero_value", "missing_values"] == 1
    assert profile.loc["zero_value", "distinct_values"] == 1
    assert profile.loc["boolean_value", "missing_values"] == 1
    assert profile.loc["boolean_value", "distinct_values"] == 1


def test_distinct_values_use_present_raw_values_without_normalization() -> None:
    source = source_frame()
    source.loc[1, "dipendente"] = " cognome001 nome001 "
    source["mixed_identifier"] = [1, "1", 1, "1"]

    profile = build_column_profile(source, findings_frame()).set_index("technical_name")

    assert profile.loc["dipendente", "distinct_values"] == 3
    assert profile.loc["extra_note", "distinct_values"] == 2
    assert profile.loc["mixed_identifier", "distinct_values"] == 2


def test_source_dtype_and_expected_type_remain_separate() -> None:
    source = source_frame()
    profile = build_column_profile(source, findings_frame()).set_index("technical_name")

    assert profile.loc["id_spesa", "source_dtype"] == str(source["id_spesa"].dtype)
    assert profile.loc["id_spesa", "expected_type"] == "integer"
    assert pd.isna(profile.loc["extra_note", "expected_type"])


def test_date_range_uses_only_strictly_valid_dates() -> None:
    profile = build_column_profile(source_frame(), findings_frame()).set_index("technical_name")

    assert profile.loc["data_spesa", "minimum_valid"] == "01/01/2026"
    assert profile.loc["data_spesa", "maximum_valid"] == "31/12/2026"


def test_amount_range_excludes_negative_and_non_numeric_values() -> None:
    profile = build_column_profile(source_frame(), findings_frame()).set_index("technical_name")

    assert profile.loc["importo", "minimum_valid"] == "10.50"
    assert profile.loc["importo", "maximum_valid"] == "20.00"
    assert pd.isna(profile.loc["categoria", "minimum_valid"])
    assert pd.isna(profile.loc["categoria", "maximum_valid"])


def test_ranges_are_empty_without_valid_dates_or_amounts() -> None:
    source = source_frame()
    source["data_spesa"] = ["1/01/2026", "29/02/2025", "", "testo"]
    source["importo"] = ["-1", "testo", "", "-0,01"]

    profile = build_column_profile(source, findings_frame()).set_index("technical_name")

    assert pd.isna(profile.loc["data_spesa", "minimum_valid"])
    assert pd.isna(profile.loc["data_spesa", "maximum_valid"])
    assert pd.isna(profile.loc["importo", "minimum_valid"])
    assert pd.isna(profile.loc["importo", "maximum_valid"])


def test_related_findings_reuse_field_and_expand_logical_duplicate_targets() -> None:
    profile = build_column_profile(source_frame(), findings_frame()).set_index("technical_name")

    assert profile.loc["id_spesa", "related_findings"] == 3
    assert profile.loc["dipendente", "related_findings"] == 2
    assert profile.loc["data_spesa", "related_findings"] == 2
    assert profile.loc["categoria", "related_findings"] == 2
    assert profile.loc["importo", "related_findings"] == 3
    assert profile.loc["centro_di_costo", "related_findings"] == 0


def test_empty_dataset_is_profiled_without_division_by_zero() -> None:
    source = pd.DataFrame(columns=["source_row_number", *EXPECTED_COLUMNS])
    findings = pd.DataFrame()

    summary = build_data_profile(source, findings)
    profile = build_column_profile(source, findings)

    assert summary.row_count == 0
    assert summary.rows_with_findings == 0
    assert profile["completeness_percentage"].tolist() == [0.0] * 10
    assert profile["missing_values"].tolist() == [0] * 10


def test_missing_canonical_columns_produce_an_explicit_partial_profile() -> None:
    source = pd.DataFrame(
        {
            "source_row_number": [2],
            "id_spesa": ["100001"],
            "extra_note": ["value"],
        }
    )

    summary = build_data_profile(source, pd.DataFrame())
    profile = build_column_profile(source, pd.DataFrame())

    assert summary.source_column_count == 2
    assert summary.canonical_column_count == 1
    assert summary.extra_columns == ("extra_note",)
    assert profile["technical_name"].tolist() == ["id_spesa", "extra_note"]


def test_profiling_does_not_mutate_source_or_findings() -> None:
    source = source_frame()
    findings = findings_frame()
    original_source = source.copy(deep=True)
    original_findings = findings.copy(deep=True)

    build_data_profile(source, findings)
    build_column_profile(source, findings)

    pd.testing.assert_frame_equal(source, original_source)
    pd.testing.assert_frame_equal(findings, original_findings)
    assert math.isnan(source.loc[3, "descrizione"])


def test_column_metadata_matches_the_confirmed_schema_and_required_fields() -> None:
    names = tuple(metadata.name for metadata in COLUMN_METADATA)

    assert names == (
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
    )
    assert len(names) == len(set(names))
    assert {metadata.name for metadata in COLUMN_METADATA if metadata.required} == REQUIRED_FIELDS


def test_rule_targets_and_quality_dimensions_are_supported() -> None:
    associated_rule_ids = set(RULE_TARGET_FIELDS)
    configured_dimensions = {
        dimension for metadata in COLUMN_METADATA for dimension in metadata.quality_dimensions
    }

    assert associated_rule_ids == set(RULE_CATALOG)
    assert all(
        field in EXPECTED_COLUMNS
        for target_fields in RULE_TARGET_FIELDS.values()
        for field in target_fields
    )
    assert configured_dimensions == set(QUALITY_DIMENSIONS)


def test_dictionary_contains_ten_language_independent_canonical_rows() -> None:
    dictionary = build_data_dictionary()

    assert dictionary["technical_name"].tolist() == [
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
    assert len(dictionary) == 10
    assert dictionary.loc[0, "label_key"] == "column.id_spesa.label"
    assert dictionary.loc[0, "description_key"] == "column.id_spesa.description"
    assert bool(dictionary.loc[0, "required"]) is True
    assert dictionary.loc[0, "expected_type"] == "integer"


def test_dictionary_reads_allowed_categories_from_the_canonical_configuration() -> None:
    dictionary = build_data_dictionary().set_index("technical_name")

    assert dictionary.loc["categoria", "allowed_values"] == (
        "Vitto",
        "Trasporto",
        "Alloggio",
        "Materiale",
        "Rappresentanza",
        "Formazione",
    )
    assert dictionary.loc["id_spesa", "allowed_values"] == ()
    assert dictionary.loc["categoria", "rules"][0] == "COMPLETENESS_MISSING_CATEGORIA"
    assert "validity" in dictionary.loc["categoria", "dimensions"]
