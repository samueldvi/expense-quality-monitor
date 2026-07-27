"""Small, deterministic internationalization utilities for the dashboard."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from string import Formatter
from types import MappingProxyType

SUPPORTED_LANGUAGES = ("it", "en")
DEFAULT_LANGUAGE = "it"

TranslationEntries = Sequence[tuple[str, str]]


def _build_catalog(entries: TranslationEntries) -> Mapping[str, str]:
    """Build an immutable catalog while rejecting duplicate or empty entries."""
    catalog: dict[str, str] = {}
    for key, value in entries:
        if key in catalog:
            raise ValueError(f"Duplicate translation key: {key}")
        if not key or not value:
            raise ValueError("Translation keys and values must not be empty")
        catalog[key] = value
    return MappingProxyType(catalog)


ITALIAN_TRANSLATIONS = _build_catalog(
    (
        ("app.title", "Expense Quality Monitor"),
        ("app.subtitle", "Controlla il file, individua le eccezioni e prepara il riepilogo."),
        ("hero.deterministic_badge", "Controlli deterministici, nessuna AI nel runtime"),
        (
            "hero.image_alt",
            "Illustrazione astratta di una tabella verificata da controlli di qualità",
        ),
        ("language.label", "Lingua"),
        ("language.italian", "Italiano"),
        ("language.english", "English"),
        ("upload.title", "Da dove vuoi partire?"),
        ("upload.description", "Scegli un CSV oppure esplora l’app con il file di esempio."),
        ("upload.button", "Scegli un CSV"),
        ("upload.example", "File di esempio"),
        ("upload.example_action", "Prova con l’esempio"),
        ("upload.privacy", "Il file viene elaborato nella sessione e non viene salvato."),
        ("upload.selected", "File selezionato"),
        ("upload.replace", "Scegli un altro CSV"),
        ("upload.template_description", "Scarica un CSV con le colonne già predisposte."),
        ("upload.template_download", "Scarica il modello CSV"),
        ("session.title", "Sessione"),
        ("session.rows.one", "{count} riga"),
        ("session.rows.many", "{count} righe"),
        ("session.findings.one", "{count} segnalazione"),
        ("session.findings.many", "{count} segnalazioni"),
        ("session.processing_info", "Informazioni sull’elaborazione"),
        ("session.processing_detail", "L’analisi resta nella sessione e non crea uno storico."),
        ("source.kind.example", "File di esempio"),
        ("status.file_loaded", "File caricato"),
        ("status.analysis_complete", "Analisi completata"),
        ("status.no_findings", "Nessuna segnalazione nella vista corrente."),
        (
            "source.extra.one",
            "Il file contiene 1 colonna aggiuntiva che non viene utilizzata nell’analisi.",
        ),
        (
            "source.extra.many",
            "Il file contiene {count} colonne aggiuntive che non vengono utilizzate nell’analisi.",
        ),
        ("schema.incompatible", "Questo CSV non corrisponde alla struttura delle spese"),
        (
            "schema.guidance",
            "Puoi confrontare le colonne del file con quelle richieste oppure partire dal modello CSV.",
        ),
        ("schema.missing_columns", "Colonne mancanti"),
        ("schema.missing_count.one", "Manca 1 colonna"),
        ("schema.missing_count.many", "Mancano {count} colonne"),
        ("schema.found_columns", "Colonne trovate"),
        ("schema.extra_columns", "Colonne aggiuntive"),
        ("nav.label", "Sezione"),
        ("nav.overview", "Panoramica"),
        ("nav.findings", "Segnalazioni"),
        ("nav.profile", "Profilo dati"),
        ("nav.data", "Dati"),
        ("nav.export", "Esporta"),
        ("metric.total_rows", "Righe"),
        ("metric.rows_to_review", "Righe da verificare"),
        ("metric.findings", "Segnalazioni"),
        ("metric.rules", "Regole coinvolte"),
        ("metric.file", "File"),
        ("metric.columns", "Colonne"),
        ("metric.rows_included", "Righe incluse"),
        ("metric.format", "Formato"),
        ("overview.findings_by_type", "Dove si concentrano le segnalazioni"),
        ("overview.findings_by_status", "Stato delle verifiche"),
        ("overview.categories", "Categorie"),
        ("common.count", "Conteggio"),
        ("common.type", "Tipo"),
        ("common.status", "Stato"),
        ("common.category", "Categoria"),
        ("common.rule", "Regola"),
        ("common.field", "Campo"),
        ("common.description", "Descrizione"),
        ("common.yes", "Sì"),
        ("common.no", "No"),
        ("common.not_applicable", "Non applicabile"),
        ("common.none", "Nessuno"),
        ("profile.title", "Profilo dati"),
        (
            "profile.description",
            "Esamina struttura, completezza e metadati del file analizzato.",
        ),
        ("profile.tab.column_profile", "Profilo per colonna"),
        ("profile.tab.data_dictionary", "Dizionario dati"),
        ("profile.metric.source_columns", "Colonne sorgente"),
        ("profile.metric.canonical_columns", "Colonne canoniche"),
        ("profile.metric.extra_columns", "Colonne aggiuntive"),
        ("profile.metric.rows_with_findings", "Righe con segnalazioni"),
        ("profile.summary.rows", "Righe sorgente"),
        ("profile.summary.findings", "Segnalazioni totali"),
        ("profile.summary.duplicate_id_rows", "Righe duplicate per ID"),
        ("profile.summary.logical_duplicate_rows", "Righe duplicate logiche"),
        ("profile.summary.validity_findings", "Segnalazioni di validità"),
        ("profile.extra.one", "Colonna aggiuntiva: {columns}"),
        ("profile.extra.many", "Colonne aggiuntive: {columns}"),
        ("profile.table.technical_name", "Nome tecnico"),
        ("profile.table.canonical", "Tipo di colonna"),
        ("profile.table.canonical_value", "Canonica"),
        ("profile.table.extra_value", "Aggiuntiva"),
        ("profile.table.missing", "Valori mancanti"),
        ("profile.table.completeness", "Completezza (%)"),
        ("profile.table.distinct", "Valori distinti"),
        ("profile.table.source_type", "Tipo sorgente"),
        ("profile.table.expected_type", "Tipo atteso"),
        ("profile.table.related_findings", "Segnalazioni associate"),
        ("profile.table.minimum", "Minimo valido"),
        ("profile.table.maximum", "Massimo valido"),
        ("profile.chart.completeness", "Completezza per colonna"),
        ("dictionary.title", "Dizionario dati"),
        ("dictionary.technical_name", "Nome tecnico"),
        ("dictionary.display_name", "Nome visualizzato"),
        ("dictionary.description", "Descrizione"),
        ("dictionary.required", "Obbligatorio"),
        ("dictionary.expected_type", "Tipo atteso"),
        ("dictionary.format", "Formato"),
        ("dictionary.allowed_values", "Valori ammessi"),
        ("dictionary.example", "Esempio"),
        ("dictionary.rules", "Regole associate"),
        ("dictionary.dimensions", "Dimensioni della qualità"),
        ("type.integer", "Intero"),
        ("type.date", "Data"),
        ("type.text", "Testo"),
        ("type.category", "Categoria"),
        ("type.decimal", "Numero decimale"),
        ("type.project_code", "Codice progetto"),
        ("format.progressive_integer", "Identificativo numerico progressivo"),
        ("format.date_ddmmyyyy", "DD/MM/YYYY"),
        ("format.surname_name", "Cognome e nome"),
        ("format.not_specified", "Formato non specificato"),
        ("format.allowed_category", "Uno dei sei valori ammessi"),
        ("format.free_text", "Testo libero"),
        ("format.eur_decimal", "EUR, separatore decimale virgola o punto"),
        ("format.original_currency", "Valuta originale, quando presente"),
        ("format.project_code", "Codice progetto; esempio non vincolante"),
        ("dimension.completeness", "Completezza"),
        ("dimension.validity", "Validità"),
        ("dimension.uniqueness", "Unicità"),
        ("dimension.statistical_anomaly", "Anomalie statistiche"),
        ("dimension.policy_compliance", "Conformità alle policy"),
        ("column.id_spesa.label", "ID spesa"),
        (
            "column.id_spesa.description",
            "Identificativo numerico progressivo della spesa.",
        ),
        ("column.data_spesa.label", "Data della spesa"),
        (
            "column.data_spesa.description",
            "Data in cui è stata sostenuta la spesa.",
        ),
        ("column.dipendente.label", "Dipendente"),
        (
            "column.dipendente.description",
            "Cognome e nome del dipendente.",
        ),
        ("column.centro_di_costo.label", "Centro di costo"),
        (
            "column.centro_di_costo.description",
            "Centro di costo associato, quando presente.",
        ),
        ("column.categoria.label", "Categoria"),
        (
            "column.categoria.description",
            "Categoria della spesa tra i valori ammessi.",
        ),
        ("column.descrizione.label", "Descrizione"),
        (
            "column.descrizione.description",
            "Testo libero descrittivo, spesso vuoto.",
        ),
        ("column.importo.label", "Importo"),
        (
            "column.importo.description",
            "Importo della spesa espresso in EUR.",
        ),
        ("column.valuta_originale.label", "Valuta originale"),
        (
            "column.valuta_originale.description",
            "Valuta originale, presente in caso di spesa estera.",
        ),
        ("column.progetto.label", "Progetto"),
        (
            "column.progetto.description",
            "Codice del progetto associato alla spesa.",
        ),
        ("column.approvatore.label", "Approvatore"),
        (
            "column.approvatore.description",
            "Approvatore associato alla spesa, quando presente.",
        ),
        ("findings.title", "Segnalazioni"),
        ("findings.search", "Cerca per ID, regola o descrizione"),
        ("findings.search_placeholder", "ID spesa, ID regola o testo"),
        ("findings.reset", "Ripristina filtri"),
        ("findings.results.one", "1 risultato su {total}"),
        ("findings.results.many", "{shown} risultati su {total}"),
        (
            "findings.no_results_hint",
            "Modifica la ricerca oppure ripristina i filtri per ampliare la vista.",
        ),
        ("findings.download", "Scarica la vista corrente"),
        ("findings.table.source_row", "Riga CSV"),
        ("findings.table.expense_id", "ID spesa"),
        ("findings.table.original_value", "Valore originale"),
        ("filters.search", "Ricerca: {query}"),
        ("filters.value", "{label}: {values}"),
        ("filters.none", "Nessun filtro attivo"),
        ("data.title", "Dati"),
        (
            "data.description",
            "Qui puoi controllare il contenuto ricevuto prima di approfondire le segnalazioni.",
        ),
        ("data.column_names", "Nomi delle colonne"),
        ("data.preview", "Anteprima"),
        ("export.title", "Esporta"),
        ("export.active_filters", "Filtri attivi"),
        ("export.empty", "La vista corrente non contiene righe da esportare."),
        ("analysis.running", "Analisi in corso"),
        ("error.empty", "Il file è vuoto."),
        (
            "error.duplicate_columns",
            "Alcune colonne hanno lo stesso nome dopo la normalizzazione.",
        ),
        ("error.unreadable", "Il contenuto non può essere letto come CSV."),
        (
            "error.unexpected",
            "L’analisi non è stata completata. Puoi scegliere un altro CSV.",
        ),
        ("finding.type.completezza", "completezza"),
        ("finding.type.unicità", "unicità"),
        ("finding.type.validità", "validità"),
        ("finding.type.anomalia_statistica", "anomalia statistica"),
        ("finding.type.valutabilità_statistica", "valutabilità statistica"),
        ("finding.type.policy", "policy"),
        ("finding.type.non_conformità", "non conformità"),
        ("finding.status.incompleta", "incompleta"),
        ("finding.status.duplicato", "duplicato"),
        ("finding.status.duplicato_logico", "duplicato logico"),
        ("finding.status.non_valido", "non valido"),
        ("finding.status.non_valida", "non valida"),
        ("finding.status.anomalia_statistica", "anomalia statistica"),
        (
            "finding.status.non_valutabile_statisticamente",
            "non valutabile statisticamente",
        ),
        ("finding.status.richiede_approvazione", "richiede approvazione"),
        ("finding.status.non_conforme", "non conforme"),
        (
            "rule.COMPLETENESS_MISSING_ID_SPESA.message",
            "campo obbligatorio mancante: id_spesa",
        ),
        (
            "rule.COMPLETENESS_MISSING_DATA_SPESA.message",
            "campo obbligatorio mancante: data_spesa",
        ),
        (
            "rule.COMPLETENESS_MISSING_DIPENDENTE.message",
            "campo obbligatorio mancante: dipendente",
        ),
        (
            "rule.COMPLETENESS_MISSING_CATEGORIA.message",
            "campo obbligatorio mancante: categoria",
        ),
        (
            "rule.COMPLETENESS_MISSING_IMPORTO.message",
            "campo obbligatorio mancante: importo",
        ),
        (
            "rule.COMPLETENESS_MISSING_PROGETTO.message",
            "campo obbligatorio mancante: progetto",
        ),
        ("rule.UNIQUENESS_ID_DUPLICATE.message", "id_spesa duplicato"),
        ("rule.UNIQUENESS_LOGICAL_DUPLICATE.message", "duplicato logico rilevato"),
        ("rule.VALIDITY_NON_NUMERIC_ID.message", "id_spesa non numerico"),
        ("rule.VALIDITY_INVALID_DATE.message", "data_spesa non valida"),
        ("rule.VALIDITY_NEGATIVE_AMOUNT.message", "importo negativo"),
        ("rule.VALIDITY_NON_NUMERIC_AMOUNT.message", "importo non numerico"),
        ("rule.VALIDITY_INVALID_CATEGORY.message", "categoria non ammessa"),
        (
            "rule.STATISTICAL_AMOUNT_ANOMALY.message",
            "importo superiore a 3 volte la mediana della categoria",
        ),
        (
            "rule.STATISTICAL_NOT_EVALUABLE.message",
            "categoria con meno di 5 osservazioni utilizzabili",
        ),
        ("rule.POLICY_APPROVAL_REQUIRED.message", "richiede approvazione"),
        (
            "rule.POLICY_MISSING_APPROVER.message",
            "non conforme: supera soglia senza approvatore assegnato",
        ),
    )
)

ENGLISH_TRANSLATIONS = _build_catalog(
    (
        ("app.title", "Expense Quality Monitor"),
        ("app.subtitle", "Check the file, identify exceptions, and prepare the summary."),
        ("hero.deterministic_badge", "Deterministic checks, no AI at runtime"),
        (
            "hero.image_alt",
            "Abstract illustration of a table verified by quality checks",
        ),
        ("language.label", "Language"),
        ("language.italian", "Italiano"),
        ("language.english", "English"),
        ("upload.title", "Where would you like to start?"),
        ("upload.description", "Choose a CSV or explore the app with the example file."),
        ("upload.button", "Choose a CSV"),
        ("upload.example", "Example file"),
        ("upload.example_action", "Try the example"),
        ("upload.privacy", "The file is processed in this session and is not saved."),
        ("upload.selected", "Selected file"),
        ("upload.replace", "Choose another CSV"),
        ("upload.template_description", "Download a CSV with the columns already prepared."),
        ("upload.template_download", "Download the CSV template"),
        ("session.title", "Session"),
        ("session.rows.one", "{count} row"),
        ("session.rows.many", "{count} rows"),
        ("session.findings.one", "{count} finding"),
        ("session.findings.many", "{count} findings"),
        ("session.processing_info", "Processing information"),
        ("session.processing_detail", "The analysis stays in this session and creates no history."),
        ("source.kind.example", "Example file"),
        ("status.file_loaded", "File loaded"),
        ("status.analysis_complete", "Analysis complete"),
        ("status.no_findings", "No findings in the current view."),
        ("source.extra.one", "The file contains 1 extra column that is not used in the analysis."),
        (
            "source.extra.many",
            "The file contains {count} extra columns that are not used in the analysis.",
        ),
        ("schema.incompatible", "This CSV does not match the expense structure"),
        (
            "schema.guidance",
            "You can compare the file columns with the required columns or start from the CSV template.",
        ),
        ("schema.missing_columns", "Missing columns"),
        ("schema.missing_count.one", "1 column is missing"),
        ("schema.missing_count.many", "{count} columns are missing"),
        ("schema.found_columns", "Found columns"),
        ("schema.extra_columns", "Extra columns"),
        ("nav.label", "Section"),
        ("nav.overview", "Overview"),
        ("nav.findings", "Findings"),
        ("nav.profile", "Data profile"),
        ("nav.data", "Data"),
        ("nav.export", "Export"),
        ("metric.total_rows", "Rows"),
        ("metric.rows_to_review", "Rows to review"),
        ("metric.findings", "Findings"),
        ("metric.rules", "Rules involved"),
        ("metric.file", "File"),
        ("metric.columns", "Columns"),
        ("metric.rows_included", "Rows included"),
        ("metric.format", "Format"),
        ("overview.findings_by_type", "Where findings are concentrated"),
        ("overview.findings_by_status", "Check status"),
        ("overview.categories", "Categories"),
        ("common.count", "Count"),
        ("common.type", "Type"),
        ("common.status", "Status"),
        ("common.category", "Category"),
        ("common.rule", "Rule"),
        ("common.field", "Field"),
        ("common.description", "Description"),
        ("common.yes", "Yes"),
        ("common.no", "No"),
        ("common.not_applicable", "Not applicable"),
        ("common.none", "None"),
        ("profile.title", "Data profile"),
        (
            "profile.description",
            "Review the structure, completeness, and metadata of the analyzed file.",
        ),
        ("profile.tab.column_profile", "Column profile"),
        ("profile.tab.data_dictionary", "Data dictionary"),
        ("profile.metric.source_columns", "Source columns"),
        ("profile.metric.canonical_columns", "Canonical columns"),
        ("profile.metric.extra_columns", "Extra columns"),
        ("profile.metric.rows_with_findings", "Rows with findings"),
        ("profile.summary.rows", "Source rows"),
        ("profile.summary.findings", "Total findings"),
        ("profile.summary.duplicate_id_rows", "Duplicate-ID rows"),
        ("profile.summary.logical_duplicate_rows", "Logical-duplicate rows"),
        ("profile.summary.validity_findings", "Validity findings"),
        ("profile.extra.one", "Extra column: {columns}"),
        ("profile.extra.many", "Extra columns: {columns}"),
        ("profile.table.technical_name", "Technical name"),
        ("profile.table.canonical", "Column type"),
        ("profile.table.canonical_value", "Canonical"),
        ("profile.table.extra_value", "Extra"),
        ("profile.table.missing", "Missing values"),
        ("profile.table.completeness", "Completeness (%)"),
        ("profile.table.distinct", "Distinct values"),
        ("profile.table.source_type", "Source type"),
        ("profile.table.expected_type", "Expected type"),
        ("profile.table.related_findings", "Related findings"),
        ("profile.table.minimum", "Valid minimum"),
        ("profile.table.maximum", "Valid maximum"),
        ("profile.chart.completeness", "Completeness by column"),
        ("dictionary.title", "Data dictionary"),
        ("dictionary.technical_name", "Technical name"),
        ("dictionary.display_name", "Display name"),
        ("dictionary.description", "Description"),
        ("dictionary.required", "Required"),
        ("dictionary.expected_type", "Expected type"),
        ("dictionary.format", "Format"),
        ("dictionary.allowed_values", "Allowed values"),
        ("dictionary.example", "Example"),
        ("dictionary.rules", "Related rules"),
        ("dictionary.dimensions", "Quality dimensions"),
        ("type.integer", "Integer"),
        ("type.date", "Date"),
        ("type.text", "Text"),
        ("type.category", "Category"),
        ("type.decimal", "Decimal number"),
        ("type.project_code", "Project code"),
        ("format.progressive_integer", "Progressive numeric identifier"),
        ("format.date_ddmmyyyy", "DD/MM/YYYY"),
        ("format.surname_name", "Surname and given name"),
        ("format.not_specified", "Format not specified"),
        ("format.allowed_category", "One of the six allowed values"),
        ("format.free_text", "Free text"),
        ("format.eur_decimal", "EUR, comma or point decimal separator"),
        ("format.original_currency", "Original currency, when present"),
        ("format.project_code", "Project code; non-binding example"),
        ("dimension.completeness", "Completeness"),
        ("dimension.validity", "Validity"),
        ("dimension.uniqueness", "Uniqueness"),
        ("dimension.statistical_anomaly", "Statistical anomalies"),
        ("dimension.policy_compliance", "Policy compliance"),
        ("column.id_spesa.label", "Expense ID"),
        (
            "column.id_spesa.description",
            "Progressive numeric identifier of the expense.",
        ),
        ("column.data_spesa.label", "Expense date"),
        (
            "column.data_spesa.description",
            "Date on which the expense was incurred.",
        ),
        ("column.dipendente.label", "Employee"),
        (
            "column.dipendente.description",
            "Employee surname and given name.",
        ),
        ("column.centro_di_costo.label", "Cost center"),
        (
            "column.centro_di_costo.description",
            "Associated cost center, when present.",
        ),
        ("column.categoria.label", "Category"),
        (
            "column.categoria.description",
            "Expense category selected from the allowed values.",
        ),
        ("column.descrizione.label", "Description"),
        (
            "column.descrizione.description",
            "Free descriptive text, often empty.",
        ),
        ("column.importo.label", "Amount"),
        (
            "column.importo.description",
            "Expense amount expressed in EUR.",
        ),
        ("column.valuta_originale.label", "Original currency"),
        (
            "column.valuta_originale.description",
            "Original currency, present for foreign expenses.",
        ),
        ("column.progetto.label", "Project"),
        (
            "column.progetto.description",
            "Project code associated with the expense.",
        ),
        ("column.approvatore.label", "Approver"),
        (
            "column.approvatore.description",
            "Approver associated with the expense, when present.",
        ),
        ("findings.title", "Findings"),
        ("findings.search", "Search by ID, rule, or description"),
        ("findings.search_placeholder", "Expense ID, rule ID, or text"),
        ("findings.reset", "Reset filters"),
        ("findings.results.one", "1 result out of {total}"),
        ("findings.results.many", "{shown} results out of {total}"),
        (
            "findings.no_results_hint",
            "Change the search or reset the filters to broaden the view.",
        ),
        ("findings.download", "Download the current view"),
        ("findings.table.source_row", "CSV row"),
        ("findings.table.expense_id", "Expense ID"),
        ("findings.table.original_value", "Original value"),
        ("filters.search", "Search: {query}"),
        ("filters.value", "{label}: {values}"),
        ("filters.none", "No active filters"),
        ("data.title", "Data"),
        (
            "data.description",
            "Review the received content here before examining the findings in detail.",
        ),
        ("data.column_names", "Column names"),
        ("data.preview", "Preview"),
        ("export.title", "Export"),
        ("export.active_filters", "Active filters"),
        ("export.empty", "The current view contains no rows to export."),
        ("analysis.running", "Analysis in progress"),
        ("error.empty", "The file is empty."),
        (
            "error.duplicate_columns",
            "Some columns have the same name after normalization.",
        ),
        ("error.unreadable", "The content cannot be read as CSV."),
        (
            "error.unexpected",
            "The analysis could not be completed. You can choose another CSV.",
        ),
        ("finding.type.completezza", "completeness"),
        ("finding.type.unicità", "uniqueness"),
        ("finding.type.validità", "validity"),
        ("finding.type.anomalia_statistica", "statistical anomaly"),
        ("finding.type.valutabilità_statistica", "statistical evaluability"),
        ("finding.type.policy", "policy"),
        ("finding.type.non_conformità", "non-compliance"),
        ("finding.status.incompleta", "incomplete"),
        ("finding.status.duplicato", "duplicate"),
        ("finding.status.duplicato_logico", "logical duplicate"),
        ("finding.status.non_valido", "invalid"),
        ("finding.status.non_valida", "invalid"),
        ("finding.status.anomalia_statistica", "statistical anomaly"),
        (
            "finding.status.non_valutabile_statisticamente",
            "not statistically evaluable",
        ),
        ("finding.status.richiede_approvazione", "requires approval"),
        ("finding.status.non_conforme", "non-compliant"),
        (
            "rule.COMPLETENESS_MISSING_ID_SPESA.message",
            "required field missing: id_spesa",
        ),
        (
            "rule.COMPLETENESS_MISSING_DATA_SPESA.message",
            "required field missing: data_spesa",
        ),
        (
            "rule.COMPLETENESS_MISSING_DIPENDENTE.message",
            "required field missing: dipendente",
        ),
        (
            "rule.COMPLETENESS_MISSING_CATEGORIA.message",
            "required field missing: categoria",
        ),
        (
            "rule.COMPLETENESS_MISSING_IMPORTO.message",
            "required field missing: importo",
        ),
        (
            "rule.COMPLETENESS_MISSING_PROGETTO.message",
            "required field missing: progetto",
        ),
        ("rule.UNIQUENESS_ID_DUPLICATE.message", "duplicate id_spesa"),
        ("rule.UNIQUENESS_LOGICAL_DUPLICATE.message", "logical duplicate detected"),
        ("rule.VALIDITY_NON_NUMERIC_ID.message", "non-numeric id_spesa"),
        ("rule.VALIDITY_INVALID_DATE.message", "invalid data_spesa"),
        ("rule.VALIDITY_NEGATIVE_AMOUNT.message", "negative amount"),
        ("rule.VALIDITY_NON_NUMERIC_AMOUNT.message", "non-numeric amount"),
        ("rule.VALIDITY_INVALID_CATEGORY.message", "category not allowed"),
        (
            "rule.STATISTICAL_AMOUNT_ANOMALY.message",
            "amount greater than 3 times the category median",
        ),
        (
            "rule.STATISTICAL_NOT_EVALUABLE.message",
            "category with fewer than 5 usable observations",
        ),
        ("rule.POLICY_APPROVAL_REQUIRED.message", "requires approval"),
        (
            "rule.POLICY_MISSING_APPROVER.message",
            "non-compliant: above threshold without an assigned approver",
        ),
    )
)

TRANSLATIONS = MappingProxyType(
    {
        "it": ITALIAN_TRANSLATIONS,
        "en": ENGLISH_TRANSLATIONS,
    }
)


def normalize_language(locale: str | None) -> str:
    """Normalize a supported locale to its language code, defaulting to Italian."""
    if not locale:
        return DEFAULT_LANGUAGE
    language = locale.strip().replace("_", "-").split("-", maxsplit=1)[0].casefold()
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def _placeholders(template: str) -> frozenset[str]:
    """Return the named placeholders used by one translation template."""
    return frozenset(
        field_name for _, field_name, _, _ in Formatter().parse(template) if field_name is not None
    )


def validate_catalogs() -> None:
    """Validate language key and placeholder parity and reject empty values."""
    italian_keys = set(ITALIAN_TRANSLATIONS)
    english_keys = set(ENGLISH_TRANSLATIONS)
    if italian_keys != english_keys:
        missing_in_english = sorted(italian_keys - english_keys)
        missing_in_italian = sorted(english_keys - italian_keys)
        raise ValueError(
            "Translation key mismatch: "
            f"missing in English={missing_in_english}, "
            f"missing in Italian={missing_in_italian}"
        )

    for key in sorted(italian_keys):
        italian = ITALIAN_TRANSLATIONS[key]
        english = ENGLISH_TRANSLATIONS[key]
        if not italian or not english:
            raise ValueError(f"Empty translation value: {key}")
        if _placeholders(italian) != _placeholders(english):
            raise ValueError(f"Translation placeholder mismatch: {key}")


def translate(key: str, language: str, **values: object) -> str:
    """Return one localized string and expose missing keys or values clearly."""
    normalized_language = normalize_language(language)
    catalog = TRANSLATIONS[normalized_language]
    try:
        template = catalog[key]
    except KeyError as error:
        raise KeyError(f"Unknown translation key: {key}") from error
    return template.format(**values)


validate_catalogs()
