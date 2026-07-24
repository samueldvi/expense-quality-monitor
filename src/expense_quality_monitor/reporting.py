"""Build analysis summaries and export findings safely as CSV."""

from __future__ import annotations

import pandas as pd

from expense_quality_monitor.config import FINDING_COLUMNS

FORMULA_PREFIXES = ("=", "+", "-", "@")


def neutralize_formula(value: object) -> object:
    """Prefix formula-like text so spreadsheet applications treat it as data."""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return f"'{value}"
    return value


def build_summary(
    source_data: pd.DataFrame,
    findings: pd.DataFrame,
) -> dict[str, object]:
    """Return deterministic totals and grouped counts for an analysis result."""
    finding_rows = set(findings["source_row_number"].astype(int).tolist())
    category_data = source_data[["source_row_number", "categoria"]].copy()
    category_data["_has_finding"] = category_data["source_row_number"].isin(finding_rows)
    category_summary = (
        category_data.groupby("categoria", dropna=False, sort=True)
        .agg(
            total_rows=("source_row_number", "size"),
            rows_with_findings=("_has_finding", "sum"),
        )
        .reset_index()
    )
    category_summary["total_rows"] = category_summary["total_rows"].astype(int)
    category_summary["rows_with_findings"] = category_summary["rows_with_findings"].astype(int)

    return {
        "total_rows": len(source_data),
        "rows_with_findings": len(finding_rows),
        "by_anomaly_type": {
            key: int(value)
            for key, value in findings["anomaly_type"].value_counts().sort_index().items()
        },
        "by_status": {
            key: int(value) for key, value in findings["status"].value_counts().sort_index().items()
        },
        "by_category": category_summary,
    }


def findings_to_csv(findings: pd.DataFrame) -> str:
    """Serialize findings in their stable schema with formula-safe text."""
    export = findings.loc[:, FINDING_COLUMNS].copy()
    for column in export.columns:
        export[column] = export[column].map(neutralize_formula)
    return export.to_csv(index=False, lineterminator="\n")
