"""Tests for deterministic Italian and English interface translations."""

from string import Formatter

import pytest

from expense_quality_monitor import i18n


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


def test_catalog_builder_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="Duplicate translation key: repeated"):
        i18n._build_catalog((("repeated", "first"), ("repeated", "second")))
