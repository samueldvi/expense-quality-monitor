"""Tests for pure, deterministic governance metadata and summaries."""

from datetime import UTC, datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pandas as pd
import pytest

from expense_quality_monitor.config import (
    MEDIAN_MULTIPLIER,
    MIN_STATISTICAL_OBSERVATIONS,
    POLICY_THRESHOLDS,
    QUALITY_DIMENSIONS,
    RULE_CATALOG,
    RULE_TARGET_FIELDS,
)
from expense_quality_monitor.governance import (
    RULE_CATALOG_COLUMNS,
    application_version,
    build_dimension_summary,
    build_processing_metadata,
    build_rule_catalog,
    calculate_sha256,
    filter_rule_catalog,
)
from expense_quality_monitor.loader import CsvFormatMetadata
from expense_quality_monitor.profiling import DataProfile

EXPECTED_RULE_IDS = (
    "COMPLETENESS_MISSING_ID_SPESA",
    "COMPLETENESS_MISSING_DATA_SPESA",
    "COMPLETENESS_MISSING_DIPENDENTE",
    "COMPLETENESS_MISSING_CATEGORIA",
    "COMPLETENESS_MISSING_IMPORTO",
    "COMPLETENESS_MISSING_PROGETTO",
    "UNIQUENESS_ID_DUPLICATE",
    "UNIQUENESS_LOGICAL_DUPLICATE",
    "VALIDITY_NON_NUMERIC_ID",
    "VALIDITY_INVALID_DATE",
    "VALIDITY_NEGATIVE_AMOUNT",
    "VALIDITY_NON_NUMERIC_AMOUNT",
    "VALIDITY_INVALID_CATEGORY",
    "STATISTICAL_AMOUNT_ANOMALY",
    "STATISTICAL_NOT_EVALUABLE",
    "POLICY_APPROVAL_REQUIRED",
    "POLICY_MISSING_APPROVER",
)


def sample_profile() -> DataProfile:
    """Return a small immutable profile for metadata tests."""
    return DataProfile(
        row_count=2,
        source_column_count=11,
        canonical_column_count=10,
        extra_columns=("nota_interna",),
        rows_with_findings=1,
        finding_count=1,
        duplicate_id_rows=0,
        logical_duplicate_rows=0,
        validity_finding_count=1,
    )


def test_calculate_sha256_uses_exact_original_bytes() -> None:
    assert calculate_sha256(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert calculate_sha256(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    assert calculate_sha256(b"\xef\xbb\xbfabc") != calculate_sha256(b"abc")


def test_processing_metadata_is_immutable_complete_and_normalizes_to_utc() -> None:
    source_time = datetime(2026, 7, 27, 12, 30, tzinfo=timezone(timedelta(hours=2)))
    metadata = build_processing_metadata(
        source_name="spese.csv",
        content=b"a,b\n1,2\n",
        profile=sample_profile(),
        csv_format=CsvFormatMetadata(delimiter=",", encoding="utf-8", has_bom=False),
        analyzed_at_utc=source_time,
        installed_version="0.1.0",
    )

    assert metadata.source_name == "spese.csv"
    assert metadata.source_size_bytes == 8
    assert metadata.analyzed_at_utc == datetime(2026, 7, 27, 10, 30, tzinfo=UTC)
    assert metadata.analyzed_at_utc.tzinfo is UTC
    assert metadata.row_count == 2
    assert metadata.source_column_count == 11
    assert metadata.canonical_column_count == 10
    assert metadata.extra_columns == ("nota_interna",)
    assert metadata.delimiter == ","
    assert metadata.encoding == "utf-8"
    assert metadata.has_bom is False
    assert metadata.application_version == "0.1.0"
    with pytest.raises(AttributeError):
        metadata.source_name = "altro.csv"  # type: ignore[misc]


def test_processing_metadata_rejects_a_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_processing_metadata(
            source_name="spese.csv",
            content=b"a,b\n1,2\n",
            profile=sample_profile(),
            csv_format=CsvFormatMetadata(",", "utf-8", False),
            analyzed_at_utc=datetime.fromisoformat("2026-07-27T10:30:00"),
            installed_version=None,
        )


def test_application_version_returns_none_only_when_distribution_is_unavailable() -> None:
    with patch("expense_quality_monitor.governance.version", return_value="2.3.4"):
        assert application_version() == "2.3.4"
    with patch(
        "expense_quality_monitor.governance.version",
        side_effect=PackageNotFoundError,
    ):
        assert application_version() is None


def test_rule_catalog_contains_all_canonical_rules_and_no_severity() -> None:
    catalog = build_rule_catalog()

    assert tuple(catalog.columns) == RULE_CATALOG_COLUMNS
    assert tuple(catalog["rule_id"]) == EXPECTED_RULE_IDS
    assert set(catalog["rule_id"]) == set(RULE_CATALOG)
    assert len(catalog) == 17
    assert catalog["rule_id"].is_unique
    assert tuple(QUALITY_DIMENSIONS) == (
        "completeness",
        "validity",
        "uniqueness",
        "statistical_anomaly",
        "policy_compliance",
    )
    assert set(catalog["dimension"]) == {
        "completeness",
        "validity",
        "uniqueness",
        "statistical_anomaly",
        "policy_compliance",
    }
    assert "severity" not in catalog.columns
    assert catalog.set_index("rule_id")["fields"].to_dict() == dict(RULE_TARGET_FIELDS)


def test_rule_catalog_exposes_only_confirmed_parameters() -> None:
    catalog = build_rule_catalog().set_index("rule_id")

    assert (
        catalog.at["UNIQUENESS_LOGICAL_DUPLICATE", "parameter_value"]
        == RULE_TARGET_FIELDS["UNIQUENESS_LOGICAL_DUPLICATE"]
    )
    assert catalog.at["STATISTICAL_AMOUNT_ANOMALY", "parameter_value"] == MEDIAN_MULTIPLIER
    assert (
        catalog.at["STATISTICAL_NOT_EVALUABLE", "parameter_value"] == MIN_STATISTICAL_OBSERVATIONS
    )
    assert catalog.at["POLICY_APPROVAL_REQUIRED", "parameter_value"] == tuple(
        POLICY_THRESHOLDS.items()
    )
    assert catalog.at["POLICY_MISSING_APPROVER", "parameter_value"] == tuple(
        POLICY_THRESHOLDS.items()
    )
    assert pd.isna(catalog.at["VALIDITY_INVALID_DATE", "parameter_kind"])


def test_rule_catalog_filters_are_canonical_and_do_not_mutate_input() -> None:
    catalog = build_rule_catalog()
    original = catalog.copy(deep=True)

    selected = filter_rule_catalog(
        catalog,
        anomaly_types=("validità",),
        dimensions=("validity",),
        statuses=("non valido",),
        fields=("importo",),
    )

    assert selected["rule_id"].tolist() == [
        "VALIDITY_NEGATIVE_AMOUNT",
        "VALIDITY_NON_NUMERIC_AMOUNT",
    ]
    pd.testing.assert_frame_equal(catalog, original)


def test_dimension_summary_counts_findings_and_unique_rows_without_mutation() -> None:
    catalog = build_rule_catalog()
    findings = pd.DataFrame(
        [
            {"source_row_number": 1, "rule_id": "VALIDITY_NEGATIVE_AMOUNT"},
            {"source_row_number": 1, "rule_id": "VALIDITY_NON_NUMERIC_ID"},
            {"source_row_number": 2, "rule_id": "POLICY_APPROVAL_REQUIRED"},
            {"source_row_number": 999, "rule_id": "VALIDITY_INVALID_DATE"},
            {"source_row_number": None, "rule_id": "POLICY_MISSING_APPROVER"},
        ]
    )
    original = findings.copy(deep=True)

    summary = build_dimension_summary(catalog, findings, {1, 2}).set_index("dimension")

    assert summary.at["validity", "rule_count"] == 5
    assert summary.at["validity", "finding_count"] == 2
    assert summary.at["validity", "row_count"] == 1
    assert summary.at["policy_compliance", "rule_count"] == 2
    assert summary.at["policy_compliance", "finding_count"] == 1
    assert summary.at["policy_compliance", "row_count"] == 1
    assert summary.at["completeness", "finding_count"] == 0
    pd.testing.assert_frame_equal(findings, original)


def test_dimension_summary_supports_an_empty_findings_frame() -> None:
    empty_findings = pd.DataFrame(columns=("source_row_number", "rule_id"))

    summary = build_dimension_summary(build_rule_catalog(), empty_findings, set())

    assert summary["dimension"].tolist() == [
        "completeness",
        "validity",
        "uniqueness",
        "statistical_anomaly",
        "policy_compliance",
    ]
    assert summary["rule_count"].tolist() == [6, 5, 2, 2, 2]
    assert summary["finding_count"].tolist() == [0, 0, 0, 0, 0]
    assert summary["row_count"].tolist() == [0, 0, 0, 0, 0]
