"""Load expense CSV files as raw text and validate their structural schema."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import IO, TypeAlias

import pandas as pd

from expense_quality_monitor.config import EXPECTED_COLUMNS

CsvSource: TypeAlias = str | Path | IO[str] | IO[bytes]
SOURCE_ROW_COLUMN = "source_row_number"
SUPPORTED_DELIMITERS = (",", ";")
CSV_ERROR_EMPTY = "empty"
CSV_ERROR_DUPLICATE_COLUMNS = "duplicate_columns"
CSV_ERROR_INCOMPATIBLE_SCHEMA = "incompatible_schema"

_CSV_ERROR_UNREADABLE = "unreadable"
_UNREADABLE_CSV_MESSAGE = "Il contenuto non può essere letto come CSV."


@dataclass(frozen=True)
class SchemaComparison:
    """Deterministic comparison between supplied and canonical expense columns."""

    found_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    extra_columns: tuple[str, ...]

    @property
    def is_compatible(self) -> bool:
        """Return whether every canonical expense column is present."""
        return not self.missing_columns


class CsvLoadError(ValueError):
    """User-facing error raised when an expense CSV cannot be loaded safely."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        schema: SchemaComparison | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.schema = schema


def normalize_column_name(name: object) -> str:
    """Return a deterministic key for matching one supplied column name."""
    return str(name).lstrip("\ufeff").strip().casefold()


def _canonical_column_map() -> dict[str, str]:
    """Map normalized names to the single canonical expense schema."""
    return {normalize_column_name(column): column for column in EXPECTED_COLUMNS}


def compare_schema(columns: tuple[object, ...] | list[object]) -> SchemaComparison:
    """Compare supplied columns with the canonical schema and order the result."""
    canonical_map = _canonical_column_map()
    found = []
    recognized = set()
    extras = []

    for column in columns:
        display_name = str(column).lstrip("\ufeff").strip()
        canonical_name = canonical_map.get(normalize_column_name(column))
        if canonical_name is None:
            found.append(display_name)
            extras.append(display_name)
        else:
            found.append(canonical_name)
            recognized.add(canonical_name)

    missing = tuple(column for column in EXPECTED_COLUMNS if column not in recognized)
    return SchemaComparison(
        found_columns=tuple(found),
        missing_columns=missing,
        extra_columns=tuple(sorted(extras, key=lambda value: (value.casefold(), value))),
    )


def normalize_dataframe_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Rename recognized headers canonically and reject normalized duplicates."""
    canonical_map = _canonical_column_map()
    normalized_names = [normalize_column_name(column) for column in data.columns]
    duplicate_names = sorted(
        {name for name in normalized_names if normalized_names.count(name) > 1}
    )
    if duplicate_names:
        raise CsvLoadError(
            "Alcune colonne hanno lo stesso nome dopo la normalizzazione.",
            code=CSV_ERROR_DUPLICATE_COLUMNS,
        )

    renamed_columns = []
    for column in data.columns:
        canonical_name = canonical_map.get(normalize_column_name(column))
        renamed_columns.append(
            canonical_name if canonical_name is not None else str(column).lstrip("\ufeff").strip()
        )

    normalized = data.copy()
    normalized.columns = renamed_columns
    return normalized


def _read_source_text(source: CsvSource) -> str:
    """Read one supported source as UTF-8 text while accepting an optional BOM."""
    try:
        if isinstance(source, (str, Path)):
            payload: str | bytes = Path(source).read_bytes()
        else:
            payload = source.read()
    except OSError as error:
        raise CsvLoadError(
            _UNREADABLE_CSV_MESSAGE,
            code=_CSV_ERROR_UNREADABLE,
        ) from error

    if isinstance(payload, bytes):
        try:
            return payload.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise CsvLoadError(
                _UNREADABLE_CSV_MESSAGE,
                code=_CSV_ERROR_UNREADABLE,
            ) from error
    if isinstance(payload, str):
        return payload.lstrip("\ufeff")
    raise CsvLoadError(
        _UNREADABLE_CSV_MESSAGE,
        code=_CSV_ERROR_UNREADABLE,
    )


def detect_csv_format(content: str) -> str:
    """Return the detected comma or semicolon delimiter for readable CSV text."""
    if not content.strip():
        raise CsvLoadError("Il file è vuoto.", code=CSV_ERROR_EMPTY)

    try:
        dialect = csv.Sniffer().sniff(content[:8192], delimiters="".join(SUPPORTED_DELIMITERS))
        header = next(csv.reader(StringIO(content), delimiter=dialect.delimiter))
    except (csv.Error, StopIteration) as error:
        raise CsvLoadError(
            _UNREADABLE_CSV_MESSAGE,
            code=_CSV_ERROR_UNREADABLE,
        ) from error

    if dialect.delimiter not in SUPPORTED_DELIMITERS or len(header) < 2:
        raise CsvLoadError(
            _UNREADABLE_CSV_MESSAGE,
            code=_CSV_ERROR_UNREADABLE,
        )
    return dialect.delimiter


def _reject_duplicate_headers(content: str, delimiter: str) -> None:
    """Reject headers that collide after deterministic name normalization."""
    try:
        header = next(csv.reader(StringIO(content), delimiter=delimiter))
    except (csv.Error, StopIteration) as error:
        raise CsvLoadError(
            _UNREADABLE_CSV_MESSAGE,
            code=_CSV_ERROR_UNREADABLE,
        ) from error

    normalized_names = [normalize_column_name(column) for column in header]
    if len(normalized_names) != len(set(normalized_names)):
        raise CsvLoadError(
            "Alcune colonne hanno lo stesso nome dopo la normalizzazione.",
            code=CSV_ERROR_DUPLICATE_COLUMNS,
        )


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
    content = _read_source_text(source)
    delimiter = detect_csv_format(content)
    _reject_duplicate_headers(content, delimiter)

    try:
        data = pd.read_csv(
            StringIO(content),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
            on_bad_lines="error",
        )
    except pd.errors.EmptyDataError as error:
        raise CsvLoadError("Il file è vuoto.", code=CSV_ERROR_EMPTY) from error
    except (pd.errors.ParserError, UnicodeError, ValueError) as error:
        raise CsvLoadError(
            _UNREADABLE_CSV_MESSAGE,
            code=_CSV_ERROR_UNREADABLE,
        ) from error

    normalized = normalize_dataframe_columns(data)
    schema = compare_schema(list(normalized.columns))
    if not schema.is_compatible:
        names = ", ".join(schema.missing_columns)
        raise CsvLoadError(
            f"Colonne previste mancanti: {names}.",
            code=CSV_ERROR_INCOMPATIBLE_SCHEMA,
            schema=schema,
        )

    if normalized.empty:
        raise CsvLoadError("Il file è vuoto.", code=CSV_ERROR_EMPTY)

    loaded = _preserve_conflicting_source_column(normalized)
    loaded.insert(0, SOURCE_ROW_COLUMN, range(1, len(loaded) + 1))
    return loaded
