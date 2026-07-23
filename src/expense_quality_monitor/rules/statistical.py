"""Produce category evaluability and median-based anomaly findings."""

from __future__ import annotations

from statistics import median

import pandas as pd

from expense_quality_monitor.config import (
    MEDIAN_MULTIPLIER,
    MIN_STATISTICAL_OBSERVATIONS,
    VALID_CATEGORIES,
)
from expense_quality_monitor.normalization import is_usable_amount
from expense_quality_monitor.rules import findings_frame, make_finding


def _usable_observations(data: pd.DataFrame) -> pd.DataFrame:
    return data[data["_category_valid"] & data["_amount_parsed"].map(is_usable_amount)]


def check_statistical(data: pd.DataFrame) -> pd.DataFrame:
    """Evaluate each valid category using its usable non-negative amounts."""
    records = []
    usable = _usable_observations(data)

    for category in VALID_CATEGORIES:
        group = usable[usable["categoria"] == category]
        if group.empty:
            continue
        if len(group) < MIN_STATISTICAL_OBSERVATIONS:
            for _, row in group.iterrows():
                records.append(
                    make_finding(
                        row,
                        "STATISTICAL_NOT_EVALUABLE",
                        "categoria",
                    )
                )
            continue

        category_median = median(group["_amount_parsed"].tolist())
        anomaly_limit = category_median * MEDIAN_MULTIPLIER
        for _, row in group.iterrows():
            if row["_amount_parsed"] > anomaly_limit:
                records.append(
                    make_finding(
                        row,
                        "STATISTICAL_AMOUNT_ANOMALY",
                        "importo",
                    )
                )

    return findings_frame(records)
