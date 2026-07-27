"""Tests for the Streamlit product experience and UI-only transformations."""

import hashlib
import struct
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from xml.etree import ElementTree

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app import (
    PROCESSING_METADATA_KEY,
    SOURCE_IDENTITY_KEY,
    TEMPLATE_FILENAME,
    accessible_hero_svg,
    activate_example_source,
    activate_uploaded_source,
    build_template_csv,
    counts_to_frame,
    current_language,
    distinct_rule_count,
    filter_findings,
    findings_for_presentation,
    findings_with_categories,
    initialize_language,
    render_findings_download,
    reset_workspace_view,
    set_active_source,
)
from expense_quality_monitor.config import EXPECTED_COLUMNS, FINDING_COLUMNS
from expense_quality_monitor.pipeline import analyze_expenses
from expense_quality_monitor.reporting import findings_to_csv

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "data" / "synthetic_expenses.csv"
HERO_PATH = ROOT / "docs" / "assets" / "dashboard-hero.svg"
DASHBOARD_PREVIEW_PATH = ROOT / "docs" / "assets" / "dashboard-overview.png"
WORKFLOW_PATH = ROOT / "docs" / "assets" / "expense-quality-monitor-flow.png"
README_PATH = ROOT / "README.md"


def png_dimensions(path: Path) -> tuple[int, int]:
    """Return dimensions from a PNG signature and IHDR header."""
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert header[12:16] == b"IHDR"
    return struct.unpack(">II", header[16:24])


def loaded_example_app(language: str = "it") -> AppTest:
    """Start the app and select its versioned example source."""
    app = AppTest.from_file(ROOT / "app.py")
    app.session_state["language"] = language
    app = app.run()
    example_label = "Prova con l’esempio" if language == "it" else "Try the example"
    example_button = next(button for button in app.button if button.label == example_label)
    return example_button.click().run(timeout=10)


def app_with_uploaded_bytes(
    name: str,
    content: bytes,
    language: str = "it",
) -> AppTest:
    """Start the app with one in-memory uploaded source."""
    app = AppTest.from_file(ROOT / "app.py").run()
    app.session_state["source_name"] = name
    app.session_state["source_bytes"] = content
    app.session_state["source_is_example"] = False
    app.session_state["language"] = language
    return app.run(timeout=10)


def one_expense_csv(**updates: str) -> bytes:
    """Return one schema-compatible expense row with optional explicit changes."""
    row = {
        "id_spesa": "100001",
        "data_spesa": "13/07/2026",
        "dipendente": "Cognome001 Nome001",
        "centro_di_costo": "CDC-001",
        "categoria": "Vitto",
        "descrizione": "Pranzo di lavoro",
        "importo": "25.00",
        "valuta_originale": "EUR",
        "progetto": "PRJ-2026-001",
        "approvatore": "Cognome002 Nome002",
    }
    row.update(updates)
    return pd.DataFrame([row], columns=EXPECTED_COLUMNS).to_csv(index=False).encode()


def test_initial_state_offers_equal_starting_paths_and_main_copy() -> None:
    app = AppTest.from_file(ROOT / "app.py").run()

    assert not app.exception
    assert app.title[0].value == "Expense Quality Monitor"
    assert any(
        "Controlla il file, individua le eccezioni e prepara il riepilogo." in message.value
        for message in app.markdown
    )
    assert app.subheader[0].value == "Da dove vuoi partire?"
    assert app.main.get("file_uploader")[0].label == "Scegli un CSV"
    assert any(button.label == "Prova con l’esempio" for button in app.button)
    assert any(
        caption.value == "Il file viene elaborato nella sessione e non viene salvato."
        for caption in app.caption
    )
    assert not app.warning


def test_documentation_assets_are_local_safe_and_referenced() -> None:
    app = AppTest.from_file(ROOT / "app.py").run()
    svg_root = ElementTree.parse(HERO_PATH).getroot()
    svg_source = HERO_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    accessible_svg = accessible_hero_svg(
        "Illustrazione astratta di una tabella verificata da controlli di qualità"
    )

    assert HERO_PATH.is_file()
    assert DASHBOARD_PREVIEW_PATH.is_file()
    assert WORKFLOW_PATH.is_file()
    assert all(
        width > 0 and height > 0
        for width, height in (
            png_dimensions(DASHBOARD_PREVIEW_PATH),
            png_dimensions(WORKFLOW_PATH),
        )
    )
    assert svg_root.tag.endswith("svg")
    assert not any(element.tag.endswith("text") for element in svg_root.iter())
    assert not any(element.tag.endswith("script") for element in svg_root.iter())
    external_references = [
        value
        for element in svg_root.iter()
        for attribute, value in element.attrib.items()
        if attribute.endswith("href") and value.startswith(("http://", "https://"))
    ]
    assert not external_references
    assert "/Users/" not in svg_source
    assert "![Panoramica di Expense Quality Monitor](docs/assets/dashboard-overview.png)" in readme
    assert (
        "![Flusso di Expense Quality Monitor](docs/assets/expense-quality-monitor-flow.png)"
        in readme
    )
    assert '<img src="data:image/svg+xml,' in accessible_svg
    assert "base64" not in accessible_svg
    assert (
        'alt="Illustrazione astratta di una tabella verificata da controlli di qualità"'
        in accessible_svg
    )
    assert any(
        caption.value == "✓ Controlli deterministici, nessuna AI nel runtime"
        for caption in app.caption
    )
    assert any(button.label == "Scarica il modello CSV" for button in app.download_button)


def test_language_initialization_uses_locale_once_and_preserves_explicit_choice() -> None:
    session_state: dict[str, object] = {}
    with (
        patch("app.st.session_state", session_state),
        patch("app.st.context", SimpleNamespace(locale="en-US")),
    ):
        initialize_language()

    assert session_state["language"] == "en"

    session_state["language"] = "it"
    with (
        patch("app.st.session_state", session_state),
        patch("app.st.context", SimpleNamespace(locale="en-US")),
    ):
        initialize_language()

    assert session_state["language"] == "it"


@pytest.mark.parametrize(
    "context",
    [SimpleNamespace(), SimpleNamespace(locale=None)],
)
def test_language_initialization_handles_a_context_without_locale(
    context: SimpleNamespace,
) -> None:
    session_state: dict[str, object] = {}
    with (
        patch("app.st.session_state", session_state),
        patch("app.st.context", context),
    ):
        initialize_language()

    assert session_state["language"] == "it"


def test_current_language_normalizes_an_unsupported_session_value() -> None:
    with patch("app.st.session_state", {"language": "fr-FR"}):
        assert current_language() == "it"


def test_example_source_keeps_confirmed_metrics_and_rule_count() -> None:
    app = loaded_example_app()

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Righe", "300"),
        ("⚠ Righe da verificare", "37"),
        ("Segnalazioni", "43"),
        ("Regole coinvolte", "17"),
    ]
    navigation = app.get("button_group")[0]
    assert navigation.options == [
        "▦ Panoramica",
        "⚑ Segnalazioni",
        "◫ Profilo dati",
        "◇ Governance",
        "▤ Dati",
        "⇩ Esporta",
    ]
    assert navigation.value == "overview"
    assert app.sidebar.get("file_uploader")[0].label == "Scegli un altro CSV"
    assert any(
        message.value
        == ":blue-background[ℹ File di esempio] :green-background[✓ Analisi completata]"
        for message in app.markdown
    )
    assert any(message.value == "📄 synthetic_expenses.csv" for message in app.text)


def test_incompatible_schema_shows_real_columns_and_available_actions() -> None:
    iris_csv = (
        b"sepal_length,sepal_width,petal_length,petal_width,species\n5.1,3.5,1.4,0.2,setosa\n"
    )

    app = app_with_uploaded_bytes("Iris.csv", iris_csv)

    assert not app.exception
    assert app.warning[0].value == "Questo CSV non corrisponde alla struttura delle spese"
    assert any(message.value == "Mancano 10 colonne" for message in app.markdown)
    assert any(
        message.value == "sepal_length, sepal_width, petal_length, petal_width, species"
        for message in app.markdown
    )
    assert any(header.value == "Colonne trovate" for header in app.subheader)
    assert any(header.value == "Colonne aggiuntive" for header in app.subheader)
    assert any(button.label == "Scarica il modello CSV" for button in app.download_button)
    assert any(
        caption.value == "Scarica un CSV con le colonne già predisposte." for caption in app.caption
    )
    assert any(button.label == "Prova con l’esempio" for button in app.button)
    assert any(caption.value == "File selezionato" for caption in app.sidebar.caption)
    assert any(message.value == "Iris.csv" for message in app.sidebar.text)
    assert not app.get("button_group")


@pytest.mark.parametrize(
    ("name", "content", "expected_message"),
    [
        ("vuoto.csv", b"", "Il file \u00e8 vuoto."),
        (
            "non-leggibile.csv",
            b"\xff\xfe\x00",
            "Il contenuto non pu\u00f2 essere letto come CSV.",
        ),
        (
            "duplicati.csv",
            (
                "id_spesa, ID_SPESA ,"
                + ",".join(EXPECTED_COLUMNS[1:])
                + "\n100001,100002,13/07/2026,Cognome001 Nome001,CDC-001,"
                "Vitto,Spesa sintetica,25.00,,PRJ-2026-001,Approvatore001 Demo\n"
            ).encode(),
            "Alcune colonne hanno lo stesso nome dopo la normalizzazione.",
        ),
    ],
)
def test_load_failures_use_specific_non_accusatory_messages(
    name: str,
    content: bytes,
    expected_message: str,
) -> None:
    app = app_with_uploaded_bytes(name, content)

    assert not app.exception
    assert app.warning[0].value == expected_message
    assert any(message.value == name for message in app.sidebar.text)


def test_example_action_from_schema_guidance_keeps_confirmed_metrics() -> None:
    app = app_with_uploaded_bytes("Iris.csv", b"a,b\n1,2\n")
    example_button = next(button for button in app.button if button.label == "Prova con l’esempio")

    app = example_button.click().run(timeout=10)

    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Righe", "300"),
        ("⚠ Righe da verificare", "37"),
        ("Segnalazioni", "43"),
        ("Regole coinvolte", "17"),
    ]


def test_template_download_contains_only_the_utf8_canonical_header() -> None:
    template = build_template_csv()
    decoded = template.decode("utf-8")
    parsed = pd.read_csv(StringIO(decoded), dtype=str, keep_default_na=False)

    assert TEMPLATE_FILENAME == "expense_quality_monitor_template.csv"
    assert decoded == ",".join(EXPECTED_COLUMNS) + "\n"
    assert parsed.columns.tolist() == list(EXPECTED_COLUMNS)
    assert parsed.empty


def test_compatible_example_with_extra_columns_keeps_metrics_and_shows_note() -> None:
    source = pd.read_csv(EXAMPLE_PATH, dtype=str, keep_default_na=False)
    source["extra_zeta"] = "z"
    source["extra_alfa"] = "a"
    content = source.to_csv(index=False).encode()

    app = app_with_uploaded_bytes("spese_con_extra.csv", content)

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Righe", "300"),
        ("⚠ Righe da verificare", "37"),
        ("Segnalazioni", "43"),
        ("Regole coinvolte", "17"),
    ]
    assert app.info[0].value == (
        "Il file contiene 2 colonne aggiuntive che non vengono utilizzate nell’analisi."
    )
    assert not app.warning


def test_uploaded_filename_is_rendered_as_plain_text() -> None:
    source = EXAMPLE_PATH.read_bytes()
    filename = "[spese](https://example.invalid).csv"

    app = app_with_uploaded_bytes(filename, source)

    assert not app.exception
    assert any(message.value == f"📄 {filename}" for message in app.text)
    assert any(message.value == filename for message in app.sidebar.text)


def test_semicolon_upload_is_accepted_by_the_existing_workspace() -> None:
    source = pd.read_csv(EXAMPLE_PATH, dtype=str, keep_default_na=False)
    content = source.to_csv(index=False, sep=";").encode()

    app = app_with_uploaded_bytes("spese_semicolon.csv", content)

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Righe", "300"),
        ("⚠ Righe da verificare", "37"),
        ("Segnalazioni", "43"),
        ("Regole coinvolte", "17"),
    ]


def test_search_is_case_insensitive_across_id_rule_and_description() -> None:
    findings = pd.DataFrame(
        [
            {
                "source_row_number": 2,
                "id_spesa": "A-200",
                "rule_id": "POLICY_CHECK",
                "message": "Richiede approvazione",
                "anomaly_type": "policy",
                "status": "richiede approvazione",
                "field": "importo",
                "original_value": "250",
                "categoria": "Trasporto",
            },
            {
                "source_row_number": 1,
                "id_spesa": "A-100",
                "rule_id": "VALIDITY_DATE",
                "message": "Data non valida",
                "anomaly_type": "validità",
                "status": "non valida",
                "field": "data_spesa",
                "original_value": "31/02/2026",
                "categoria": "Vitto",
            },
        ]
    )

    by_rule = filter_findings(findings, query="policy")
    by_id = filter_findings(findings, query="a-100")
    by_description = filter_findings(findings, query="APPROVAZIONE")

    assert by_rule["id_spesa"].tolist() == ["A-200"]
    assert by_id["id_spesa"].tolist() == ["A-100"]
    assert by_description["id_spesa"].tolist() == ["A-200"]


def test_reset_filters_keeps_source_and_clears_table_controls() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("findings").run(timeout=10)
    app = app.text_input[0].input("PoLiCy").run(timeout=10)
    app = app.multiselect[0].select("policy").run(timeout=10)

    assert any(message.value == "4 risultati su 43" for message in app.markdown)
    reset_button = next(button for button in app.button if button.label == "Ripristina filtri")
    app = reset_button.click().run(timeout=10)

    assert app.text_input[0].value == ""
    assert [control.value for control in app.multiselect] == [[], [], [], []]
    assert app.session_state["source_name"] == "synthetic_expenses.csv"


def test_source_change_restores_overview_and_clears_filters() -> None:
    session_state = {
        "workspace_section": "export",
        "finding_search": "policy",
        "filter_types": ["policy"],
        "filter_statuses": ["richiede approvazione"],
        "filter_categories": ["Vitto"],
        "filter_rules": ["POLICY_APPROVAL_REQUIRED"],
    }

    with patch("app.st.session_state", session_state):
        reset_workspace_view()

    assert session_state == {
        "workspace_section": "overview",
        "workspace_section_widget": "overview",
        "finding_search": "",
        "filter_types": [],
        "filter_statuses": [],
        "filter_categories": [],
        "filter_rules": [],
    }


def test_invalid_navigation_state_returns_to_the_stable_default() -> None:
    app = loaded_example_app()
    app.session_state["workspace_section"] = "invalid"
    app.session_state["workspace_section_widget"] = "export"

    app = app.run(timeout=10)

    assert app.session_state["workspace_section"] == "overview"
    assert app.session_state["workspace_section_widget"] == "overview"
    assert app.get("button_group")[0].value == "overview"
    assert any(header.value == "▦ Categorie" for header in app.subheader)


def test_upload_and_example_store_the_same_source_keys() -> None:
    uploaded_state = {
        "upload": SimpleNamespace(name="spese.csv", getvalue=lambda: b"contenuto"),
    }
    with patch("app.st.session_state", uploaded_state):
        activate_uploaded_source("upload")

    example_state: dict[str, object] = {}
    with patch("app.st.session_state", example_state):
        activate_example_source()

    source_keys = {"source_name", "source_bytes", "source_is_example"}
    assert source_keys <= uploaded_state.keys()
    assert source_keys <= example_state.keys()
    assert uploaded_state["source_name"] == "spese.csv"
    assert uploaded_state["source_bytes"] == b"contenuto"
    assert uploaded_state["source_is_example"] is False
    assert example_state["source_name"] == "synthetic_expenses.csv"
    assert example_state["source_bytes"] is None
    assert example_state["source_is_example"] is True


def test_distinct_rules_are_calculated_from_current_findings() -> None:
    result = analyze_expenses(EXAMPLE_PATH)

    assert distinct_rule_count(result.findings) == result.findings["rule_id"].nunique()
    assert distinct_rule_count(result.findings) == 17


def test_filtered_export_preserves_confirmed_schema_and_content() -> None:
    result = analyze_expenses(EXAMPLE_PATH)
    enriched = findings_with_categories(result.findings, result.source_data)
    filtered = filter_findings(enriched, anomaly_types=["policy"])

    exported = findings_to_csv(filtered.loc[:, FINDING_COLUMNS])
    expected = findings_to_csv(
        result.findings[result.findings["anomaly_type"].eq("policy")].reset_index(drop=True)
    )
    parsed = pd.read_csv(StringIO(exported), dtype=str, keep_default_na=False)

    assert exported == expected
    assert parsed.columns.tolist() == list(FINDING_COLUMNS)
    assert len(parsed) == 4


def test_findings_download_preserves_public_csv_contract() -> None:
    result = analyze_expenses(EXAMPLE_PATH)
    filtered = result.findings[result.findings["anomaly_type"].eq("policy")].reset_index(drop=True)
    expected = findings_to_csv(filtered.loc[:, FINDING_COLUMNS])

    with patch("app.st.download_button") as download_button:
        render_findings_download(filtered, key="test_download")

    download_button.assert_called_once_with(
        "Scarica la vista corrente",
        data=expected,
        file_name="expense_quality_findings.csv",
        mime="text/csv",
        type="primary",
        icon=":material/download:",
        key="test_download",
    )


def test_data_and_export_sections_present_factual_context() -> None:
    app = loaded_example_app()
    navigation = app.get("button_group")[0]

    app = navigation.set_value("data").run(timeout=10)
    assert any(header.value == "▤ Dati" for header in app.subheader)
    assert any(
        "Qui puoi controllare il contenuto ricevuto" in message.value for message in app.markdown
    )

    navigation = app.get("button_group")[0]
    app = navigation.set_value("export").run(timeout=10)
    assert any(header.value == "⇩ Esporta" for header in app.subheader)
    assert any(button.label == "Scarica la vista corrente" for button in app.get("download_button"))


def test_italian_profile_shows_tabs_metrics_tables_and_example_facts() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("profile").run(timeout=10)

    assert not app.exception
    assert app.session_state["workspace_section"] == "profile"
    assert [tab.label for tab in app.get("tab")] == [
        "Profilo per colonna",
        "Dizionario dati",
    ]
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Colonne sorgente", "10"),
        ("Colonne canoniche", "10"),
        ("Colonne aggiuntive", "0"),
        ("Righe con segnalazioni", "37"),
    ]
    assert any(
        caption.value
        == (
            "Righe sorgente: 300 · Segnalazioni totali: 43 · "
            "Righe duplicate per ID: 6 · Righe duplicate logiche: 6 · "
            "Segnalazioni di validità: 10"
        )
        for caption in app.caption
    )
    column_tab, dictionary_tab = app.get("tab")
    column_profile = column_tab.get("dataframe")[0].value
    dictionary = dictionary_tab.get("dataframe")[0].value
    assert column_profile["technical_name"].tolist() == list(EXPECTED_COLUMNS)
    assert column_profile["missing_values"].ge(0).all()
    assert dictionary["technical_name"].tolist() == list(EXPECTED_COLUMNS)
    assert dictionary.loc[0, "display_name"] == "ID spesa"
    assert dictionary.loc[0, "description"] == ("Identificativo numerico progressivo della spesa.")
    assert len(app.get("vega_lite_chart")) == 1


def test_profile_language_change_preserves_stable_section_and_translates_dictionary() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("profile").run(timeout=10)

    app = app.sidebar.selectbox[0].set_value("English").run(timeout=10)

    assert not app.exception
    assert app.session_state["workspace_section"] == "profile"
    assert app.get("button_group")[0].value == "profile"
    assert [tab.label for tab in app.get("tab")] == [
        "Column profile",
        "Data dictionary",
    ]
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Source columns", "10"),
        ("Canonical columns", "10"),
        ("Extra columns", "0"),
        ("Rows with findings", "37"),
    ]
    dictionary = app.get("tab")[1].get("dataframe")[0].value
    assert dictionary.loc[0, "technical_name"] == "id_spesa"
    assert dictionary.loc[0, "display_name"] == "Expense ID"
    assert dictionary.loc[0, "description"] == ("Progressive numeric identifier of the expense.")


def test_profile_distinguishes_extra_columns_without_changing_example_metrics() -> None:
    source = pd.read_csv(EXAMPLE_PATH, dtype=str, keep_default_na=False)
    source["extra_note"] = "source value"
    app = app_with_uploaded_bytes(
        "spese_con_extra.csv",
        source.to_csv(index=False).encode(),
    )

    app = app.get("button_group")[0].set_value("profile").run(timeout=10)

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Colonne sorgente", "11"),
        ("Colonne canoniche", "10"),
        ("Colonne aggiuntive", "1"),
        ("Righe con segnalazioni", "37"),
    ]
    assert any(warning.value == "Colonna aggiuntiva: extra_note" for warning in app.warning)
    column_profile = app.get("tab")[0].get("dataframe")[0].value
    assert column_profile.iloc[-1]["technical_name"] == "extra_note"
    assert column_profile.iloc[-1]["column_kind"] == "Aggiuntiva"


@pytest.mark.parametrize(
    ("updates", "expected_missing"),
    [
        ({}, 0),
        ({"progetto": "   "}, 1),
    ],
)
def test_profile_reports_column_missing_values_without_a_quality_score(
    updates: dict[str, str],
    expected_missing: int,
) -> None:
    app = app_with_uploaded_bytes("spesa.csv", one_expense_csv(**updates))
    app = app.get("button_group")[0].set_value("profile").run(timeout=10)

    assert not app.exception
    profile = app.get("tab")[0].get("dataframe")[0].value.set_index("technical_name")
    assert profile.loc["progetto", "missing_values"] == expected_missing
    assert profile.loc["progetto", "completeness_percentage"] == (
        100.0 if expected_missing == 0 else 0.0
    )
    visible_text = " ".join(
        str(element.value)
        for element_type in ("markdown", "caption", "subheader")
        for element in app.get(element_type)
    ).casefold()
    assert "quality score" not in visible_text
    assert "punteggio globale" not in visible_text


def test_profile_handles_a_valid_dataset_without_findings() -> None:
    rows = []
    for offset in range(5):
        rows.append(
            {
                "id_spesa": str(100001 + offset),
                "data_spesa": f"{13 + offset:02d}/07/2026",
                "dipendente": f"Cognome{offset + 1:03d} Nome{offset + 1:03d}",
                "centro_di_costo": "CDC-001",
                "categoria": "Vitto",
                "descrizione": "Pranzo di lavoro",
                "importo": f"{20 + offset}.00",
                "valuta_originale": "EUR",
                "progetto": "PRJ-2026-001",
                "approvatore": "Cognome010 Nome010",
            }
        )
    content = pd.DataFrame(rows, columns=EXPECTED_COLUMNS).to_csv(index=False).encode()

    app = app_with_uploaded_bytes("spese_valide.csv", content)
    app = app.get("button_group")[0].set_value("profile").run(timeout=10)

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Colonne sorgente", "10"),
        ("Colonne canoniche", "10"),
        ("Colonne aggiuntive", "0"),
        ("Righe con segnalazioni", "0"),
    ]
    assert any("Segnalazioni totali: 0" in caption.value for caption in app.caption)
    profile = app.get("tab")[0].get("dataframe")[0].value
    assert profile["related_findings"].eq(0).all()


def test_english_initial_state_and_language_selector_use_explicit_copy() -> None:
    app = AppTest.from_file(ROOT / "app.py")
    app.session_state["language"] = "en"
    app = app.run()

    assert not app.exception
    assert app.title[0].value == "Expense Quality Monitor"
    assert any(
        message.value == "Check the file, identify exceptions, and prepare the summary."
        for message in app.markdown
    )
    assert app.subheader[0].value == "Where would you like to start?"
    assert app.main.get("file_uploader")[0].label == "Choose a CSV"
    assert any(button.label == "Try the example" for button in app.button)
    language_selector = app.sidebar.selectbox[0]
    assert language_selector.label == "🌐 Language"
    assert language_selector.options == ["Italiano", "English"]
    assert language_selector.value == "en"
    assert (
        'alt="Abstract illustration of a table verified by quality checks"'
        in accessible_hero_svg("Abstract illustration of a table verified by quality checks")
    )
    assert any(
        caption.value == "✓ Deterministic checks, no AI at runtime" for caption in app.caption
    )


def test_english_example_keeps_metrics_and_uses_stable_navigation_ids() -> None:
    app = loaded_example_app("en")

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Rows", "300"),
        ("⚠ Rows to review", "37"),
        ("Findings", "43"),
        ("Rules involved", "17"),
    ]
    navigation = app.get("button_group")[0]
    assert navigation.options == [
        "▦ Overview",
        "⚑ Findings",
        "◫ Data profile",
        "◇ Governance",
        "▤ Data",
        "⇩ Export",
    ]
    assert navigation.value == "overview"
    assert any(
        message.value == ":blue-background[ℹ Example file] :green-background[✓ Analysis complete]"
        for message in app.markdown
    )
    assert any(message.value == "📄 synthetic_expenses.csv" for message in app.text)


def test_english_schema_guidance_translates_copy_but_not_column_names() -> None:
    iris_csv = (
        b"sepal_length,sepal_width,petal_length,petal_width,species\n5.1,3.5,1.4,0.2,setosa\n"
    )

    app = app_with_uploaded_bytes("Iris.csv", iris_csv, language="en")

    assert not app.exception
    assert app.warning[0].value == "This CSV does not match the expense structure"
    assert any(message.value == "10 columns are missing" for message in app.markdown)
    assert any(header.value == "Found columns" for header in app.subheader)
    assert any(header.value == "Extra columns" for header in app.subheader)
    assert any(button.label == "Download the CSV template" for button in app.download_button)
    assert any(
        message.value.startswith("id_spesa, data_spesa, dipendente") for message in app.markdown
    )


def test_english_extra_column_message_keeps_confirmed_metrics() -> None:
    source = pd.read_csv(EXAMPLE_PATH, dtype=str, keep_default_na=False)
    source["extra_column"] = "value"

    app = app_with_uploaded_bytes(
        "expenses_with_extra.csv",
        source.to_csv(index=False).encode(),
        language="en",
    )

    assert not app.exception
    assert app.info[0].value == (
        "The file contains 1 extra column that is not used in the analysis."
    )
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Rows", "300"),
        ("⚠ Rows to review", "37"),
        ("Findings", "43"),
        ("Rules involved", "17"),
    ]


def test_english_search_filters_localized_messages_with_canonical_values() -> None:
    app = loaded_example_app("en")
    app = app.get("button_group")[0].set_value("⚑ Findings").run(timeout=10)
    app = app.text_input[0].input("approval").run(timeout=10)
    app = app.multiselect[0].select("policy").run(timeout=10)

    assert any(message.value == "4 results out of 43" for message in app.markdown)
    assert app.multiselect[0].value == ["policy"]
    assert any(button.label == "Reset filters" for button in app.button)
    assert any(button.label == "Download the current view" for button in app.download_button)


def test_english_data_and_export_keep_canonical_data_and_export_contract() -> None:
    app = loaded_example_app("en")
    navigation = app.get("button_group")[0]

    app = navigation.set_value("▤ Data").run(timeout=10)
    assert any(header.value == "▤ Data" for header in app.subheader)
    assert any(
        message.value.startswith("id_spesa, data_spesa, dipendente") for message in app.markdown
    )

    navigation = app.get("button_group")[0]
    app = navigation.set_value("⇩ Export").run(timeout=10)
    assert any(header.value == "⇩ Export" for header in app.subheader)
    download = next(
        button
        for button in app.get("download_button")
        if button.label == "Download the current view"
    )
    assert download.key == "export_download"


def test_english_download_label_does_not_change_filename_or_csv_content() -> None:
    result = analyze_expenses(EXAMPLE_PATH)
    expected = findings_to_csv(result.findings)

    with (
        patch("app.st.session_state", {"language": "en"}),
        patch("app.st.download_button") as download_button,
    ):
        render_findings_download(result.findings, key="english_download")

    download_button.assert_called_once_with(
        "Download the current view",
        data=expected,
        file_name="expense_quality_findings.csv",
        mime="text/csv",
        type="primary",
        icon=":material/download:",
        key="english_download",
    )


def test_language_change_keeps_source_filters_and_stable_section() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("findings").run(timeout=10)
    app = app.text_input[0].input("policy").run(timeout=10)

    app = app.sidebar.selectbox[0].set_value("English").run(timeout=10)

    assert app.session_state["language"] == "en"
    assert app.session_state["source_name"] == "synthetic_expenses.csv"
    assert app.session_state["workspace_section"] == "findings"
    assert app.session_state["finding_search"] == "policy"
    assert app.get("button_group")[0].options == [
        "▦ Overview",
        "⚑ Findings",
        "◫ Data profile",
        "◇ Governance",
        "▤ Data",
        "⇩ Export",
    ]
    assert any(header.value == "⚑ Findings" for header in app.subheader)

    app = app.text_input[0].input("approval").run(timeout=10)

    assert app.session_state["workspace_section"] == "findings"
    assert any(header.value == "⚑ Findings" for header in app.subheader)
    assert any(message.value == "4 results out of 43" for message in app.markdown)


def test_findings_presentation_is_localized_without_changing_canonical_data() -> None:
    result = analyze_expenses(EXAMPLE_PATH)
    canonical = result.findings.copy(deep=True)

    presented = findings_for_presentation(result.findings, "en")
    policy = presented[presented["rule_id"].eq("POLICY_APPROVAL_REQUIRED")].iloc[0]

    assert policy["anomaly_type"] == "policy"
    assert policy["status"] == "⚠ requires approval"
    assert policy["message"] == "requires approval"
    pd.testing.assert_frame_equal(result.findings, canonical)


def test_empty_filtered_view_uses_success_copy_and_reset_guidance() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("findings").run(timeout=10)
    app = app.text_input[0].input("nessun-risultato-possibile").run(timeout=10)

    assert app.success[0].value == "Nessuna segnalazione nella vista corrente."
    assert any(
        caption.value == "Modifica la ricerca oppure ripristina i filtri per ampliare la vista."
        for caption in app.caption
    )
    assert any(button.label == "Ripristina filtri" for button in app.button)


def test_new_ui_copy_avoids_disallowed_marketing_and_directive_terms() -> None:
    source = (ROOT / "app.py").read_text(encoding="utf-8").casefold()
    disallowed = (
        "pro" + "fessionale",
        "intel" + "ligente",
        "avan" + "zato",
        "po" + "tente",
        "synthetic" + "-only",
        "carica " + "solo",
        "de" + "vi",
        "obbli" + "gatorio",
    )

    assert not any(term in source for term in disallowed)


def test_counts_to_frame_orders_values_and_preserves_columns() -> None:
    result = counts_to_frame({"zeta": 2, "alfa": 1}, "Stato")

    assert result.columns.tolist() == ["Stato", "Conteggio"]
    assert result.to_dict("records") == [
        {"Stato": "alfa", "Conteggio": 1},
        {"Stato": "zeta", "Conteggio": 2},
    ]


def test_counts_to_frame_preserves_columns_when_empty() -> None:
    result = counts_to_frame({}, "Tipo di anomalia")

    assert result.empty
    assert result.columns.tolist() == ["Tipo di anomalia", "Conteggio"]


def test_governance_navigation_metadata_and_catalog_are_complete_in_italian() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("governance").run(timeout=10)

    assert not app.exception
    assert app.get("button_group")[0].value == "governance"
    assert [tab.label for tab in app.tabs] == [
        "Metadati",
        "Catalogo delle regole",
        "Responsabilità",
    ]
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Dimensione (byte)", "27572"),
        ("Righe", "300"),
        ("Colonne sorgente", "10"),
        ("Colonne canoniche", "10"),
    ]
    expected_sha256 = hashlib.sha256(EXAMPLE_PATH.read_bytes()).hexdigest()
    assert app.code[0].value == expected_sha256
    assert len(app.code[0].value) == 64
    assert set(app.code[0].value) <= set("0123456789abcdef")
    assert app.dataframe[1].value.shape == (5, 4)
    assert app.dataframe[2].value.shape == (17, 8)
    assert [widget.label for widget in app.multiselect] == [
        "Tipo di controllo",
        "Dimensione",
        "Stato",
        "Campo",
    ]
    assert [widget.label for widget in app.text_input] == [
        "Data owner",
        "Data steward",
        "Unità organizzativa",
        "Periodo di riferimento",
    ]
    assert not app.warning


def test_governance_filters_rule_catalog_without_changing_finding_filters() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("governance").run(timeout=10)
    dimension_filter = next(widget for widget in app.multiselect if widget.label == "Dimensione")

    app = dimension_filter.select("validity").run(timeout=10)

    catalog = app.dataframe[2].value
    assert catalog.shape == (5, 8)
    assert set(catalog["Dimensione"]) == {"Validità"}
    assert app.session_state["filter_types"] == []
    assert app.session_state["filter_statuses"] == []
    assert app.session_state["filter_categories"] == []
    assert app.session_state["filter_rules"] == []

    status_filter = next(widget for widget in app.multiselect if widget.label == "Stato")
    app = status_filter.select("non conforme").run(timeout=10)

    assert app.dataframe[2].value.empty
    assert any(
        caption.value == "Nessuna regola corrisponde ai filtri selezionati."
        for caption in app.caption
    )


def test_governance_language_change_preserves_section_timestamp_and_responsibilities() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("governance").run(timeout=10)
    timestamp = app.session_state[PROCESSING_METADATA_KEY].analyzed_at_utc
    owner = next(widget for widget in app.text_input if widget.label == "Data owner")
    app = owner.input("Responsabile locale").run(timeout=10)

    app = app.sidebar.selectbox[0].set_value("English").run(timeout=10)

    assert app.session_state["workspace_section"] == "governance"
    assert app.get("button_group")[0].value == "governance"
    assert app.session_state[PROCESSING_METADATA_KEY].analyzed_at_utc == timestamp
    assert app.session_state["governance_owner"] == "Responsabile locale"
    assert [tab.label for tab in app.tabs] == [
        "Metadata",
        "Rule catalog",
        "Responsibilities",
    ]
    assert any(
        "does not constitute an enterprise responsibility assignment system" in info.value
        for info in app.info
    )


def test_governance_responsibilities_persist_across_section_changes() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("governance").run(timeout=10)
    timestamp = app.session_state[PROCESSING_METADATA_KEY].analyzed_at_utc
    owner = next(widget for widget in app.text_input if widget.label == "Data owner")
    app = owner.input("Responsabile locale").run(timeout=10)

    app = app.get("button_group")[0].set_value("data").run(timeout=10)
    app = app.get("button_group")[0].set_value("governance").run(timeout=10)

    owner = next(widget for widget in app.text_input if widget.label == "Data owner")
    assert owner.value == "Responsabile locale"
    assert app.session_state["governance_owner"] == "Responsabile locale"
    assert app.session_state[PROCESSING_METADATA_KEY].analyzed_at_utc == timestamp


def test_governance_reset_clears_optional_responsibilities() -> None:
    app = loaded_example_app()
    app = app.get("button_group")[0].set_value("governance").run(timeout=10)
    unsafe_owner = "<script>alert('test')</script> [link](https://example.invalid)"
    long_notes = "nota " * 1000
    owner = next(widget for widget in app.text_input if widget.label == "Data owner")
    app = owner.input(unsafe_owner).run(timeout=10)
    steward = next(widget for widget in app.text_input if widget.label == "Data steward")
    app = steward.input("Steward locale").run(timeout=10)
    notes = next(widget for widget in app.text_area if widget.label == "Note")
    app = notes.input(long_notes).run(timeout=10)

    assert app.session_state["governance_owner"] == unsafe_owner
    assert app.session_state["governance_notes"] == long_notes
    assert not any(unsafe_owner in message.value for message in app.markdown)

    reset = next(button for button in app.button if button.label == "Azzera metadati inseriti")
    app = reset.click().run(timeout=10)

    assert app.session_state["governance_owner"] == ""
    assert app.session_state["governance_steward"] == ""
    assert app.session_state["governance_notes"] == ""
    assert app.session_state[PROCESSING_METADATA_KEY].row_count == 300

    reset = next(button for button in app.button if button.label == "Azzera metadati inseriti")
    app = reset.click().run(timeout=10)
    assert app.session_state["governance_owner"] == ""


def test_reselecting_the_same_source_preserves_source_bound_governance_state() -> None:
    content = b"a,b\n1,2\n"
    metadata = object()
    session_state = {
        SOURCE_IDENTITY_KEY: ("stesso.csv", content),
        PROCESSING_METADATA_KEY: metadata,
        "governance_owner": "Responsabile locale",
        "governance_steward": "Steward locale",
        "governance_filter_types": ["validità"],
    }
    with patch("app.st.session_state", session_state):
        set_active_source(name="stesso.csv", content=content, is_example=False)

    assert session_state[PROCESSING_METADATA_KEY] is metadata
    assert session_state["governance_owner"] == "Responsabile locale"
    assert session_state["governance_steward"] == "Steward locale"
    assert session_state["governance_filter_types"] == ["validità"]


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("stesso.csv", b"a,b\n3,4\n"),
        ("rinominato.csv", b"a,b\n1,2\n"),
    ],
)
def test_changing_source_name_or_bytes_clears_source_bound_governance_state(
    name: str,
    content: bytes,
) -> None:
    session_state = {
        SOURCE_IDENTITY_KEY: ("stesso.csv", b"a,b\n1,2\n"),
        PROCESSING_METADATA_KEY: object(),
        "governance_owner": "Responsabile locale",
        "governance_steward": "Steward locale",
        "governance_filter_types": ["validità"],
    }
    with patch("app.st.session_state", session_state):
        set_active_source(name=name, content=content, is_example=False)

    assert PROCESSING_METADATA_KEY not in session_state
    assert "governance_owner" not in session_state
    assert "governance_steward" not in session_state
    assert "governance_filter_types" not in session_state
    assert session_state["source_name"] == name
    assert session_state[SOURCE_IDENTITY_KEY] == (name, content)


def test_incompatible_changed_source_clears_governance_without_creating_metadata() -> None:
    app = loaded_example_app()
    app.session_state["governance_owner"] = "Responsabile locale"
    app.session_state["source_name"] = "incompatibile.csv"
    app.session_state["source_bytes"] = b"a,b\n1,2\n"
    app.session_state["source_is_example"] = False

    app = app.run(timeout=10)

    assert PROCESSING_METADATA_KEY not in app.session_state
    assert "governance_owner" not in app.session_state
    assert app.warning[0].value == "Questo CSV non corrisponde alla struttura delle spese"


def test_governance_responsibilities_do_not_change_findings_export() -> None:
    expected = findings_to_csv(analyze_expenses(EXAMPLE_PATH).findings)
    findings = analyze_expenses(EXAMPLE_PATH).findings
    with (
        patch("app.st.session_state", {"governance_owner": "Responsabile locale"}),
        patch("app.st.download_button") as download_button,
    ):
        render_findings_download(findings, key="governance_export_invariance")

    assert download_button.call_args.kwargs["data"] == expected
    assert "Responsabile locale" not in download_button.call_args.kwargs["data"]


def test_governance_reports_bom_semicolon_and_extra_columns_for_an_upload() -> None:
    source = pd.read_csv(StringIO(one_expense_csv().decode()), dtype=str)
    source["nota_locale"] = "valore"
    content = source.to_csv(index=False, sep=";").encode("utf-8-sig")
    app = app_with_uploaded_bytes("spese-extra.csv", content)

    app = app.get("button_group")[0].set_value("governance").run(timeout=10)

    metadata = app.session_state[PROCESSING_METADATA_KEY]
    assert metadata.source_name == "spese-extra.csv"
    assert metadata.source_size_bytes == len(content)
    assert metadata.delimiter == ";"
    assert metadata.encoding == "utf-8"
    assert metadata.has_bom is True
    assert metadata.extra_columns == ("nota_locale",)
    assert metadata.row_count == 1
    assert metadata.source_column_count == 11
    assert metadata.canonical_column_count == 10
    details = app.dataframe[0].value
    assert "UTF-8 con BOM" in details["Valore"].tolist()
    assert "Sì" in details["Valore"].tolist()
    assert "nota_locale" in details["Valore"].tolist()
