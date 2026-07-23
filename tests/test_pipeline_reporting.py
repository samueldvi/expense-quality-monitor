"""Integration tests for pipeline coordination and reporting."""

from io import StringIO

import pandas as pd

from expense_quality_monitor.config import EXPECTED_COLUMNS, FINDING_COLUMNS
from expense_quality_monitor.pipeline import analyze_expenses
from expense_quality_monitor.reporting import (
    build_summary,
    findings_to_csv,
)


def test_pipeline_returns_source_findings_and_summary() -> None:
    header = ",".join(EXPECTED_COLUMNS)
    rows = [
        f"{number},13/07/2026,Demo {number},,Vitto,,{amount},,PRJ-TEST,"
        for number, amount in enumerate(["10", "10", "10", "10", "81"], start=1)
    ]

    result = analyze_expenses(StringIO("\n".join([header, *rows])))

    assert len(result.source_data) == 5
    assert result.summary["total_rows"] == 5
    assert result.summary["rows_with_findings"] == 1
    assert result.findings.equals(
        result.findings.sort_values(
            by=["source_row_number", "rule_id"],
        ).reset_index(drop=True)
    )


def test_reporting_counts_rows_types_statuses_and_categories() -> None:
    source = pd.DataFrame(
        {
            "source_row_number": [1, 2],
            "categoria": ["Vitto", "Trasporto"],
        }
    )
    findings = pd.DataFrame(
        [
            [1, "1", "RULE_A", "validità", "importo", "non valido", "A", "x"],
            [1, "1", "RULE_B", "policy", "importo", "richiede approvazione", "B", "x"],
        ],
        columns=FINDING_COLUMNS,
    )

    summary = build_summary(source, findings)

    assert summary["total_rows"] == 2
    assert summary["rows_with_findings"] == 1
    assert summary["by_anomaly_type"] == {"policy": 1, "validità": 1}
    assert summary["by_status"] == {
        "non valido": 1,
        "richiede approvazione": 1,
    }
    assert summary["by_category"]["total_rows"].sum() == 2


def test_csv_export_neutralizes_formula_prefixes() -> None:
    findings = pd.DataFrame(
        [
            [
                1,
                "=ID",
                "RULE",
                "validità",
                "@campo",
                "non valido",
                "+messaggio",
                "-valore",
            ]
        ],
        columns=FINDING_COLUMNS,
    )

    exported = findings_to_csv(findings)
    parsed = pd.read_csv(StringIO(exported), dtype=str, keep_default_na=False)

    assert parsed.loc[0, "id_spesa"] == "'=ID"
    assert parsed.loc[0, "field"] == "'@campo"
    assert parsed.loc[0, "message"] == "'+messaggio"
    assert parsed.loc[0, "original_value"] == "'-valore"
