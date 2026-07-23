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

FINDING_COLUMNS = (
    "source_row_number",
    "id_spesa",
    "rule_id",
    "anomaly_type",
    "field",
    "status",
    "message",
    "original_value",
)

RULE_CATALOG = MappingProxyType(
    {
        "COMPLETENESS_MISSING_ID_SPESA": (
            "completezza",
            "incompleta",
            "campo obbligatorio mancante: id_spesa",
        ),
        "COMPLETENESS_MISSING_DATA_SPESA": (
            "completezza",
            "incompleta",
            "campo obbligatorio mancante: data_spesa",
        ),
        "COMPLETENESS_MISSING_DIPENDENTE": (
            "completezza",
            "incompleta",
            "campo obbligatorio mancante: dipendente",
        ),
        "COMPLETENESS_MISSING_CATEGORIA": (
            "completezza",
            "incompleta",
            "campo obbligatorio mancante: categoria",
        ),
        "COMPLETENESS_MISSING_IMPORTO": (
            "completezza",
            "incompleta",
            "campo obbligatorio mancante: importo",
        ),
        "COMPLETENESS_MISSING_PROGETTO": (
            "completezza",
            "incompleta",
            "campo obbligatorio mancante: progetto",
        ),
        "UNIQUENESS_ID_DUPLICATE": (
            "unicità",
            "duplicato",
            "id_spesa duplicato",
        ),
        "UNIQUENESS_LOGICAL_DUPLICATE": (
            "unicità",
            "duplicato logico",
            "duplicato logico rilevato",
        ),
        "VALIDITY_NON_NUMERIC_ID": (
            "validità",
            "non valido",
            "id_spesa non numerico",
        ),
        "VALIDITY_INVALID_DATE": (
            "validità",
            "non valida",
            "data_spesa non valida",
        ),
        "VALIDITY_NEGATIVE_AMOUNT": (
            "validità",
            "non valido",
            "importo negativo",
        ),
        "VALIDITY_NON_NUMERIC_AMOUNT": (
            "validità",
            "non valido",
            "importo non numerico",
        ),
        "VALIDITY_INVALID_CATEGORY": (
            "validità",
            "non valida",
            "categoria non ammessa",
        ),
        "STATISTICAL_AMOUNT_ANOMALY": (
            "anomalia statistica",
            "anomalia statistica",
            "importo superiore a 3 volte la mediana della categoria",
        ),
        "STATISTICAL_NOT_EVALUABLE": (
            "valutabilità statistica",
            "non valutabile statisticamente",
            "categoria con meno di 5 righe",
        ),
        "POLICY_APPROVAL_REQUIRED": (
            "policy",
            "richiede approvazione",
            "richiede approvazione",
        ),
        "POLICY_MISSING_APPROVER": (
            "non conformità",
            "non conforme",
            "non conforme: supera soglia senza approvatore assegnato",
        ),
    }
)
