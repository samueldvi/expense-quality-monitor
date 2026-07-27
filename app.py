"""Streamlit workspace for deterministic expense-quality analysis."""

from __future__ import annotations

import csv
import html
import logging
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import cast
from urllib.parse import quote

import pandas as pd
import streamlit as st

from expense_quality_monitor import i18n
from expense_quality_monitor.config import EXPECTED_COLUMNS, FINDING_COLUMNS
from expense_quality_monitor.governance import (
    ProcessingMetadata,
    application_version,
    build_dimension_summary,
    build_processing_metadata,
    build_rule_catalog,
    filter_rule_catalog,
)
from expense_quality_monitor.loader import (
    CSV_ERROR_DUPLICATE_COLUMNS,
    CSV_ERROR_EMPTY,
    CSV_ERROR_INCOMPATIBLE_SCHEMA,
    SOURCE_ROW_COLUMN,
    CsvLoadError,
    SchemaComparison,
    compare_schema,
    inspect_csv_source,
)
from expense_quality_monitor.pipeline import AnalysisResult, analyze_expenses
from expense_quality_monitor.profiling import (
    DataProfile,
    build_column_profile,
    build_data_dictionary,
    build_data_profile,
)
from expense_quality_monitor.reporting import findings_to_csv
from expense_quality_monitor.ui_theme import (
    chart_color_for_status,
    role_icon,
    semantic_role_for_status,
    status_cell_style,
    theme_tokens,
)

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
EXAMPLE_PATH = ROOT / "data" / "synthetic_expenses.csv"
HERO_PATH = ROOT / "docs" / "assets" / "dashboard-hero.svg"
TEMPLATE_FILENAME = "expense_quality_monitor_template.csv"
FINDINGS_FILENAME = "expense_quality_findings.csv"
CSV_MIME_TYPE = "text/csv"
SECTION_IDS = ("overview", "findings", "profile", "governance", "data", "export")
DEFAULT_SECTION = SECTION_IDS[0]
SECTION_WIDGET_KEY = "workspace_section_widget"
SOURCE_IDENTITY_KEY = "source_identity"
FILTER_KEYS = (
    "finding_search",
    "filter_types",
    "filter_statuses",
    "filter_categories",
    "filter_rules",
)
GOVERNANCE_FILTER_KEYS = (
    "governance_filter_types",
    "governance_filter_dimensions",
    "governance_filter_statuses",
    "governance_filter_fields",
)
GOVERNANCE_RULE_PRESENTATION_COLUMNS = (
    "rule_id",
    "name",
    "description",
    "anomaly_type",
    "dimension",
    "status",
    "fields",
    "parameters",
)
RESPONSIBILITY_KEYS = (
    "governance_owner",
    "governance_steward",
    "governance_organization",
    "governance_period",
    "governance_notes",
)
RESPONSIBILITY_WIDGET_KEYS = tuple(f"_{key}_widget" for key in RESPONSIBILITY_KEYS)
PROCESSING_METADATA_KEY = "processing_metadata"
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
DICTIONARY_TABLE_COLUMNS = (
    "technical_name",
    "display_name",
    "description",
    "required",
    "expected_type",
    "format",
    "allowed_values",
    "example",
    "rules",
    "dimensions",
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
SECTION_ICONS = {
    "overview": "▦",
    "findings": "⚑",
    "profile": "◫",
    "governance": "◇",
    "data": "▤",
    "export": "⇩",
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


def current_theme() -> str:
    """Return the active Streamlit theme with a deterministic light fallback."""
    try:
        theme = st.context.theme.type
    except (AttributeError, RuntimeError):
        theme = None
    return theme if theme in {"light", "dark"} else "light"


def accessible_hero_svg(description: str) -> str:
    """Return the local hero SVG with a localized accessible name."""
    svg = HERO_PATH.read_text(encoding="utf-8")
    label = html.escape(description, quote=True)
    return (
        f'<img src="data:image/svg+xml,{quote(svg)}" alt="{label}" '
        'style="display:block;width:100%;height:auto;max-height:16rem">'
    )


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
    presented["status"] = [
        (
            f"{role_icon(semantic_role_for_status(value))} "
            f"{localized_value(value, STATUS_KEYS, language)}"
        )
        for value in presented["status"]
    ]
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


def reset_governance_state() -> None:
    """Discard source-bound metadata and optional local responsibilities."""
    st.session_state.pop(PROCESSING_METADATA_KEY, None)
    for key in RESPONSIBILITY_KEYS:
        st.session_state.pop(key, None)
    for key in RESPONSIBILITY_WIDGET_KEYS:
        st.session_state.pop(key, None)
    for key in GOVERNANCE_FILTER_KEYS:
        st.session_state.pop(key, None)


def synchronize_source_identity(name: str, content: bytes) -> bool:
    """Reset source-bound state only when name or exact bytes change."""
    identity = (name, content)
    if st.session_state.get(SOURCE_IDENTITY_KEY) == identity:
        return False
    reset_governance_state()
    st.session_state[SOURCE_IDENTITY_KEY] = identity
    return True


def set_active_source(
    *,
    name: str,
    content: bytes | None,
    is_example: bool,
) -> None:
    """Store one active source without rendering or reading external data."""
    identity_content = EXAMPLE_PATH.read_bytes() if is_example else content
    if identity_content is None:
        raise ValueError("An uploaded source requires byte content")
    synchronize_source_identity(name, identity_content)
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
        icon=":material/science:",
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


def current_source_bytes() -> bytes | None:
    """Return the exact original bytes for the active source."""
    if st.session_state.get("source_is_example"):
        return EXAMPLE_PATH.read_bytes()
    source_bytes = st.session_state.get("source_bytes")
    return source_bytes if isinstance(source_bytes, bytes) else None


def friendly_load_error(error: CsvLoadError) -> str:
    """Translate loader details into concise, actionable UI messages."""
    if error.code == CSV_ERROR_EMPTY:
        return tr("error.empty")
    if error.code == CSV_ERROR_DUPLICATE_COLUMNS:
        return tr("error.duplicate_columns")
    return tr("error.unreadable")


def render_schema_guidance(schema: SchemaComparison) -> None:
    """Explain an incompatible expense schema and offer useful local actions."""
    st.warning(tr("schema.incompatible"), icon=":material/warning:")
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
            icon=":material/download:",
            width="stretch",
        )
    with action_columns[1]:
        render_example_button(key="use_example_after_schema_error")


def render_header() -> None:
    """Render a compact product hero with a local, descriptive illustration."""
    text_column, image_column = st.columns([3, 1], gap="large")
    with text_column:
        st.title(tr("app.title"))
        st.write(tr("app.subtitle"))
        st.caption(f"✓ {tr('hero.deterministic_badge')}")
    with image_column:
        st.html(accessible_hero_svg(tr("hero.image_alt")))


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
        st.divider()
        st.caption(tr("upload.template_description"))
        st.download_button(
            tr("upload.template_download"),
            data=build_template_csv(),
            file_name=TEMPLATE_FILENAME,
            mime=CSV_MIME_TYPE,
            icon=":material/download:",
        )
    st.caption(tr("upload.privacy"))


def render_language_selector() -> None:
    """Render a persistent selector whose values remain stable language codes."""
    language = current_language()
    st.sidebar.selectbox(
        f"🌐 {i18n.translate('language.label', language)}",
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
        st.sidebar.text(source_name)
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


def render_file_context(
    source_name: str,
    *,
    is_example: bool,
    extra_columns: tuple[str, ...],
) -> None:
    """Show compact source provenance and analysis status without repeating KPIs."""
    source_kind = tr("source.kind.example" if is_example else "status.file_loaded")
    with st.container(border=True):
        st.text(f"📄 {source_name}")
        st.markdown(
            ":blue-background["
            f"{role_icon('information')} {source_kind}] "
            ":green-background["
            f"{role_icon('success')} {tr('status.analysis_complete')}]"
        )
        if extra_columns:
            extra_count = len(extra_columns)
            extra_key = "source.extra.one" if extra_count == 1 else "source.extra.many"
            st.info(tr(extra_key, count=extra_count), icon=":material/info:")


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
    metric_columns[0].metric(tr("metric.total_rows"), total_rows, border=True)
    metric_columns[1].metric(
        f"{role_icon('warning')} {tr('metric.rows_to_review')}",
        rows_with_findings,
        border=True,
    )
    metric_columns[2].metric(tr("metric.findings"), len(result.findings), border=True)
    metric_columns[3].metric(
        tr("metric.rules"),
        distinct_rule_count(result.findings),
        border=True,
    )

    distribution_column, status_column = st.columns(2, gap="large")
    with distribution_column:
        st.subheader(f"▥ {tr('overview.findings_by_type')}")
        type_label = tr("common.type")
        count_label = tr("common.count")
        anomaly_frame = counts_to_frame(
            by_anomaly_type,
            type_label,
            lambda value: localized_value(value, ANOMALY_TYPE_KEYS, language),
            count_label,
        )
        if anomaly_frame.empty:
            st.caption(tr("status.no_findings"))
        else:
            st.bar_chart(anomaly_frame, x=type_label, y=count_label, height=260)
    with status_column:
        st.subheader(f"◉ {tr('overview.findings_by_status')}")
        status_label = tr("common.status")
        count_label = tr("common.count")
        status_rows = [
            {
                status_label: localized_value(status, STATUS_KEYS, language),
                count_label: count,
                "_color": chart_color_for_status(status, current_theme()),
            }
            for status, count in sorted(by_status.items())
        ]
        status_frame = pd.DataFrame(
            status_rows,
            columns=[status_label, count_label, "_color"],
        )
        if status_frame.empty:
            st.caption(tr("status.no_findings"))
        else:
            st.vega_lite_chart(
                status_frame,
                spec={
                    "mark": {"type": "bar", "cornerRadiusEnd": 4},
                    "encoding": {
                        "x": {
                            "field": status_label,
                            "type": "nominal",
                            "axis": {"labelAngle": -35, "title": status_label},
                            "sort": None,
                        },
                        "y": {
                            "field": count_label,
                            "type": "quantitative",
                            "title": count_label,
                        },
                        "color": {
                            "field": "_color",
                            "type": "nominal",
                            "scale": None,
                            "legend": None,
                        },
                        "tooltip": [
                            {"field": status_label, "type": "nominal"},
                            {"field": count_label, "type": "quantitative"},
                        ],
                    },
                },
                height=260,
            )

    st.subheader(f"▦ {tr('overview.categories')}")
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
    st.button(
        tr("findings.reset"),
        on_click=reset_filters,
        icon=":material/filter_alt_off:",
    )
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
    table = presented.loc[:, TABLE_COLUMNS]
    status_styles = {
        displayed: status_cell_style(canonical, current_theme())
        for displayed, canonical in zip(
            table["status"],
            findings["status"],
            strict=True,
        )
    }
    styled_table = table.style.map(
        lambda value: status_styles.get(str(value), ""),
        subset=["status"],
    )
    st.dataframe(
        styled_table,
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
        icon=":material/download:",
        key=key,
    )


def render_findings(result: AnalysisResult, enriched_findings: pd.DataFrame) -> pd.DataFrame:
    """Render the primary findings workspace and return its current view."""
    language = current_language()
    st.subheader(f"{SECTION_ICONS['findings']} {tr('findings.title')}")
    filtered = render_filter_controls(enriched_findings)
    shown = len(filtered)
    total = len(result.findings)
    results_key = "findings.results.one" if shown == 1 else "findings.results.many"
    st.write(tr(results_key, shown=shown, total=total))
    if filtered.empty:
        st.success(tr("status.no_findings"), icon=":material/check_circle:")
        st.caption(tr("findings.no_results_hint"))
    findings_table(filtered, language)
    render_findings_download(filtered, key="findings_download")
    return filtered


def render_data(result: AnalysisResult, source_name: str) -> None:
    """Render source metadata and a preview without internal working columns."""
    st.subheader(f"{SECTION_ICONS['data']} {tr('data.title')}")
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


def _localized_column_profile(profile: pd.DataFrame, language: str) -> pd.DataFrame:
    """Return a localized presentation copy of the stable column profile."""
    presented = profile.copy()
    presented["column_kind"] = presented["column_kind"].map(
        lambda value: i18n.translate(f"profile.table.{value}_value", language)
    )
    presented["expected_type"] = presented["expected_type"].map(
        lambda value: (
            i18n.translate(f"type.{value}", language)
            if isinstance(value, str)
            else i18n.translate("common.not_applicable", language)
        )
    )
    for column in ("minimum_valid", "maximum_valid"):
        presented[column] = presented[column].fillna(
            i18n.translate("common.not_applicable", language)
        )
    return presented


def _localized_data_dictionary(
    dictionary: pd.DataFrame,
    language: str,
) -> pd.DataFrame:
    """Return a localized presentation copy of canonical dictionary records."""
    no_values = i18n.translate("common.none", language)
    records = []
    for _, metadata in dictionary.iterrows():
        records.append(
            {
                "technical_name": metadata["technical_name"],
                "display_name": i18n.translate(metadata["label_key"], language),
                "description": i18n.translate(metadata["description_key"], language),
                "required": i18n.translate(
                    "common.yes" if metadata["required"] else "common.no",
                    language,
                ),
                "expected_type": i18n.translate(
                    f"type.{metadata['expected_type']}",
                    language,
                ),
                "format": i18n.translate(metadata["format_key"], language),
                "allowed_values": ", ".join(metadata["allowed_values"]) or no_values,
                "example": metadata["example"],
                "rules": ", ".join(metadata["rules"]) or no_values,
                "dimensions": (
                    ", ".join(
                        i18n.translate(f"dimension.{dimension}", language)
                        for dimension in metadata["dimensions"]
                    )
                    or no_values
                ),
            }
        )
    return pd.DataFrame.from_records(records, columns=DICTIONARY_TABLE_COLUMNS)


def _render_profile_summary(profile: DataProfile) -> None:
    """Render profile KPIs and factual rule-result counts."""
    metric_columns = st.columns(4)
    metric_columns[0].metric(
        tr("profile.metric.source_columns"),
        profile.source_column_count,
        border=True,
    )
    metric_columns[1].metric(
        tr("profile.metric.canonical_columns"),
        profile.canonical_column_count,
        border=True,
    )
    metric_columns[2].metric(
        tr("profile.metric.extra_columns"),
        len(profile.extra_columns),
        border=True,
    )
    metric_columns[3].metric(
        tr("profile.metric.rows_with_findings"),
        profile.rows_with_findings,
        border=True,
    )
    st.caption(
        " · ".join(
            (
                f"{tr('profile.summary.rows')}: {profile.row_count}",
                f"{tr('profile.summary.findings')}: {profile.finding_count}",
                (f"{tr('profile.summary.duplicate_id_rows')}: {profile.duplicate_id_rows}"),
                (
                    f"{tr('profile.summary.logical_duplicate_rows')}: "
                    f"{profile.logical_duplicate_rows}"
                ),
                (f"{tr('profile.summary.validity_findings')}: {profile.validity_finding_count}"),
            )
        )
    )
    if profile.extra_columns:
        extra_key = "profile.extra.one" if len(profile.extra_columns) == 1 else "profile.extra.many"
        st.warning(
            tr(extra_key, columns=", ".join(profile.extra_columns)),
            icon=":material/info:",
        )


def _render_column_profile(column_profile: pd.DataFrame, language: str) -> None:
    """Render the localized profile table and informational completeness chart."""
    table = _localized_column_profile(column_profile, language)
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "technical_name": st.column_config.TextColumn(tr("profile.table.technical_name")),
            "column_kind": st.column_config.TextColumn(tr("profile.table.canonical")),
            "missing_values": st.column_config.NumberColumn(tr("profile.table.missing")),
            "completeness_percentage": st.column_config.ProgressColumn(
                tr("profile.table.completeness"),
                min_value=0,
                max_value=100,
                format="%.2f%%",
            ),
            "distinct_values": st.column_config.NumberColumn(tr("profile.table.distinct")),
            "source_dtype": st.column_config.TextColumn(tr("profile.table.source_type")),
            "expected_type": st.column_config.TextColumn(tr("profile.table.expected_type")),
            "related_findings": st.column_config.NumberColumn(tr("profile.table.related_findings")),
            "minimum_valid": st.column_config.TextColumn(tr("profile.table.minimum")),
            "maximum_valid": st.column_config.TextColumn(tr("profile.table.maximum")),
        },
    )
    st.subheader(tr("profile.chart.completeness"))
    chart_data = table[["technical_name", "completeness_percentage", "column_kind"]].copy()
    canonical_label = tr("profile.table.canonical_value")
    chart_data["_color"] = chart_data["column_kind"].map(
        lambda value: theme_tokens(
            "information" if value == canonical_label else "warning",
            current_theme(),
        )["border"]
    )
    st.vega_lite_chart(
        chart_data,
        spec={
            "mark": {"type": "bar", "cornerRadiusEnd": 4},
            "encoding": {
                "x": {
                    "field": "technical_name",
                    "type": "nominal",
                    "sort": None,
                    "title": tr("profile.table.technical_name"),
                },
                "y": {
                    "field": "completeness_percentage",
                    "type": "quantitative",
                    "scale": {"domain": [0, 100]},
                    "title": tr("profile.table.completeness"),
                },
                "color": {
                    "field": "_color",
                    "type": "nominal",
                    "scale": None,
                    "legend": None,
                },
                "tooltip": [
                    {
                        "field": "technical_name",
                        "type": "nominal",
                        "title": tr("profile.table.technical_name"),
                    },
                    {
                        "field": "completeness_percentage",
                        "type": "quantitative",
                        "title": tr("profile.table.completeness"),
                    },
                    {
                        "field": "column_kind",
                        "type": "nominal",
                        "title": tr("profile.table.canonical"),
                    },
                ],
            },
        },
        height=300,
    )


def _render_data_dictionary(dictionary: pd.DataFrame, language: str) -> None:
    """Render localized canonical column metadata."""
    presented = _localized_data_dictionary(dictionary, language)
    st.subheader(tr("dictionary.title"))
    st.dataframe(
        presented,
        hide_index=True,
        width="stretch",
        column_config={
            "technical_name": st.column_config.TextColumn(tr("dictionary.technical_name")),
            "display_name": st.column_config.TextColumn(tr("dictionary.display_name")),
            "description": st.column_config.TextColumn(tr("dictionary.description")),
            "required": st.column_config.TextColumn(tr("dictionary.required")),
            "expected_type": st.column_config.TextColumn(tr("dictionary.expected_type")),
            "format": st.column_config.TextColumn(tr("dictionary.format")),
            "allowed_values": st.column_config.TextColumn(tr("dictionary.allowed_values")),
            "example": st.column_config.TextColumn(tr("dictionary.example")),
            "rules": st.column_config.TextColumn(tr("dictionary.rules")),
            "dimensions": st.column_config.TextColumn(tr("dictionary.dimensions")),
        },
    )


def render_profile(result: AnalysisResult) -> None:
    """Render deterministic structural profiling and the canonical dictionary."""
    language = current_language()
    profile = build_data_profile(result.source_data, result.findings)
    column_profile = build_column_profile(result.source_data, result.findings)
    dictionary = build_data_dictionary()

    st.subheader(f"{SECTION_ICONS['profile']} {tr('profile.title')}")
    st.write(tr("profile.description"))
    _render_profile_summary(profile)
    column_tab, dictionary_tab = st.tabs(
        (
            tr("profile.tab.column_profile"),
            tr("profile.tab.data_dictionary"),
        )
    )
    with column_tab:
        _render_column_profile(column_profile, language)
    with dictionary_tab:
        _render_data_dictionary(dictionary, language)


def clear_governance_responsibilities() -> None:
    """Clear only optional responsibility fields for the active source."""
    for key in RESPONSIBILITY_KEYS:
        st.session_state[key] = ""
    for key in RESPONSIBILITY_WIDGET_KEYS:
        st.session_state[key] = ""


def persist_governance_responsibility(value_key: str, widget_key: str) -> None:
    """Copy one temporary widget value to source-bound session state."""
    st.session_state[value_key] = st.session_state[widget_key]


def initialize_governance_responsibility_widgets() -> None:
    """Restore temporary widget keys from persistent session values."""
    for value_key, widget_key in zip(
        RESPONSIBILITY_KEYS,
        RESPONSIBILITY_WIDGET_KEYS,
        strict=True,
    ):
        if widget_key not in st.session_state:
            st.session_state[widget_key] = st.session_state.get(value_key, "")


def _localized_rule_parameter(
    parameter_kind: object,
    parameter_value: object,
    language: str,
) -> str:
    """Return a localized presentation of one confirmed rule parameter."""
    if not isinstance(parameter_kind, str):
        return i18n.translate("common.not_applicable", language)
    if parameter_kind == "logical_duplicate_fields":
        fields = ", ".join(cast(tuple[str, ...], parameter_value))
        return i18n.translate("governance.parameter.fields", language, values=fields)
    if parameter_kind == "median_multiplier":
        return i18n.translate(
            "governance.parameter.multiplier",
            language,
            value=parameter_value,
        )
    if parameter_kind == "minimum_observations":
        return i18n.translate(
            "governance.parameter.minimum_observations",
            language,
            value=parameter_value,
        )
    thresholds = ", ".join(
        f"{category}: {amount} EUR"
        for category, amount in cast(tuple[tuple[str, object], ...], parameter_value)
    )
    return i18n.translate(
        "governance.parameter.policy_thresholds",
        language,
        values=thresholds,
    )


def _localized_rule_catalog(catalog: pd.DataFrame, language: str) -> pd.DataFrame:
    """Return a localized presentation copy of the canonical rule catalog."""
    rows = []
    for _, rule in catalog.iterrows():
        rows.append(
            {
                "rule_id": rule["rule_id"],
                "name": i18n.translate(rule["name_key"], language),
                "description": i18n.translate(rule["description_key"], language),
                "anomaly_type": localized_value(
                    rule["anomaly_type"],
                    ANOMALY_TYPE_KEYS,
                    language,
                ),
                "dimension": i18n.translate(f"dimension.{rule['dimension']}", language),
                "status": localized_value(rule["status"], STATUS_KEYS, language),
                "fields": ", ".join(rule["fields"]),
                "parameters": _localized_rule_parameter(
                    rule["parameter_kind"],
                    rule["parameter_value"],
                    language,
                ),
            }
        )
    return pd.DataFrame(rows, columns=GOVERNANCE_RULE_PRESENTATION_COLUMNS)


def _render_processing_metadata(metadata: ProcessingMetadata) -> None:
    """Render immutable source and processing facts."""
    st.write(tr("governance.metadata.description"))
    metrics = st.columns(4)
    metrics[0].metric(tr("governance.metadata.size"), metadata.source_size_bytes)
    metrics[1].metric(tr("governance.metadata.rows"), metadata.row_count)
    metrics[2].metric(tr("governance.metadata.columns"), metadata.source_column_count)
    metrics[3].metric(
        tr("governance.metadata.canonical_columns"),
        metadata.canonical_column_count,
    )
    details = pd.DataFrame(
        [
            (tr("governance.metadata.source_name"), metadata.source_name),
            (
                tr("governance.metadata.analyzed_at"),
                metadata.analyzed_at_utc.isoformat(timespec="seconds"),
            ),
            (tr("governance.metadata.delimiter"), metadata.delimiter),
            (
                tr("governance.metadata.encoding"),
                tr(
                    "governance.encoding.utf8_bom"
                    if metadata.has_bom
                    else "governance.encoding.utf8"
                ),
            ),
            (
                tr("governance.metadata.bom"),
                tr("common.yes" if metadata.has_bom else "common.no"),
            ),
            (
                tr("governance.metadata.extra_columns"),
                ", ".join(metadata.extra_columns) or tr("common.none"),
            ),
            (
                tr("governance.metadata.app_version"),
                metadata.application_version or tr("common.not_available"),
            ),
        ],
        columns=(tr("governance.metadata.property"), tr("governance.metadata.value")),
    )
    st.dataframe(details, hide_index=True, width="stretch")
    st.caption(tr("governance.metadata.sha256"))
    st.code(metadata.sha256, language=None)


def _render_rule_catalog(
    findings: pd.DataFrame,
    source_row_numbers: Sequence[object],
) -> None:
    """Render canonical rules, independent filters, and observed dimension counts."""
    language = current_language()
    catalog = build_rule_catalog()
    summary = build_dimension_summary(
        catalog,
        findings,
        source_row_numbers,
    ).copy()
    summary["dimension"] = summary["dimension"].map(
        lambda value: i18n.translate(f"dimension.{value}", language)
    )
    summary.columns = (
        tr("governance.dimension.name"),
        tr("governance.dimension.rule_count"),
        tr("governance.dimension.finding_count"),
        tr("governance.dimension.row_count"),
    )
    st.subheader(tr("governance.dimension.title"))
    st.dataframe(summary, hide_index=True, width="stretch")

    filter_columns = st.columns(4)
    with filter_columns[0]:
        st.multiselect(
            tr("governance.filter.type"),
            sorted(catalog["anomaly_type"].unique()),
            key=GOVERNANCE_FILTER_KEYS[0],
            format_func=lambda value: localized_value(value, ANOMALY_TYPE_KEYS, language),
        )
    with filter_columns[1]:
        st.multiselect(
            tr("governance.filter.dimension"),
            list(dict.fromkeys(catalog["dimension"])),
            key=GOVERNANCE_FILTER_KEYS[1],
            format_func=lambda value: i18n.translate(f"dimension.{value}", language),
        )
    with filter_columns[2]:
        st.multiselect(
            tr("governance.filter.status"),
            sorted(catalog["status"].unique()),
            key=GOVERNANCE_FILTER_KEYS[2],
            format_func=lambda value: localized_value(value, STATUS_KEYS, language),
        )
    with filter_columns[3]:
        fields = sorted({field for values in catalog["fields"] for field in values})
        st.multiselect(
            tr("governance.filter.field"),
            fields,
            key=GOVERNANCE_FILTER_KEYS[3],
        )
    filtered = filter_rule_catalog(
        catalog,
        anomaly_types=st.session_state.get(GOVERNANCE_FILTER_KEYS[0], ()),
        dimensions=st.session_state.get(GOVERNANCE_FILTER_KEYS[1], ()),
        statuses=st.session_state.get(GOVERNANCE_FILTER_KEYS[2], ()),
        fields=st.session_state.get(GOVERNANCE_FILTER_KEYS[3], ()),
    )
    presented = _localized_rule_catalog(filtered, language)
    presented.columns = (
        tr("governance.rules.rule_id"),
        tr("governance.rules.name"),
        tr("governance.rules.description"),
        tr("governance.rules.type"),
        tr("governance.rules.dimension"),
        tr("governance.rules.status"),
        tr("governance.rules.fields"),
        tr("governance.rules.parameter"),
    )
    if presented.empty:
        st.caption(tr("governance.rules.empty"))
    st.dataframe(presented, hide_index=True, width="stretch")


def _render_responsibilities() -> None:
    """Render optional, session-local responsibility notes."""
    initialize_governance_responsibility_widgets()
    st.info(tr("governance.responsibility.notice"), icon=":material/info:")
    first_row = st.columns(2)
    with first_row[0]:
        st.text_input(
            tr("governance.responsibility.owner"),
            key=RESPONSIBILITY_WIDGET_KEYS[0],
            on_change=persist_governance_responsibility,
            args=(RESPONSIBILITY_KEYS[0], RESPONSIBILITY_WIDGET_KEYS[0]),
        )
    with first_row[1]:
        st.text_input(
            tr("governance.responsibility.steward"),
            key=RESPONSIBILITY_WIDGET_KEYS[1],
            on_change=persist_governance_responsibility,
            args=(RESPONSIBILITY_KEYS[1], RESPONSIBILITY_WIDGET_KEYS[1]),
        )
    second_row = st.columns(2)
    with second_row[0]:
        st.text_input(
            tr("governance.responsibility.organization"),
            key=RESPONSIBILITY_WIDGET_KEYS[2],
            on_change=persist_governance_responsibility,
            args=(RESPONSIBILITY_KEYS[2], RESPONSIBILITY_WIDGET_KEYS[2]),
        )
    with second_row[1]:
        st.text_input(
            tr("governance.responsibility.period"),
            key=RESPONSIBILITY_WIDGET_KEYS[3],
            on_change=persist_governance_responsibility,
            args=(RESPONSIBILITY_KEYS[3], RESPONSIBILITY_WIDGET_KEYS[3]),
        )
    st.text_area(
        tr("governance.responsibility.notes"),
        key=RESPONSIBILITY_WIDGET_KEYS[4],
        on_change=persist_governance_responsibility,
        args=(RESPONSIBILITY_KEYS[4], RESPONSIBILITY_WIDGET_KEYS[4]),
    )
    st.button(
        tr("governance.responsibility.reset"),
        on_click=clear_governance_responsibilities,
        icon=":material/delete_sweep:",
    )


def render_governance(result: AnalysisResult, metadata: ProcessingMetadata) -> None:
    """Render local governance facts without changing analysis outputs."""
    st.subheader(f"{SECTION_ICONS['governance']} {tr('governance.title')}")
    st.write(tr("governance.description"))
    metadata_tab, rules_tab, responsibilities_tab = st.tabs(
        (
            tr("governance.tab.metadata"),
            tr("governance.tab.rules"),
            tr("governance.tab.responsibilities"),
        )
    )
    with metadata_tab:
        _render_processing_metadata(metadata)
    with rules_tab:
        _render_rule_catalog(
            result.findings,
            result.source_data[SOURCE_ROW_COLUMN],
        )
    with responsibilities_tab:
        _render_responsibilities()


def render_export(filtered: pd.DataFrame, language: str) -> None:
    """Render export facts and download the current filtered schema."""
    st.subheader(f"{SECTION_ICONS['export']} {tr('export.title')}")
    export_columns = st.columns(3)
    export_columns[0].metric(tr("metric.rows_included"), len(filtered))
    export_columns[1].metric(tr("metric.format"), "CSV")
    export_columns[2].metric(tr("metric.columns"), len(FINDING_COLUMNS))
    st.caption(tr("export.active_filters"))
    st.write(current_filter_description(language))
    if filtered.empty:
        st.success(tr("export.empty"), icon=":material/check_circle:")
        return
    render_findings_download(filtered, key="export_download")


def analyze_current_source() -> AnalysisResult | None:
    """Analyze the active session source and show concise load errors."""
    content = current_source_bytes()
    if content is None:
        return None
    source_name = cast(str, st.session_state["source_name"])
    synchronize_source_identity(source_name, content)
    try:
        with st.spinner(tr("analysis.running")):
            result = analyze_expenses(BytesIO(content))
        if PROCESSING_METADATA_KEY not in st.session_state:
            profile = build_data_profile(result.source_data, result.findings)
            st.session_state[PROCESSING_METADATA_KEY] = build_processing_metadata(
                source_name=source_name,
                content=content,
                profile=profile,
                csv_format=inspect_csv_source(BytesIO(content)),
                analyzed_at_utc=datetime.now(UTC),
                installed_version=application_version(),
            )
        return result
    except CsvLoadError as error:
        if error.code == CSV_ERROR_INCOMPATIBLE_SCHEMA and error.schema is not None:
            render_schema_guidance(error.schema)
        else:
            st.warning(friendly_load_error(error), icon=":material/warning:")
    except Exception:
        LOGGER.exception("Errore imprevisto durante l'analisi del CSV.")
        st.error(tr("error.unexpected"), icon=":material/error:")
    return None


def render_dashboard() -> None:
    """Render the session-based expense-quality workspace."""
    st.set_page_config(
        page_title="Expense Quality Monitor",
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="auto",
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
    extra_columns = source_extra_columns(result.source_data)
    render_file_context(
        source_name,
        is_example=bool(st.session_state.get("source_is_example")),
        extra_columns=extra_columns,
    )
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
        format_func=lambda section_id: f"{SECTION_ICONS[section_id]} {tr(f'nav.{section_id}')}",
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
    elif section == "profile":
        render_profile(result)
    elif section == "governance":
        render_governance(
            result,
            cast(ProcessingMetadata, st.session_state[PROCESSING_METADATA_KEY]),
        )
    elif section == "data":
        render_data(result, source_name)
    elif section == "export":
        render_export(filtered, language)


render_dashboard()
