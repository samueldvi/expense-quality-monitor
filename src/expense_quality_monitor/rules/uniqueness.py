"""Produce findings for repeated identifiers and eligible logical duplicates."""

from __future__ import annotations

import pandas as pd

from expense_quality_monitor.normalization import is_missing, is_usable_amount
from expense_quality_monitor.rules import findings_frame, make_finding


def _eligible_logical_duplicate(row: pd.Series) -> bool:
    amount = row["_amount_parsed"]
    return bool(
        not row["_missing_id_spesa"]
        and not is_missing(row["_employee_normalized"])
        and not is_missing(row["_date_parsed"])
        and is_usable_amount(amount)
        and row["_category_valid"]
    )


def check_uniqueness(data: pd.DataFrame) -> pd.DataFrame:
    """Find every row in duplicate-ID and valid logical-duplicate groups."""
    records = []

    present_ids = data.loc[~data["_missing_id_spesa"], "id_spesa"].astype(str)
    duplicate_id_mask = present_ids.duplicated(keep=False)
    for index in present_ids.index[duplicate_id_mask]:
        records.append(make_finding(data.loc[index], "UNIQUENESS_ID_DUPLICATE", "id_spesa"))

    eligible = data[data.apply(_eligible_logical_duplicate, axis=1)].copy()
    logical_key = [
        "_employee_normalized",
        "_date_parsed",
        "_amount_parsed",
        "categoria",
    ]
    for _, group in eligible.groupby(logical_key, sort=False, dropna=False):
        if len(group) < 2 or group["id_spesa"].astype(str).nunique() < 2:
            continue
        for _, row in group.iterrows():
            records.append(
                make_finding(
                    row,
                    "UNIQUENESS_LOGICAL_DUPLICATE",
                    "",
                    original_value="",
                )
            )

    return findings_frame(records)
