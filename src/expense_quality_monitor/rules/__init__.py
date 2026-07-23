"""Shared construction utilities for deterministic expense-quality findings."""

from __future__ import annotations

import pandas as pd

from expense_quality_monitor.config import FINDING_COLUMNS, RULE_CATALOG
from expense_quality_monitor.normalization import is_missing


FindingRecord = dict[str, object]


def raw_text(value: object) -> str:
    """Convert a raw scalar to stable text without exposing pandas null values."""
    return "" if is_missing(value) else str(value)


def make_finding(
    row: pd.Series,
    rule_id: str,
    field: str,
    original_value: object | None = None,
) -> FindingRecord:
    """Build one finding from a normalized source row and the confirmed catalog."""
    anomaly_type, status, message = RULE_CATALOG[rule_id]
    value = row[field] if original_value is None and field else original_value
    return {
        "source_row_number": int(row["source_row_number"]),
        "id_spesa": raw_text(row["id_spesa"]),
        "rule_id": rule_id,
        "anomaly_type": anomaly_type,
        "field": field,
        "status": status,
        "message": message,
        "original_value": raw_text(value),
    }


def findings_frame(records: list[FindingRecord]) -> pd.DataFrame:
    """Return findings with a stable schema, including when no records exist."""
    return pd.DataFrame.from_records(records, columns=FINDING_COLUMNS)
