"""
UI Builder Module - Builds UI components according to UI_SPECIFICATION.md

This module provides a clean, specification-compliant way to build UI components.
All components follow the strict rules defined in UI_SPECIFICATION.md.
"""

import flet as ft
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class FieldSpec:
    """Specification for a single field."""
    name: str
    label: str
    width: int
    default_value: str = ""
    read_only: bool = False
    multiline: bool = False
    text_align: Optional[ft.TextAlign] = None


class UIBuilder:
    """
    Builds UI components according to UI_SPECIFICATION.md.
    
    MANDATORY RULES:
    1. ALL TextFields MUST have a label (in frame)
    2. NO hint_text or placeholder inside boxes
    3. Boxes start empty (except direction defaults)
    4. Consistent widths: 80px (coords/dirs), 180px (height)
    """
    
    # Field widths per specification
    COORD_FIELD_WIDTH = 159  # DD boxes increased by 50%
    DIRECTION_FIELD_WIDTH = 60
    HEIGHT_FIELD_WIDTH = 108  # Reduced by 40%
    
    @staticmethod
    def create_coordinate_field(
        label: str,
        name: str,
        autofocus: bool = False,
        read_only: bool = False,
        on_focus: Optional[Callable] = None,
        on_blur: Optional[Callable] = None,
        on_change: Optional[Callable] = None,
    ) -> ft.TextField:
        """
        Create a coordinate input field (degrees, minutes, or seconds).
        
        Per specification:
        - Label in frame (outside box)
        - Width: 159px
        - Box starts empty
        - NO hint_text
        """
        field = ft.TextField(
            label=label,  # MUST have label
            width=UIBuilder.COORD_FIELD_WIDTH,
            autofocus=autofocus,
            read_only=read_only,
        )
        if read_only:
            field.text_style = ft.TextStyle(weight=ft.FontWeight.BOLD)
        if on_focus:
            field.on_focus = on_focus
        if on_blur:
            field.on_blur = on_blur
        if on_change:
            field.on_change = on_change
        return field
    
    @staticmethod
    def create_direction_field(
        label: str,
        name: str,
        default_value: str,
        read_only: bool = False,
        on_change: Optional[Callable] = None,
    ) -> ft.TextField:
        """
        Create a direction input field (N/S or E/W).
        
        Per specification:
        - Label in frame: "N/S" or "E/W"
        - Width: 60px
        - Default value: "N" or "E"
        - Center-aligned text
        - NO hint_text
        """
        field = ft.TextField(
            label=label,  # MUST have label
            value=default_value,
            width=UIBuilder.DIRECTION_FIELD_WIDTH,
            text_align=ft.TextAlign.CENTER,
            read_only=read_only,
        )
        if read_only:
            field.text_style = ft.TextStyle(weight=ft.FontWeight.BOLD)
        if on_change:
            field.on_change = on_change
        return field
    
    @staticmethod
    def create_height_field(
        read_only: bool = False,
        on_focus: Optional[Callable] = None,
        on_blur: Optional[Callable] = None,
        on_change: Optional[Callable] = None,
    ) -> ft.TextField:
        """
        Create a height field.
        
        Per specification:
        - Label: "Height (m)" (system shown in dropdown)
        - Width: 180px
        - Box starts empty
        - NO hint_text
        """
        field = ft.TextField(
            label="Height (m)",  # MUST have label
            width=UIBuilder.HEIGHT_FIELD_WIDTH,
            read_only=read_only,
            helper_text="",
        )
        if on_focus:
            field.on_focus = on_focus
        if on_blur:
            field.on_blur = on_blur
        if on_change:
            field.on_change = on_change
        return field
    
    @staticmethod
    def create_coordinate_row(
        fields: List[ft.TextField],
        label: str,
        spacing: int = 8,
    ) -> Tuple[ft.Text, ft.Row]:
        """
        Create a coordinate row with label above.
        
        Per specification:
        - Row label: "Latitude:" or "Longitude:" above the fields
        - Fields arranged horizontally (tab goes right)
        - Spacing: 8px between fields
        - All field labels on TextField borders
        
        Returns:
            Tuple of (label_widget, row_widget)
        """
        # Ensure tab order is the same as fields list and skip read-only by disabling focus
        for f in fields:
            if isinstance(f, ft.TextField) and f.read_only:
                f.can_reveal_password = False  # no-op; maintain editability flags
                try:
                    setattr(f, "focusable", False)
                except Exception:
                    pass
        label_widget = ft.Text(label, style=ft.TextThemeStyle.BODY_MEDIUM)
        row_widget = ft.Row(controls=fields, spacing=spacing, alignment=ft.MainAxisAlignment.START)
        return label_widget, row_widget
    
    @staticmethod
    def build_dd_input_fields(
        field_registry: Dict[str, ft.TextField],
        on_focus: Callable,
        on_blur: Callable,
        on_change: Callable,
    ) -> List[ft.Control]:
        """
        Build DD format input fields.
        
        Structure:
        - Latitude: [N/S] [Lat Degrees]
        - Longitude: [E/W] [Lon Degrees]
        
        Tab order: lat_deg → lat_dir → lon_deg → lon_dir
        """
        controls = []
        
        # Latitude row: N/S first, then degrees
        lat_dir = UIBuilder.create_direction_field(
            "Lat N/S", "lat_dir", "N", on_change=on_change
        )
        lat_deg = UIBuilder.create_coordinate_field(
            "Lat Degrees", "lat_deg", autofocus=True,
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        
        field_registry["lat_deg"] = lat_deg
        field_registry["lat_dir"] = lat_dir
        
        lat_label, lat_row = UIBuilder.create_coordinate_row([lat_dir, lat_deg], "Latitude:")
        controls.extend([lat_label, lat_row])
        
        # Longitude row: E/W first, then degrees
        lon_dir = UIBuilder.create_direction_field(
            "Lon E/W", "lon_dir", "E", on_change=on_change
        )
        lon_deg = UIBuilder.create_coordinate_field(
            "Lon Degrees", "lon_deg",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        
        field_registry["lon_deg"] = lon_deg
        field_registry["lon_dir"] = lon_dir
        
        lon_label, lon_row = UIBuilder.create_coordinate_row([lon_dir, lon_deg], "Longitude:")
        controls.extend([lon_label, lon_row])
        
        return controls
    
    @staticmethod
    def build_ddm_input_fields(
        field_registry: Dict[str, ft.TextField],
        on_focus: Callable,
        on_blur: Callable,
        on_change: Callable,
    ) -> List[ft.Control]:
        """
        Build DDM format input fields.
        
        Structure:
        - Latitude: [N/S] [Lat Degrees] [Lat Minutes]
        - Longitude: [E/W] [Lon Degrees] [Lon Minutes]
        
        Tab order: lat_deg → lat_min → lat_dir → lon_deg → lon_min → lon_dir
        """
        controls = []
        
        # Latitude row: N/S first, then degrees, then minutes
        lat_dir = UIBuilder.create_direction_field(
            "Lat N/S", "lat_dir", "N", on_change=on_change
        )
        lat_deg = UIBuilder.create_coordinate_field(
            "Lat Degrees", "lat_deg", autofocus=True,
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        lat_min = UIBuilder.create_coordinate_field(
            "Lat Minutes", "lat_min",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        
        field_registry["lat_deg"] = lat_deg
        field_registry["lat_min"] = lat_min
        field_registry["lat_dir"] = lat_dir
        
        lat_label, lat_row = UIBuilder.create_coordinate_row([lat_dir, lat_deg, lat_min], "Latitude:")
        controls.extend([lat_label, lat_row])
        
        # Longitude row: E/W first, then degrees, then minutes
        lon_dir = UIBuilder.create_direction_field(
            "Lon E/W", "lon_dir", "E", on_change=on_change
        )
        lon_deg = UIBuilder.create_coordinate_field(
            "Lon Degrees", "lon_deg",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        lon_min = UIBuilder.create_coordinate_field(
            "Lon Minutes", "lon_min",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        
        field_registry["lon_deg"] = lon_deg
        field_registry["lon_min"] = lon_min
        field_registry["lon_dir"] = lon_dir
        
        lon_label, lon_row = UIBuilder.create_coordinate_row([lon_dir, lon_deg, lon_min], "Longitude:")
        controls.extend([lon_label, lon_row])
        
        return controls
    
    @staticmethod
    def build_dms_input_fields(
        field_registry: Dict[str, ft.TextField],
        on_focus: Callable,
        on_blur: Callable,
        on_change: Callable,
    ) -> List[ft.Control]:
        """
        Build DMS format input fields.
        
        Structure:
        - Latitude: [N/S] [Lat Degrees] [Lat Minutes] [Lat Seconds]
        - Longitude: [E/W] [Lon Degrees] [Lon Minutes] [Lon Seconds]
        
        Tab order: lat_deg → lat_min → lat_sec → lat_dir → lon_deg → lon_min → lon_sec → lon_dir
        """
        controls = []
        
        # Latitude row: N/S first, then degrees, minutes, seconds
        lat_dir = UIBuilder.create_direction_field(
            "Lat N/S", "lat_dir", "N", on_change=on_change
        )
        lat_deg = UIBuilder.create_coordinate_field(
            "Lat Degrees", "lat_deg", autofocus=True,
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        lat_min = UIBuilder.create_coordinate_field(
            "Lat Minutes", "lat_min",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        lat_sec = UIBuilder.create_coordinate_field(
            "Lat Seconds", "lat_sec",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        
        field_registry["lat_deg"] = lat_deg
        field_registry["lat_min"] = lat_min
        field_registry["lat_sec"] = lat_sec
        field_registry["lat_dir"] = lat_dir
        
        lat_label, lat_row = UIBuilder.create_coordinate_row([lat_dir, lat_deg, lat_min, lat_sec], "Latitude:")
        controls.extend([lat_label, lat_row])
        
        # Longitude row: E/W first, then degrees, minutes, seconds
        lon_dir = UIBuilder.create_direction_field(
            "Lon E/W", "lon_dir", "E", on_change=on_change
        )
        lon_deg = UIBuilder.create_coordinate_field(
            "Lon Degrees", "lon_deg",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        lon_min = UIBuilder.create_coordinate_field(
            "Lon Minutes", "lon_min",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        lon_sec = UIBuilder.create_coordinate_field(
            "Lon Seconds", "lon_sec",
            on_focus=on_focus, on_blur=on_blur, on_change=on_change
        )
        
        field_registry["lon_deg"] = lon_deg
        field_registry["lon_min"] = lon_min
        field_registry["lon_sec"] = lon_sec
        field_registry["lon_dir"] = lon_dir
        
        lon_label, lon_row = UIBuilder.create_coordinate_row([lon_dir, lon_deg, lon_min, lon_sec], "Longitude:")
        controls.extend([lon_label, lon_row])
        
        return controls
    
    @staticmethod
    def build_dd_output_fields(
        field_registry: Dict[str, ft.TextField],
    ) -> List[ft.Control]:
        """Build DD format output fields (read-only)."""
        controls = []
        
        # Latitude row: N/S first, then degrees
        lat_dir = UIBuilder.create_direction_field(
            "Lat N/S", "lat_dir", "", read_only=True
        )
        lat_deg = UIBuilder.create_coordinate_field(
            "Lat Degrees", "lat_deg", read_only=True
        )
        
        field_registry["lat_deg"] = lat_deg
        field_registry["lat_dir"] = lat_dir
        
        lat_label, lat_row = UIBuilder.create_coordinate_row([lat_dir, lat_deg], "Latitude:")
        controls.extend([lat_label, lat_row])
        
        # Longitude row: E/W first, then degrees
        lon_dir = UIBuilder.create_direction_field(
            "Lon E/W", "lon_dir", "", read_only=True
        )
        lon_deg = UIBuilder.create_coordinate_field(
            "Lon Degrees", "lon_deg", read_only=True
        )
        
        field_registry["lon_deg"] = lon_deg
        field_registry["lon_dir"] = lon_dir
        
        lon_label, lon_row = UIBuilder.create_coordinate_row([lon_dir, lon_deg], "Longitude:")
        controls.extend([lon_label, lon_row])
        
        return controls
    
    @staticmethod
    def build_ddm_output_fields(
        field_registry: Dict[str, ft.TextField],
    ) -> List[ft.Control]:
        """Build DDM format output fields (read-only)."""
        controls = []
        
        # Latitude row: N/S first, then degrees, minutes
        lat_dir = UIBuilder.create_direction_field("Lat N/S", "lat_dir", "", read_only=True)
        lat_deg = UIBuilder.create_coordinate_field("Lat Degrees", "lat_deg", read_only=True)
        lat_min = UIBuilder.create_coordinate_field("Lat Minutes", "lat_min", read_only=True)
        
        field_registry["lat_deg"] = lat_deg
        field_registry["lat_min"] = lat_min
        field_registry["lat_dir"] = lat_dir
        
        lat_label, lat_row = UIBuilder.create_coordinate_row([lat_dir, lat_deg, lat_min], "Latitude:")
        controls.extend([lat_label, lat_row])
        
        # Longitude row: E/W first, then degrees, minutes
        lon_dir = UIBuilder.create_direction_field("Lon E/W", "lon_dir", "", read_only=True)
        lon_deg = UIBuilder.create_coordinate_field("Lon Degrees", "lon_deg", read_only=True)
        lon_min = UIBuilder.create_coordinate_field("Lon Minutes", "lon_min", read_only=True)
        
        field_registry["lon_deg"] = lon_deg
        field_registry["lon_min"] = lon_min
        field_registry["lon_dir"] = lon_dir
        
        lon_label, lon_row = UIBuilder.create_coordinate_row([lon_dir, lon_deg, lon_min], "Longitude:")
        controls.extend([lon_label, lon_row])
        
        return controls
    
    @staticmethod
    def build_dms_output_fields(
        field_registry: Dict[str, ft.TextField],
    ) -> List[ft.Control]:
        """Build DMS format output fields (read-only)."""
        controls = []
        
        # Latitude row: N/S first, then degrees, minutes, seconds
        lat_dir = UIBuilder.create_direction_field("Lat N/S", "lat_dir", "", read_only=True)
        lat_deg = UIBuilder.create_coordinate_field("Lat Degrees", "lat_deg", read_only=True)
        lat_min = UIBuilder.create_coordinate_field("Lat Minutes", "lat_min", read_only=True)
        lat_sec = UIBuilder.create_coordinate_field("Lat Seconds", "lat_sec", read_only=True)
        
        field_registry["lat_deg"] = lat_deg
        field_registry["lat_min"] = lat_min
        field_registry["lat_sec"] = lat_sec
        field_registry["lat_dir"] = lat_dir
        
        lat_label, lat_row = UIBuilder.create_coordinate_row([lat_dir, lat_deg, lat_min, lat_sec], "Latitude:")
        controls.extend([lat_label, lat_row])
        
        # Longitude row: E/W first, then degrees, minutes, seconds
        lon_dir = UIBuilder.create_direction_field("Lon E/W", "lon_dir", "", read_only=True)
        lon_deg = UIBuilder.create_coordinate_field("Lon Degrees", "lon_deg", read_only=True)
        lon_min = UIBuilder.create_coordinate_field("Lon Minutes", "lon_min", read_only=True)
        lon_sec = UIBuilder.create_coordinate_field("Lon Seconds", "lon_sec", read_only=True)
        
        field_registry["lon_deg"] = lon_deg
        field_registry["lon_min"] = lon_min
        field_registry["lon_sec"] = lon_sec
        field_registry["lon_dir"] = lon_dir
        
        lon_label, lon_row = UIBuilder.create_coordinate_row([lon_dir, lon_deg, lon_min, lon_sec], "Longitude:")
        controls.extend([lon_label, lon_row])
        
        return controls


__all__ = ["UIBuilder", "FieldSpec"]



