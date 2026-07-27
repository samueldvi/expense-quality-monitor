"""Build deterministic governance metadata and summaries without UI dependencies."""

from __future__ import annotations

import hashlib
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version

import pandas as pd

from expense_quality_monitor.config import (
    MEDIAN_MULTIPLIER,
    MIN_STATISTICAL_OBSERVATIONS,
    POLICY_THRESHOLDS,
    QUALITY_DIMENSIONS,
    RULE_CATALOG,
    RULE_TARGET_FIELDS,
)
from expense_quality_monitor.loader import SOURCE_ROW_COLUMN, CsvFormatMetadata
from expense_quality_monitor.profiling import DataProfile

PACKAGE_NAME = "expense-quality-monitor"
RULE_CATALOG_COLUMNS = (
    "rule_id",
    "name_key",
    "description_key",
    "anomaly_type",
    "dimension",
    "status",
    "fields",
    "parameter_kind",
    "parameter_value",
)
DIMENSION_SUMMARY_COLUMNS = (
    "dimension",
    "rule_count",
    "finding_count",
    "row_count",
)


@dataclass(frozen=True)
class ProcessingMetadata:
    """Immutable facts about one analyzed source and processing event."""

    source_name: str
    source_size_bytes: int
    analyzed_at_utc: datetime
    sha256: str
    row_count: int
    source_column_count: int
    canonical_column_count: int
    extra_columns: tuple[str, ...]
    delimiter: str
    encoding: str
    has_bom: bool
    application_version: str | None


def calculate_sha256(content: bytes) -> str:
    """Return the SHA-256 digest of the exact original source bytes."""
    return hashlib.sha256(content).hexdigest()


def application_version() -> str | None:
    """Return the installed package version, or no value when unavailable."""
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return None


def build_processing_metadata(
    *,
    source_name: str,
    content: bytes,
    profile: DataProfile,
    csv_format: CsvFormatMetadata,
    analyzed_at_utc: datetime,
    installed_version: str | None,
) -> ProcessingMetadata:
    """Build immutable source metadata from already-computed analysis facts."""
    if analyzed_at_utc.tzinfo is None or analyzed_at_utc.utcoffset() is None:
        raise ValueError("analyzed_at_utc must be timezone-aware")
    return ProcessingMetadata(
        source_name=source_name,
        source_size_bytes=len(content),
        analyzed_at_utc=analyzed_at_utc.astimezone(UTC),
        sha256=calculate_sha256(content),
        row_count=profile.row_count,
        source_column_count=profile.source_column_count,
        canonical_column_count=profile.canonical_column_count,
        extra_columns=profile.extra_columns,
        delimiter=csv_format.delimiter,
        encoding=csv_format.encoding,
        has_bom=csv_format.has_bom,
        application_version=installed_version,
    )


def _dimension_for_rule(rule_id: str) -> str:
    prefixes = (
        ("COMPLETENESS_", "completeness"),
        ("VALIDITY_", "validity"),
        ("UNIQUENESS_", "uniqueness"),
        ("STATISTICAL_", "statistical_anomaly"),
        ("POLICY_", "policy_compliance"),
    )
    for prefix, dimension in prefixes:
        if rule_id.startswith(prefix):
            return dimension
    raise ValueError(f"Unknown quality dimension for rule: {rule_id}")


def _rule_parameter(rule_id: str) -> tuple[str | None, object]:
    if rule_id == "UNIQUENESS_LOGICAL_DUPLICATE":
        return "logical_duplicate_fields", RULE_TARGET_FIELDS[rule_id]
    if rule_id == "STATISTICAL_AMOUNT_ANOMALY":
        return "median_multiplier", MEDIAN_MULTIPLIER
    if rule_id == "STATISTICAL_NOT_EVALUABLE":
        return "minimum_observations", MIN_STATISTICAL_OBSERVATIONS
    if rule_id.startswith("POLICY_"):
        return "policy_thresholds", tuple(POLICY_THRESHOLDS.items())
    return None, None


def build_rule_catalog() -> pd.DataFrame:
    """Return the canonical 17-rule catalog derived from application configuration."""
    rows = []
    for rule_id, (anomaly_type, status, _) in RULE_CATALOG.items():
        dimension = _dimension_for_rule(rule_id)
        if dimension not in QUALITY_DIMENSIONS:
            raise ValueError(f"Unsupported quality dimension: {dimension}")
        parameter_kind, parameter_value = _rule_parameter(rule_id)
        rows.append(
            {
                "rule_id": rule_id,
                "name_key": f"rule.{rule_id}.name",
                "description_key": f"rule.{rule_id}.message",
                "anomaly_type": anomaly_type,
                "dimension": dimension,
                "status": status,
                "fields": RULE_TARGET_FIELDS[rule_id],
                "parameter_kind": parameter_kind,
                "parameter_value": parameter_value,
            }
        )
    return pd.DataFrame.from_records(rows, columns=RULE_CATALOG_COLUMNS)


def filter_rule_catalog(
    catalog: pd.DataFrame,
    *,
    anomaly_types: Sequence[str] = (),
    dimensions: Sequence[str] = (),
    statuses: Sequence[str] = (),
    fields: Sequence[str] = (),
) -> pd.DataFrame:
    """Return a filtered catalog copy while preserving canonical rule order."""
    selected = catalog
    if anomaly_types:
        selected = selected[selected["anomaly_type"].isin(anomaly_types)]
    if dimensions:
        selected = selected[selected["dimension"].isin(dimensions)]
    if statuses:
        selected = selected[selected["status"].isin(statuses)]
    if fields:
        selected_fields = frozenset(fields)
        selected = selected[
            selected["fields"].map(lambda values: bool(selected_fields.intersection(values)))
        ]
    return selected.copy().reset_index(drop=True)


def build_dimension_summary(
    catalog: pd.DataFrame,
    findings: pd.DataFrame,
    source_row_numbers: Collection[object],
) -> pd.DataFrame:
    """Summarize configured rules and observed findings by quality dimension."""
    rule_dimensions = dict(zip(catalog["rule_id"], catalog["dimension"], strict=True))
    if {"rule_id", SOURCE_ROW_COLUMN} <= set(findings.columns):
        valid_findings = findings[findings[SOURCE_ROW_COLUMN].isin(frozenset(source_row_numbers))]
    else:
        valid_findings = findings.iloc[0:0]
    rows = []
    for dimension in QUALITY_DIMENSIONS:
        rule_ids = {
            rule_id
            for rule_id, rule_dimension in rule_dimensions.items()
            if rule_dimension == dimension
        }
        dimension_findings = valid_findings[valid_findings["rule_id"].isin(rule_ids)]
        finding_count = len(dimension_findings)
        row_count = int(dimension_findings[SOURCE_ROW_COLUMN].nunique())
        rows.append(
            {
                "dimension": dimension,
                "rule_count": len(rule_ids),
                "finding_count": finding_count,
                "row_count": row_count,
            }
        )
    return pd.DataFrame.from_records(rows, columns=DIMENSION_SUMMARY_COLUMNS)
