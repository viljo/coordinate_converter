"""Flet desktop app entry point."""

from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import flet as ft

from core import parser as core_parser
from core.parser import ParseError, ParsedCoordinate
from core.transform import HeightSystem, TransformError, convert_to_targets
from core.crs_registry import CRSCode

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
            FieldSpec("lat", "Latitude (DD.ddddd°)", decimals=6, is_angle=True, format_mode="DD"),
            FieldSpec("lon", "Longitude (DD.ddddd°)", decimals=6, is_angle=True, format_mode="DD"),
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
            FieldSpec("lat", "Latitude (DD° MM.mmmm')", decimals=6, is_angle=True, format_mode="DDM"),
            FieldSpec("lon", "Longitude (DD° MM.mmmm')", decimals=6, is_angle=True, format_mode="DDM"),
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
            FieldSpec("lat", "Latitude (DD° MM' SS.s\")", decimals=6, is_angle=True, format_mode="DMS"),
            FieldSpec("lon", "Longitude (DD° MM' SS.s\")", decimals=6, is_angle=True, format_mode="DMS"),
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
            FieldSpec("lat", "Latitude (DD.ddddd°)", decimals=6, is_angle=True, format_mode="DD"),
            FieldSpec("lon", "Longitude (DD.ddddd°)", decimals=6, is_angle=True, format_mode="DD"),
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
            FieldSpec("lat", "Latitude (DD° MM.mmmm')", decimals=6, is_angle=True, format_mode="DDM"),
            FieldSpec("lon", "Longitude (DD° MM.mmmm')", decimals=6, is_angle=True, format_mode="DDM"),
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
            FieldSpec("lat", "Latitude (DD° MM' SS.s\")", decimals=6, is_angle=True, format_mode="DMS"),
            FieldSpec("lon", "Longitude (DD° MM' SS.s\")", decimals=6, is_angle=True, format_mode="DMS"),
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
            FieldSpec("northing", "Northing (m)", decimals=3),
            FieldSpec("easting", "Easting (m)", decimals=3),
        ],
        source_format="RT90",
        result_key=CRSCode.RT90_3021.value,
        crs=CRSCode.RT90_3021,
        default_crs=CRSCode.RT90_3021,
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
        separate_height=False,
    ),
]

COORDINATE_OPTIONS: Dict[str, CoordinateOption] = {option.key: option for option in COORDINATE_OPTIONS_LIST}

HEIGHT_LABELS = {
    HeightSystem.ELLIPSOIDAL: "Ellipsoidal height (m)",
    HeightSystem.RH2000: "RH2000 height (m)",
    HeightSystem.RFN: "RFN height (m)",
}


class CoordinateApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "Coordinate Converter"
        self.page.padding = 16
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.on_keyboard_event = self._on_page_key
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
            label=HEIGHT_LABELS.get(HeightSystem.ELLIPSOIDAL, "Height (m)"),
            read_only=True,
            helper_text="",
        )
        self.output_height_row = ft.Row(
            controls=[self.output_height_selector, self.output_height_field],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.status_text = ft.Text(value="Ready", color=ft.Colors.ON_SURFACE_VARIANT)
        self.warning_text = ft.Text(value="", color=ft.Colors.AMBER)
        self.formatted_text = ft.Text(value="", color=ft.Colors.PRIMARY)

        self.input_fields: Dict[str, ft.TextField] = {}
        self.input_fields_container = ft.Column(spacing=8)
        self.input_height_field: Optional[ft.TextField] = None

        self.output_fields: Dict[str, ft.TextField] = {}
        self.output_fields_container = ft.Column(spacing=8)

        self._suspend_input_events = False

        self.current_parsed: Optional[ParsedCoordinate] = None
        self.current_results: Dict[str, List[float] | Tuple[float, ...] | str] = {}
        self.focused_field: Optional[str] = None
        self.focused_field_spec: Optional[FieldSpec] = None

        self._rebuild_input_fields()
        self._rebuild_output_fields()

        map_url = self._map_url()
        self.map_ready = False
        webview_kwargs: Dict[str, object] = {
            "url": map_url,
            "expand": True,
            "on_page_ended": self._handle_map_page_event,
        }
        javascript_mode = getattr(ft, "JavascriptMode", None)
        if javascript_mode is not None:
            webview_kwargs["javascript_mode"] = javascript_mode.UNRESTRICTED
        self.map_view = ft.WebView(**webview_kwargs)

        controls_column = ft.Column(
            [
                ft.Text("Input", style=ft.TextThemeStyle.TITLE_SMALL),
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
            scroll=ft.ScrollMode.AUTO,
        )

        self.page.add(
            ft.Row(
                [
                    ft.Container(controls_column, width=420),
                    ft.VerticalDivider(width=1),
                    ft.Container(self.map_view, expand=True),
                ],
                expand=True,
            )
        )

    def _rebuild_input_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        self.input_fields.clear()
        controls: List[ft.Control] = []
        self._suspend_input_events = True
        for index, spec in enumerate(option.fields):
            field = ft.TextField(
                label=spec.label,
                autofocus=index == 0,
                multiline=spec.name in {"mgrs", "text"},
            )
            if spec.name != "mgrs":
                field.on_focus = lambda _e, s=spec: self._on_input_focus(s)
                field.on_blur = self._on_input_blur
            field.on_change = lambda _e, name=spec.name: self._on_input_change(name)
            self.input_fields[spec.name] = field
            controls.append(field)
        self.input_height_row.controls = [self.input_height_selector]
        if option.separate_height:
            label = HEIGHT_LABELS.get(self.input_height_selector.value, "Height (m)")
            self.input_height_field = ft.TextField(label=label)
            height_spec = FieldSpec("height", label, decimals=3)
            self.input_height_field.on_focus = lambda _e, s=height_spec: self._on_input_focus(s)
            self.input_height_field.on_blur = self._on_input_blur
            self.input_height_field.on_change = lambda _e: self._on_input_change("height")
            self.input_height_row.controls.append(self.input_height_field)
            self.input_height_row.visible = True
        else:
            self.input_height_field = None
            self.input_height_row.visible = False
        self._suspend_input_events = False
        self.input_fields_container.controls = controls
        self.focused_field = None
        self.focused_field_spec = None
        self._populate_input_from_results(option)
        self.page.update()

    def _populate_input_from_results(self, option: CoordinateOption) -> None:
        if not self.current_results:
            return
        values = self.current_results.get(option.result_key)
        if isinstance(values, str):
            if option.key == "MGRS":
                field = self.input_fields.get("mgrs")
                if field is not None:
                    field.value = values
            return
        if not values:
            if option.key == "MGRS" and "MGRS" in self.current_results:
                self._suspend_input_events = True
                try:
                    field = self.input_fields.get("mgrs")
                    if field is not None:
                        field.value = str(self.current_results.get("MGRS") or "")
                finally:
                    self._suspend_input_events = False
            return
        if not isinstance(values, (list, tuple)):
            return
        self._suspend_input_events = True
        try:
            for index, spec in enumerate(option.fields):
                field = self.input_fields.get(spec.name)
                if field is None:
                    continue
                if index >= len(values):
                    field.value = ""
                    continue
                value = float(values[index])
                if spec.is_angle and spec.format_mode == "DDM":
                    positive, negative = ("N", "S") if spec.name == "lat" else ("E", "W")
                    field.value = self._deg_to_ddm(value, positive, negative)
                elif spec.is_angle and spec.format_mode == "DMS":
                    positive, negative = ("N", "S") if spec.name == "lat" else ("E", "W")
                    field.value = self._deg_to_dms(value, positive, negative)
                else:
                    decimals = spec.decimals if not spec.is_angle else 6
                    field.value = f"{value:.{decimals}f}"
            if option.separate_height and self.input_height_field is not None:
                height_values = self.current_results.get("HEIGHT")
                if isinstance(height_values, (list, tuple)) and height_values:
                    self.input_height_field.value = f"{float(height_values[0]):.3f}"
        finally:
            self._suspend_input_events = False

    def _rebuild_output_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.output_coord_selector.value]
        self.output_fields.clear()
        controls: List[ft.Control] = []
        for spec in option.fields:
            field = ft.TextField(label=spec.label, read_only=True)
            self.output_fields[spec.name] = field
            controls.append(field)
        self.output_fields_container.controls = controls
        self.output_height_row.visible = option.separate_height
        self._update_output_height_display()
        self.page.update()

    def _map_url(self) -> str:
        html_path = Path(__file__).resolve().parent / "map_view" / "leaflet.html"
        tile_url = os.getenv("OSM_TILE_URL")
        if tile_url:
            return f"{html_path.as_uri()}?tile={urllib.parse.quote(tile_url)}"
        return html_path.as_uri()

    def _handle_map_page_event(self, _event) -> None:
        """Mark the embedded map as ready once its initial load completes."""

        self.map_ready = True
        if self.current_results.get("WGS84_GEO"):
            lat, lon, *_ = self.current_results["WGS84_GEO"]
            self._update_map(lat, lon)

    def _update_map(self, lat: float, lon: float) -> None:
        if not self.map_ready:
            return
        self.map_view.eval_js(f"updateMapCenter({lat}, {lon});")

    def _format_latlon(self, lat: float, lon: float, fmt: str) -> str:
        if fmt == "DDM":
            return f"{self._deg_to_ddm(lat, 'N', 'S')} / {self._deg_to_ddm(lon, 'E', 'W')}"
        if fmt == "DMS":
            return f"{self._deg_to_dms(lat, 'N', 'S')} / {self._deg_to_dms(lon, 'E', 'W')}"
        return f"{lat:.6f}, {lon:.6f}"

    def _height_summary(self) -> str:
        if "HEIGHT_ERROR" in self.current_results:
            return str(self.current_results["HEIGHT_ERROR"])
        if "HEIGHT" in self.current_results:
            height_value = float(self.current_results["HEIGHT"][0])
            label = HEIGHT_LABELS.get(self.output_height_selector.value, "Height")
            summary = f"{label}: {height_value:.3f} m"
            if "HEIGHT_INFO" in self.current_results:
                separation = float(self.current_results["HEIGHT_INFO"][0])
                summary += f" (Geoid sep: {separation:.3f} m)"
            return summary
        return ""

    def _update_output_height_display(self) -> None:
        label = HEIGHT_LABELS.get(self.output_height_selector.value, "Height (m)")
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
            self.input_height_field.label = HEIGHT_LABELS.get(
                self.input_height_selector.value, "Height (m)"
            )
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

    def _on_input_change(self, _field_name: Optional[str] = None) -> None:
        if self._suspend_input_events:
            return
        if not self._inputs_complete():
            return
        self._on_convert(None)

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
            lat_text = self.input_fields["lat"].value.strip()
            lon_text = self.input_fields["lon"].value.strip()
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
        self.status_text.value = (
            f"Parsed CRS: {parsed.crs.value} | Format: {parsed.source_format} | Height: {parsed.height_system}"
        )
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
        for index, spec in enumerate(option.fields):
            field = self.output_fields.get(spec.name)
            if not field:
                continue
            if values_seq and index < len(values_seq):
                value = values_seq[index]
                if spec.is_angle and spec.format_mode == "DDM":
                    positive, negative = ("N", "S") if spec.name == "lat" else ("E", "W")
                    field.value = self._deg_to_ddm(value, positive, negative)
                elif spec.is_angle and spec.format_mode == "DMS":
                    positive, negative = ("N", "S") if spec.name == "lat" else ("E", "W")
                    field.value = self._deg_to_dms(value, positive, negative)
                else:
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


def main(page: ft.Page) -> None:
    CoordinateApp(page)


if __name__ == "__main__":  # pragma: no cover
    ft.app(target=main)
