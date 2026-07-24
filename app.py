"""Streamlit workspace for deterministic expense-quality analysis."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import cast

import pandas as pd
import streamlit as st

from expense_quality_monitor.config import FINDING_COLUMNS
from expense_quality_monitor.loader import CsvLoadError
from expense_quality_monitor.pipeline import AnalysisResult, analyze_expenses
from expense_quality_monitor.reporting import findings_to_csv

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
EXAMPLE_PATH = ROOT / "data" / "synthetic_expenses.csv"
SECTIONS = ("Panoramica", "Segnalazioni", "Dati", "Esporta")
FILTER_KEYS = (
    "finding_search",
    "filter_types",
    "filter_statuses",
    "filter_categories",
    "filter_rules",
)
TABLE_COLUMNS = (
    "source_row_number",
    "id_spesa",
    "status",
    "anomaly_type",
    "field",
    "message",
    "original_value",
    "rule_id",
)


def counts_to_frame(counts: Mapping[str, int], label: str) -> pd.DataFrame:
    """Return deterministic count rows suitable for charts and tables."""
    rows = [{label: name, "Conteggio": count} for name, count in sorted(counts.items())]
    return pd.DataFrame(rows, columns=[label, "Conteggio"])


def findings_with_categories(
    findings: pd.DataFrame,
    source_data: pd.DataFrame,
) -> pd.DataFrame:
    """Add source categories to findings for UI filtering without changing findings."""
    categories = source_data[["source_row_number", "categoria"]]
    return findings.merge(
        categories,
        on="source_row_number",
        how="left",
        validate="many_to_one",
    )


def filter_findings(
    findings: pd.DataFrame,
    query: str = "",
    anomaly_types: Sequence[str] = (),
    statuses: Sequence[str] = (),
    categories: Sequence[str] = (),
    rule_ids: Sequence[str] = (),
) -> pd.DataFrame:
    """Return a deterministic filtered copy of the enriched findings."""
    filtered = findings
    normalized_query = query.strip().casefold()
    if normalized_query:
        searchable = (
            filtered[["id_spesa", "rule_id", "message"]]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.casefold()
        )
        filtered = filtered[searchable.str.contains(normalized_query, regex=False)]
    if anomaly_types:
        filtered = filtered[filtered["anomaly_type"].isin(anomaly_types)]
    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    if categories:
        filtered = filtered[filtered["categoria"].isin(categories)]
    if rule_ids:
        filtered = filtered[filtered["rule_id"].isin(rule_ids)]
    return filtered.sort_values(
        by=["source_row_number", "rule_id"],
    ).reset_index(drop=True)


def distinct_rule_count(findings: pd.DataFrame) -> int:
    """Return the number of distinct rules represented in the findings."""
    return int(findings["rule_id"].nunique())


def reset_filters() -> None:
    """Clear only the search and table filters."""
    st.session_state["finding_search"] = ""
    for key in FILTER_KEYS[1:]:
        st.session_state[key] = []


def reset_workspace_view() -> None:
    """Return navigation and filters to their initial state after changing source."""
    st.session_state["workspace_section"] = "Panoramica"
    reset_filters()


def activate_uploaded_source(widget_key: str) -> None:
    """Keep a selected upload in session memory across subsequent reruns."""
    uploaded_file = st.session_state.get(widget_key)
    if uploaded_file is None:
        return
    st.session_state["source_name"] = uploaded_file.name
    st.session_state["source_bytes"] = uploaded_file.getvalue()
    st.session_state["source_is_example"] = False
    reset_workspace_view()


def activate_example_source() -> None:
    """Select the versioned example without copying or changing it."""
    st.session_state["source_name"] = EXAMPLE_PATH.name
    st.session_state["source_bytes"] = None
    st.session_state["source_is_example"] = True
    reset_workspace_view()


def current_source() -> Path | BytesIO | None:
    """Return the active example path or an in-memory upload."""
    if st.session_state.get("source_is_example"):
        return EXAMPLE_PATH
    source_bytes = st.session_state.get("source_bytes")
    if source_bytes is None:
        return None
    return BytesIO(source_bytes)


def friendly_load_error(error: CsvLoadError) -> str:
    """Translate loader details into concise, actionable UI messages."""
    detail = str(error).casefold()
    if "colonne previste mancanti" in detail or "intestazione" in detail:
        return "Il CSV non contiene tutte le colonne previste."
    if "vuoto" in detail or "non contiene righe" in detail:
        return "Il file è vuoto."
    return "Il contenuto non può essere letto come CSV."


def render_header() -> None:
    """Render the product name and factual description."""
    st.title("Expense Quality Monitor")
    st.write("Controlla il file, individua le eccezioni e prepara il riepilogo.")


def render_initial_state() -> None:
    """Offer upload and example as equivalent starting paths."""
    st.subheader("Da dove vuoi partire?")
    st.write("Scegli un CSV oppure esplora l’app con il file di esempio.")
    with st.container(border=True):
        upload_column, example_column = st.columns(2, gap="large")
        with upload_column:
            st.file_uploader(
                "Scegli un CSV",
                type=["csv"],
                key="initial_upload",
                on_change=activate_uploaded_source,
                args=("initial_upload",),
            )
        with example_column:
            st.write("File di esempio")
            st.button(
                "Prova con l’esempio",
                key="use_example",
                on_click=activate_example_source,
                type="primary",
                width="stretch",
            )
            st.caption("data/synthetic_expenses.csv")
    st.caption("Il file viene elaborato nella sessione e non viene salvato.")


def render_sidebar(result: AnalysisResult | None = None) -> None:
    """Render source controls and session-level processing information."""
    st.sidebar.title("Expense Quality Monitor")
    source_name = st.session_state.get("source_name")
    if source_name:
        st.sidebar.caption("File selezionato")
        st.sidebar.write(source_name)
        st.sidebar.file_uploader(
            "Scegli un altro CSV",
            type=["csv"],
            key="replacement_upload",
            on_change=activate_uploaded_source,
            args=("replacement_upload",),
        )
    if result is not None:
        st.sidebar.divider()
        st.sidebar.caption("Sessione")
        st.sidebar.write(f"{len(result.source_data)} righe")
        st.sidebar.write(f"{len(result.findings)} segnalazioni")
    with st.sidebar.popover("Informazioni sull’elaborazione"):
        st.write("L’analisi resta nella sessione e non crea uno storico.")


def render_file_context(source_name: str, total_rows: int) -> None:
    """Show compact source and analysis status."""
    st.caption(f"{source_name} · {total_rows} righe · Analisi completata")


def render_overview(result: AnalysisResult) -> None:
    """Render metrics before compact distributions and category detail."""
    summary = result.summary
    total_rows = cast(int, summary["total_rows"])
    rows_with_findings = cast(int, summary["rows_with_findings"])
    by_anomaly_type = cast(dict[str, int], summary["by_anomaly_type"])
    by_status = cast(dict[str, int], summary["by_status"])
    by_category = cast(pd.DataFrame, summary["by_category"])

    metric_columns = st.columns(4)
    metric_columns[0].metric("Righe", total_rows)
    metric_columns[1].metric("Righe da verificare", rows_with_findings)
    metric_columns[2].metric("Segnalazioni", len(result.findings))
    metric_columns[3].metric("Regole coinvolte", distinct_rule_count(result.findings))

    distribution_column, status_column = st.columns(2, gap="large")
    with distribution_column:
        st.subheader("Dove si concentrano le segnalazioni")
        anomaly_frame = counts_to_frame(by_anomaly_type, "Tipo")
        st.bar_chart(anomaly_frame, x="Tipo", y="Conteggio", height=260)
    with status_column:
        st.subheader("Stato delle verifiche")
        status_frame = counts_to_frame(by_status, "Stato")
        st.bar_chart(status_frame, x="Stato", y="Conteggio", height=260)

    st.subheader("Categorie")
    st.dataframe(
        by_category,
        hide_index=True,
        width="stretch",
        column_config={
            "categoria": st.column_config.TextColumn("Categoria", width="medium"),
            "total_rows": st.column_config.NumberColumn("Righe", width="small"),
            "rows_with_findings": st.column_config.NumberColumn(
                "Righe da verificare",
                width="small",
            ),
        },
    )


def render_filter_controls(enriched_findings: pd.DataFrame) -> pd.DataFrame:
    """Render search and compact filters next to the findings table."""
    st.text_input(
        "Cerca per ID, regola o descrizione",
        key="finding_search",
        placeholder="ID spesa, rule ID o testo",
    )
    filter_columns = st.columns(4)
    with filter_columns[0]:
        st.multiselect(
            "Tipo",
            sorted(enriched_findings["anomaly_type"].dropna().unique()),
            key="filter_types",
        )
    with filter_columns[1]:
        st.multiselect(
            "Stato",
            sorted(enriched_findings["status"].dropna().unique()),
            key="filter_statuses",
        )
    with filter_columns[2]:
        st.multiselect(
            "Categoria",
            sorted(enriched_findings["categoria"].dropna().unique()),
            key="filter_categories",
        )
    with filter_columns[3]:
        st.multiselect(
            "Regola",
            sorted(enriched_findings["rule_id"].dropna().unique()),
            key="filter_rules",
        )
    st.button("Ripristina filtri", on_click=reset_filters)
    return filter_findings(
        enriched_findings,
        query=st.session_state["finding_search"],
        anomaly_types=st.session_state["filter_types"],
        statuses=st.session_state["filter_statuses"],
        categories=st.session_state["filter_categories"],
        rule_ids=st.session_state["filter_rules"],
    )


def findings_table(findings: pd.DataFrame) -> None:
    """Render findings with user-facing labels and stable source ordering."""
    st.dataframe(
        findings.loc[:, TABLE_COLUMNS],
        hide_index=True,
        width="stretch",
        height=520,
        column_config={
            "source_row_number": st.column_config.NumberColumn(
                "Riga CSV",
                width="small",
                format="%d",
            ),
            "id_spesa": st.column_config.TextColumn("ID spesa", width="small"),
            "status": st.column_config.TextColumn("Stato", width="medium"),
            "anomaly_type": st.column_config.TextColumn("Tipo", width="medium"),
            "field": st.column_config.TextColumn("Campo", width="small"),
            "message": st.column_config.TextColumn("Descrizione", width="large"),
            "original_value": st.column_config.TextColumn(
                "Valore originale",
                width="medium",
            ),
            "rule_id": st.column_config.TextColumn("Regola", width="large"),
        },
    )


def current_filter_description() -> str:
    """Return a factual description of active search and filters."""
    descriptions = []
    query = st.session_state["finding_search"].strip()
    if query:
        descriptions.append(f"Ricerca: {query}")
    labels = (
        ("Tipo", "filter_types"),
        ("Stato", "filter_statuses"),
        ("Categoria", "filter_categories"),
        ("Regola", "filter_rules"),
    )
    for label, key in labels:
        values = st.session_state[key]
        if values:
            descriptions.append(f"{label}: {', '.join(values)}")
    return " · ".join(descriptions) if descriptions else "Nessun filtro attivo"


def render_findings(result: AnalysisResult, enriched_findings: pd.DataFrame) -> pd.DataFrame:
    """Render the primary findings workspace and return its current view."""
    st.subheader("Segnalazioni")
    filtered = render_filter_controls(enriched_findings)
    st.write(f"{len(filtered)} risultati su {len(result.findings)}")
    if filtered.empty:
        st.info("Nessun risultato con i filtri attuali.")
    findings_table(filtered)
    st.download_button(
        "Scarica la vista corrente",
        data=findings_to_csv(filtered.loc[:, FINDING_COLUMNS]),
        file_name="expense_quality_findings.csv",
        mime="text/csv",
        type="primary",
    )
    return filtered


def render_data(result: AnalysisResult, source_name: str) -> None:
    """Render source metadata and a preview without internal working columns."""
    st.subheader("Dati")
    st.write("Qui puoi controllare il contenuto ricevuto prima di approfondire le segnalazioni.")
    source_view = result.source_data.drop(columns=["source_row_number"], errors="ignore")
    metadata_columns = st.columns(3)
    metadata_columns[0].metric("File", source_name)
    metadata_columns[1].metric("Righe", len(source_view))
    metadata_columns[2].metric("Colonne", len(source_view.columns))
    st.caption("Nomi delle colonne")
    st.write(", ".join(source_view.columns))
    st.caption("Anteprima")
    st.dataframe(source_view.head(50), hide_index=True, width="stretch", height=480)


def render_export(filtered: pd.DataFrame) -> None:
    """Render export facts and download the current filtered schema."""
    st.subheader("Esporta")
    export_columns = st.columns(3)
    export_columns[0].metric("Righe incluse", len(filtered))
    export_columns[1].metric("Formato", "CSV")
    export_columns[2].metric("Colonne", len(FINDING_COLUMNS))
    st.caption("Filtri attivi")
    st.write(current_filter_description())
    if filtered.empty:
        st.info("La vista corrente non contiene righe da esportare.")
        return
    st.download_button(
        "Scarica la vista corrente",
        data=findings_to_csv(filtered.loc[:, FINDING_COLUMNS]),
        file_name="expense_quality_findings.csv",
        mime="text/csv",
        type="primary",
    )


def analyze_current_source() -> AnalysisResult | None:
    """Analyze the active session source and show concise load errors."""
    source = current_source()
    if source is None:
        return None
    try:
        with st.spinner("Analisi in corso"):
            return analyze_expenses(source)
    except CsvLoadError as error:
        st.error(friendly_load_error(error))
    except Exception:
        LOGGER.exception("Errore imprevisto durante l'analisi del CSV.")
        st.error("L’analisi non è stata completata. Puoi scegliere un altro CSV.")
    return None


def render_dashboard() -> None:
    """Render the session-based expense-quality workspace."""
    st.set_page_config(
        page_title="Expense Quality Monitor",
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_header()
    result = analyze_current_source()
    if result is None:
        render_sidebar()
        if current_source() is None:
            render_initial_state()
        return

    render_sidebar(result)
    source_name = cast(str, st.session_state["source_name"])
    render_file_context(source_name, len(result.source_data))
    st.session_state.setdefault("workspace_section", "Panoramica")
    section = st.segmented_control(
        "Sezione",
        SECTIONS,
        key="workspace_section",
        label_visibility="collapsed",
    )
    enriched_findings = findings_with_categories(result.findings, result.source_data)
    filtered = filter_findings(
        enriched_findings,
        query=st.session_state.get("finding_search", ""),
        anomaly_types=st.session_state.get("filter_types", []),
        statuses=st.session_state.get("filter_statuses", []),
        categories=st.session_state.get("filter_categories", []),
        rule_ids=st.session_state.get("filter_rules", []),
    )

    if section == "Panoramica":
        render_overview(result)
    elif section == "Segnalazioni":
        render_findings(result, enriched_findings)
    elif section == "Dati":
        render_data(result, source_name)
    elif section == "Esporta":
        render_export(filtered)


render_dashboard()
