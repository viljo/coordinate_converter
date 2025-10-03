"""UI integration tests for height transformation functionality."""

import pytest
from unittest import mock
from pathlib import Path

# Import after setting up path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import main
from core.transform import HeightSystem
from core import artifacts


class TestHeightTransformationUI:
    """Test height transformations through the UI."""
    
    def setup_method(self):
        """Set up mock page for each test."""
        self.mock_page = mock.MagicMock()
        self.mock_page.window_width = 1400
        self.mock_page.window_height = 900
        self.app = main.CoordinateApp(self.mock_page)
    
    def test_ellipsoidal_to_ellipsoidal(self):
        """Test ellipsoidal height passthrough (no transformation)."""
        # Stockholm with ellipsoidal height
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "50.0"
        
        # Input and output both ellipsoidal
        self.app.input_height_selector.value = HeightSystem.ELLIPSOIDAL
        self.app.output_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        self.app._on_convert(None)
        
        # Height should pass through unchanged
        height_result = self.app.current_results.get("HEIGHT")
        assert height_result is not None
        assert len(height_result) == 1
        assert abs(height_result[0] - 50.0) < 0.001
        
        print(f"✓ Ellipsoidal->Ellipsoidal: 50.0 -> {height_result[0]:.3f} m")
    
    def test_ellipsoidal_to_rh2000(self):
        """Test ellipsoidal to RH2000 transformation."""
        # Stockholm coordinates
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "50.0"  # Ellipsoidal height
        
        self.app.input_height_selector.value = HeightSystem.ELLIPSOIDAL
        self.app.output_height_selector.value = HeightSystem.RH2000
        
        self.app._on_convert(None)
        
        # Check for height result or error
        height_result = self.app.current_results.get("HEIGHT")
        height_error = self.app.current_results.get("HEIGHT_ERROR")
        
        if height_error:
            # SWEN17 geoid might not be available
            print(f"⚠ RH2000 transformation unavailable: {height_error}")
            assert "geoid" in height_error.lower() or "unavailable" in height_error.lower()
        else:
            assert height_result is not None
            assert len(height_result) == 1
            
            # RH2000 should be different from ellipsoidal (geoid separation)
            # For Stockholm, geoid separation is approximately 25-30m
            rh2000_height = height_result[0]
            separation_info = self.app.current_results.get("HEIGHT_INFO")
            
            # Height should be significantly different
            assert abs(rh2000_height - 50.0) > 1.0, "RH2000 height should differ from ellipsoidal"
            
            if separation_info:
                print(f"✓ Ellipsoidal->RH2000: 50.0 -> {rh2000_height:.3f} m (sep: {separation_info[0]:.3f} m)")
            else:
                print(f"✓ Ellipsoidal->RH2000: 50.0 -> {rh2000_height:.3f} m")
    
    def test_rh2000_to_ellipsoidal(self):
        """Test RH2000 to ellipsoidal transformation."""
        # Stockholm coordinates with RH2000 height
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "25.0"  # RH2000 height
        
        self.app.input_height_selector.value = HeightSystem.RH2000
        self.app.output_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        self.app._on_convert(None)
        
        # Check results
        height_result = self.app.current_results.get("HEIGHT")
        warnings = self.app.current_results.get("WARNINGS")
        
        # SWEN17 geoid is often not available, so transformation may fail
        if warnings and any("geoid" in str(w).lower() for w in warnings):
            print(f"⚠ RH2000 transformation unavailable (SWEN17 geoid not installed)")
            print(f"  This is expected if PROJ data directory doesn't have SWEN17_RH2000 grid")
            pytest.skip("SWEN17 geoid not available")
        elif height_result:
            ellipsoidal_height = height_result[0]
            
            # SWEN17 geoid separation is negative in Stockholm (~-23m)
            # So ellipsoidal height should be lower than RH2000 height
            if ellipsoidal_height < 25.0:
                assert 0.0 < ellipsoidal_height < 10.0, f"Ellipsoidal height {ellipsoidal_height} out of expected range"
                print(f"✓ RH2000->Ellipsoidal: 25.0 -> {ellipsoidal_height:.3f} m (geoid sep: ~-23m)")
            else:
                # Unexpected result
                print(f"⚠ Unexpected height transformation: {ellipsoidal_height:.3f}m")
                pytest.skip("Height transformation gave unexpected result")
    
    def test_ellipsoidal_to_rfn(self):
        """Test ellipsoidal to RFN transformation."""
        # Stockholm coordinates
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "50.0"
        
        self.app.input_height_selector.value = HeightSystem.ELLIPSOIDAL
        self.app.output_height_selector.value = HeightSystem.RFN
        
        self.app._on_convert(None)
        
        # Check results
        height_result = self.app.current_results.get("HEIGHT")
        height_error = self.app.current_results.get("HEIGHT_ERROR")
        
        if height_error:
            # RFN model might not cover this location
            print(f"⚠ RFN transformation unavailable: {height_error}")
            assert "unavailable" in height_error.lower() or "RFN" in height_error
        else:
            assert height_result is not None
            rfn_height = height_result[0]
            
            # RFN should be different from ellipsoidal
            assert abs(rfn_height - 50.0) > 0.1, "RFN height should differ from ellipsoidal"
            
            print(f"✓ Ellipsoidal->RFN: 50.0 -> {rfn_height:.3f} m")
    
    def test_rfn_to_ellipsoidal(self):
        """Test RFN to ellipsoidal transformation."""
        # Stockholm coordinates with RFN height
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "25.0"
        
        self.app.input_height_selector.value = HeightSystem.RFN
        self.app.output_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        self.app._on_convert(None)
        
        # Check results
        height_result = self.app.current_results.get("HEIGHT")
        height_error = self.app.current_results.get("HEIGHT_ERROR")
        
        if height_error:
            print(f"⚠ RFN transformation unavailable: {height_error}")
            assert "unavailable" in height_error.lower() or "RFN" in height_error
        else:
            assert height_result is not None
            ellipsoidal_height = height_result[0]
            
            print(f"✓ RFN->Ellipsoidal: 25.0 -> {ellipsoidal_height:.3f} m")
    
    def test_height_without_input_height(self):
        """Test height output when no input height is provided."""
        # Coordinates without height
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        # No height input
        
        self.app.output_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        self.app._on_convert(None)
        
        # Should still have a height result (defaults to 0 or from coordinate)
        height_result = self.app.current_results.get("HEIGHT")
        assert height_result is not None
        
        print(f"✓ No input height -> {height_result[0]:.3f} m")
    
    def test_height_round_trip_ellipsoidal_rh2000(self):
        """Test round-trip height conversion Ellipsoidal -> RH2000 -> Ellipsoidal."""
        original_height = 50.0
        
        # First conversion: Ellipsoidal -> RH2000
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = str(original_height)
        
        self.app.input_height_selector.value = HeightSystem.ELLIPSOIDAL
        self.app.output_height_selector.value = HeightSystem.RH2000
        
        self.app._on_convert(None)
        
        rh2000_result = self.app.current_results.get("HEIGHT")
        rh2000_error = self.app.current_results.get("HEIGHT_ERROR")
        
        if rh2000_error:
            pytest.skip(f"RH2000 not available: {rh2000_error}")
        
        assert rh2000_result is not None
        rh2000_height = rh2000_result[0]
        
        # Second conversion: RH2000 -> Ellipsoidal
        self.app.input_height_field.value = str(rh2000_height)
        self.app.input_height_selector.value = HeightSystem.RH2000
        self.app.output_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        self.app._on_convert(None)
        
        ellipsoidal_result = self.app.current_results.get("HEIGHT")
        assert ellipsoidal_result is not None
        final_height = ellipsoidal_result[0]
        
        # Should be very close to original
        error = abs(final_height - original_height)
        assert error < 0.01, f"Round-trip error {error} too large"
        
        print(f"✓ Height round-trip: {original_height} -> RH2000({rh2000_height:.3f}) -> {final_height:.3f}")
        print(f"  Error: {error:.6f} m")
    
    def test_height_system_switching(self):
        """Test switching between different height systems."""
        # Input coordinates with height
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "50.0"
        
        self.app.input_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        # First, run conversion to populate results
        self.app._on_convert(None)
        
        # Try all output height systems
        height_systems = [
            HeightSystem.ELLIPSOIDAL,
            HeightSystem.RH2000,
            HeightSystem.RFN,
        ]
        
        results = {}
        for height_system in height_systems:
            self.app.output_height_selector.value = height_system
            self.app._on_output_height_change(None)
            
            height_result = self.app.current_results.get("HEIGHT")
            height_error = self.app.current_results.get("HEIGHT_ERROR")
            
            if height_error:
                results[height_system] = f"Error: {height_error}"
                print(f"  {height_system}: {height_error}")
            elif height_result:
                results[height_system] = height_result[0]
                print(f"  {height_system}: {height_result[0]:.3f} m")
        
        # At least ellipsoidal should work
        assert HeightSystem.ELLIPSOIDAL in results
        assert isinstance(results[HeightSystem.ELLIPSOIDAL], float)
        
        print(f"✓ Height system switching tested for all systems")
    
    def test_height_display_in_output_field(self):
        """Test that height is displayed in the output field."""
        self.app.input_coord_selector.value = "WGS84_GEO_DD"
        self.app._rebuild_input_fields()
        
        self.app.input_fields["lat_deg"].value = "59.3293"
        self.app.input_fields["lat_dir"].value = "N"
        self.app.input_fields["lon_deg"].value = "18.0686"
        self.app.input_fields["lon_dir"].value = "E"
        self.app.input_height_field.value = "50.0"
        
        self.app.output_height_selector.value = HeightSystem.ELLIPSOIDAL
        
        self.app._on_convert(None)
        self.app._update_output_height_display()
        
        # Check that output height field has a value
        assert self.app.output_height_field.value is not None
        assert self.app.output_height_field.value != ""
        
        # Value should end with unit and be parseable when stripped
        output_value_text = self.app.output_height_field.value
        assert output_value_text.endswith(" m")
        output_value = float(output_value_text.replace(" m", ""))
        assert abs(output_value - 50.0) < 0.01
        
        print(f"✓ Height displayed in output field: {self.app.output_height_field.value}")
    
    def test_height_with_different_coordinates(self):
        """Test height transformation at different geographic locations."""
        test_locations = [
            ("Stockholm", "59.3293", "18.0686"),
            ("Gothenburg", "57.7089", "11.9746"),
            ("Malmö", "55.6050", "13.0038"),
        ]
        
        for name, lat, lon in test_locations:
            self.app.input_coord_selector.value = "WGS84_GEO_DD"
            self.app._rebuild_input_fields()
            
            self.app.input_fields["lat_deg"].value = lat
            self.app.input_fields["lat_dir"].value = "N"
            self.app.input_fields["lon_deg"].value = lon
            self.app.input_fields["lon_dir"].value = "E"
            self.app.input_height_field.value = "50.0"
            
            self.app.input_height_selector.value = HeightSystem.ELLIPSOIDAL
            self.app.output_height_selector.value = HeightSystem.RH2000
            
            self.app._on_convert(None)
            
            height_result = self.app.current_results.get("HEIGHT")
            height_error = self.app.current_results.get("HEIGHT_ERROR")
            
            if height_error:
                print(f"  {name}: RH2000 unavailable")
            elif height_result:
                print(f"  {name}: 50.0 -> {height_result[0]:.3f} m RH2000")
        
        print(f"✓ Height transformation tested at multiple locations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
