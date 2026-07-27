"""Tests for deterministic semantic roles and accessible UI tokens."""

import pytest

from expense_quality_monitor.ui_theme import (
    SEMANTIC_ROLES,
    THEME_TOKENS,
    chart_color_for_status,
    role_icon,
    semantic_role_for_status,
    status_cell_style,
    theme_tokens,
)


@pytest.mark.parametrize(
    ("status", "expected_role"),
    [
        ("non conforme", "critical"),
        ("richiede approvazione", "warning"),
        ("anomalia statistica", "outlier"),
        ("non valutabile statisticamente", "neutral"),
        ("duplicato", "information"),
        ("valore futuro", "neutral"),
    ],
)
def test_statuses_map_to_semantic_roles(status: str, expected_role: str) -> None:
    assert semantic_role_for_status(status) == expected_role


def test_every_role_has_complete_light_and_dark_tokens() -> None:
    for theme in ("light", "dark"):
        assert set(THEME_TOKENS[theme]) == set(SEMANTIC_ROLES)
        for role in SEMANTIC_ROLES:
            assert set(theme_tokens(role, theme)) == {"foreground", "background", "border"}
            assert all(theme_tokens(role, theme).values())


def _relative_luminance(hex_color: str) -> float:
    channels = []
    for offset in (1, 3, 5):
        value = int(hex_color[offset : offset + 2], 16) / 255
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_role_tokens_meet_text_and_indicator_contrast_targets() -> None:
    for theme in ("light", "dark"):
        for role in SEMANTIC_ROLES:
            tokens = theme_tokens(role, theme)
            assert _contrast_ratio(tokens["foreground"], tokens["background"]) >= 4.5
            assert _contrast_ratio(tokens["border"], tokens["background"]) >= 3


def test_unknown_role_and_theme_fall_back_to_neutral_light() -> None:
    assert theme_tokens("unknown", "unknown") == theme_tokens("neutral", "light")


def test_icons_are_companions_to_text_not_language_dependent() -> None:
    assert role_icon("critical") == "⛔"
    assert role_icon("unknown") == role_icon("neutral")


def test_status_cell_style_uses_role_colors_without_hiding_text() -> None:
    style = status_cell_style("non conforme", "dark")

    assert theme_tokens("critical", "dark")["foreground"] in style
    assert theme_tokens("critical", "dark")["background"] in style
    assert "font-weight: 600" in style


def test_status_chart_uses_same_semantic_role_color() -> None:
    assert (
        chart_color_for_status("richiede approvazione", "light")
        == theme_tokens("warning", "light")["border"]
    )
