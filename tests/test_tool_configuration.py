"""Tests for quality-tool exclusions that protect review coverage."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generator_exclusion_is_limited_to_formatter() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        configuration = tomllib.load(handle)

    ruff = configuration["tool"]["ruff"]
    assert "exclude" not in ruff
    assert "extend-exclude" not in ruff
    assert ruff["format"]["exclude"] == ["scripts/generate_dataset.py"]
    assert all(path not in ruff["format"]["exclude"] for path in ("src", "tests"))
