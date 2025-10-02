"""Integration test for the map view in the application."""

import os
from pathlib import Path
from unittest import mock

import pytest


def test_app_initialization_with_map():
    """Test that the app initializes with map view correctly."""
    from app import main
    
    # Create a mock page
    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800
    
    # Initialize the app
    app = main.CoordinateApp(mock_page)
    
    # Verify map view was created
    assert app.map_view is not None, "Map view was not created"
    
    # Verify map URL is provided as an inline base64 data URL
    map_url = app._map_url()
    assert map_url.startswith(
        "data:text/html;base64,"
    ), f"Map URL should be a base64 data URL, got: {map_url}"
    
    print(f"✓ App initialized successfully")
    print(f"  Map URL: {map_url}")


def test_map_view_properties():
    """Test that the map view has correct properties."""
    from app import main
    import flet as ft
    
    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800
    
    app = main.CoordinateApp(mock_page)
    
    # Check that map view has expand property
    assert app.map_view.expand is True, "Map view should have expand=True"
    
    # Check that map view URL uses inline data URL
    assert app.map_view.url.startswith("data:text/html;base64,"), \
        f"Map view URL should be a base64 data URL, got: {app.map_view.url}"
    
    print(f"✓ Map view properties are correct")


def test_map_ready_callback():
    """Test that map ready callback is set up."""
    from app import main
    
    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800
    
    app = main.CoordinateApp(mock_page)
    
    # Initially map should not be ready
    assert app.map_ready is False, "Map should not be ready initially"
    
    # Simulate page load completion
    app._handle_map_page_event(None)
    
    # Now map should be ready
    assert app.map_ready is True, "Map should be ready after page load event"
    
    print(f"✓ Map ready callback works correctly")


def test_map_center_update():
    """Test that map center can be updated."""
    from app import main
    
    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800
    
    app = main.CoordinateApp(mock_page)
    
    # Create a mock WebView with eval_js
    app.map_view.eval_js = mock.MagicMock()
    
    # Mark map as ready
    app.map_ready = True
    
    # Update map center
    test_lat, test_lon = 59.3293, 18.0686  # Stockholm
    app._update_map(test_lat, test_lon)
    
    # Verify eval_js was called with correct coordinates
    app.map_view.eval_js.assert_called_once()
    call_args = app.map_view.eval_js.call_args[0][0]
    assert "updateMapCenter" in call_args, "Should call updateMapCenter function"
    assert str(test_lat) in call_args, f"Latitude {test_lat} should be in call"
    assert str(test_lon) in call_args, f"Longitude {test_lon} should be in call"
    
    print(f"✓ Map center update works correctly")
    print(f"  JavaScript call: {call_args}")


def test_map_update_before_ready():
    """Test that map update is safe when map is not ready."""
    from app import main

    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800
    
    app = main.CoordinateApp(mock_page)
    
    # Create a mock WebView with eval_js
    app.map_view.eval_js = mock.MagicMock()
    
    # Map is not ready (default state)
    assert app.map_ready is False
    
    # Try to update map center
    app._update_map(59.3293, 18.0686)
    
    # eval_js should NOT have been called
    app.map_view.eval_js.assert_not_called()
    
    print(f"✓ Map update is safely skipped when map is not ready")


def test_double_click_capture_does_not_pan_map():
    """Double-click capture should not trigger a map pan."""
    from app import main

    mock_page = mock.MagicMock()
    mock_page.window_width = 1200
    mock_page.window_height = 800

    app = main.CoordinateApp(mock_page)

    app.map_ready = True
    app._invoke_map_js = mock.MagicMock(return_value=True)

    app._set_input_coordinate_from_latlon(10.0, 20.0)

    app._invoke_map_js.assert_not_called()

    app._update_map(11.0, 22.0)

    app._invoke_map_js.assert_called_once()

    print("✓ Map stays put when capturing coordinates from double-click")


def test_webview_deprecation_notice():
    """Display information about WebView deprecation."""
    import flet as ft

    # Check if flet-webview is available
    try:
        import flet_webview
        print(f"✓ flet-webview package is installed")
        has_new_package = True
    except ImportError:
        print(f"⚠ flet-webview package is NOT installed")
        print(f"  Note: WebView is deprecated in Flet and will be removed in v0.29.0")
        print(f"  Consider installing: pip install flet-webview")
        has_new_package = False
    
    # Check Flet version
    flet_version = getattr(ft, "__version__", "unknown")
    print(f"  Flet version: {flet_version}")
    
    # If using deprecated WebView, suggest upgrade
    if not has_new_package:
        print(f"\n  Migration steps:")
        print(f"  1. Install: uv pip install flet-webview")
        print(f"  2. Import: from flet_webview import WebView")
        print(f"  3. Use: WebView instead of ft.WebView")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
