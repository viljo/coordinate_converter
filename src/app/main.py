"""Flet desktop app entry point."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import flet as ft

from core import parser as core_parser
from core.parser import ParseError, ParsedCoordinate
from core.transform import HeightSystem, TransformError, convert_to_targets
from core.crs_registry import CRSCode
from core import artifacts
from app import ui_builder

APP_TARGETS = [
    CRSCode.WGS84_GEO,
    CRSCode.SWEREF99_GEO,
    CRSCode.RT90_3021,
    CRSCode.WGS84_XYZ,
    CRSCode.RR92_XYZ,
]


@dataclass
class FieldSpec:
    name: str
    label: str
    decimals: int = 3
    is_angle: bool = False
    format_mode: Optional[str] = None


@dataclass
class CoordinateOption:
    key: str
    label: str
    fields: List[FieldSpec]
    source_format: str
    result_key: str
    crs: CRSCode | None = None
    parse_hint: Optional[str] = None
    default_crs: CRSCode = CRSCode.WGS84_GEO
    separate_height: bool = False
    allow_input: bool = True
    allow_output: bool = True


COORDINATE_OPTIONS_LIST: List[CoordinateOption] = [
    CoordinateOption(
        key="FREE_TEXT",
        label="Free-text parser",
        fields=[FieldSpec("text", "Coordinate text (auto-detect)", decimals=0)],
        source_format="FREE_TEXT",
        result_key=CRSCode.WGS84_GEO.value,
        crs=None,
        default_crs=CRSCode.SWEREF99_GEO,
        separate_height=False,
        allow_output=False,
    ),
    CoordinateOption(
        key="WGS84_GEO_DD",
        label="WGS84 geographic (DD)",
        fields=[
            FieldSpec(
                "lat_deg", "Degrees", decimals=6, is_angle=True, format_mode="DD"
            ),
            FieldSpec("lat_dir", "N/S", decimals=0, is_angle=True, format_mode="DD"),
            FieldSpec(
                "lon_deg", "Degrees", decimals=6, is_angle=True, format_mode="DD"
            ),
            FieldSpec("lon_dir", "E/W", decimals=0, is_angle=True, format_mode="DD"),
        ],
        source_format="DD",
        result_key=CRSCode.WGS84_GEO.value,
        crs=CRSCode.WGS84_GEO,
        default_crs=CRSCode.WGS84_GEO,
        separate_height=True,
    ),
    CoordinateOption(
        key="WGS84_GEO_DDM",
        label="WGS84 geographic (DDM)",
        fields=[
            FieldSpec(
                "lat_deg", "Degrees", decimals=0, is_angle=True, format_mode="DDM"
            ),
            FieldSpec(
                "lat_min", "Minutes", decimals=4, is_angle=True, format_mode="DDM"
            ),
            FieldSpec("lat_dir", "N/S", decimals=0, is_angle=True, format_mode="DDM"),
            FieldSpec(
                "lon_deg", "Degrees", decimals=0, is_angle=True, format_mode="DDM"
            ),
            FieldSpec(
                "lon_min", "Minutes", decimals=4, is_angle=True, format_mode="DDM"
            ),
            FieldSpec("lon_dir", "E/W", decimals=0, is_angle=True, format_mode="DDM"),
        ],
        source_format="DDM",
        result_key=CRSCode.WGS84_GEO.value,
        crs=CRSCode.WGS84_GEO,
        default_crs=CRSCode.WGS84_GEO,
        separate_height=True,
    ),
    CoordinateOption(
        key="WGS84_GEO_DMS",
        label="WGS84 geographic (DMS)",
        fields=[
            FieldSpec(
                "lat_deg", "Degrees", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lat_min", "Minutes", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lat_sec", "Seconds", decimals=1, is_angle=True, format_mode="DMS"
            ),
            FieldSpec("lat_dir", "N/S", decimals=0, is_angle=True, format_mode="DMS"),
            FieldSpec(
                "lon_deg", "Degrees", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lon_min", "Minutes", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lon_sec", "Seconds", decimals=1, is_angle=True, format_mode="DMS"
            ),
            FieldSpec("lon_dir", "E/W", decimals=0, is_angle=True, format_mode="DMS"),
        ],
        source_format="DMS",
        result_key=CRSCode.WGS84_GEO.value,
        crs=CRSCode.WGS84_GEO,
        default_crs=CRSCode.WGS84_GEO,
        separate_height=True,
    ),
    CoordinateOption(
        key="SWEREF99_GEO_DD",
        label="SWEREF99 geographic (DD)",
        fields=[
            FieldSpec(
                "lat_deg", "Degrees", decimals=6, is_angle=True, format_mode="DD"
            ),
            FieldSpec("lat_dir", "N/S", decimals=0, is_angle=True, format_mode="DD"),
            FieldSpec(
                "lon_deg", "Degrees", decimals=6, is_angle=True, format_mode="DD"
            ),
            FieldSpec("lon_dir", "E/W", decimals=0, is_angle=True, format_mode="DD"),
        ],
        source_format="DD",
        result_key=CRSCode.SWEREF99_GEO.value,
        crs=CRSCode.SWEREF99_GEO,
        default_crs=CRSCode.SWEREF99_GEO,
        separate_height=True,
    ),
    CoordinateOption(
        key="SWEREF99_GEO_DDM",
        label="SWEREF99 geographic (DDM)",
        fields=[
            FieldSpec(
                "lat_deg", "Degrees", decimals=0, is_angle=True, format_mode="DDM"
            ),
            FieldSpec(
                "lat_min", "Minutes", decimals=4, is_angle=True, format_mode="DDM"
            ),
            FieldSpec("lat_dir", "N/S", decimals=0, is_angle=True, format_mode="DDM"),
            FieldSpec(
                "lon_deg", "Degrees", decimals=0, is_angle=True, format_mode="DDM"
            ),
            FieldSpec(
                "lon_min", "Minutes", decimals=4, is_angle=True, format_mode="DDM"
            ),
            FieldSpec("lon_dir", "E/W", decimals=0, is_angle=True, format_mode="DDM"),
        ],
        source_format="DDM",
        result_key=CRSCode.SWEREF99_GEO.value,
        crs=CRSCode.SWEREF99_GEO,
        default_crs=CRSCode.SWEREF99_GEO,
        separate_height=True,
    ),
    CoordinateOption(
        key="SWEREF99_GEO_DMS",
        label="SWEREF99 geographic (DMS)",
        fields=[
            FieldSpec(
                "lat_deg", "Degrees", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lat_min", "Minutes", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lat_sec", "Seconds", decimals=1, is_angle=True, format_mode="DMS"
            ),
            FieldSpec("lat_dir", "N/S", decimals=0, is_angle=True, format_mode="DMS"),
            FieldSpec(
                "lon_deg", "Degrees", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lon_min", "Minutes", decimals=0, is_angle=True, format_mode="DMS"
            ),
            FieldSpec(
                "lon_sec", "Seconds", decimals=1, is_angle=True, format_mode="DMS"
            ),
            FieldSpec("lon_dir", "E/W", decimals=0, is_angle=True, format_mode="DMS"),
        ],
        source_format="DMS",
        result_key=CRSCode.SWEREF99_GEO.value,
        crs=CRSCode.SWEREF99_GEO,
        default_crs=CRSCode.SWEREF99_GEO,
        separate_height=True,
    ),
    CoordinateOption(
        key=CRSCode.RT90_3021.value,
        label="RT90 2.5 gon V",
        fields=[
            FieldSpec("easting", "Easting (m)", decimals=2),
            FieldSpec("northing", "Northing (m)", decimals=2),
        ],
        source_format="RT90",
        result_key=CRSCode.RT90_3021.value,
        crs=CRSCode.RT90_3021,
        default_crs=CRSCode.RT90_3021,
        separate_height=True,
    ),
    CoordinateOption(
        key=CRSCode.WGS84_XYZ.value,
        label="WGS84 geocentric XYZ",
        fields=[
            FieldSpec("x", "X (m)", decimals=3),
            FieldSpec("y", "Y (m)", decimals=3),
            FieldSpec("z", "Z (m)", decimals=3),
        ],
        source_format="XYZ",
        result_key=CRSCode.WGS84_XYZ.value,
        crs=CRSCode.WGS84_XYZ,
        default_crs=CRSCode.WGS84_XYZ,
        separate_height=False,
    ),
    CoordinateOption(
        key=CRSCode.RR92_XYZ.value,
        label="RR92 geocentric XYZ",
        fields=[
            FieldSpec("x", "X (m)", decimals=3),
            FieldSpec("y", "Y (m)", decimals=3),
            FieldSpec("z", "Z (m)", decimals=3),
        ],
        source_format="RR92_XYZ",
        result_key=CRSCode.RR92_XYZ.value,
        crs=CRSCode.RR92_XYZ,
        default_crs=CRSCode.RR92_XYZ,
        separate_height=False,
    ),
    CoordinateOption(
        key="MGRS",
        label="MGRS (WGS84 grid)",
        fields=[FieldSpec("mgrs", "MGRS", decimals=0)],
        source_format="MGRS",
        result_key="MGRS",
        crs=None,
        default_crs=CRSCode.WGS84_GEO,
        separate_height=True,
    ),
]

COORDINATE_OPTIONS: Dict[str, CoordinateOption] = {
    option.key: option for option in COORDINATE_OPTIONS_LIST
}

HEIGHT_LABEL = "Height (m)"


class CoordinateApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "Coordinate Converter"
        self.page.padding = 16
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.window_width = 1998
        self.page.window_height = 1606
        self.page.on_keyboard_event = self._on_page_key
        self.input_tab_order: List[str] = (
            []
        )  # Ordered list of input field names for tab navigation
        self.input_coord_selector = ft.Dropdown(
            label="Input coordinate source",
            options=[
                ft.dropdown.Option(option.key, option.label)
                for option in COORDINATE_OPTIONS_LIST
                if option.allow_input
            ],
            value="WGS84_GEO_DD",
            on_change=self._on_input_type_change,
        )
        self.input_height_selector = ft.Dropdown(
            label="Input height reference",
            options=[
                ft.dropdown.Option(HeightSystem.ELLIPSOIDAL, "Ellipsoidal"),
                ft.dropdown.Option(HeightSystem.RH2000, "RH2000 (SWEN17)"),
                ft.dropdown.Option(HeightSystem.RFN, "RFN"),
            ],
            value=HeightSystem.ELLIPSOIDAL,
            on_change=self._on_input_height_change,
        )
        self.input_height_row = ft.Row(
            controls=[self.input_height_selector],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.output_coord_selector = ft.Dropdown(
            label="Output coordinate",
            options=[
                ft.dropdown.Option(option.key, option.label)
                for option in COORDINATE_OPTIONS_LIST
                if option.allow_output
            ],
            value="WGS84_GEO_DD",
            on_change=self._on_output_type_change,
        )
        self.output_height_selector = ft.Dropdown(
            label="Output height system",
            options=[
                ft.dropdown.Option(HeightSystem.ELLIPSOIDAL, "Ellipsoidal"),
                ft.dropdown.Option(HeightSystem.RH2000, "RH2000 (SWEN17)"),
                ft.dropdown.Option(HeightSystem.RFN, "RFN"),
            ],
            value=HeightSystem.ELLIPSOIDAL,
            on_change=self._on_output_height_change,
        )
        self.output_height_field = ft.TextField(
            label=HEIGHT_LABEL,
            read_only=True,
            helper_text="",
            width=ui_builder.UIBuilder.coordinate_width("height"),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        )
        self.output_height_row = ft.Row(
            controls=[self.output_height_selector, self.output_height_field],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.status_text = ft.Text(value="Ready", color=ft.Colors.ON_SURFACE_VARIANT)
        self.warning_text = ft.Text(value="", color=ft.Colors.AMBER)
        self.formatted_text = ft.Text(value="", color=ft.Colors.PRIMARY)
        # Accuracy indicators (input rows only)
        self.input_accuracy_text = ft.Text(
            value="", size=11, color=ft.Colors.ON_SURFACE_VARIANT
        )

        self.input_fields: Dict[str, ft.TextField] = {}
        self.input_fields_container = ft.Column(spacing=8)
        self.input_height_field: Optional[ft.TextField] = None

        self.output_fields: Dict[str, ft.TextField] = {}
        self.output_fields_container = ft.Column(spacing=8)

        self._suspend_input_events = False
        self._current_option: Optional[CoordinateOption] = None
        self._row_accuracy_labels: Dict[str, ft.Text] = {}
        self._field_accuracy_labels: Dict[str, ft.Text] = {}
        self._row_specs: Dict[str, List[FieldSpec]] = {}
        self._field_specs: Dict[str, FieldSpec] = {}

        self.current_parsed: Optional[ParsedCoordinate] = None
        self.current_results: Dict[str, List[float] | Tuple[float, ...] | str] = {}
        self.focused_field: Optional[str] = None
        self.focused_field_spec: Optional[FieldSpec] = None

        warnings = artifacts.ensure_runtime_artifacts()
        for warning in warnings:
            print(f"[ARTIFACT WARNING] {warning}")
        self._rebuild_input_fields()
        self._rebuild_output_fields()

        # Map setup using data URL inline HTML
        map_html_content = (
            Path(__file__).resolve().parent / "map_view" / "leaflet.html"
        ).read_text()
        tile_url = os.getenv("OSM_TILE_URL")
        if tile_url:
            map_html_content = map_html_content.replace(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                tile_url,
            )
        import base64

        map_html_b64 = base64.b64encode(map_html_content.encode("utf-8")).decode(
            "ascii"
        )
        map_url = f"data:text/html;base64,{map_html_b64}"
        self.map_ready = False
        self._suppress_map_update = False

        def on_console_message(e):
            try:
                msg = str(getattr(e, "message", "")).strip()
                if not msg:
                    return
                # Prefer JSON payload
                if msg.startswith("{") and msg.endswith("}"):
                    import json

                    data = json.loads(msg)
                    if data.get("type") == "map_click":
                        lat = float(data["lat"])
                        lon = float(data["lon"])
                        self._set_input_coordinate_from_latlon(lat, lon)
                        return
                # Fallback plain text: "map_click <lat> <lon>"
                parts = msg.split()
                if len(parts) == 3 and parts[0] == "map_click":
                    lat = float(parts[1])
                    lon = float(parts[2])
                    self._set_input_coordinate_from_latlon(lat, lon)
            except Exception:
                # Ignore malformed console messages
                pass

        webview_kwargs = {
            "url": map_url,
            "expand": True,
            "on_page_ended": self._handle_map_page_event,
            "on_console_message": on_console_message,
        }

        # Try to enable JavaScript with the correct property name
        javascript_mode = getattr(ft, "JavascriptMode", None)
        if javascript_mode is not None:
            webview_kwargs["javascript_mode"] = javascript_mode.UNRESTRICTED

        self.map_view = ft.WebView(**webview_kwargs)

        print(f"[INIT] WebView created, type: {type(self.map_view)}")
        print(
            f"[INIT] WebView methods: {[m for m in dir(self.map_view) if not m.startswith('_')][:20]}"
        )

        self.map_selector = ft.Dropdown(
            label="Map Type",
            options=[
                ft.dropdown.Option("osm", "OSM"),
                ft.dropdown.Option("satellite", "Satellite"),
                ft.dropdown.Option("terrain", "Terrain"),
            ],
            value="terrain",
            on_change=self._on_map_type_change,
        )
        print(
            f"[INIT] Map selector created with on_change handler: {self._on_map_type_change}"
        )

        controls_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Input", style=ft.TextThemeStyle.TITLE_SMALL),
                    ]
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            text="Paste from clipboard",
                            icon=ft.Icons.CONTENT_PASTE,
                            on_click=self._on_paste_clipboard,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                self.input_coord_selector,
                self.input_height_row,
                self.input_fields_container,
                ft.Divider(),
                ft.Text("Output", style=ft.TextThemeStyle.TITLE_SMALL),
                self.output_coord_selector,
                self.output_height_row,
                self.output_fields_container,
                ft.Divider(),
                self.status_text,
                self.warning_text,
                self.formatted_text,
            ],
            expand=True,
        )

        self.page.add(
            ft.Row(
                [
                    ft.Container(
                        content=controls_column,
                        width=450,
                        padding=ft.padding.only(left=10, right=10, top=10, bottom=10),
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        content=self.map_view,
                        expand=True,
                    ),
                ],
                expand=True,
            )
        )

        self.page.add(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=450),
                        ft.VerticalDivider(width=1),
                        ft.Container(
                            content=self.map_selector,
                            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
                        ),
                    ],
                ),
                height=60,
            )
        )

    def _rebuild_input_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        self._current_option = option
        self.input_fields.clear()
        controls: List[ft.Control] = []
        self._suspend_input_events = True
        self._row_accuracy_labels = {}
        self._field_accuracy_labels = {}
        self._row_specs = {}
        self._field_specs = {spec.name: spec for spec in option.fields}

        # Use UIBuilder for DD/DDM/DMS formats
        # UIBuilder callbacks receive event object only, not FieldSpec
        # We need to create FieldSpec from the field name for focus tracking
        def make_on_focus(field_name: str, label: str):
            def handler(e):
                spec = FieldSpec(field_name, label, decimals=6, is_angle=True)
                self._on_input_focus(spec)

            return handler

        if option.source_format == "DD":
            # Create the fields first, then set up callbacks
            controls = ui_builder.UIBuilder.build_dd_input_fields(
                self.input_fields,
                lambda e: None,  # Placeholder, we'll override
                self._on_input_blur,
                lambda e: self._on_input_change(None),
            )
            # Set tab order: lat_dir → lat_deg → lon_dir → lon_deg (direction first)
            self.input_tab_order = ["lat_dir", "lat_deg", "lon_dir", "lon_deg"]
            # Now set proper focus handlers with FieldSpec
            self.input_fields["lat_deg"].on_focus = make_on_focus("lat_deg", "Degrees")
            self.input_fields["lat_dir"].on_focus = make_on_focus("lat_dir", "N/S")
            self.input_fields["lon_deg"].on_focus = make_on_focus("lon_deg", "Degrees")
            self.input_fields["lon_dir"].on_focus = make_on_focus("lon_dir", "E/W")
            self._row_specs["lat"] = self._specs_with_prefix(option, "lat")
            self._row_specs["lon"] = self._specs_with_prefix(option, "lon")

        elif option.source_format == "DDM":
            controls = ui_builder.UIBuilder.build_ddm_input_fields(
                self.input_fields,
                lambda e: None,
                self._on_input_blur,
                lambda e: self._on_input_change(None),
            )
            # Set tab order: lat_dir → lat_deg → lat_min → lon_dir → lon_deg → lon_min (direction first)
            self.input_tab_order = [
                "lat_dir",
                "lat_deg",
                "lat_min",
                "lon_dir",
                "lon_deg",
                "lon_min",
            ]
            self.input_fields["lat_deg"].on_focus = make_on_focus("lat_deg", "Degrees")
            self.input_fields["lat_min"].on_focus = make_on_focus("lat_min", "Minutes")
            self.input_fields["lat_dir"].on_focus = make_on_focus("lat_dir", "N/S")
            self.input_fields["lon_deg"].on_focus = make_on_focus("lon_deg", "Degrees")
            self.input_fields["lon_min"].on_focus = make_on_focus("lon_min", "Minutes")
            self.input_fields["lon_dir"].on_focus = make_on_focus("lon_dir", "E/W")
            self._row_specs["lat"] = self._specs_with_prefix(option, "lat")
            self._row_specs["lon"] = self._specs_with_prefix(option, "lon")

        elif option.source_format == "DMS":
            controls = ui_builder.UIBuilder.build_dms_input_fields(
                self.input_fields,
                lambda e: None,
                self._on_input_blur,
                lambda e: self._on_input_change(None),
            )
            # Set tab order: lat_dir → lat_deg → lat_min → lat_sec → lon_dir → lon_deg → lon_min → lon_sec (direction first)
            self.input_tab_order = [
                "lat_dir",
                "lat_deg",
                "lat_min",
                "lat_sec",
                "lon_dir",
                "lon_deg",
                "lon_min",
                "lon_sec",
            ]
            self.input_fields["lat_deg"].on_focus = make_on_focus("lat_deg", "Degrees")
            self.input_fields["lat_min"].on_focus = make_on_focus("lat_min", "Minutes")
            self.input_fields["lat_sec"].on_focus = make_on_focus("lat_sec", "Seconds")
            self.input_fields["lat_dir"].on_focus = make_on_focus("lat_dir", "N/S")
            self.input_fields["lon_deg"].on_focus = make_on_focus("lon_deg", "Degrees")
            self.input_fields["lon_min"].on_focus = make_on_focus("lon_min", "Minutes")
            self.input_fields["lon_sec"].on_focus = make_on_focus("lon_sec", "Seconds")
            self.input_fields["lon_dir"].on_focus = make_on_focus("lon_dir", "E/W")
            self._row_specs["lat"] = self._specs_with_prefix(option, "lat")
            self._row_specs["lon"] = self._specs_with_prefix(option, "lon")
        else:
            # Legacy formats (RT90, XYZ, MGRS, etc.)
            self.input_tab_order = []
            for index, spec in enumerate(option.fields):
                if spec.name == "text":
                    field = ft.TextField(
                        label=spec.label,
                        autofocus=index == 0,
                        multiline=True,
                        width=ui_builder.UIBuilder.coordinate_width(
                            spec.name, spec.format_mode
                        ),
                    )
                    field.on_change = lambda _e, name=spec.name: self._on_input_change(
                        name
                    )
                else:
                    field = ui_builder.UIBuilder.create_coordinate_field(
                        name=spec.name,
                        format_mode=spec.format_mode,
                        autofocus=index == 0,
                    )
                    if spec.name != "mgrs":
                        field.on_focus = lambda _e, s=spec: self._on_input_focus(s)
                        field.on_blur = self._on_input_blur
                    field.on_change = lambda _e, name=spec.name: self._on_input_change(
                        name
                    )
                self.input_fields[spec.name] = field
                self.input_tab_order.append(spec.name)
                accuracy = self._accuracy_from_specs([spec])
                if accuracy is not None:
                    controls.append(
                        self._wrap_with_accuracy(field, accuracy, spec.name)
                    )
                else:
                    controls.append(field)

        if option.source_format in {"DD", "DDM", "DMS"}:
            row_accuracies = [
                ("lat", self._accuracy_from_specs(self._row_specs.get("lat", []))),
                ("lon", self._accuracy_from_specs(self._row_specs.get("lon", []))),
            ]
            self._apply_accuracy_to_rows(controls, row_accuracies)

        for name, field in self.input_fields.items():
            field.on_change = lambda _e, field_name=name: self._on_input_change(
                field_name
            )

        self.input_height_row.controls = [self.input_height_selector]
        if option.separate_height:
            height_spec = FieldSpec("height", HEIGHT_LABEL, decimals=3)
            self.input_height_field = ui_builder.UIBuilder.create_height_field(
                on_focus=lambda e: self._on_input_focus(height_spec),
                on_blur=self._on_input_blur,
                on_change=lambda e: self._on_input_change("height"),
            )
            self.input_height_row.controls.append(self.input_height_field)
            self.input_height_row.visible = True
            # Add height to tab order after the coordinate fields
            self.input_tab_order.append("height")
        else:
            self.input_height_field = None
            self.input_height_row.visible = False
        self._suspend_input_events = False
        self.input_fields_container.controls = controls
        self.focused_field = None
        self.focused_field_spec = None
        self._populate_input_from_results(option)
        self.page.update()

    @staticmethod
    def _specs_with_prefix(option: CoordinateOption, prefix: str) -> List[FieldSpec]:
        return [spec for spec in option.fields if spec.name.startswith(prefix)]

    def _apply_accuracy_to_rows(
        self,
        controls: List[ft.Control],
        row_accuracies: List[Tuple[str, Optional[str]]],
    ) -> None:
        row_index = 0
        for control in controls:
            if isinstance(control, ft.Row) and row_index < len(row_accuracies):
                key, accuracy = row_accuracies[row_index]
                self._append_accuracy_to_row(control, key, accuracy)
                row_index += 1

    def _append_accuracy_to_row(
        self, row: ft.Row, key: str, accuracy: Optional[str]
    ) -> None:
        row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        accuracy_text = self._row_accuracy_labels.get(key)
        if accuracy_text is None:
            accuracy_text = ft.Text(
                accuracy or "", size=12, color=ft.Colors.ON_SURFACE_VARIANT
            )
            self._row_accuracy_labels[key] = accuracy_text
            row.controls.append(accuracy_text)
        else:
            accuracy_text.value = accuracy or ""
            if accuracy_text not in row.controls:
                row.controls.append(accuracy_text)

    def _wrap_with_accuracy(
        self, control: ft.Control, accuracy: Optional[str], field_name: str
    ) -> ft.Control:
        if not accuracy:
            return control
        accuracy_text = ft.Text(
            accuracy, size=12, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self._field_accuracy_labels[field_name] = accuracy_text
        return ft.Row(
            controls=[
                control,
                accuracy_text,
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _decimals_from_field_value(self, field_name: str) -> Optional[int]:
        field = self.input_fields.get(field_name)
        if not field or field.value is None:
            return None
        text = field.value.strip()
        if not text:
            return None
        normalized = text.replace(",", ".")
        if normalized.count(".") > 1:
            return None
        sign_stripped = normalized.lstrip("+-")
        if not sign_stripped:
            return None
        if "." in sign_stripped:
            integer_part, fractional_part = sign_stripped.split(".", 1)
            if integer_part and not integer_part.isdigit():
                return None
            if not fractional_part.isdigit():
                return None
            return len(fractional_part)
        return 0 if sign_stripped.isdigit() else None

    def _accuracy_from_specs(self, specs: List[FieldSpec]) -> Optional[str]:
        if not specs:
            return None
        numeric_specs = [
            spec
            for spec in specs
            if spec.name not in {"text"} and not spec.name.endswith("_dir")
        ]
        if not numeric_specs:
            return None
        preferred_order = ("_sec", "_min", "_deg")
        selected: Optional[FieldSpec] = None
        selected_decimals: Optional[int] = None
        fallback: Optional[FieldSpec] = None
        for suffix in preferred_order:
            for spec in numeric_specs:
                if spec.name.endswith(suffix):
                    decimals_override = self._decimals_from_field_value(spec.name)
                    if decimals_override is not None:
                        selected = spec
                        selected_decimals = decimals_override
                        break
                    if fallback is None:
                        fallback = spec
            if selected is not None:
                break
        if selected is None:
            if fallback is not None:
                selected = fallback
                selected_decimals = self._decimals_from_field_value(selected.name)
            else:
                selected = max(numeric_specs, key=lambda s: (s.decimals, s.name))
                selected_decimals = self._decimals_from_field_value(selected.name)
        if selected_decimals is None:
            selected_decimals = self._decimals_from_field_value(selected.name)
        decimals_value = (
            selected_decimals if selected_decimals is not None else selected.decimals
        )
        return ui_builder.UIBuilder.accuracy_label(
            decimals=decimals_value,
            is_angle=selected.is_angle,
            format_mode=selected.format_mode,
            field_name=selected.name,
        )

    def _row_key_for_field(self, field_name: str) -> Optional[str]:
        for key, specs in self._row_specs.items():
            if any(spec.name == field_name for spec in specs):
                return key
        return None

    def _update_accuracy_for_field(self, field_name: str) -> bool:
        accuracy_text = self._field_accuracy_labels.get(field_name)
        spec = self._field_specs.get(field_name)
        if accuracy_text is None or spec is None:
            return False
        new_value = self._accuracy_from_specs([spec]) or ""
        if accuracy_text.value == new_value:
            return False
        accuracy_text.value = new_value
        return True

    def _update_row_accuracy(self, row_key: str) -> bool:
        accuracy_text = self._row_accuracy_labels.get(row_key)
        specs = self._row_specs.get(row_key)
        if accuracy_text is None or not specs:
            return False
        new_value = self._accuracy_from_specs(specs) or ""
        if accuracy_text.value == new_value:
            return False
        accuracy_text.value = new_value
        return True

    def _refresh_accuracy_for_change(self, field_name: Optional[str]) -> bool:
        updated = False
        if field_name:
            updated |= self._update_accuracy_for_field(field_name)
            row_key = self._row_key_for_field(field_name)
            if row_key:
                updated |= self._update_row_accuracy(row_key)
        else:
            for name in list(self._field_accuracy_labels):
                updated |= self._update_accuracy_for_field(name)
            for row_key in list(self._row_accuracy_labels):
                updated |= self._update_row_accuracy(row_key)
        return updated

    def _populate_input_from_results(self, option: CoordinateOption) -> None:
        if not self.current_results:
            return
        # Handle MGRS separately
        values_any = self.current_results.get(option.result_key)
        if isinstance(values_any, str):
            if option.key == "MGRS":
                field = self.input_fields.get("mgrs")
                if field is not None:
                    field.value = values_any
            return
        if option.key == "MGRS":
            mgrs_value = self.current_results.get("MGRS")
            if mgrs_value is None:
                return
        if not isinstance(values_any, (list, tuple)):
            return

        values_seq = tuple(float(v) for v in values_any)

        self._suspend_input_events = True
        try:
            if option.source_format == "DD" and len(values_seq) >= 2:
                lat_value = values_seq[0]
                lon_value = values_seq[1]
                lat_deg_field = self.input_fields.get("lat_deg")
                lon_deg_field = self.input_fields.get("lon_deg")
                lat_dir_field = self.input_fields.get("lat_dir")
                lon_dir_field = self.input_fields.get("lon_dir")
                if lat_deg_field:
                    lat_deg_field.value = f"{abs(lat_value):.6f}"
                if lon_deg_field:
                    lon_deg_field.value = f"{abs(lon_value):.6f}"
                if lat_dir_field:
                    lat_dir_field.value = "N" if lat_value >= 0 else "S"
                if lon_dir_field:
                    lon_dir_field.value = "E" if lon_value >= 0 else "W"

            elif option.source_format == "DDM" and len(values_seq) >= 2:
                lat_value = values_seq[0]
                lon_value = values_seq[1]
                # Latitude
                lat_deg = int(abs(lat_value))
                lat_min = (abs(lat_value) - lat_deg) * 60.0
                lat_deg_field = self.input_fields.get("lat_deg")
                lat_min_field = self.input_fields.get("lat_min")
                lat_dir_field = self.input_fields.get("lat_dir")
                if lat_deg_field:
                    lat_deg_field.value = f"{lat_deg}"
                if lat_min_field:
                    lat_min_field.value = f"{lat_min:.4f}"
                if lat_dir_field:
                    lat_dir_field.value = "N" if lat_value >= 0 else "S"
                # Longitude
                lon_deg = int(abs(lon_value))
                lon_min = (abs(lon_value) - lon_deg) * 60.0
                lon_deg_field = self.input_fields.get("lon_deg")
                lon_min_field = self.input_fields.get("lon_min")
                lon_dir_field = self.input_fields.get("lon_dir")
                if lon_deg_field:
                    lon_deg_field.value = f"{lon_deg}"
                if lon_min_field:
                    lon_min_field.value = f"{lon_min:.4f}"
                if lon_dir_field:
                    lon_dir_field.value = "E" if lon_value >= 0 else "W"

            elif option.source_format == "DMS" and len(values_seq) >= 2:
                lat_value = values_seq[0]
                lon_value = values_seq[1]
                # Latitude
                lat_deg = int(abs(lat_value))
                lat_min_dec = (abs(lat_value) - lat_deg) * 60.0
                lat_min = int(lat_min_dec)
                lat_sec = (lat_min_dec - lat_min) * 60.0
                if f := self.input_fields.get("lat_deg"):
                    f.value = f"{lat_deg}"
                if f := self.input_fields.get("lat_min"):
                    f.value = f"{lat_min}"
                if f := self.input_fields.get("lat_sec"):
                    f.value = f"{lat_sec:.1f}"
                if f := self.input_fields.get("lat_dir"):
                    f.value = "N" if lat_value >= 0 else "S"
                # Longitude
                lon_deg = int(abs(lon_value))
                lon_min_dec = (abs(lon_value) - lon_deg) * 60.0
                lon_min = int(lon_min_dec)
                lon_sec = (lon_min_dec - lon_min) * 60.0
                if f := self.input_fields.get("lon_deg"):
                    f.value = f"{lon_deg}"
                if f := self.input_fields.get("lon_min"):
                    f.value = f"{lon_min}"
                if f := self.input_fields.get("lon_sec"):
                    f.value = f"{lon_sec:.1f}"
                if f := self.input_fields.get("lon_dir"):
                    f.value = "E" if lon_value >= 0 else "W"

            else:
                for index, spec in enumerate(option.fields):
                    field = self.input_fields.get(spec.name)
                    if not field:
                        continue
                    if index < len(values_seq):
                        value = values_seq[index]
                        decimals = spec.decimals if not spec.is_angle else 6
                        field.value = f"{value:.{decimals}f}"
                    else:
                        field.value = ""

            # Populate height if present
            if option.separate_height and self.input_height_field is not None:
                height_values = self.current_results.get("HEIGHT")
                if isinstance(height_values, (list, tuple)) and height_values:
                    self.input_height_field.value = f"{float(height_values[0]):.3f}"
        finally:
            self._suspend_input_events = False

        if self._refresh_accuracy_for_change(None):
            self.page.update()

    def _rebuild_output_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.output_coord_selector.value]
        self.output_fields.clear()
        controls: List[ft.Control] = []

        # Use UIBuilder for DD/DDM/DMS formats
        if option.source_format == "DD":
            controls = ui_builder.UIBuilder.build_dd_output_fields(self.output_fields)
        elif option.source_format == "DDM":
            controls = ui_builder.UIBuilder.build_ddm_output_fields(self.output_fields)
        elif option.source_format == "DMS":
            controls = ui_builder.UIBuilder.build_dms_output_fields(self.output_fields)
        else:
            # Legacy formats
            for spec in option.fields:
                field = ui_builder.UIBuilder.create_coordinate_field(
                    name=spec.name,
                    format_mode=spec.format_mode,
                    read_only=True,
                )
                self.output_fields[spec.name] = field
                controls.append(field)

        self.output_fields_container.controls = controls
        self.output_height_row.visible = option.separate_height
        self._update_output_height_display()
        self.page.update()

    def _map_url(self) -> str:
        inline_html = (
            Path(__file__).resolve().parent / "map_view" / "leaflet.html"
        ).read_text()
        tile_url = os.getenv("OSM_TILE_URL")
        if tile_url:
            inline_html = inline_html.replace(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                tile_url,
            )
        import base64

        encoded = base64.b64encode(inline_html.encode("utf-8")).decode("ascii")
        return f"data:text/html;base64,{encoded}"

    def _invoke_map_js(self, script: str) -> bool:
        executed = False
        if hasattr(self.map_view, "run_javascript"):
            try:
                self.map_view.run_javascript(script)
                executed = True
            except Exception as exc:  # pragma: no cover - logging only
                print(f"[MAP] Error executing script via run_javascript: {exc}")
                import traceback

                traceback.print_exc()
        if not executed and hasattr(self.map_view, "eval_js"):
            try:
                self.map_view.eval_js(script)
                executed = True
            except Exception as exc:  # pragma: no cover - logging only
                print(f"[MAP] Error executing script via eval_js: {exc}")
                import traceback

                traceback.print_exc()
        return executed

    def _handle_map_page_event(self, _event) -> None:
        print("[MAP] Page loaded, map is ready")
        self.map_ready = True
        # Ensure default map type is applied
        self._invoke_map_js("changeMapType('terrain');")
        if self.current_results.get("WGS84_GEO"):
            lat, lon, *_ = self.current_results["WGS84_GEO"]
            self._update_map(lat, lon)

    def _update_map(self, lat: float, lon: float) -> None:
        if not self.map_ready or self._suppress_map_update:
            return
        command = f"updateMapCenter({lat}, {lon});"
        if not self._invoke_map_js(command):
            print(
                f"[MAP] Unable to execute map update script. Available methods: {[m for m in dir(self.map_view) if 'java' in m.lower() or 'eval' in m.lower()]}"
            )

    def _format_latlon(self, lat: float, lon: float, fmt: str) -> str:
        if fmt == "DDM":
            return (
                f"{self._deg_to_ddm(lat, 'N', 'S')} / {self._deg_to_ddm(lon, 'E', 'W')}"
            )
        if fmt == "DMS":
            return (
                f"{self._deg_to_dms(lat, 'N', 'S')} / {self._deg_to_dms(lon, 'E', 'W')}"
            )
        return f"{lat:.6f}, {lon:.6f}"

    def _height_summary(self) -> str:
        if "HEIGHT_ERROR" in self.current_results:
            return str(self.current_results["HEIGHT_ERROR"])
        if "HEIGHT" in self.current_results:
            height_value = float(self.current_results["HEIGHT"][0])
            label = HEIGHT_LABEL
            summary = f"{label}: {height_value:.3f} m"
            if "HEIGHT_INFO" in self.current_results:
                separation = float(self.current_results["HEIGHT_INFO"][0])
                summary += f" (Geoid sep: {separation:.3f} m)"
            return summary
        return ""

    def _update_output_height_display(self) -> None:
        label = HEIGHT_LABEL
        self.output_height_field.label = label
        helper = ""
        if "HEIGHT_ERROR" in self.current_results:
            self.output_height_field.value = ""
            helper = str(self.current_results["HEIGHT_ERROR"])
        else:
            height_values = self.current_results.get("HEIGHT")
            if isinstance(height_values, (tuple, list)) and height_values:
                self.output_height_field.value = f"{float(height_values[0]):.3f}"
                if "HEIGHT_INFO" in self.current_results:
                    separation = float(self.current_results["HEIGHT_INFO"][0])
                    helper = f"Geoid separation: {separation:.3f} m"
            else:
                self.output_height_field.value = ""
        self.output_height_field.helper_text = helper
        if self.output_height_field.page is not None:
            self.output_height_field.update()

    @staticmethod
    def _deg_to_ddm(value: float, positive: str, negative: str) -> str:
        sign = positive if value >= 0 else negative
        abs_val = abs(value)
        degrees = int(abs_val)
        minutes = (abs_val - degrees) * 60
        return f"{degrees}° {minutes:.4f}' {sign}"

    @staticmethod
    def _deg_to_dms(value: float, positive: str, negative: str) -> str:
        sign = positive if value >= 0 else negative
        abs_val = abs(value)
        degrees = int(abs_val)
        minutes_full = (abs_val - degrees) * 60
        minutes = int(minutes_full)
        seconds = (minutes_full - minutes) * 60
        return f"{degrees}° {minutes}' {seconds:.2f}\" {sign}"

    def _on_input_type_change(self, _event) -> None:
        self._rebuild_input_fields()
        if self._inputs_complete():
            self._on_convert(None)

    def _on_input_height_change(self, _event) -> None:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        if option.separate_height and self.input_height_field is not None:
            self.input_height_field.label = HEIGHT_LABEL
        self.page.update()
        if self._inputs_complete():
            self._on_convert(None)

    def _on_output_type_change(self, _event) -> None:
        self._rebuild_output_fields()
        if self.current_parsed:
            self._run_conversion(self.current_parsed)
        else:
            self._update_output_fields()

    def _on_output_height_change(self, _event) -> None:
        self._update_output_height_display()
        if self.current_parsed:
            self._run_conversion(self.current_parsed)
        else:
            self._update_output_fields()

    def _on_paste_clipboard(self, _event) -> None:
        """Paste clipboard into free-text parser and parse immediately."""
        try:
            get_clip = getattr(self.page, "get_clipboard", None)
            clipboard_text: str = get_clip() if callable(get_clip) else ""
        except Exception:
            clipboard_text = ""
        if not clipboard_text:
            self.status_text.value = "Clipboard is empty"
            self.page.update()
            return
        # Pre-parse without changing inputs
        try:
            preview = core_parser.parse(
                clipboard_text, default_crs=CRSCode.SWEREF99_GEO
            )
        except Exception:
            preview = None
        if preview is None:
            self.status_text.value = "No coordinate detected in clipboard"
            self.page.update()
            return
        # Switch to free-text parser only when a coordinate was detected
        self.input_coord_selector.value = "FREE_TEXT"
        self._rebuild_input_fields()
        text_field = self.input_fields.get("text")
        if text_field is not None:
            text_field.value = clipboard_text
        # Attempt to parse and update UI/map
        self._on_convert(None)
        self.page.update()

    def _on_input_focus(self, spec: FieldSpec) -> None:
        self.focused_field = spec.name
        self.focused_field_spec = spec

    def _on_input_blur(self, _event) -> None:
        self.focused_field = None
        self.focused_field_spec = None

    def _inputs_complete(self) -> bool:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        if option.source_format == "FREE_TEXT":
            field = self.input_fields.get("text")
            return bool(field and field.value.strip())
        if option.source_format == "MGRS":
            field = self.input_fields.get("mgrs")
            return bool(field and field.value.strip())
        for spec in option.fields:
            field = self.input_fields.get(spec.name)
            if field is None or not field.value.strip():
                return False
        return True

    def _on_input_change(self, field_name: Optional[str] = None) -> None:
        if self._suspend_input_events:
            return
        accuracy_changed = self._refresh_accuracy_for_change(field_name)
        if not self._inputs_complete():
            if accuracy_changed:
                self.page.update()
            return
        self._on_convert(None)
        self.page.update()

    def _on_convert(self, _event) -> None:
        try:
            parsed = self._parse_input_fields()
        except (ParseError, ValueError) as exc:
            self.status_text.value = f"Input error: {exc}"
            self.warning_text.value = ""
            self.formatted_text.value = ""
            self.page.update()
            return
        self._run_conversion(parsed)

    def _parse_input_fields(self) -> ParsedCoordinate:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        if option.source_format == "FREE_TEXT":
            value = self.input_fields["text"].value.strip()
            if not value:
                raise ParseError("Enter a coordinate")
            parsed = core_parser.parse(value, default_crs=option.default_crs)
        elif option.source_format == "MGRS":
            value = self.input_fields["mgrs"].value.strip()
            if not value:
                raise ParseError("Enter an MGRS coordinate")
            parsed = core_parser.parse(value, default_crs=CRSCode.SWEREF99_GEO)
        elif option.crs in {CRSCode.WGS84_GEO, CRSCode.SWEREF99_GEO}:
            # Handle DD/DDM/DMS formats with separate direction fields
            if option.source_format in {"DD", "DDM", "DMS"}:
                # Get direction values
                lat_dir_field = self.input_fields.get("lat_dir")
                lon_dir_field = self.input_fields.get("lon_dir")
                lat_dir = (
                    lat_dir_field.value.strip().upper()
                    if lat_dir_field and lat_dir_field.value
                    else "N"
                )
                lon_dir = (
                    lon_dir_field.value.strip().upper()
                    if lon_dir_field and lon_dir_field.value
                    else "E"
                )

                if option.source_format == "DD":
                    lat_deg = self.input_fields["lat_deg"].value.strip()
                    lon_deg = self.input_fields["lon_deg"].value.strip()
                    if not lat_deg or not lon_deg:
                        raise ParseError("Latitude and longitude degrees are required")

                    # Apply direction signs
                    lat_val = float(lat_deg) if lat_dir == "N" else -float(lat_deg)
                    lon_val = float(lon_deg) if lon_dir == "E" else -float(lon_deg)
                    composed = f"{lat_val} {lon_val}"
                elif option.source_format == "DDM":
                    lat_deg = self.input_fields["lat_deg"].value.strip()
                    lat_min = self.input_fields["lat_min"].value.strip()
                    lon_deg = self.input_fields["lon_deg"].value.strip()
                    lon_min = self.input_fields["lon_min"].value.strip()
                    if not all([lat_deg, lat_min, lon_deg, lon_min]):
                        raise ParseError(
                            "All latitude and longitude components are required"
                        )

                    # Convert to decimal degrees and apply direction signs
                    lat_val = float(lat_deg) + float(lat_min) / 60.0
                    lon_val = float(lon_deg) + float(lon_min) / 60.0
                    lat_val = lat_val if lat_dir == "N" else -lat_val
                    lon_val = lon_val if lon_dir == "E" else -lon_val
                    composed = f"{lat_val} {lon_val}"
                elif option.source_format == "DMS":
                    lat_deg = self.input_fields["lat_deg"].value.strip()
                    lat_min = self.input_fields["lat_min"].value.strip()
                    lat_sec = self.input_fields["lat_sec"].value.strip()
                    lon_deg = self.input_fields["lon_deg"].value.strip()
                    lon_min = self.input_fields["lon_min"].value.strip()
                    lon_sec = self.input_fields["lon_sec"].value.strip()
                    if not all([lat_deg, lat_min, lat_sec, lon_deg, lon_min, lon_sec]):
                        raise ParseError(
                            "All latitude and longitude components are required"
                        )

                    # Convert to decimal degrees and apply direction signs
                    lat_val = (
                        float(lat_deg) + float(lat_min) / 60.0 + float(lat_sec) / 3600.0
                    )
                    lon_val = (
                        float(lon_deg) + float(lon_min) / 60.0 + float(lon_sec) / 3600.0
                    )
                    lat_val = lat_val if lat_dir == "N" else -lat_val
                    lon_val = lon_val if lon_dir == "E" else -lon_val
                    composed = f"{lat_val} {lon_val}"

                height_text = None
                if option.separate_height and self.input_height_field is not None:
                    height_text = self.input_height_field.value.strip()
                    if height_text:
                        composed = f"{composed} {height_text}"
                parsed = core_parser.parse(composed, default_crs=option.default_crs)
                parsed.crs = option.crs or option.default_crs
                if height_text:
                    try:
                        parsed.height = float(height_text.replace(",", "."))
                    except ValueError as exc:  # pragma: no cover - validated earlier
                        raise ParseError("Height must be numeric") from exc
            else:
                # Fallback for legacy lat/lon format
                lat_text = self.input_fields.get("lat", ft.TextField()).value.strip()
                lon_text = self.input_fields.get("lon", ft.TextField()).value.strip()
                if not lat_text or not lon_text:
                    raise ParseError("Latitude and longitude are required")
                composed = f"{lat_text} {lon_text}".strip()
                height_text = None
                if option.separate_height and self.input_height_field is not None:
                    height_text = self.input_height_field.value.strip()
                    if height_text:
                        composed = f"{composed} {height_text}"
                parsed = core_parser.parse(composed, default_crs=option.default_crs)
                parsed.crs = option.crs or option.default_crs
                if height_text:
                    try:
                        parsed.height = float(height_text.replace(",", "."))
                    except ValueError as exc:  # pragma: no cover - validated earlier
                        raise ParseError("Height must be numeric") from exc
        else:
            values: List[float] = []
            for spec in option.fields:
                raw = self.input_fields[spec.name].value.strip()
                if not raw:
                    raise ParseError(f"{spec.label} is required")
                try:
                    values.append(float(raw.replace(",", ".")))
                except ValueError as exc:
                    raise ParseError(f"{spec.label} must be numeric") from exc
            parsed = ParsedCoordinate(
                crs=option.crs or option.default_crs,
                values=tuple(values),
                source_format=option.source_format,
                height=values[2] if len(values) > 2 else None,
            )
        parsed.height_system = self.input_height_selector.value
        return parsed

    def _run_conversion(self, parsed: ParsedCoordinate) -> None:
        self.current_parsed = parsed
        targets: List[str | CRSCode] = [code.value for code in APP_TARGETS]
        selected_output = self.output_coord_selector.value
        selected_option = COORDINATE_OPTIONS[selected_output]
        selected_target = selected_option.result_key
        if selected_target not in targets:
            targets.append(selected_target)
        if "MGRS" not in targets:
            targets.append("MGRS")
        try:
            results = convert_to_targets(
                parsed,
                targets,
                height_target=self.output_height_selector.value,
            )
        except TransformError as exc:
            self.status_text.value = f"Transform error: {exc}"
            self.warning_text.value = ""
            self.formatted_text.value = ""
            self.page.update()
            return
        self.current_results = results

        self._update_output_fields()
        self._update_output_height_display()

        lat, lon, *_ = results.get("WGS84_GEO", (0.0, 0.0, 0.0))
        self.status_text.value = f"Parsed CRS: {parsed.crs.value} | Format: {parsed.source_format} | Height: {parsed.height_system}"
        warnings = list(parsed.warnings)
        if "WARNINGS" in results:
            warnings.extend(results["WARNINGS"])
        self.warning_text.value = "; ".join(warnings)
        display_values = self.current_results.get(selected_option.result_key)
        formatted_parts: List[str] = []
        if (
            selected_option.result_key
            in {CRSCode.WGS84_GEO.value, CRSCode.SWEREF99_GEO.value}
            and isinstance(display_values, (tuple, list))
            and len(display_values) >= 2
        ):
            lat_val = float(display_values[0])
            lon_val = float(display_values[1])
            format_mode = selected_option.fields[0].format_mode or "DD"
            formatted_parts.append(self._format_latlon(lat_val, lon_val, format_mode))
        elif selected_output == "MGRS" and "MGRS" in results:
            formatted_parts.append(str(results["MGRS"]))
        height_summary = self._height_summary()
        if height_summary:
            formatted_parts.append(height_summary)
        self.formatted_text.value = " | ".join(part for part in formatted_parts if part)
        self._update_map(lat, lon)
        self.page.update()

    def _on_page_key(self, event: ft.KeyboardEvent) -> None:
        # Handle Tab and Enter keys for custom tab order (right then down, skip output fields)
        if (event.key == "Tab" and not event.shift) or event.key == "Enter":
            if self.focused_field and self.focused_field in self.input_tab_order:
                try:
                    current_idx = self.input_tab_order.index(self.focused_field)
                    next_idx = (current_idx + 1) % len(self.input_tab_order)
                    next_field_name = self.input_tab_order[next_idx]
                    next_field = self.input_fields.get(next_field_name)
                    if not next_field and next_field_name == "height":
                        next_field = self.input_height_field
                    if next_field:
                        next_field.focus()
                        event.page.update()
                        # Prevent default tab behavior
                        return
                except (ValueError, AttributeError):
                    pass

        # Handle Shift+Tab for reverse tab order
        if event.key == "Tab" and event.shift:
            if self.focused_field and self.focused_field in self.input_tab_order:
                try:
                    current_idx = self.input_tab_order.index(self.focused_field)
                    prev_idx = (current_idx - 1) % len(self.input_tab_order)
                    prev_field_name = self.input_tab_order[prev_idx]
                    prev_field = self.input_fields.get(prev_field_name)
                    if not prev_field and prev_field_name == "height":
                        prev_field = self.input_height_field
                    if prev_field:
                        prev_field.focus()
                        event.page.update()
                        return
                except (ValueError, AttributeError):
                    pass

        # Handle arrow keys for increment/decrement
        if self.focused_field is None or event.key not in ("ArrowUp", "ArrowDown"):
            return
        field = self.input_fields.get(self.focused_field)
        if field is None and self.focused_field == "height":
            field = self.input_height_field
        if field is None:
            return
        try:
            current = float(field.value or 0.0)
        except ValueError:
            current = 0.0
        step = 1.0
        if event.shift:
            step *= 10
        direction = 1 if event.key == "ArrowUp" else -1
        spec = self.focused_field_spec
        decimals = 3
        if spec is not None:
            decimals = spec.decimals if not spec.is_angle else 6
        new_value = current + direction * step
        field.value = f"{new_value:.{decimals}f}"
        self._on_convert(None)

    def _update_output_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.output_coord_selector.value]
        values = self.current_results.get(option.result_key)
        if isinstance(values, tuple):
            values_seq: Tuple[float, ...] = tuple(float(v) for v in values)
        elif isinstance(values, list):
            values_seq = tuple(float(v) for v in values)
        else:
            values_seq = ()

        # Handle DD/DDM/DMS formats with separate fields
        if option.source_format in {"DD", "DDM", "DMS"} and len(values_seq) >= 2:
            lat_value = values_seq[0]
            lon_value = values_seq[1]

            # Populate latitude fields
            if option.source_format == "DD":
                lat_deg_field = self.output_fields.get("lat_deg")
                if lat_deg_field:
                    lat_deg_field.value = f"{abs(lat_value):.6f}"
                lat_dir_field = self.output_fields.get("lat_dir")
                if lat_dir_field:
                    lat_dir_field.value = "N" if lat_value >= 0 else "S"
            elif option.source_format == "DDM":
                lat_deg = int(abs(lat_value))
                lat_min = (abs(lat_value) - lat_deg) * 60.0
                lat_deg_field = self.output_fields.get("lat_deg")
                if lat_deg_field:
                    lat_deg_field.value = f"{lat_deg}"
                lat_min_field = self.output_fields.get("lat_min")
                if lat_min_field:
                    lat_min_field.value = f"{lat_min:.4f}"
                lat_dir_field = self.output_fields.get("lat_dir")
                if lat_dir_field:
                    lat_dir_field.value = "N" if lat_value >= 0 else "S"
            elif option.source_format == "DMS":
                lat_deg = int(abs(lat_value))
                lat_min_dec = (abs(lat_value) - lat_deg) * 60.0
                lat_min = int(lat_min_dec)
                lat_sec = (lat_min_dec - lat_min) * 60.0
                lat_deg_field = self.output_fields.get("lat_deg")
                if lat_deg_field:
                    lat_deg_field.value = f"{lat_deg}"
                lat_min_field = self.output_fields.get("lat_min")
                if lat_min_field:
                    lat_min_field.value = f"{lat_min}"
                lat_sec_field = self.output_fields.get("lat_sec")
                if lat_sec_field:
                    lat_sec_field.value = f"{lat_sec:.1f}"
                lat_dir_field = self.output_fields.get("lat_dir")
                if lat_dir_field:
                    lat_dir_field.value = "N" if lat_value >= 0 else "S"

            # Populate longitude fields
            if option.source_format == "DD":
                lon_deg_field = self.output_fields.get("lon_deg")
                if lon_deg_field:
                    lon_deg_field.value = f"{abs(lon_value):.6f}"
                lon_dir_field = self.output_fields.get("lon_dir")
                if lon_dir_field:
                    lon_dir_field.value = "E" if lon_value >= 0 else "W"
            elif option.source_format == "DDM":
                lon_deg = int(abs(lon_value))
                lon_min = (abs(lon_value) - lon_deg) * 60.0
                lon_deg_field = self.output_fields.get("lon_deg")
                if lon_deg_field:
                    lon_deg_field.value = f"{lon_deg}"
                lon_min_field = self.output_fields.get("lon_min")
                if lon_min_field:
                    lon_min_field.value = f"{lon_min:.4f}"
                lon_dir_field = self.output_fields.get("lon_dir")
                if lon_dir_field:
                    lon_dir_field.value = "E" if lon_value >= 0 else "W"
            elif option.source_format == "DMS":
                lon_deg = int(abs(lon_value))
                lon_min_dec = (abs(lon_value) - lon_deg) * 60.0
                lon_min = int(lon_min_dec)
                lon_sec = (lon_min_dec - lon_min) * 60.0
                lon_deg_field = self.output_fields.get("lon_deg")
                if lon_deg_field:
                    lon_deg_field.value = f"{lon_deg}"
                lon_min_field = self.output_fields.get("lon_min")
                if lon_min_field:
                    lon_min_field.value = f"{lon_min}"
                lon_sec_field = self.output_fields.get("lon_sec")
                if lon_sec_field:
                    lon_sec_field.value = f"{lon_sec:.1f}"
                lon_dir_field = self.output_fields.get("lon_dir")
                if lon_dir_field:
                    lon_dir_field.value = "E" if lon_value >= 0 else "W"
        else:
            # Legacy format for other coordinate systems
            for index, spec in enumerate(option.fields):
                field = self.output_fields.get(spec.name)
                if not field:
                    continue
                if values_seq and index < len(values_seq):
                    value = values_seq[index]
                    decimals = spec.decimals if not spec.is_angle else 6
                    field.value = f"{value:.{decimals}f}"
                else:
                    field.value = ""

        if option.key == "MGRS":
            mgrs_value = self.current_results.get("MGRS")
            field = self.output_fields.get("mgrs")
            if field is not None:
                field.value = str(mgrs_value or "")
        self.page.update()

    def _on_map_type_change(self, event) -> None:
        print(f"[MAP] _on_map_type_change called! Event: {event}")
        print(f"[MAP] Current selector value: {self.map_selector.value}")

        map_type = self.map_selector.value
        if not map_type:
            map_type = "terrain"
        if map_type not in {"osm", "satellite", "terrain"}:
            map_type = "terrain"
        self.map_selector.value = map_type
        self.map_selector.update()

        print(
            f"[MAP] Attempting to change map type to: {map_type}, map_ready={self.map_ready}"
        )

        command = f"changeMapType('{map_type}');"
        if self._invoke_map_js(command):
            print(f"[MAP] Successfully sent changeMapType command for {map_type}")
        else:
            print(
                "[MAP] WebView does not have a JavaScript execution method. Available: "
                f"{[m for m in dir(self.map_view) if 'java' in m.lower() or 'eval' in m.lower()]}"
            )

    def _set_input_coordinate_from_latlon(self, lat: float, lon: float) -> None:
        option = COORDINATE_OPTIONS.get(self.input_coord_selector.value)
        if option is None:
            return

        parsed = ParsedCoordinate(
            crs=CRSCode.WGS84_GEO,
            values=(lat, lon),
            source_format="DD",
            height=None,
            height_system=self.input_height_selector.value,
        )

        self._suppress_map_update = True
        try:
            self._run_conversion(parsed)
        finally:
            self._suppress_map_update = False

        if option.key == "FREE_TEXT":
            text_field = self.input_fields.get("text")
            if text_field is not None:
                self._suspend_input_events = True
                try:
                    text_field.value = f"{lat:.6f} {lon:.6f}"
                finally:
                    self._suspend_input_events = False
            self.page.update()
            return

        if not self.current_results:
            return

        self._populate_input_from_results(option)
        self.page.update()


def main(page: ft.Page) -> None:
    CoordinateApp(page)


if __name__ == "__main__":  # pragma: no cover
    ft.app(target=main)
