"""Semantic visual roles shared by the dashboard presentation layer."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

SEMANTIC_ROLES = (
    "critical",
    "warning",
    "success",
    "information",
    "outlier",
    "neutral",
)

STATUS_ROLES: Mapping[str, str] = MappingProxyType(
    {
        "non conforme": "critical",
        "richiede approvazione": "warning",
        "anomalia statistica": "outlier",
        "non valutabile statisticamente": "neutral",
        "incompleta": "information",
        "duplicato": "information",
        "duplicato logico": "information",
        "non valido": "information",
        "non valida": "information",
    }
)

ROLE_ICONS: Mapping[str, str] = MappingProxyType(
    {
        "critical": "⛔",
        "warning": "⚠",
        "success": "✓",
        "information": "ℹ",
        "outlier": "◈",
        "neutral": "•",
    }
)

THEME_TOKENS: Mapping[str, Mapping[str, Mapping[str, str]]] = MappingProxyType(
    {
        "light": MappingProxyType(
            {
                "critical": MappingProxyType(
                    {"foreground": "#991B1B", "background": "#FEF2F2", "border": "#DC2626"}
                ),
                "warning": MappingProxyType(
                    {"foreground": "#854D0E", "background": "#FFFBEB", "border": "#D97706"}
                ),
                "success": MappingProxyType(
                    {"foreground": "#166534", "background": "#F0FDF4", "border": "#16A34A"}
                ),
                "information": MappingProxyType(
                    {"foreground": "#1E3A8A", "background": "#EFF6FF", "border": "#2563EB"}
                ),
                "outlier": MappingProxyType(
                    {"foreground": "#6B21A8", "background": "#FAF5FF", "border": "#9333EA"}
                ),
                "neutral": MappingProxyType(
                    {"foreground": "#374151", "background": "#F9FAFB", "border": "#6B7280"}
                ),
            }
        ),
        "dark": MappingProxyType(
            {
                "critical": MappingProxyType(
                    {"foreground": "#FCA5A5", "background": "#450A0A", "border": "#F87171"}
                ),
                "warning": MappingProxyType(
                    {"foreground": "#FDE68A", "background": "#422006", "border": "#FBBF24"}
                ),
                "success": MappingProxyType(
                    {"foreground": "#BBF7D0", "background": "#052E16", "border": "#4ADE80"}
                ),
                "information": MappingProxyType(
                    {"foreground": "#BFDBFE", "background": "#172554", "border": "#60A5FA"}
                ),
                "outlier": MappingProxyType(
                    {"foreground": "#E9D5FF", "background": "#3B0764", "border": "#C084FC"}
                ),
                "neutral": MappingProxyType(
                    {"foreground": "#E5E7EB", "background": "#1F2937", "border": "#9CA3AF"}
                ),
            }
        ),
    }
)


def semantic_role_for_status(status: object) -> str:
    """Return the semantic role for a canonical status."""
    return STATUS_ROLES.get(str(status), "neutral")


def role_icon(role: str) -> str:
    """Return an accessible companion icon for a semantic role."""
    return ROLE_ICONS.get(role, ROLE_ICONS["neutral"])


def theme_tokens(role: str, theme: str) -> Mapping[str, str]:
    """Return immutable visual tokens, falling back to neutral light styling."""
    normalized_theme = theme if theme in THEME_TOKENS else "light"
    normalized_role = role if role in SEMANTIC_ROLES else "neutral"
    return THEME_TOKENS[normalized_theme][normalized_role]


def status_cell_style(status: object, theme: str) -> str:
    """Return compact, theme-aware CSS for one status table cell."""
    tokens = theme_tokens(semantic_role_for_status(status), theme)
    return (
        f"color: {tokens['foreground']}; "
        f"background-color: {tokens['background']}; "
        f"border-left: 3px solid {tokens['border']}; "
        "font-weight: 600"
    )


def chart_color_for_status(status: object, theme: str) -> str:
    """Return the semantic border color used by status charts."""
    role = semantic_role_for_status(status)
    return theme_tokens(role, theme)["border"]
