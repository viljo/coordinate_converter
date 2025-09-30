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


@dataclass
class CoordinateOption:
    key: str
    label: str
    fields: List[FieldSpec]
    crs: CRSCode | None
    source_format: str
    parse_hint: Optional[str] = None
    default_crs: CRSCode = CRSCode.WGS84_GEO
    separate_height: bool = False


COORDINATE_OPTIONS: Dict[str, CoordinateOption] = {
    CRSCode.WGS84_GEO.value: CoordinateOption(
        key=CRSCode.WGS84_GEO.value,
        label="WGS84 geographic",
        fields=[
            FieldSpec("lat", "Latitude", decimals=6, is_angle=True),
            FieldSpec("lon", "Longitude", decimals=6, is_angle=True),
        ],
        crs=CRSCode.WGS84_GEO,
        source_format="DD",
        parse_hint="WGS84",
        default_crs=CRSCode.WGS84_GEO,
        separate_height=True,
    ),
    CRSCode.SWEREF99_GEO.value: CoordinateOption(
        key=CRSCode.SWEREF99_GEO.value,
        label="SWEREF99 geographic",
        fields=[
            FieldSpec("lat", "Latitude", decimals=6, is_angle=True),
            FieldSpec("lon", "Longitude", decimals=6, is_angle=True),
        ],
        crs=CRSCode.SWEREF99_GEO,
        source_format="DD",
        parse_hint="SWEREF99",
        default_crs=CRSCode.SWEREF99_GEO,
        separate_height=True,
    ),
    CRSCode.RT90_3021.value: CoordinateOption(
        key=CRSCode.RT90_3021.value,
        label="RT90 2.5 gon V",
        fields=[
            FieldSpec("northing", "Northing (m)", decimals=3),
            FieldSpec("easting", "Easting (m)", decimals=3),
        ],
        crs=CRSCode.RT90_3021,
        source_format="RT90",
        default_crs=CRSCode.RT90_3021,
    ),
    CRSCode.WGS84_XYZ.value: CoordinateOption(
        key=CRSCode.WGS84_XYZ.value,
        label="WGS84 geocentric XYZ",
        fields=[
            FieldSpec("x", "X (m)", decimals=3),
            FieldSpec("y", "Y (m)", decimals=3),
            FieldSpec("z", "Z (m)", decimals=3),
        ],
        crs=CRSCode.WGS84_XYZ,
        source_format="XYZ",
        default_crs=CRSCode.WGS84_XYZ,
    ),
    CRSCode.RR92_XYZ.value: CoordinateOption(
        key=CRSCode.RR92_XYZ.value,
        label="RR92 geocentric XYZ",
        fields=[
            FieldSpec("x", "X (m)", decimals=3),
            FieldSpec("y", "Y (m)", decimals=3),
            FieldSpec("z", "Z (m)", decimals=3),
        ],
        crs=CRSCode.RR92_XYZ,
        source_format="RR92_XYZ",
        default_crs=CRSCode.RR92_XYZ,
    ),
    "MGRS": CoordinateOption(
        key="MGRS",
        label="MGRS (WGS84 grid)",
        fields=[FieldSpec("mgrs", "MGRS", decimals=0)],
        crs=None,
        source_format="MGRS",
        parse_hint=None,
        default_crs=CRSCode.WGS84_GEO,
    ),
}

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
            options=[ft.dropdown.Option(option.key, option.label) for option in COORDINATE_OPTIONS.values()],
            value=CRSCode.WGS84_GEO.value,
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
        self.output_coord_selector = ft.Dropdown(
            label="Output coordinate",
            options=[ft.dropdown.Option(option.key, option.label) for option in COORDINATE_OPTIONS.values()],
            value=CRSCode.WGS84_GEO.value,
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
        self.output_angle_selector = ft.Dropdown(
            label="Geographic display format",
            options=[
                ft.dropdown.Option("DD"),
                ft.dropdown.Option("DDM"),
                ft.dropdown.Option("DMS"),
            ],
            value="DD",
            on_change=self._on_output_format_change,
        )

        self.status_text = ft.Text(value="Ready", color=ft.Colors.ON_SURFACE_VARIANT)
        self.warning_text = ft.Text(value="", color=ft.Colors.AMBER)
        self.formatted_text = ft.Text(value="", color=ft.Colors.PRIMARY)

        self.input_fields: Dict[str, ft.TextField] = {}
        self.input_fields_container = ft.Column(spacing=8)
        self.input_height_field: Optional[ft.TextField] = None

        self.output_fields: Dict[str, ft.TextField] = {}
        self.output_fields_container = ft.Column(spacing=8)

        self.convert_button = ft.FilledButton("Convert", on_click=self._on_convert)

        self.height_field = ft.TextField(label="Height result", read_only=True)
        self.height_info_field = ft.TextField(label="Height info", read_only=True)

        self._rebuild_input_fields()
        self._rebuild_output_fields()

        map_url = self._map_url()
        self.map_ready = False
        self.map_view = ft.WebView(
            url=map_url,
            expand=True,
            on_page_ended=self._handle_map_page_event,
        )

        controls_column = ft.Column(
            [
                ft.Text("Input", style=ft.TextThemeStyle.TITLE_SMALL),
                self.input_coord_selector,
                self.input_height_selector,
                self.input_fields_container,
                self.convert_button,
                ft.Divider(),
                ft.Text("Output", style=ft.TextThemeStyle.TITLE_SMALL),
                self.output_coord_selector,
                self.output_height_selector,
                self.output_angle_selector,
                self.output_fields_container,
                ft.Divider(),
                self.height_field,
                self.height_info_field,
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

        self.current_parsed: Optional[ParsedCoordinate] = None
        self.current_results: Dict[str, List[float] | Tuple[float, ...] | str] = {}
        self.focused_field: Optional[str] = None
        self.focused_field_spec: Optional[FieldSpec] = None

    def _rebuild_input_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        self.input_fields.clear()
        controls: List[ft.Control] = []
        for index, spec in enumerate(option.fields):
            field = ft.TextField(
                label=spec.label,
                autofocus=index == 0,
                multiline=spec.name == "mgrs",
                on_submit=self._on_convert,
            )
            if spec.name != "mgrs":
                field.on_focus = lambda _e, s=spec: self._on_input_focus(s)
                field.on_blur = self._on_input_blur
            self.input_fields[spec.name] = field
            controls.append(field)
        if option.separate_height:
            label = HEIGHT_LABELS.get(self.input_height_selector.value, "Height (m)")
            self.input_height_field = ft.TextField(
                label=label,
                on_submit=self._on_convert,
            )
            height_spec = FieldSpec("height", label, decimals=3)
            self.input_height_field.on_focus = lambda _e, s=height_spec: self._on_input_focus(s)
            self.input_height_field.on_blur = self._on_input_blur
            controls.append(self.input_height_field)
        else:
            self.input_height_field = None
        self.input_fields_container.controls = controls
        self.focused_field = None
        self.focused_field_spec = None
        self.page.update()

    def _rebuild_output_fields(self) -> None:
        option = COORDINATE_OPTIONS[self.output_coord_selector.value]
        self.output_fields.clear()
        controls: List[ft.Control] = []
        for spec in option.fields:
            field = ft.TextField(label=spec.label, read_only=True)
            self.output_fields[spec.name] = field
            controls.append(field)
        self.output_fields_container.controls = controls
        self.output_angle_selector.visible = option.crs in {
            CRSCode.WGS84_GEO,
            CRSCode.SWEREF99_GEO,
        }
        self.height_field.label = HEIGHT_LABELS.get(self.output_height_selector.value, "Height result")
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

    def _format_latlon(self, lat: float, lon: float) -> str:
        fmt = self.output_angle_selector.value
        if fmt == "DDM":
            return f"{self._deg_to_ddm(lat, 'N', 'S')} / {self._deg_to_ddm(lon, 'E', 'W')}"
        if fmt == "DMS":
            return f"{self._deg_to_dms(lat, 'N', 'S')} / {self._deg_to_dms(lon, 'E', 'W')}"
        return f"{lat:.6f}, {lon:.6f}"

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

    def _on_input_height_change(self, _event) -> None:
        option = COORDINATE_OPTIONS[self.input_coord_selector.value]
        if option.separate_height and self.input_height_field is not None:
            self.input_height_field.label = HEIGHT_LABELS.get(
                self.input_height_selector.value, "Height (m)"
            )
        self.page.update()

    def _on_output_type_change(self, _event) -> None:
        self._rebuild_output_fields()
        self._update_output_fields()

    def _on_output_height_change(self, _event) -> None:
        self.height_field.label = HEIGHT_LABELS.get(
            self.output_height_selector.value, "Height result"
        )
        if self.current_parsed:
            self._run_conversion(self.current_parsed)

    def _on_output_format_change(self, _event) -> None:
        self._update_output_fields()

    def _on_input_focus(self, spec: FieldSpec) -> None:
        self.focused_field = spec.name
        self.focused_field_spec = spec

    def _on_input_blur(self, _event) -> None:
        self.focused_field = None
        self.focused_field_spec = None

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
        if option.key == "MGRS":
            value = self.input_fields["mgrs"].value.strip()
            if not value:
                raise ParseError("Enter an MGRS coordinate")
            parsed = core_parser.parse(value, default_crs=CRSCode.SWEREF99_GEO)
        elif option.crs in {CRSCode.WGS84_GEO, CRSCode.SWEREF99_GEO}:
            lat_text = self.input_fields["lat"].value.strip()
            lon_text = self.input_fields["lon"].value.strip()
            if not lat_text or not lon_text:
                raise ParseError("Latitude and longitude are required")
            composed = f"{option.parse_hint or ''} {lat_text} {lon_text}".strip()
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
        if selected_output not in targets:
            targets.append(selected_output)
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

        lat, lon, *_ = results.get("WGS84_GEO", (0.0, 0.0, 0.0))
        self.status_text.value = (
            f"Parsed CRS: {parsed.crs.value} | Format: {parsed.source_format} | Height: {parsed.height_system}"
        )
        warnings = list(parsed.warnings)
        if "WARNINGS" in results:
            warnings.extend(results["WARNINGS"])
        self.warning_text.value = "; ".join(warnings)
        display_values = self.current_results.get(selected_output)
        if (
            selected_output in {CRSCode.WGS84_GEO.value, CRSCode.SWEREF99_GEO.value}
            and isinstance(display_values, (tuple, list))
            and len(display_values) >= 2
        ):
            lat_val = float(display_values[0])
            lon_val = float(display_values[1])
            self.formatted_text.value = self._format_latlon(lat_val, lon_val)
        elif selected_output == "MGRS" and "MGRS" in results:
            self.formatted_text.value = str(results["MGRS"])
        else:
            self.formatted_text.value = ""
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
        values = self.current_results.get(option.key)
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
                decimals = spec.decimals if not spec.is_angle else 6
                field.value = f"{values_seq[index]:.{decimals}f}"
            else:
                field.value = ""
        if option.key == "MGRS":
            mgrs_value = self.current_results.get("MGRS")
            field = self.output_fields.get("mgrs")
            if field is not None:
                field.value = str(mgrs_value or "")
        if "HEIGHT" in self.current_results:
            height_value = self.current_results["HEIGHT"][0]
            self.height_field.value = f"{float(height_value):.3f}"
        else:
            self.height_field.value = ""
        if "HEIGHT_INFO" in self.current_results:
            separation = self.current_results["HEIGHT_INFO"][0]
            self.height_info_field.value = f"Geoid sep: {float(separation):.3f} m"
        elif "HEIGHT_ERROR" in self.current_results:
            self.height_field.value = ""
            self.height_info_field.value = str(self.current_results["HEIGHT_ERROR"])
        else:
            self.height_info_field.value = ""


def main(page: ft.Page) -> None:
    CoordinateApp(page)


if __name__ == "__main__":  # pragma: no cover
    ft.app(target=main)
