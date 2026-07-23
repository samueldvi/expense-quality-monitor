"""Streamlit dashboard for deterministic expense-quality analysis."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import cast

import pandas as pd
import streamlit as st

from expense_quality_monitor.loader import CsvLoadError
from expense_quality_monitor.pipeline import analyze_expenses
from expense_quality_monitor.reporting import findings_to_csv


LOGGER = logging.getLogger(__name__)


def counts_to_frame(counts: Mapping[str, int], label: str) -> pd.DataFrame:
    """Return deterministic count rows suitable for display."""
    rows = [{label: name, "Conteggio": count} for name, count in sorted(counts.items())]
    return pd.DataFrame(rows, columns=[label, "Conteggio"])


def filter_findings(
    findings: pd.DataFrame,
    anomaly_types: Sequence[str],
    statuses: Sequence[str],
) -> pd.DataFrame:
    """Return a sorted filtered copy without changing the original findings."""
    filtered = findings
    if anomaly_types:
        filtered = filtered[filtered["anomaly_type"].isin(anomaly_types)]
    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    return filtered.sort_values(
        ["source_row_number", "rule_id"],
        kind="stable",
    ).reset_index(drop=True)


def render_dashboard() -> None:
    """Render the upload, analysis results, filters, and safe CSV download."""
    st.set_page_config(page_title="Expense Quality Monitor", layout="wide")
    st.title("Expense Quality Monitor")
    st.write(
        "Controllo deterministico della qualità e delle anomalie delle note spese settimanali."
    )
    st.info("Usa esclusivamente dati sintetici. Non caricare dati aziendali o di clienti reali.")

    uploaded_file = st.file_uploader(
        "Carica un export settimanale in formato CSV",
        type=["csv"],
    )
    if uploaded_file is None:
        return

    try:
        with st.spinner("Analisi del file in corso..."):
            result = analyze_expenses(uploaded_file)
    except CsvLoadError as error:
        st.error(str(error))
        return
    except Exception:
        LOGGER.exception("Errore imprevisto durante l'analisi del CSV.")
        st.error("Si è verificato un errore imprevisto durante l'analisi del file.")
        return

    summary = result.summary
    total_rows = cast(int, summary["total_rows"])
    rows_with_findings = cast(int, summary["rows_with_findings"])
    by_anomaly_type = cast(dict[str, int], summary["by_anomaly_type"])
    by_status = cast(dict[str, int], summary["by_status"])
    by_category = cast(pd.DataFrame, summary["by_category"])

    total_metric, affected_metric, findings_metric = st.columns(3)
    total_metric.metric("Righe totali", total_rows)
    affected_metric.metric("Righe con segnalazioni", rows_with_findings)
    findings_metric.metric("Segnalazioni totali", len(result.findings))

    st.subheader("Riepilogo")
    type_column, status_column = st.columns(2)
    with type_column:
        st.write("Per tipo di anomalia")
        st.dataframe(
            counts_to_frame(by_anomaly_type, "Tipo di anomalia"),
            hide_index=True,
            use_container_width=True,
        )
    with status_column:
        st.write("Per stato")
        st.dataframe(
            counts_to_frame(by_status, "Stato"),
            hide_index=True,
            use_container_width=True,
        )

    st.write("Per categoria")
    st.dataframe(by_category, hide_index=True, use_container_width=True)

    st.subheader("Segnalazioni")
    if result.findings.empty:
        st.success("Nessuna segnalazione rilevata nel file analizzato.")

    anomaly_options = sorted(result.findings["anomaly_type"].unique().tolist())
    status_options = sorted(result.findings["status"].unique().tolist())
    filter_column, status_filter_column = st.columns(2)
    with filter_column:
        selected_types = st.multiselect("Filtra per tipo di anomalia", anomaly_options)
    with status_filter_column:
        selected_statuses = st.multiselect("Filtra per stato", status_options)

    filtered_findings = filter_findings(
        result.findings,
        selected_types,
        selected_statuses,
    )
    st.write(f"Risultati visualizzati: {len(filtered_findings)}")
    st.dataframe(filtered_findings, hide_index=True, use_container_width=True)
    st.download_button(
        "Scarica le segnalazioni filtrate",
        data=findings_to_csv(filtered_findings),
        file_name="expense_quality_findings.csv",
        mime="text/csv",
    )


render_dashboard()
