"""Import and confirmed-configuration checks for the package scaffold."""

import expense_quality_monitor
from expense_quality_monitor import config


def test_package_and_confirmed_configuration_are_available() -> None:
    assert expense_quality_monitor.__name__ == "expense_quality_monitor"

    expected_constants = (
        "EXPECTED_COLUMNS",
        "REQUIRED_FIELDS",
        "VALID_CATEGORIES",
        "POLICY_THRESHOLDS",
        "MIN_STATISTICAL_OBSERVATIONS",
        "MEDIAN_MULTIPLIER",
    )
    assert all(hasattr(config, name) for name in expected_constants)
    assert len(config.EXPECTED_COLUMNS) == 10
    assert len(config.VALID_CATEGORIES) == 6
