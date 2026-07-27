"""Build deterministic dataset profiles and the canonical data dictionary."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from expense_quality_monitor.config import (
    COLUMN_METADATA,
    EXPECTED_COLUMNS,
    RULE_TARGET_FIELDS,
    VALID_CATEGORIES,
    rules_for_column,
)
from expense_quality_monitor.loader import SOURCE_ROW_COLUMN
from expense_quality_monitor.normalization import (
    is_missing,
    is_usable_amount,
    parse_amount,
    parse_expense_date,
)

COLUMN_PROFILE_COLUMNS = (
    "technical_name",
    "column_kind",
    "missing_values",
    "completeness_percentage",
    "distinct_values",
    "source_dtype",
    "expected_type",
    "related_findings",
    "minimum_valid",
    "maximum_valid",
)

DATA_DICTIONARY_COLUMNS = (
    "technical_name",
    "label_key",
    "description_key",
    "required",
    "expected_type",
    "format_key",
    "allowed_values",
    "example",
    "rules",
    "dimensions",
)


@dataclass(frozen=True)
class DataProfile:
    """Immutable structural and rule-result summary for one analyzed source."""

    row_count: int
    source_column_count: int
    canonical_column_count: int
    extra_columns: tuple[str, ...]
    rows_with_findings: int
    finding_count: int
    duplicate_id_rows: int
    logical_duplicate_rows: int
    validity_finding_count: int


def _source_columns(source_data: pd.DataFrame) -> tuple[str, ...]:
    return tuple(column for column in source_data.columns if column != SOURCE_ROW_COLUMN)


def _source_row_numbers(source_data: pd.DataFrame) -> frozenset[object]:
    if SOURCE_ROW_COLUMN not in source_data:
        return frozenset()
    return frozenset(source_data[SOURCE_ROW_COLUMN].dropna())


def _finding_rows(
    findings: pd.DataFrame,
    source_row_numbers: frozenset[object],
    rule_id: str | None = None,
) -> int:
    if SOURCE_ROW_COLUMN not in findings or "rule_id" not in findings:
        return 0
    selected = findings
    if rule_id is not None:
        selected = findings[findings["rule_id"].eq(rule_id)]
    selected = selected[selected[SOURCE_ROW_COLUMN].isin(source_row_numbers)]
    return int(selected[SOURCE_ROW_COLUMN].nunique())


def build_data_profile(
    source_data: pd.DataFrame,
    findings: pd.DataFrame,
) -> DataProfile:
    """Return structural metrics and separate deterministic rule-result counts."""
    source_columns = _source_columns(source_data)
    source_row_numbers = _source_row_numbers(source_data)
    extra_columns = tuple(column for column in source_columns if column not in EXPECTED_COLUMNS)
    canonical_count = sum(column in EXPECTED_COLUMNS for column in source_columns)
    if {"rule_id", SOURCE_ROW_COLUMN} <= set(findings.columns):
        valid_findings = findings[findings[SOURCE_ROW_COLUMN].isin(source_row_numbers)]
        validity_count = int(
            valid_findings["rule_id"].astype(str).str.startswith("VALIDITY_").sum()
        )
    else:
        validity_count = 0
    return DataProfile(
        row_count=len(source_data),
        source_column_count=len(source_columns),
        canonical_column_count=canonical_count,
        extra_columns=extra_columns,
        rows_with_findings=_finding_rows(findings, source_row_numbers),
        finding_count=len(findings),
        duplicate_id_rows=_finding_rows(
            findings,
            source_row_numbers,
            "UNIQUENESS_ID_DUPLICATE",
        ),
        logical_duplicate_rows=_finding_rows(
            findings,
            source_row_numbers,
            "UNIQUENESS_LOGICAL_DUPLICATE",
        ),
        validity_finding_count=validity_count,
    )


def _profile_order(source_data: pd.DataFrame) -> tuple[str, ...]:
    source_columns = _source_columns(source_data)
    canonical = tuple(column for column in EXPECTED_COLUMNS if column in source_columns)
    extra = tuple(column for column in source_columns if column not in EXPECTED_COLUMNS)
    return canonical + extra


def _finding_targets(finding: pd.Series) -> tuple[str, ...]:
    field = finding.get("field")
    if not is_missing(field):
        return (str(field),)
    return RULE_TARGET_FIELDS.get(str(finding.get("rule_id")), ())


def _related_finding_counts(
    findings: pd.DataFrame,
    source_row_numbers: frozenset[object],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, finding in findings.iterrows():
        if finding.get(SOURCE_ROW_COLUMN) not in source_row_numbers:
            continue
        for field in _finding_targets(finding):
            counts[field] = counts.get(field, 0) + 1
    return counts


def _valid_range(column_name: str, values: pd.Series) -> tuple[str | None, str | None]:
    if column_name == "data_spesa":
        parsed_dates = [date for date in values.map(parse_expense_date) if date is not None]
        if parsed_dates:
            return (
                min(parsed_dates).strftime("%d/%m/%Y"),
                max(parsed_dates).strftime("%d/%m/%Y"),
            )
    if column_name == "importo":
        parsed_amounts = [amount for amount in values.map(parse_amount) if is_usable_amount(amount)]
        if parsed_amounts:
            return (
                format(min(parsed_amounts), "f"),
                format(max(parsed_amounts), "f"),
            )
    return None, None


def build_column_profile(
    source_data: pd.DataFrame,
    findings: pd.DataFrame,
) -> pd.DataFrame:
    """Return one deterministic profile row for every non-technical source column."""
    related_counts = _related_finding_counts(findings, _source_row_numbers(source_data))
    metadata_by_name = {metadata.name: metadata for metadata in COLUMN_METADATA}
    rows = []
    for column_name in _profile_order(source_data):
        values = source_data[column_name]
        present_values = values[~values.map(is_missing)]
        missing_count = len(values) - len(present_values)
        completeness = 0.0 if len(values) == 0 else 100 * len(present_values) / len(values)
        minimum, maximum = _valid_range(column_name, values)
        metadata = metadata_by_name.get(column_name)
        rows.append(
            {
                "technical_name": column_name,
                "column_kind": "canonical" if metadata is not None else "extra",
                "missing_values": missing_count,
                "completeness_percentage": round(completeness, 2),
                "distinct_values": int(present_values.nunique(dropna=False)),
                "source_dtype": str(values.dtype),
                "expected_type": metadata.expected_type if metadata else None,
                "related_findings": related_counts.get(column_name, 0),
                "minimum_valid": minimum,
                "maximum_valid": maximum,
            }
        )
    return pd.DataFrame.from_records(rows, columns=COLUMN_PROFILE_COLUMNS)


def build_data_dictionary() -> pd.DataFrame:
    """Return language-independent canonical dictionary records."""
    rows = []
    for metadata in COLUMN_METADATA:
        rows.append(
            {
                "technical_name": metadata.name,
                "label_key": metadata.label_key,
                "description_key": metadata.description_key,
                "required": metadata.required,
                "expected_type": metadata.expected_type,
                "format_key": metadata.format_key,
                "allowed_values": (VALID_CATEGORIES if metadata.name == "categoria" else ()),
                "example": metadata.example,
                "rules": rules_for_column(metadata.name),
                "dimensions": metadata.quality_dimensions,
            }
        )
    return pd.DataFrame.from_records(rows, columns=DATA_DICTIONARY_COLUMNS)
