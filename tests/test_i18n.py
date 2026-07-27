"""Tests for deterministic Italian and English interface translations."""

from string import Formatter

import pytest

from expense_quality_monitor import i18n
from expense_quality_monitor.config import RULE_CATALOG


@pytest.mark.parametrize("locale", ["it", "it-IT", "it_IT", "IT-it"])
def test_normalize_language_accepts_italian_locales(locale: str) -> None:
    assert i18n.normalize_language(locale) == "it"


@pytest.mark.parametrize("locale", ["en", "en-US", "en_GB", "EN-gb"])
def test_normalize_language_accepts_english_locales(locale: str) -> None:
    assert i18n.normalize_language(locale) == "en"


@pytest.mark.parametrize("locale", [None, "", " ", "fr-FR", "de"])
def test_normalize_language_defaults_unknown_values_to_italian(
    locale: str | None,
) -> None:
    assert i18n.normalize_language(locale) == "it"


def test_translate_returns_explicit_italian_text() -> None:
    assert i18n.translate("upload.example_action", "it") == "Prova con l’esempio"


def test_translate_returns_explicit_english_text() -> None:
    assert i18n.translate("upload.example_action", "en") == "Try the example"


def test_translate_uses_italian_for_an_unsupported_language() -> None:
    assert i18n.translate("metric.total_rows", "fr") == "Righe"


def test_translate_interpolates_named_values() -> None:
    assert (
        i18n.translate(
            "findings.results.many",
            "en",
            shown=4,
            total=43,
        )
        == "4 results out of 43"
    )


def test_translate_exposes_a_missing_placeholder() -> None:
    with pytest.raises(KeyError, match="shown"):
        i18n.translate("findings.results.many", "en", total=43)


def test_translate_exposes_an_unknown_key() -> None:
    with pytest.raises(KeyError, match="Unknown translation key: missing.key"):
        i18n.translate("missing.key", "it")


def test_catalogs_have_the_same_keys() -> None:
    assert set(i18n.ITALIAN_TRANSLATIONS) == set(i18n.ENGLISH_TRANSLATIONS)


def test_catalogs_have_matching_placeholders() -> None:
    for key in i18n.ITALIAN_TRANSLATIONS:
        italian_fields = {
            field
            for _, field, _, _ in Formatter().parse(i18n.ITALIAN_TRANSLATIONS[key])
            if field is not None
        }
        english_fields = {
            field
            for _, field, _, _ in Formatter().parse(i18n.ENGLISH_TRANSLATIONS[key])
            if field is not None
        }
        assert italian_fields == english_fields, key


def test_catalogs_have_no_empty_values() -> None:
    assert all(i18n.ITALIAN_TRANSLATIONS.values())
    assert all(i18n.ENGLISH_TRANSLATIONS.values())


@pytest.mark.parametrize(
    "key",
    [
        "hero.image_alt",
        "hero.deterministic_badge",
        "status.file_loaded",
        "status.analysis_complete",
        "status.no_findings",
    ],
)
def test_visual_status_copy_exists_in_both_languages(key: str) -> None:
    assert i18n.translate(key, "it")
    assert i18n.translate(key, "en")


@pytest.mark.parametrize(
    "key",
    [
        "nav.profile",
        "profile.title",
        "profile.tab.column_profile",
        "profile.tab.data_dictionary",
        "profile.metric.source_columns",
        "profile.table.completeness",
        "dictionary.technical_name",
        "dictionary.dimensions",
        "column.id_spesa.description",
        "column.approvatore.description",
        "dimension.policy_compliance",
        "type.decimal",
        "format.date_ddmmyyyy",
        "common.not_applicable",
    ],
)
def test_profile_and_dictionary_copy_exists_in_both_languages(key: str) -> None:
    assert i18n.translate(key, "it")
    assert i18n.translate(key, "en")


def test_extra_column_copy_uses_explicit_singular_and_plural_forms() -> None:
    assert (
        i18n.translate("profile.extra.one", "it", columns="extra_note")
        == "Colonna aggiuntiva: extra_note"
    )
    assert (
        i18n.translate("profile.extra.many", "en", columns="first, second")
        == "Extra columns: first, second"
    )


@pytest.mark.parametrize(
    ("key", "italian", "english"),
    [
        ("profile.table.distinct", "Valori distinti", "Distinct values"),
        ("profile.table.source_type", "Tipo sorgente", "Source type"),
        ("profile.table.expected_type", "Tipo atteso", "Expected type"),
        ("dimension.completeness", "Completezza", "Completeness"),
        ("dimension.validity", "Validità", "Validity"),
        ("dimension.uniqueness", "Unicità", "Uniqueness"),
        (
            "dimension.statistical_anomaly",
            "Anomalie statistiche",
            "Statistical anomalies",
        ),
        (
            "dimension.policy_compliance",
            "Conformità alle policy",
            "Policy compliance",
        ),
    ],
)
def test_profile_terms_have_explicit_equivalent_meanings(
    key: str,
    italian: str,
    english: str,
) -> None:
    assert i18n.translate(key, "it") == italian
    assert i18n.translate(key, "en") == english


def test_catalog_builder_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="Duplicate translation key: repeated"):
        i18n._build_catalog((("repeated", "first"), ("repeated", "second")))


@pytest.mark.parametrize(
    "key",
    [
        "nav.governance",
        "governance.title",
        "governance.description",
        "governance.tab.metadata",
        "governance.tab.rules",
        "governance.tab.responsibilities",
        "governance.metadata.source_name",
        "governance.metadata.size",
        "governance.metadata.analyzed_at",
        "governance.metadata.sha256",
        "governance.metadata.rows",
        "governance.metadata.columns",
        "governance.metadata.delimiter",
        "governance.metadata.encoding",
        "governance.metadata.bom",
        "governance.metadata.extra_columns",
        "governance.metadata.app_version",
        "governance.rules.rule_id",
        "governance.rules.name",
        "governance.rules.description",
        "governance.rules.type",
        "governance.rules.dimension",
        "governance.rules.status",
        "governance.rules.fields",
        "governance.rules.parameter",
        "governance.rules.empty",
        "governance.responsibility.owner",
        "governance.responsibility.steward",
        "governance.responsibility.organization",
        "governance.responsibility.period",
        "governance.responsibility.notes",
        "governance.responsibility.notice",
        "governance.responsibility.reset",
    ],
)
def test_governance_copy_exists_in_both_languages(key: str) -> None:
    assert i18n.translate(key, "it")
    assert i18n.translate(key, "en")


def test_all_canonical_rules_have_localized_names_and_descriptions() -> None:
    for rule_id in RULE_CATALOG:
        assert i18n.translate(f"rule.{rule_id}.name", "it")
        assert i18n.translate(f"rule.{rule_id}.name", "en")
        assert i18n.translate(f"rule.{rule_id}.message", "it")
        assert i18n.translate(f"rule.{rule_id}.message", "en")
