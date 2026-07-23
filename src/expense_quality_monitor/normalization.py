"""Create parsed and normalized working values without changing raw data."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import TypeGuard

import pandas as pd

from expense_quality_monitor.config import EXPECTED_COLUMNS, REQUIRED_FIELDS, VALID_CATEGORIES


ID_PATTERN = re.compile(r"[0-9]+")
AMOUNT_PATTERN = re.compile(r"[+-]?[0-9]+(?:[.,][0-9]+)?")
DATE_PATTERN = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")


def is_missing(value: object) -> bool:
    """Return whether a scalar is null, empty, or contains only whitespace."""
    if value is None or value is pd.NA:
        return True
    try:
        if bool(pd.isna(value)):
            return True
    except (TypeError, ValueError):
        return False
    return isinstance(value, str) and not value.strip()


def parse_identifier(value: object) -> int | None:
    """Parse a decimal integer identifier, returning none for invalid values."""
    if is_missing(value):
        return None
    text = str(value).strip()
    return int(text) if ID_PATTERN.fullmatch(text) else None


def parse_expense_date(value: object) -> date | None:
    """Parse a date only when its text exactly follows DD/MM/YYYY."""
    if is_missing(value):
        return None
    text = str(value)
    if not DATE_PATTERN.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_amount(value: object) -> Decimal | None:
    """Parse a comma- or point-decimal amount without binary floating errors."""
    if is_missing(value):
        return None
    text = str(value).strip()
    if not AMOUNT_PATTERN.fullmatch(text):
        return None
    try:
        return Decimal(text.replace(",", "."))
    except InvalidOperation:
        return None


def normalize_text(value: object) -> str | None:
    """Trim, collapse internal whitespace, and casefold a present text value."""
    if is_missing(value):
        return None
    return " ".join(str(value).strip().split()).casefold()


def is_usable_amount(value: object) -> TypeGuard[Decimal]:
    """Return whether a parsed amount can participate in rules and statistics."""
    return isinstance(value, Decimal) and value >= 0


def normalize_expenses(data: pd.DataFrame) -> pd.DataFrame:
    """Return a working copy containing parsed values and eligibility flags."""
    normalized = data.copy()

    for field in EXPECTED_COLUMNS:
        if field in REQUIRED_FIELDS:
            normalized[f"_missing_{field}"] = normalized[field].map(is_missing)

    normalized["_id_parsed"] = normalized["id_spesa"].map(parse_identifier)
    normalized["_date_parsed"] = normalized["data_spesa"].map(parse_expense_date)
    normalized["_amount_parsed"] = normalized["importo"].map(parse_amount)
    normalized["_employee_normalized"] = normalized["dipendente"].map(normalize_text)
    normalized["_category_normalized"] = normalized["categoria"].map(normalize_text)
    normalized["_category_valid"] = normalized["categoria"].map(
        lambda value: not is_missing(value) and value in VALID_CATEGORIES
    )
    normalized["_approver_missing"] = normalized["approvatore"].map(is_missing)
    return normalized
