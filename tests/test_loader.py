"""Tests for CSV loading, schema validation, and raw-value preservation."""

from io import StringIO

import pytest

from expense_quality_monitor.config import EXPECTED_COLUMNS
from expense_quality_monitor.loader import CsvLoadError, load_expenses


def test_loader_preserves_text_adds_row_numbers_and_accepts_extra_columns() -> None:
    header = ",".join((*EXPECTED_COLUMNS, "colonna_extra"))
    row = "1,13/07/2026,Demo Uno,CDC-001,Vitto,,10.50,,PRJ-001,,extra"
    loaded = load_expenses(StringIO(f"{header}\n{row}\n"))

    assert loaded.loc[0, "source_row_number"] == 1
    assert loaded.loc[0, "importo"] == "10.50"
    assert loaded.loc[0, "colonna_extra"] == "extra"


def test_loader_preserves_extra_column_that_conflicts_with_technical_row_number() -> None:
    header = ",".join((*EXPECTED_COLUMNS, "source_row_number"))
    row = "1,13/07/2026,Demo Uno,CDC-001,Vitto,,10.50,,PRJ-001,,valore-originale"

    loaded = load_expenses(StringIO(f"{header}\n{row}\n"))

    assert loaded.loc[0, "source_row_number"] == 1
    assert loaded.loc[0, "source_row_number_input"] == "valore-originale"


def test_loader_blocks_missing_expected_columns() -> None:
    with pytest.raises(CsvLoadError, match="Colonne previste mancanti"):
        load_expenses(StringIO("id_spesa,data_spesa\n1,13/07/2026\n"))


@pytest.mark.parametrize("content", ["", "a,b\n1,2\n"])
def test_loader_reports_empty_or_unrecognizable_csv(content: str) -> None:
    with pytest.raises(CsvLoadError):
        load_expenses(StringIO(content))
