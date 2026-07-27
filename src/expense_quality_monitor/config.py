"""Confirmed schema, category, policy, and statistical configuration."""

from dataclasses import dataclass
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
        "Vitto": Decimal(80),
        "Trasporto": Decimal(200),
        "Alloggio": Decimal(250),
        "Materiale": Decimal(150),
        "Rappresentanza": Decimal(300),
        "Formazione": Decimal(500),
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
            "categoria con meno di 5 osservazioni utilizzabili",
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

QUALITY_DIMENSIONS = (
    "completeness",
    "validity",
    "uniqueness",
    "statistical_anomaly",
    "policy_compliance",
)

RULE_TARGET_FIELDS = MappingProxyType(
    {
        "COMPLETENESS_MISSING_ID_SPESA": ("id_spesa",),
        "COMPLETENESS_MISSING_DATA_SPESA": ("data_spesa",),
        "COMPLETENESS_MISSING_DIPENDENTE": ("dipendente",),
        "COMPLETENESS_MISSING_CATEGORIA": ("categoria",),
        "COMPLETENESS_MISSING_IMPORTO": ("importo",),
        "COMPLETENESS_MISSING_PROGETTO": ("progetto",),
        "UNIQUENESS_ID_DUPLICATE": ("id_spesa",),
        "UNIQUENESS_LOGICAL_DUPLICATE": (
            "dipendente",
            "data_spesa",
            "importo",
            "categoria",
        ),
        "VALIDITY_NON_NUMERIC_ID": ("id_spesa",),
        "VALIDITY_INVALID_DATE": ("data_spesa",),
        "VALIDITY_NEGATIVE_AMOUNT": ("importo",),
        "VALIDITY_NON_NUMERIC_AMOUNT": ("importo",),
        "VALIDITY_INVALID_CATEGORY": ("categoria",),
        "STATISTICAL_AMOUNT_ANOMALY": ("categoria", "importo"),
        "STATISTICAL_NOT_EVALUABLE": ("categoria", "importo"),
        "POLICY_APPROVAL_REQUIRED": ("categoria", "importo"),
        "POLICY_MISSING_APPROVER": ("categoria", "importo", "approvatore"),
    }
)


@dataclass(frozen=True)
class ColumnMetadata:
    """Canonical, language-independent metadata for one input column."""

    name: str
    label_key: str
    description_key: str
    required: bool
    expected_type: str
    format_key: str
    example: str
    quality_dimensions: tuple[str, ...]


def _column(
    name: str,
    expected_type: str,
    format_key: str,
    example: str,
    quality_dimensions: tuple[str, ...],
) -> ColumnMetadata:
    return ColumnMetadata(
        name=name,
        label_key=f"column.{name}.label",
        description_key=f"column.{name}.description",
        required=name in REQUIRED_FIELDS,
        expected_type=expected_type,
        format_key=format_key,
        example=example,
        quality_dimensions=quality_dimensions,
    )


COLUMN_METADATA = (
    _column(
        "id_spesa",
        "integer",
        "format.progressive_integer",
        "100001",
        ("completeness", "validity", "uniqueness"),
    ),
    _column(
        "data_spesa",
        "date",
        "format.date_ddmmyyyy",
        "13/07/2026",
        ("completeness", "validity", "uniqueness"),
    ),
    _column(
        "dipendente",
        "text",
        "format.surname_name",
        "Cognome001 Nome001",
        ("completeness", "uniqueness"),
    ),
    _column(
        "centro_di_costo",
        "text",
        "format.not_specified",
        "CDC-001",
        (),
    ),
    _column(
        "categoria",
        "category",
        "format.allowed_category",
        "Vitto",
        (
            "completeness",
            "validity",
            "uniqueness",
            "statistical_anomaly",
            "policy_compliance",
        ),
    ),
    _column(
        "descrizione",
        "text",
        "format.free_text",
        "Pranzo di lavoro",
        (),
    ),
    _column(
        "importo",
        "decimal",
        "format.eur_decimal",
        "25.00",
        (
            "completeness",
            "validity",
            "uniqueness",
            "statistical_anomaly",
            "policy_compliance",
        ),
    ),
    _column(
        "valuta_originale",
        "text",
        "format.original_currency",
        "EUR",
        (),
    ),
    _column(
        "progetto",
        "project_code",
        "format.project_code",
        "PRJ-2026-001",
        ("completeness",),
    ),
    _column(
        "approvatore",
        "text",
        "format.not_specified",
        "Cognome002 Nome002",
        ("policy_compliance",),
    ),
)


def rules_for_column(column_name: str) -> tuple[str, ...]:
    """Return stable rule identifiers associated with one canonical column."""
    return tuple(
        rule_id
        for rule_id, target_fields in RULE_TARGET_FIELDS.items()
        if column_name in target_fields
    )
