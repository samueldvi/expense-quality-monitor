"""Smoke tests for the Streamlit dashboard."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from app import counts_to_frame

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_starts_with_required_upload_guidance() -> None:
    app = AppTest.from_file(ROOT / "app.py").run()

    assert not app.exception
    assert app.title[0].value == "Expense Quality Monitor"
    assert len(app.get("file_uploader")) == 1
    assert any("esclusivamente dati sintetici" in message.value.lower() for message in app.info)


def test_counts_to_frame_orders_values_and_preserves_columns() -> None:
    result = counts_to_frame({"zeta": 2, "alfa": 1}, "Stato")

    assert result.columns.tolist() == ["Stato", "Conteggio"]
    assert result.to_dict("records") == [
        {"Stato": "alfa", "Conteggio": 1},
        {"Stato": "zeta", "Conteggio": 2},
    ]


def test_counts_to_frame_preserves_columns_when_empty() -> None:
    result = counts_to_frame({}, "Tipo di anomalia")

    assert result.empty
    assert result.columns.tolist() == ["Tipo di anomalia", "Conteggio"]
