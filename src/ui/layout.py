"""
Responsive layout helpers for Coordinate Converter UI
with auto tab-index assignment.
"""

from __future__ import annotations

import flet as ft
import src.ui.theme as theme
from src.app.components import Card, LabelledField


def assign_tab_indices(cards: list[Card], start_index: int = 1) -> list[Card]:
    """
    Assign sequential tab_index values to all LabelledField children.
    """
    counter = start_index
    for card in cards:
        if not isinstance(card.content, ft.Column):
            continue
        for ctrl in card.content.controls:
            if isinstance(ctrl, LabelledField):
                ctrl.field.tab_index = counter
                counter += 1
    return cards


def card_grid(cards: list[Card], auto_tab: bool = True) -> ft.ResponsiveRow:
    """
    Arrange cards in a responsive grid with auto-tab assignment.
    """
    if auto_tab:
        cards = assign_tab_indices(cards)

    return ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=card,
                col={"xs": 12, "sm": 6, "md": 4},
                padding=theme.SPACING_SM,
            )
            for card in cards
        ],
        run_spacing=theme.SPACING_MD,
        spacing=theme.SPACING_MD,
    )


def page_wrapper(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        padding=theme.SPACING_LG,
        bgcolor=theme.BACKGROUND_COLOR,
        expand=True,
    )
