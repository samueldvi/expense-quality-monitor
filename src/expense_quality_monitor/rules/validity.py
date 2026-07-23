"""Produce row-level findings for invalid confirmed fields and formats."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from expense_quality_monitor.normalization import is_missing
from expense_quality_monitor.rules import findings_frame, make_finding


def check_validity(data: pd.DataFrame) -> pd.DataFrame:
    """Validate identifiers, dates, amounts, and strict category values."""
    records = []
    zero = Decimal("0")

    for _, row in data.iterrows():
        if not row["_missing_id_spesa"] and is_missing(row["_id_parsed"]):
            records.append(make_finding(row, "VALIDITY_NON_NUMERIC_ID", "id_spesa"))

        if not row["_missing_data_spesa"] and is_missing(row["_date_parsed"]):
            records.append(make_finding(row, "VALIDITY_INVALID_DATE", "data_spesa"))

        if not row["_missing_importo"]:
            amount = row["_amount_parsed"]
            if is_missing(amount):
                records.append(make_finding(row, "VALIDITY_NON_NUMERIC_AMOUNT", "importo"))
            elif amount < zero:
                records.append(make_finding(row, "VALIDITY_NEGATIVE_AMOUNT", "importo"))

        if not row["_missing_categoria"] and not row["_category_valid"]:
            records.append(make_finding(row, "VALIDITY_INVALID_CATEGORY", "categoria"))

    return findings_frame(records)
