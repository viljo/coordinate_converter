"""
Reusable UI components for Coordinate Converter
with built-in tab order support and consistent
coordinate field generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

import flet as ft
import src.ui.theme as theme
import src.ui.styles as styles


CoordinateFieldKind = Literal["angular", "linear", "grid", "height"]


@dataclass(frozen=True)
class CoordinateFieldSpec:
    """Configuration describing a coordinate field."""

    label: str
    unit: str = ""
    kind: CoordinateFieldKind = "linear"


def _field_width(kind: CoordinateFieldKind) -> int | None:
    mapping: dict[CoordinateFieldKind, int] = {
        "angular": theme.FIELD_WIDTH_ANGULAR,
        "linear": theme.FIELD_WIDTH_LINEAR,
        "grid": theme.FIELD_WIDTH_GRID,
        "height": theme.FIELD_WIDTH_HEIGHT,
    }
    return mapping.get(kind)


class Card(ft.Container):
    def __init__(self, title: str, content: list[ft.Control]):
        super().__init__(
            content=ft.Column(
                [
                    ft.Text(title, style=styles.TITLE),
                    *content,
                ],
                spacing=theme.SPACING_SM,
            ),
            bgcolor=theme.CARD_BACKGROUND,
            padding=theme.SPACING_MD,
            border_radius=theme.RADIUS_MD,
            shadow=theme.CARD_SHADOW,
            expand=True,
        )


class LabelledField(ft.Column):
    def __init__(
        self,
        label: str,
        value: str = "",
        unit: str = "",
        error: str | None = None,
        tab_index: int | None = None,
        width: int | None = None,
    ) -> None:
        """
        A field with label, value, optional unit, and error state.
        Supports tab_index for proper traversal order.
        """

        # Input field (focusable)
        field = ft.TextField(
            value=value,
            label=f"{label}{f' ({unit})' if unit else ''}",
            width=width,
        )
        if tab_index is not None:
            field.tab_index = tab_index

        controls: list[ft.Control] = [field]

        if error:
            controls.append(ft.Text(error, style=styles.ERROR))

        super().__init__(controls, spacing=theme.SPACING_XS)
        self.field = field  # Expose inner field for programmatic focus


def ErrorMessage(text: str) -> ft.Text:
    return ft.Text(text, style=styles.ERROR)


def build_coordinate_fields(
    specs: Iterable[CoordinateFieldSpec],
    *,
    start_tab_index: int = 1,
) -> list[LabelledField]:
    """Create fields from shared specs to guarantee identical formatting."""

    fields: list[LabelledField] = []
    tab_index = start_tab_index

    for spec in specs:
        field = LabelledField(
            label=spec.label,
            unit=spec.unit,
            tab_index=tab_index,
            width=_field_width(spec.kind),
        )
        fields.append(field)
        tab_index += 1

    return fields
