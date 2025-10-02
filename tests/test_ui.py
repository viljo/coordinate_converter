"""
UI component tests for Coordinate Converter
Includes tab order validation.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import flet as ft
from src.app.components import Card, LabelledField
import src.ui.layout as layout
import src.ui.theme as theme


def test_card_renders_with_title():
    card = Card("WGS84", [LabelledField("Latitude", "59.3", "°", tab_index=1)])
    assert isinstance(card.content, ft.Column)
    assert any(isinstance(c, ft.Text) and c.value == "WGS84" for c in card.content.controls)


def test_labelled_field_with_unit():
    field = LabelledField("Latitude", "59.3", "°", tab_index=1)
    assert isinstance(field.field, ft.TextField)
    assert field.field.tab_index == 1


def test_labelled_field_with_error():
    field = LabelledField("Longitude", "18.0", "°", error="Invalid", tab_index=2)
    assert any(isinstance(c, ft.Text) and c.value == "Invalid" for c in field.controls)
    assert field.field.tab_index == 2


def test_card_grid_responsiveness_and_auto_tab():
    fields1 = [LabelledField("Lat", "59.3", "°"), LabelledField("Lon", "18.0", "°")]
    fields2 = [LabelledField("Northing", "6583052", "m")]
    cards = [Card("WGS84", fields1), Card("SWEREF99", fields2)]

    grid = layout.card_grid(cards, auto_tab=True)

    assert isinstance(grid, ft.ResponsiveRow)

    indices = [f.field.tab_index for f in fields1 + fields2]
    assert indices == [1, 2, 3], "Tab indices must be sequential"


def test_page_wrapper_applies_background_and_padding():
    content = ft.Text("dummy")
    wrapped = layout.page_wrapper(content)
    assert wrapped.bgcolor == theme.BACKGROUND_COLOR
    assert wrapped.padding == theme.SPACING_LG
