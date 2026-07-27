"""Streamlit workspace for deterministic expense-quality analysis."""

from __future__ import annotations

import csv
import logging
from collections.abc import Callable, Mapping, Sequence
from io import BytesIO, StringIO
from pathlib import Path
from typing import cast

import pandas as pd
import streamlit as st

from expense_quality_monitor import i18n
from expense_quality_monitor.config import EXPECTED_COLUMNS, FINDING_COLUMNS
from expense_quality_monitor.loader import (
    CSV_ERROR_DUPLICATE_COLUMNS,
    CSV_ERROR_EMPTY,
    CSV_ERROR_INCOMPATIBLE_SCHEMA,
    SOURCE_ROW_COLUMN,
    CsvLoadError,
    SchemaComparison,
    compare_schema,
)
from expense_quality_monitor.pipeline import AnalysisResult, analyze_expenses
from expense_quality_monitor.reporting import findings_to_csv

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
EXAMPLE_PATH = ROOT / "data" / "synthetic_expenses.csv"
TEMPLATE_FILENAME = "expense_quality_monitor_template.csv"
FINDINGS_FILENAME = "expense_quality_findings.csv"
CSV_MIME_TYPE = "text/csv"
SECTION_IDS = ("overview", "findings", "data", "export")
DEFAULT_SECTION = SECTION_IDS[0]
SECTION_WIDGET_KEY = "workspace_section_widget"
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
ANOMALY_TYPE_KEYS = {
    "completezza": "finding.type.completezza",
    "unicità": "finding.type.unicità",
    "validità": "finding.type.validità",
    "anomalia statistica": "finding.type.anomalia_statistica",
    "valutabilità statistica": "finding.type.valutabilità_statistica",
    "policy": "finding.type.policy",
    "non conformità": "finding.type.non_conformità",
}
STATUS_KEYS = {
    "incompleta": "finding.status.incompleta",
    "duplicato": "finding.status.duplicato",
    "duplicato logico": "finding.status.duplicato_logico",
    "non valido": "finding.status.non_valido",
    "non valida": "finding.status.non_valida",
    "anomalia statistica": "finding.status.anomalia_statistica",
    "non valutabile statisticamente": "finding.status.non_valutabile_statisticamente",
    "richiede approvazione": "finding.status.richiede_approvazione",
    "non conforme": "finding.status.non_conforme",
}


def counts_to_frame(
    counts: Mapping[str, int],
    label: str,
    value_formatter: Callable[[str], str] | None = None,
    count_label: str = "Conteggio",
) -> pd.DataFrame:
    """Return deterministic count rows suitable for charts and tables."""
    format_value = value_formatter or (lambda value: value)
    rows = [
        {label: format_value(name), count_label: count} for name, count in sorted(counts.items())
    ]
    return pd.DataFrame(rows, columns=[label, count_label])


def initialize_language() -> None:
    """Initialize the session language once from the available browser locale."""
    if "language" in st.session_state:
        return
    try:
        locale = st.context.locale
    except (AttributeError, RuntimeError):
        locale = None
    st.session_state["language"] = i18n.normalize_language(locale)


def current_language() -> str:
    """Return the normalized language stored for the current session."""
    return i18n.normalize_language(st.session_state.get("language"))


def tr(key: str, **values: object) -> str:
    """Translate one UI key using the current session language."""
    return i18n.translate(key, current_language(), **values)


def localized_value(
    value: object,
    keys: Mapping[str, str],
    language: str,
) -> str:
    """Localize a known canonical display value without changing its source."""
    canonical_value = str(value)
    translation_key = keys.get(canonical_value)
    if translation_key is None:
        return canonical_value
    return i18n.translate(translation_key, language)


def localized_rule_message(rule_id: object, original: object, language: str) -> str:
    """Localize a known rule message while preserving unknown canonical values."""
    key = f"rule.{rule_id}.message"
    try:
        return i18n.translate(key, language)
    except KeyError:
        return str(original)


def findings_for_presentation(findings: pd.DataFrame, language: str) -> pd.DataFrame:
    """Return a localized UI copy without changing findings or their export."""
    presented = findings.copy()
    presented["anomaly_type"] = presented["anomaly_type"].map(
        lambda value: localized_value(value, ANOMALY_TYPE_KEYS, language)
    )
    presented["status"] = presented["status"].map(
        lambda value: localized_value(value, STATUS_KEYS, language)
    )
    presented["message"] = [
        localized_rule_message(rule_id, message, language)
        for rule_id, message in zip(
            presented["rule_id"],
            presented["message"],
            strict=True,
        )
    ]
    return presented


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
    language: str = i18n.DEFAULT_LANGUAGE,
) -> pd.DataFrame:
    """Return a deterministic filtered copy of the enriched findings."""
    filtered = findings
    normalized_query = query.strip().casefold()
    if normalized_query:
        localized_messages = [
            localized_rule_message(rule_id, message, language)
            for rule_id, message in zip(
                filtered["rule_id"],
                filtered["message"],
                strict=True,
            )
        ]
        searchable = filtered[["id_spesa", "rule_id", "message"]].fillna("").astype(str)
        searchable["_localized_message"] = localized_messages
        searchable = searchable.agg(" ".join, axis=1).str.casefold()
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


def build_template_csv() -> bytes:
    """Return a UTF-8 CSV template containing only the canonical header."""
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(EXPECTED_COLUMNS)
    return buffer.getvalue().encode("utf-8")


def source_extra_columns(source_data: pd.DataFrame) -> tuple[str, ...]:
    """Return deterministic extra source columns, excluding the technical row number."""
    columns = [column for column in source_data.columns if column != SOURCE_ROW_COLUMN]
    return compare_schema(columns).extra_columns


def reset_filters() -> None:
    """Clear only the search and table filters."""
    st.session_state["finding_search"] = ""
    for key in FILTER_KEYS[1:]:
        st.session_state[key] = []


def reset_workspace_view() -> None:
    """Return navigation and filters to their initial state after changing source."""
    st.session_state["workspace_section"] = DEFAULT_SECTION
    st.session_state[SECTION_WIDGET_KEY] = DEFAULT_SECTION
    reset_filters()


def set_active_source(
    *,
    name: str,
    content: bytes | None,
    is_example: bool,
) -> None:
    """Store one active source without rendering or reading external data."""
    st.session_state["source_name"] = name
    st.session_state["source_bytes"] = content
    st.session_state["source_is_example"] = is_example


def activate_uploaded_source(widget_key: str) -> None:
    """Keep a selected upload in session memory across subsequent reruns."""
    uploaded_file = st.session_state.get(widget_key)
    if uploaded_file is None:
        return
    set_active_source(
        name=uploaded_file.name,
        content=uploaded_file.getvalue(),
        is_example=False,
    )
    reset_workspace_view()


def activate_example_source() -> None:
    """Select the versioned example without copying or changing it."""
    set_active_source(name=EXAMPLE_PATH.name, content=None, is_example=True)
    reset_workspace_view()


def render_example_button(*, key: str) -> None:
    """Render the shared action that selects the versioned example."""
    st.button(
        tr("upload.example_action"),
        key=key,
        on_click=activate_example_source,
        type="primary",
        width="stretch",
    )


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
    if error.code == CSV_ERROR_EMPTY:
        return tr("error.empty")
    if error.code == CSV_ERROR_DUPLICATE_COLUMNS:
        return tr("error.duplicate_columns")
    return tr("error.unreadable")


def render_schema_guidance(schema: SchemaComparison) -> None:
    """Explain an incompatible expense schema and offer useful local actions."""
    st.warning(tr("schema.incompatible"))
    st.write(tr("schema.guidance"))
    with st.container(border=True):
        st.subheader(tr("schema.missing_columns"))
        missing_count = len(schema.missing_columns)
        missing_key = (
            "schema.missing_count.one" if missing_count == 1 else "schema.missing_count.many"
        )
        st.write(tr(missing_key, count=missing_count))
        st.write(", ".join(schema.missing_columns))
        st.subheader(tr("schema.found_columns"))
        st.write(", ".join(schema.found_columns))
        if schema.extra_columns:
            st.subheader(tr("schema.extra_columns"))
            st.write(", ".join(schema.extra_columns))

    action_columns = st.columns(2)
    with action_columns[0]:
        st.caption(tr("upload.template_description"))
        st.download_button(
            tr("upload.template_download"),
            data=build_template_csv(),
            file_name=TEMPLATE_FILENAME,
            mime=CSV_MIME_TYPE,
            width="stretch",
        )
    with action_columns[1]:
        render_example_button(key="use_example_after_schema_error")


def render_header() -> None:
    """Render the product name and factual description."""
    st.title(tr("app.title"))
    st.write(tr("app.subtitle"))


def render_initial_state() -> None:
    """Offer upload and example as equivalent starting paths."""
    st.subheader(tr("upload.title"))
    st.write(tr("upload.description"))
    with st.container(border=True):
        upload_column, example_column = st.columns(2, gap="large")
        with upload_column:
            st.file_uploader(
                tr("upload.button"),
                type=["csv"],
                key="initial_upload",
                on_change=activate_uploaded_source,
                args=("initial_upload",),
            )
        with example_column:
            st.write(tr("upload.example"))
            render_example_button(key="use_example")
            st.caption("data/synthetic_expenses.csv")
    st.caption(tr("upload.privacy"))


def render_language_selector() -> None:
    """Render a persistent selector whose values remain stable language codes."""
    language = current_language()
    st.sidebar.selectbox(
        i18n.translate("language.label", language),
        i18n.SUPPORTED_LANGUAGES,
        key="language",
        format_func=lambda code: i18n.translate(
            "language.italian" if code == "it" else "language.english",
            language,
        ),
    )


def render_sidebar(result: AnalysisResult | None = None) -> None:
    """Render source controls and session-level processing information."""
    st.sidebar.title(tr("app.title"))
    render_language_selector()
    source_name = st.session_state.get("source_name")
    if source_name:
        st.sidebar.caption(tr("upload.selected"))
        st.sidebar.write(source_name)
        st.sidebar.file_uploader(
            tr("upload.replace"),
            type=["csv"],
            key="replacement_upload",
            on_change=activate_uploaded_source,
            args=("replacement_upload",),
        )
    if result is not None:
        st.sidebar.divider()
        st.sidebar.caption(tr("session.title"))
        row_count = len(result.source_data)
        row_key = "session.rows.one" if row_count == 1 else "session.rows.many"
        st.sidebar.write(tr(row_key, count=row_count))
        finding_count = len(result.findings)
        finding_key = "session.findings.one" if finding_count == 1 else "session.findings.many"
        st.sidebar.write(tr(finding_key, count=finding_count))
    with st.sidebar.popover(tr("session.processing_info")):
        st.write(tr("session.processing_detail"))


def render_file_context(source_name: str, total_rows: int) -> None:
    """Show compact source and analysis status."""
    st.caption(tr("source.context", name=source_name, rows=total_rows))


def render_overview(result: AnalysisResult) -> None:
    """Render metrics before compact distributions and category detail."""
    summary = result.summary
    total_rows = cast(int, summary["total_rows"])
    rows_with_findings = cast(int, summary["rows_with_findings"])
    by_anomaly_type = cast(dict[str, int], summary["by_anomaly_type"])
    by_status = cast(dict[str, int], summary["by_status"])
    by_category = cast(pd.DataFrame, summary["by_category"])
    language = current_language()

    metric_columns = st.columns(4)
    metric_columns[0].metric(tr("metric.total_rows"), total_rows)
    metric_columns[1].metric(tr("metric.rows_to_review"), rows_with_findings)
    metric_columns[2].metric(tr("metric.findings"), len(result.findings))
    metric_columns[3].metric(tr("metric.rules"), distinct_rule_count(result.findings))

    distribution_column, status_column = st.columns(2, gap="large")
    with distribution_column:
        st.subheader(tr("overview.findings_by_type"))
        type_label = tr("common.type")
        count_label = tr("common.count")
        anomaly_frame = counts_to_frame(
            by_anomaly_type,
            type_label,
            lambda value: localized_value(value, ANOMALY_TYPE_KEYS, language),
            count_label,
        )
        st.bar_chart(anomaly_frame, x=type_label, y=count_label, height=260)
    with status_column:
        st.subheader(tr("overview.findings_by_status"))
        status_label = tr("common.status")
        count_label = tr("common.count")
        status_frame = counts_to_frame(
            by_status,
            status_label,
            lambda value: localized_value(value, STATUS_KEYS, language),
            count_label,
        )
        st.bar_chart(status_frame, x=status_label, y=count_label, height=260)

    st.subheader(tr("overview.categories"))
    st.dataframe(
        by_category,
        hide_index=True,
        width="stretch",
        column_config={
            "categoria": st.column_config.TextColumn(tr("common.category"), width="medium"),
            "total_rows": st.column_config.NumberColumn(
                tr("metric.total_rows"),
                width="small",
            ),
            "rows_with_findings": st.column_config.NumberColumn(
                tr("metric.rows_to_review"),
                width="small",
            ),
        },
    )


def render_filter_controls(enriched_findings: pd.DataFrame) -> pd.DataFrame:
    """Render search and compact filters next to the findings table."""
    language = current_language()
    st.text_input(
        tr("findings.search"),
        key="finding_search",
        placeholder=tr("findings.search_placeholder"),
    )
    filter_columns = st.columns(4)
    with filter_columns[0]:
        st.multiselect(
            tr("common.type"),
            sorted(enriched_findings["anomaly_type"].dropna().unique()),
            key="filter_types",
            format_func=lambda value: localized_value(value, ANOMALY_TYPE_KEYS, language),
        )
    with filter_columns[1]:
        st.multiselect(
            tr("common.status"),
            sorted(enriched_findings["status"].dropna().unique()),
            key="filter_statuses",
            format_func=lambda value: localized_value(value, STATUS_KEYS, language),
        )
    with filter_columns[2]:
        st.multiselect(
            tr("common.category"),
            sorted(enriched_findings["categoria"].dropna().unique()),
            key="filter_categories",
        )
    with filter_columns[3]:
        st.multiselect(
            tr("common.rule"),
            sorted(enriched_findings["rule_id"].dropna().unique()),
            key="filter_rules",
        )
    st.button(tr("findings.reset"), on_click=reset_filters)
    return filter_findings(
        enriched_findings,
        query=st.session_state["finding_search"],
        anomaly_types=st.session_state["filter_types"],
        statuses=st.session_state["filter_statuses"],
        categories=st.session_state["filter_categories"],
        rule_ids=st.session_state["filter_rules"],
        language=language,
    )


def findings_table(findings: pd.DataFrame, language: str) -> None:
    """Render findings with user-facing labels and stable source ordering."""
    presented = findings_for_presentation(findings, language)
    st.dataframe(
        presented.loc[:, TABLE_COLUMNS],
        hide_index=True,
        width="stretch",
        height=520,
        column_config={
            "source_row_number": st.column_config.NumberColumn(
                tr("findings.table.source_row"),
                width="small",
                format="%d",
            ),
            "id_spesa": st.column_config.TextColumn(
                tr("findings.table.expense_id"),
                width="small",
            ),
            "status": st.column_config.TextColumn(tr("common.status"), width="medium"),
            "anomaly_type": st.column_config.TextColumn(
                tr("common.type"),
                width="medium",
            ),
            "field": st.column_config.TextColumn(tr("common.field"), width="small"),
            "message": st.column_config.TextColumn(
                tr("common.description"),
                width="large",
            ),
            "original_value": st.column_config.TextColumn(
                tr("findings.table.original_value"),
                width="medium",
            ),
            "rule_id": st.column_config.TextColumn(tr("common.rule"), width="large"),
        },
    )


def current_filter_description(language: str) -> str:
    """Return a factual description of active search and filters."""
    descriptions = []
    query = st.session_state["finding_search"].strip()
    if query:
        descriptions.append(i18n.translate("filters.search", language, query=query))
    labels = (
        ("common.type", "filter_types", ANOMALY_TYPE_KEYS),
        ("common.status", "filter_statuses", STATUS_KEYS),
        ("common.category", "filter_categories", {}),
        ("common.rule", "filter_rules", {}),
    )
    for label_key, key, value_keys in labels:
        values = st.session_state[key]
        if values:
            displayed_values = [localized_value(value, value_keys, language) for value in values]
            descriptions.append(
                i18n.translate(
                    "filters.value",
                    language,
                    label=i18n.translate(label_key, language),
                    values=", ".join(displayed_values),
                )
            )
    if not descriptions:
        return i18n.translate("filters.none", language)
    return " · ".join(descriptions)


def render_findings_download(findings: pd.DataFrame, *, key: str) -> None:
    """Render the shared CSV download for one findings view."""
    st.download_button(
        tr("findings.download"),
        data=findings_to_csv(findings.loc[:, FINDING_COLUMNS]),
        file_name=FINDINGS_FILENAME,
        mime=CSV_MIME_TYPE,
        type="primary",
        key=key,
    )


def render_findings(result: AnalysisResult, enriched_findings: pd.DataFrame) -> pd.DataFrame:
    """Render the primary findings workspace and return its current view."""
    language = current_language()
    st.subheader(tr("findings.title"))
    filtered = render_filter_controls(enriched_findings)
    shown = len(filtered)
    total = len(result.findings)
    results_key = "findings.results.one" if shown == 1 else "findings.results.many"
    st.write(tr(results_key, shown=shown, total=total))
    if filtered.empty:
        st.info(tr("findings.no_results"))
    findings_table(filtered, language)
    render_findings_download(filtered, key="findings_download")
    return filtered


def render_data(result: AnalysisResult, source_name: str) -> None:
    """Render source metadata and a preview without internal working columns."""
    st.subheader(tr("data.title"))
    st.write(tr("data.description"))
    source_view = result.source_data.drop(columns=["source_row_number"], errors="ignore")
    metadata_columns = st.columns(3)
    metadata_columns[0].metric(tr("metric.file"), source_name)
    metadata_columns[1].metric(tr("metric.total_rows"), len(source_view))
    metadata_columns[2].metric(tr("metric.columns"), len(source_view.columns))
    st.caption(tr("data.column_names"))
    st.write(", ".join(source_view.columns))
    st.caption(tr("data.preview"))
    st.dataframe(source_view.head(50), hide_index=True, width="stretch", height=480)


def render_export(filtered: pd.DataFrame, language: str) -> None:
    """Render export facts and download the current filtered schema."""
    st.subheader(tr("export.title"))
    export_columns = st.columns(3)
    export_columns[0].metric(tr("metric.rows_included"), len(filtered))
    export_columns[1].metric(tr("metric.format"), "CSV")
    export_columns[2].metric(tr("metric.columns"), len(FINDING_COLUMNS))
    st.caption(tr("export.active_filters"))
    st.write(current_filter_description(language))
    if filtered.empty:
        st.info(tr("export.empty"))
        return
    render_findings_download(filtered, key="export_download")


def analyze_current_source() -> AnalysisResult | None:
    """Analyze the active session source and show concise load errors."""
    source = current_source()
    if source is None:
        return None
    try:
        with st.spinner(tr("analysis.running")):
            return analyze_expenses(source)
    except CsvLoadError as error:
        if error.code == CSV_ERROR_INCOMPATIBLE_SCHEMA and error.schema is not None:
            render_schema_guidance(error.schema)
        else:
            st.warning(friendly_load_error(error))
    except Exception:
        LOGGER.exception("Errore imprevisto durante l'analisi del CSV.")
        st.error(tr("error.unexpected"))
    return None


def render_dashboard() -> None:
    """Render the session-based expense-quality workspace."""
    st.set_page_config(
        page_title="Expense Quality Monitor",
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    initialize_language()
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
    extra_columns = source_extra_columns(result.source_data)
    if extra_columns:
        extra_count = len(extra_columns)
        extra_key = "source.extra.one" if extra_count == 1 else "source.extra.many"
        st.info(tr(extra_key, count=extra_count))
    stable_section = st.session_state.setdefault("workspace_section", DEFAULT_SECTION)
    if stable_section not in SECTION_IDS:
        stable_section = DEFAULT_SECTION
        st.session_state["workspace_section"] = stable_section
        st.session_state[SECTION_WIDGET_KEY] = stable_section
    elif st.session_state.get(SECTION_WIDGET_KEY) not in SECTION_IDS:
        st.session_state[SECTION_WIDGET_KEY] = stable_section
    section = st.segmented_control(
        tr("nav.label"),
        SECTION_IDS,
        key=SECTION_WIDGET_KEY,
        label_visibility="collapsed",
        format_func=lambda section_id: tr(f"nav.{section_id}"),
    )
    if section in SECTION_IDS:
        st.session_state["workspace_section"] = section
    else:
        section = stable_section
    language = current_language()
    enriched_findings = findings_with_categories(result.findings, result.source_data)
    filtered = filter_findings(
        enriched_findings,
        query=st.session_state.get("finding_search", ""),
        anomaly_types=st.session_state.get("filter_types", []),
        statuses=st.session_state.get("filter_statuses", []),
        categories=st.session_state.get("filter_categories", []),
        rule_ids=st.session_state.get("filter_rules", []),
        language=language,
    )

    if section == "overview":
        render_overview(result)
    elif section == "findings":
        render_findings(result, enriched_findings)
    elif section == "data":
        render_data(result, source_name)
    elif section == "export":
        render_export(filtered, language)


render_dashboard()
