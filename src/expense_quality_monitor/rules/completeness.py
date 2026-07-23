"""Produce row-level findings for missing required values."""

from __future__ import annotations

import pandas as pd

from expense_quality_monitor.config import EXPECTED_COLUMNS, REQUIRED_FIELDS
from expense_quality_monitor.rules import findings_frame, make_finding


def check_completeness(data: pd.DataFrame) -> pd.DataFrame:
    """Return one finding for each missing required field."""
    records = []
    ordered_fields = [field for field in EXPECTED_COLUMNS if field in REQUIRED_FIELDS]
    for _, row in data.iterrows():
        for field in ordered_fields:
            if bool(row[f"_missing_{field}"]):
                rule_id = f"COMPLETENESS_MISSING_{field.upper()}"
                records.append(make_finding(row, rule_id, field))
    return findings_frame(records)
