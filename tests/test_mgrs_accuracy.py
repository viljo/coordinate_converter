"""Tests for MGRS accuracy labels."""

from __future__ import annotations

from unittest import mock


def _make_app():
    from app import main

    page = mock.MagicMock()
    page.window_width = 1200
    page.window_height = 800
    return main.CoordinateApp(page)


def _set_mgrs_value(app, value: str) -> None:
    app.input_coord_selector.value = "MGRS"
    app._rebuild_input_fields()
    app.input_fields["mgrs"].value = value


def test_mgrs_accuracy_for_all_supported_precisions():
    app = _make_app()

    cases = [
        ("33UXP", "±100000 m"),
        ("33UXP04", "±10000 m"),
        ("33UXP0481", "±1000 m"),
        ("33UXP048114", "±100 m"),
        ("33UXP04811421", "±10 m"),
        ("33UXP0481142198", "±1 m"),
    ]

    for value, expected in cases:
        _set_mgrs_value(app, value)
        assert app._accuracy_for_mgrs_field() == expected


def test_mgrs_accuracy_hidden_for_invalid_values():
    app = _make_app()

    invalid_values = [
        "",  # empty
        "  ",  # whitespace
        "33",  # missing grid letters
        "33UAA1",  # odd number of digits
        "33UXP000000000000",  # too many digits
        "33UX?0481",  # illegal character
    ]

    for value in invalid_values:
        _set_mgrs_value(app, value)
        assert app._accuracy_for_mgrs_field() is None
