"""
Reusable UI components for Coordinate Converter
with built-in tab order support
"""

from __future__ import annotations

import flet as ft
import src.ui.theme as theme
import src.ui.styles as styles


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
    ) -> None:
        """
        A field with label, value, optional unit, and error state.
        Supports tab_index for proper traversal order.
        """

        # Input field (focusable)
        field = ft.TextField(
            value=value,
            label=f"{label}{f' ({unit})' if unit else ''}",
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
