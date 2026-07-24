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

APP_STYLES = """
<style>
    :root {
        --eqm-navy: #0f172a;
        --eqm-slate: #475569;
        --eqm-border: #e2e8f0;
        --eqm-surface: #ffffff;
        --eqm-background: #f8fafc;
        --eqm-accent: #0f766e;
        --eqm-accent-soft: #ccfbf1;
    }

    .stApp {
        background: var(--eqm-background);
    }

    [data-testid="stSidebar"] {
        background: var(--eqm-navy);
        border-right: 1px solid #1e293b;
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background: rgba(15, 118, 110, 0.18);
        border: 1px solid rgba(45, 212, 191, 0.35);
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.06);
        border-color: #475569;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * {
        color: var(--eqm-navy);
    }

    [data-testid="stSidebar"] [data-testid="stFileChip"] * {
        color: var(--eqm-navy);
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]
    [aria-label="Add files"],
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]
    [aria-label="Add files"] * {
        color: #e2e8f0;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #1e293b;
        border-color: #475569;
    }

    [data-testid="stMetric"] {
        background: var(--eqm-surface);
        border: 1px solid var(--eqm-border);
        border-radius: 0.75rem;
        padding: 1rem 1.1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: var(--eqm-slate);
    }

    [data-testid="stMetricValue"] {
        color: var(--eqm-navy);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--eqm-border);
        border-radius: 0.75rem;
        overflow: hidden;
    }

    .eqm-kicker {
        color: var(--eqm-accent);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
    }

    .eqm-subtitle {
        color: var(--eqm-slate);
        font-size: 1rem;
        margin: -0.45rem 0 1.4rem;
    }

    .eqm-sidebar-brand {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 700;
        line-height: 1.25;
        margin: 0.35rem 0 0.2rem;
    }

    .eqm-sidebar-caption {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }

    .eqm-empty-state {
        background: var(--eqm-surface);
        border: 1px solid var(--eqm-border);
        border-radius: 1rem;
        margin-top: 1rem;
        padding: 2rem;
        text-align: center;
    }

    .eqm-empty-state h3 {
        color: var(--eqm-navy);
        margin: 0 0 0.45rem;
    }

    .eqm-empty-state p {
        color: var(--eqm-slate);
        margin: 0 auto;
        max-width: 38rem;
    }

    .eqm-file-context {
        align-items: center;
        color: var(--eqm-slate);
        display: flex;
        font-size: 0.9rem;
        gap: 0.45rem;
        margin-bottom: 1rem;
    }

    .eqm-status-dot {
        background: var(--eqm-accent);
        border-radius: 999px;
        display: inline-block;
        height: 0.5rem;
        width: 0.5rem;
    }

    @media (max-width: 768px) {
        [data-testid="stMetric"] {
            margin-bottom: 0.5rem;
        }

        .eqm-empty-state {
            padding: 1.35rem 1rem;
        }
    }
</style>
"""


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
        by=["source_row_number", "rule_id"],
    ).reset_index(drop=True)


def render_page_header() -> None:
    """Render the dashboard title and concise product context."""
    st.markdown('<div class="eqm-kicker">Analisi settimanale</div>', unsafe_allow_html=True)
    st.title("Expense Quality Monitor")
    st.markdown(
        '<div class="eqm-subtitle">'
        "Controllo deterministico della qualità e delle anomalie delle note spese."
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar_header() -> None:
    """Render compact navigation context in the dark sidebar."""
    st.sidebar.markdown(
        '<div class="eqm-sidebar-brand">Expense Quality Monitor</div>'
        '<div class="eqm-sidebar-caption">Controlli chiari, risultati verificabili</div>',
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    """Guide the user before a weekly CSV has been selected."""
    st.markdown(
        """
        <div class="eqm-empty-state">
            <h3>Carica il CSV settimanale per iniziare</h3>
            <p>
                Seleziona un file sintetico dalla barra laterale. Il controllo verifica
                completezza, validità, duplicati, anomalie statistiche e policy.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(
    by_anomaly_type: Mapping[str, int],
    by_status: Mapping[str, int],
    by_category: pd.DataFrame,
) -> None:
    """Render compact summary tables grouped by the confirmed dimensions."""
    st.subheader("Riepilogo dell’analisi")
    type_column, status_column = st.columns(2)
    with type_column:
        st.caption("Per tipo di anomalia")
        st.dataframe(
            counts_to_frame(by_anomaly_type, "Tipo di anomalia"),
            hide_index=True,
            width="stretch",
        )
    with status_column:
        st.caption("Per stato")
        st.dataframe(
            counts_to_frame(by_status, "Stato"),
            hide_index=True,
            width="stretch",
        )

    st.caption("Per categoria")
    st.dataframe(by_category, hide_index=True, width="stretch")


def render_findings(
    findings: pd.DataFrame,
    selected_types: Sequence[str],
    selected_statuses: Sequence[str],
) -> None:
    """Render the central findings table and its deterministic CSV export."""
    filtered_findings = filter_findings(findings, selected_types, selected_statuses)
    heading_column, count_column = st.columns([4, 1])
    with heading_column:
        st.subheader("Segnalazioni")
    with count_column:
        st.metric("Visualizzate", len(filtered_findings))

    if findings.empty:
        st.success("Nessuna segnalazione rilevata nel file analizzato.")
    elif filtered_findings.empty:
        st.info("Nessuna segnalazione corrisponde ai filtri selezionati.")

    st.dataframe(
        filtered_findings,
        hide_index=True,
        width="stretch",
        height=500,
    )
    st.download_button(
        "Scarica le segnalazioni filtrate",
        data=findings_to_csv(filtered_findings),
        file_name="expense_quality_findings.csv",
        mime="text/csv",
        type="primary",
        width="content",
    )


def render_dashboard() -> None:
    """Render the upload, analysis results, filters, and safe CSV download."""
    st.set_page_config(
        page_title="Expense Quality Monitor",
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(APP_STYLES, unsafe_allow_html=True)
    render_sidebar_header()
    render_page_header()

    st.sidebar.subheader("Dati di ingresso")
    st.sidebar.info(
        "Usa esclusivamente dati sintetici. Non caricare dati aziendali o di clienti reali."
    )
    uploaded_file = st.sidebar.file_uploader(
        "Carica un export settimanale in formato CSV",
        type=["csv"],
    )
    if uploaded_file is None:
        render_empty_state()
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

    st.markdown(
        '<div class="eqm-file-context"><span class="eqm-status-dot"></span>'
        f"Analisi completata: {uploaded_file.name}</div>",
        unsafe_allow_html=True,
    )
    total_metric, affected_metric, findings_metric = st.columns(3)
    total_metric.metric("Righe totali", total_rows)
    affected_metric.metric("Righe con segnalazioni", rows_with_findings)
    findings_metric.metric("Segnalazioni totali", len(result.findings))

    anomaly_options = sorted(result.findings["anomaly_type"].unique().tolist())
    status_options = sorted(result.findings["status"].unique().tolist())
    st.sidebar.divider()
    st.sidebar.subheader("Filtri")
    selected_types = st.sidebar.multiselect(
        "Tipo di anomalia",
        anomaly_options,
        placeholder="Tutti i tipi",
    )
    selected_statuses = st.sidebar.multiselect(
        "Stato",
        status_options,
        placeholder="Tutti gli stati",
    )

    overview_tab, findings_tab = st.tabs(["Panoramica", "Segnalazioni"])
    with overview_tab:
        render_summary(by_anomaly_type, by_status, by_category)
    with findings_tab:
        render_findings(result.findings, selected_types, selected_statuses)


render_dashboard()
