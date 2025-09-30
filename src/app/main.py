"""Flet desktop app entry point."""

from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import flet as ft

from core import parser as core_parser
from core.parser import ParseError, ParsedCoordinate
from core.transform import HeightSystem, convert_to_targets, to_canonical
from core.crs_registry import CRSCode

APP_TARGETS = [
    CRSCode.WGS84_GEO,
    CRSCode.SWEREF99_GEO,
    CRSCode.RT90_3021,
    CRSCode.WGS84_XYZ,
    CRSCode.RR92_XYZ,
]


@dataclass
class NumericField:
    field: ft.TextField
    decimals: int

    def set_value(self, value: float) -> None:
        self.field.value = f"{value:.{self.decimals}f}"


class CoordinateApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "Coordinate Converter"
        self.page.padding = 16
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.on_keyboard_event = self._on_page_key

        self.format_selector = ft.Dropdown(
            label="Display format",
            options=[
                ft.dropdown.Option("DD"),
                ft.dropdown.Option("DDM"),
                ft.dropdown.Option("DMS"),
            ],
            value="DD",
            on_change=self._on_format_change,
        )
        self.height_selector = ft.Dropdown(
            label="Height system",
            options=[
                ft.dropdown.Option(HeightSystem.ELLIPSOIDAL),
                ft.dropdown.Option(HeightSystem.RH2000),
                ft.dropdown.Option(HeightSystem.RFN),
            ],
            value=HeightSystem.ELLIPSOIDAL,
            on_change=self._on_height_change,
        )
        self.coordinate_input = ft.TextField(
            label="Coordinate input",
            autofocus=True,
            multiline=True,
            min_lines=2,
            max_lines=3,
            on_submit=self._on_commit,
            on_blur=self._on_commit,
        )
        self.status_text = ft.Text(value="Ready", color=ft.Colors.ON_SURFACE_VARIANT)
        self.warning_text = ft.Text(value="", color=ft.Colors.AMBER)
        self.formatted_text = ft.Text(value="", color=ft.Colors.PRIMARY)

        self.wgs_lat_field = NumericField(
            ft.TextField(
                label="Latitude (°)",
                on_blur=self._on_wgs_blur,
                on_submit=self._on_wgs_commit,
                on_focus=lambda _e, axis="lat": self._on_wgs_focus(axis),
            ),
            6,
        )
        self.wgs_lon_field = NumericField(
            ft.TextField(
                label="Longitude (°)",
                on_blur=self._on_wgs_blur,
                on_submit=self._on_wgs_commit,
                on_focus=lambda _e, axis="lon": self._on_wgs_focus(axis),
            ),
            6,
        )
        self.wgs_h_field = NumericField(
            ft.TextField(
                label="Ellipsoidal height (m)",
                on_blur=self._on_wgs_blur,
                on_submit=self._on_wgs_commit,
                on_focus=lambda _e, axis="h": self._on_wgs_focus(axis),
            ),
            3,
        )

        self.focused_axis: Optional[str] = None

        self.output_fields: Dict[str, List[ft.TextField]] = {}
        for target in APP_TARGETS:
            if target == CRSCode.WGS84_GEO:
                self.output_fields[target.value] = [
                    self.wgs_lat_field.field,
                    self.wgs_lon_field.field,
                    self.wgs_h_field.field,
                ]
            elif target == CRSCode.SWEREF99_GEO:
                self.output_fields[target.value] = [
                    ft.TextField(label="SWEREF99 lat (°)", read_only=True),
                    ft.TextField(label="SWEREF99 lon (°)", read_only=True),
                ]
            elif target == CRSCode.RT90_3021:
                self.output_fields[target.value] = [
                    ft.TextField(label="RT90 northing (m)", read_only=True),
                    ft.TextField(label="RT90 easting (m)", read_only=True),
                ]
            elif target == CRSCode.WGS84_XYZ:
                self.output_fields[target.value] = [
                    ft.TextField(label="ECEF X (m)", read_only=True),
                    ft.TextField(label="ECEF Y (m)", read_only=True),
                    ft.TextField(label="ECEF Z (m)", read_only=True),
                ]
            elif target == CRSCode.RR92_XYZ:
                self.output_fields[target.value] = [
                    ft.TextField(label="RR92 X (m)", read_only=True),
                    ft.TextField(label="RR92 Y (m)", read_only=True),
                    ft.TextField(label="RR92 Z (m)", read_only=True),
                ]

        self.mgrs_field = ft.TextField(label="MGRS", read_only=True)
        self.height_field = ft.TextField(label="Height result", read_only=True)
        self.height_info_field = ft.TextField(label="Height info", read_only=True)

        map_url = self._map_url()
        self.map_ready = False
        self.map_view = ft.WebView(
            url=map_url,
            expand=True,
            on_page_ended=self._handle_map_page_event,
        )

        controls_column = ft.Column(
            [
                self.format_selector,
                self.height_selector,
                self.coordinate_input,
                self.status_text,
                self.warning_text,
                self.formatted_text,
                ft.Divider(),
                ft.Text("WGS84"),
                self.wgs_lat_field.field,
                self.wgs_lon_field.field,
                self.wgs_h_field.field,
                ft.Divider(),
                ft.Text("Outputs"),
            ]
            + [field for fields in self.output_fields.values() for field in fields if fields[0] not in {self.wgs_lat_field.field, self.wgs_lon_field.field, self.wgs_h_field.field}]
            + [ft.Divider(), self.mgrs_field, self.height_field, self.height_info_field],
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
        self.current_results: Dict[str, List[float] | str] = {}

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
        fmt = self.format_selector.value
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

    def _on_format_change(self, _event) -> None:
        if self.current_results.get("WGS84_GEO"):
            lat, lon, *_ = self.current_results["WGS84_GEO"]
            self.formatted_text.value = self._format_latlon(lat, lon)
            self.page.update()

    def _on_height_change(self, _event) -> None:
        if self.current_parsed:
            self._run_conversion(self.current_parsed)

    def _on_commit(self, _event) -> None:
        text = self.coordinate_input.value or ""
        try:
            parsed = core_parser.parse(text, default_crs=CRSCode.SWEREF99_GEO)
        except ParseError as exc:
            self.status_text.value = f"Parse error: {exc}"
            self.warning_text.value = ""
            self.page.update()
            return
        self._run_conversion(parsed)

    def _run_conversion(self, parsed: ParsedCoordinate) -> None:
        self.current_parsed = parsed
        canonical = to_canonical(parsed)
        results = convert_to_targets(
            parsed,
            [code.value for code in APP_TARGETS] + ["MGRS"],
            height_target=self.height_selector.value,
        )
        self.current_results = results

        for target in APP_TARGETS:
            values = results.get(target.value)
            fields = self.output_fields[target.value]
            if not values:
                continue
            for field, value in zip(fields, values):
                if isinstance(field, ft.TextField):
                    decimals = 6
                    if field.label and any(unit in field.label.lower() for unit in ("m", "ecef", "rt90", "height", "rr92")):
                        decimals = 3
                    field.value = f"{float(value):.{decimals}f}"

        if "MGRS" in results:
            self.mgrs_field.value = str(results["MGRS"])
        if "HEIGHT" in results:
            self.height_field.value = f"{results['HEIGHT'][0]:.3f}"
        else:
            self.height_field.value = ""
        if "HEIGHT_INFO" in results:
            self.height_info_field.value = f"Geoid sep: {results['HEIGHT_INFO'][0]:.3f} m"
        else:
            self.height_info_field.value = ""
        if "HEIGHT_ERROR" in results:
            self.height_field.value = ""
            self.height_info_field.value = results["HEIGHT_ERROR"]

        lat, lon, *_ = results.get("WGS84_GEO", (0.0, 0.0, 0.0))
        self.wgs_lat_field.set_value(lat)
        self.wgs_lon_field.set_value(lon)
        self.wgs_h_field.set_value(canonical.geographic[2])

        self.status_text.value = f"Parsed CRS: {parsed.crs.value} | Format: {parsed.source_format}"
        self.warning_text.value = "; ".join(parsed.warnings)
        self.formatted_text.value = self._format_latlon(lat, lon)
        self._update_map(lat, lon)
        self.page.update()

    def _on_wgs_focus(self, axis: str) -> None:
        self.focused_axis = axis

    def _on_wgs_blur(self, event) -> None:
        self.focused_axis = None
        self._on_wgs_commit(event)

    def _on_wgs_commit(self, _event) -> None:
        try:
            lat = float(self.wgs_lat_field.field.value)
            lon = float(self.wgs_lon_field.field.value)
            h = float(self.wgs_h_field.field.value or 0.0)
        except ValueError:
            self.warning_text.value = "Invalid numeric entry in WGS84 fields"
            self.page.update()
            return
        parsed = ParsedCoordinate(
            crs=CRSCode.WGS84_GEO,
            values=(lat, lon, h),
            source_format="DD",
            height=h,
        )
        self.coordinate_input.value = f"{lat:.6f} {lon:.6f} {h:.3f}"
        self._run_conversion(parsed)

    def _nudge_wgs_axis(self, axis: str, delta: float) -> None:
        field = {
            "lat": self.wgs_lat_field,
            "lon": self.wgs_lon_field,
            "h": self.wgs_h_field,
        }[axis]
        try:
            current = float(field.field.value or 0.0)
        except ValueError:
            current = 0.0
        field.set_value(current + delta)
        self._on_wgs_commit(None)

    def _on_page_key(self, event: ft.KeyboardEvent) -> None:
        if self.focused_axis not in {"lat", "lon", "h"}:
            return
        if event.key not in ("ArrowUp", "ArrowDown"):
            return
        step = 1.0
        if event.shift:
            step *= 10
        direction = 1 if event.key == "ArrowUp" else -1
        self._nudge_wgs_axis(self.focused_axis, direction * step)


def main(page: ft.Page) -> None:
    CoordinateApp(page)


if __name__ == "__main__":  # pragma: no cover
    ft.app(target=main)
