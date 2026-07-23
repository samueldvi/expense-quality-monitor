"""Confirmed schema, category, policy, and statistical configuration."""

from decimal import Decimal
from types import MappingProxyType


EXPECTED_COLUMNS = (
    "id_spesa",
    "data_spesa",
    "dipendente",
    "centro_di_costo",
    "categoria",
    "descrizione",
    "importo",
    "valuta_originale",
    "progetto",
    "approvatore",
)

REQUIRED_FIELDS = frozenset(
    {
        "id_spesa",
        "data_spesa",
        "dipendente",
        "categoria",
        "importo",
        "progetto",
    }
)

VALID_CATEGORIES = (
    "Vitto",
    "Trasporto",
    "Alloggio",
    "Materiale",
    "Rappresentanza",
    "Formazione",
)

POLICY_THRESHOLDS = MappingProxyType(
    {
        "Vitto": Decimal("80"),
        "Trasporto": Decimal("200"),
        "Alloggio": Decimal("250"),
        "Materiale": Decimal("150"),
        "Rappresentanza": Decimal("300"),
        "Formazione": Decimal("500"),
    }
)

MIN_STATISTICAL_OBSERVATIONS = 5
MEDIAN_MULTIPLIER = 3
