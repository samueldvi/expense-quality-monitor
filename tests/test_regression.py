"""Regression comparison against the synthetic dataset ground truth."""

from pathlib import Path

import pandas as pd

from expense_quality_monitor.pipeline import analyze_expenses


ROOT = Path(__file__).resolve().parents[1]
COMPARISON_COLUMNS = [
    "source_row_number",
    "id_spesa",
    "rule_id",
    "anomaly_type",
    "field",
    "status",
    "message",
]


def test_synthetic_dataset_matches_ground_truth_exactly() -> None:
    actual = (
        analyze_expenses(ROOT / "data/synthetic_expenses.csv").findings[COMPARISON_COLUMNS].copy()
    )
    expected = pd.read_csv(
        ROOT / "data/expected_anomalies.csv",
        dtype=str,
        keep_default_na=False,
    ).rename(
        columns={
            "expected_status": "status",
            "expected_message": "message",
        }
    )[COMPARISON_COLUMNS]

    actual["source_row_number"] = actual["source_row_number"].astype(int)
    expected["source_row_number"] = expected["source_row_number"].astype(int)
    text_columns = [column for column in COMPARISON_COLUMNS if column != "source_row_number"]
    actual[text_columns] = actual[text_columns].astype(str)
    expected[text_columns] = expected[text_columns].astype(str)

    actual = actual.sort_values(
        ["source_row_number", "rule_id"],
        kind="stable",
    ).reset_index(drop=True)
    expected = expected.sort_values(
        ["source_row_number", "rule_id"],
        kind="stable",
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(actual, expected, check_dtype=True)
