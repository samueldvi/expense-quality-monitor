"""Coordinate the ordered deterministic expense analysis workflow."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from expense_quality_monitor.config import FINDING_COLUMNS
from expense_quality_monitor.loader import CsvSource, load_expenses
from expense_quality_monitor.normalization import normalize_expenses
from expense_quality_monitor.reporting import build_summary
from expense_quality_monitor.rules.completeness import check_completeness
from expense_quality_monitor.rules.policy import check_policy
from expense_quality_monitor.rules.statistical import check_statistical
from expense_quality_monitor.rules.uniqueness import check_uniqueness
from expense_quality_monitor.rules.validity import check_validity


@dataclass(frozen=True)
class AnalysisResult:
    """Source rows, ordered findings, and summary produced by one analysis."""

    source_data: pd.DataFrame
    findings: pd.DataFrame
    summary: dict[str, object]


def analyze_expenses(source: CsvSource) -> AnalysisResult:
    """Load, normalize, check, and summarize one weekly expense CSV."""
    source_data = load_expenses(source)
    working_data = normalize_expenses(source_data)

    rule_outputs = (
        check_completeness(working_data),
        check_validity(working_data),
        check_uniqueness(working_data),
        check_statistical(working_data),
        check_policy(working_data),
    )
    findings = pd.concat(rule_outputs, ignore_index=True)
    findings = findings.loc[:, FINDING_COLUMNS].sort_values(
        by=["source_row_number", "rule_id"],
    )
    findings = findings.reset_index(drop=True)
    summary = build_summary(source_data, findings)
    return AnalysisResult(
        source_data=source_data,
        findings=findings,
        summary=summary,
    )
