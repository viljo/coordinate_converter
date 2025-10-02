from __future__ import annotations

from unittest import mock

from app import main


def _create_app() -> main.CoordinateApp:
    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800
    with mock.patch("app.main.artifacts.ensure_runtime_artifacts", return_value=[]):
        app = main.CoordinateApp(mock_page)
    return app


def test_ddm_copy_uses_standardised_format():
    app = _create_app()
    app.output_coord_selector.value = "WGS84_GEO_DDM"
    app._rebuild_output_fields()

    app.output_fields["lat_dir"].value = "N"
    app.output_fields["lat_deg"].value = "59"
    app.output_fields["lat_min"].value = "30.1234"
    app.output_fields["lon_dir"].value = "E"
    app.output_fields["lon_deg"].value = "18"
    app.output_fields["lon_min"].value = "45.6789"

    lat_formatted = app._format_output_angle("DDM", "lat")
    lon_formatted = app._format_output_angle("DDM", "lon")

    assert lat_formatted == "59deg30.1234'N"
    assert lon_formatted == "018deg45.6789'E"
    assert app._collect_selected_output_values() == "59deg30.1234'N,018deg45.6789'E"


def test_dms_copy_uses_standardised_format():
    app = _create_app()
    app.output_coord_selector.value = "WGS84_GEO_DMS"
    app._rebuild_output_fields()

    app.output_fields["lat_dir"].value = "N"
    app.output_fields["lat_deg"].value = "59"
    app.output_fields["lat_min"].value = "30"
    app.output_fields["lat_sec"].value = "15.2"
    app.output_fields["lon_dir"].value = "E"
    app.output_fields["lon_deg"].value = "18"
    app.output_fields["lon_min"].value = "45"
    app.output_fields["lon_sec"].value = "5.1"

    lat_formatted = app._format_output_angle("DMS", "lat")
    lon_formatted = app._format_output_angle("DMS", "lon")

    assert lat_formatted == "59deg30'15.20\"N"
    assert lon_formatted == "018deg45'05.10\"E"
    assert app._collect_selected_output_values() == "59deg30'15.20\"N,018deg45'05.10\"E"
