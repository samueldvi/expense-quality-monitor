"""Produce policy-threshold, approval, and compliance findings."""

from __future__ import annotations

import pandas as pd

from expense_quality_monitor.config import POLICY_THRESHOLDS
from expense_quality_monitor.normalization import is_usable_amount
from expense_quality_monitor.rules import findings_frame, make_finding


def check_policy(data: pd.DataFrame) -> pd.DataFrame:
    """Flag valid expenses strictly above policy thresholds."""
    records = []

    for _, row in data.iterrows():
        amount = row["_amount_parsed"]
        if not row["_category_valid"] or not is_usable_amount(amount):
            continue
        if amount <= POLICY_THRESHOLDS[row["categoria"]]:
            continue

        records.append(make_finding(row, "POLICY_APPROVAL_REQUIRED", "importo"))
        if row["_approver_missing"]:
            records.append(make_finding(row, "POLICY_MISSING_APPROVER", "approvatore"))

    return findings_frame(records)
