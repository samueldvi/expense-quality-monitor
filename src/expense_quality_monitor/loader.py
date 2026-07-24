"""Load expense CSV files as raw text and validate their structural schema."""

from __future__ import annotations

from pathlib import Path
from typing import IO, TypeAlias

import pandas as pd

from expense_quality_monitor.config import EXPECTED_COLUMNS

CsvSource: TypeAlias = str | Path | IO[str] | IO[bytes]
SOURCE_ROW_COLUMN = "source_row_number"


class CsvLoadError(ValueError):
    """User-facing error raised when an expense CSV cannot be loaded safely."""


def _preserve_conflicting_source_column(data: pd.DataFrame) -> pd.DataFrame:
    """Rename a user-provided source-row column before adding the technical one."""
    if SOURCE_ROW_COLUMN not in data.columns:
        return data

    preserved_name = f"{SOURCE_ROW_COLUMN}_input"
    suffix = 2
    while preserved_name in data.columns:
        preserved_name = f"{SOURCE_ROW_COLUMN}_input_{suffix}"
        suffix += 1
    return data.rename(columns={SOURCE_ROW_COLUMN: preserved_name})


def load_expenses(source: CsvSource) -> pd.DataFrame:
    """Load a CSV source as text, preserve raw values, and add row numbers."""
    try:
        data = pd.read_csv(
            source,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
            on_bad_lines="error",
        )
    except pd.errors.EmptyDataError as error:
        raise CsvLoadError("Il file CSV è vuoto o privo di intestazione.") from error
    except pd.errors.ParserError as error:
        raise CsvLoadError("Il file CSV contiene una struttura non leggibile.") from error
    except (OSError, UnicodeError) as error:
        raise CsvLoadError("Non è stato possibile leggere il file CSV.") from error
    except ValueError as error:
        raise CsvLoadError("Il file fornito non è un CSV leggibile.") from error

    columns = tuple(str(column) for column in data.columns)
    missing_columns = [column for column in EXPECTED_COLUMNS if column not in columns]
    if missing_columns:
        if not set(columns).intersection(EXPECTED_COLUMNS):
            raise CsvLoadError("Intestazione CSV assente o non riconoscibile.")
        names = ", ".join(missing_columns)
        raise CsvLoadError(f"Colonne previste mancanti: {names}.")

    if data.empty:
        raise CsvLoadError("Il file CSV non contiene righe di dati.")

    loaded = _preserve_conflicting_source_column(data.copy())
    loaded.insert(0, SOURCE_ROW_COLUMN, range(1, len(loaded) + 1))
    return loaded
