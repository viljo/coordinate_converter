"""CSV batch conversion CLI."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

from core import parser as core_parser
from core.crs_registry import CRSCode
from core.transform import HeightSystem, convert_to_targets


@dataclass
class DetectionResult:
    kind: str
    columns: Tuple[str, ...]


def _detect_columns(fieldnames: Sequence[str]) -> DetectionResult:
    lower = {name.lower(): name for name in fieldnames}
    if "mgrs" in lower:
        return DetectionResult("mgrs", (lower["mgrs"],))
    for lat_key in ("latitude", "lat"):
        if lat_key in lower:
            lat = lower[lat_key]
            for lon_key in ("longitude", "lon", "long"):
                if lon_key in lower:
                    lon = lower[lon_key]
                    height = lower.get("height") or lower.get("h")
                    cols = (lat, lon) if height is None else (lat, lon, height)
                    return DetectionResult("latlon", cols)
    if {"northing", "easting"}.issubset(lower.keys()):
        return DetectionResult("rt90", (lower["northing"], lower["easting"]))
    if {"x", "y", "z"}.issubset(lower.keys()):
        return DetectionResult("xyz", (lower["x"], lower["y"], lower["z"]))
    return DetectionResult("free", tuple(fieldnames))


def _row_to_text(row: Mapping[str, str], detection: DetectionResult) -> str:
    values: List[str] = []
    if detection.kind == "mgrs":
        return row.get(detection.columns[0], "")
    if detection.kind in {"latlon", "rt90", "xyz"}:
        for column in detection.columns:
            if column in row and row[column]:
                values.append(row[column])
        return " ".join(values)
    # free-form fallback
    for column in detection.columns:
        value = row.get(column)
        if value:
            values.append(str(value))
    return " ".join(values)


def _target_columns(code: str) -> Tuple[str, ...]:
    upper = code.upper()
    if upper == "WGS84_GEO":
        return ("WGS84_GEO_LAT", "WGS84_GEO_LON", "WGS84_GEO_H")
    if upper == "SWEREF99_GEO":
        return ("SWEREF99_GEO_LAT", "SWEREF99_GEO_LON")
    if upper == "RT90_3021":
        return ("RT90_3021_X", "RT90_3021_Y")
    if upper == "WGS84_XYZ":
        return ("WGS84_XYZ_X", "WGS84_XYZ_Y", "WGS84_XYZ_Z")
    if upper == "RR92_XYZ":
        return ("RR92_XYZ_X", "RR92_XYZ_Y", "RR92_XYZ_Z")
    if upper == "MGRS":
        return ("MGRS",)
    return (upper,)


def _format_value(value: float, decimals: int = 6) -> str:
    return f"{value:.{decimals}f}"


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CSV coordinate converter")
    parser.add_argument("--in", dest="in_csv", required=True, help="Input CSV path")
    parser.add_argument("--out", dest="out_csv", required=True, help="Output CSV path")
    parser.add_argument(
        "--from",
        dest="from_crs",
        required=True,
        help="Default CRS code when inference fails",
        choices=[code.value for code in CRSCode],
    )
    parser.add_argument(
        "--to",
        dest="to_crs",
        required=True,
        help="Comma-separated list of target CRS codes (include MGRS)",
    )
    parser.add_argument(
        "--height",
        dest="height",
        default=HeightSystem.ELLIPSOIDAL,
        choices=[HeightSystem.ELLIPSOIDAL, HeightSystem.RH2000, HeightSystem.RFN],
    )
    parser.add_argument("--mgrs-precision", type=int, default=5)
    args = parser.parse_args(argv)

    in_path = Path(args.in_csv)
    out_path = Path(args.out_csv)

    targets = [code.strip().upper() for code in args.to_crs.split(",") if code.strip()]
    for code in targets:
        if code != "MGRS":
            CRSCode(code)  # validates code

    with in_path.open(newline="", encoding="utf-8") as input_stream:
        reader = csv.DictReader(input_stream)
        fieldnames = reader.fieldnames or []
        detection = _detect_columns(fieldnames)

        extra_fields = []
        for target in targets:
            for column in _target_columns(target):
                if column not in fieldnames and column not in extra_fields:
                    extra_fields.append(column)
        height_column = f"HEIGHT_{args.height}"
        if height_column not in extra_fields:
            extra_fields.append(height_column)
        if args.height != HeightSystem.ELLIPSOIDAL and "HEIGHT_INFO" not in extra_fields:
            extra_fields.append("HEIGHT_INFO")

        with out_path.open("w", newline="", encoding="utf-8") as output_stream:
            writer = csv.DictWriter(output_stream, fieldnames=fieldnames + extra_fields + ["ERROR"])
            writer.writeheader()

            errors: List[str] = []
            for index, row in enumerate(reader, start=1):
                row_output = dict(row)
                text = _row_to_text(row, detection)
                try:
                    parsed = core_parser.parse(text, default_crs=CRSCode(args.from_crs))
                    results = convert_to_targets(
                        parsed,
                        targets,
                        height_target=args.height,
                        mgrs_precision=args.mgrs_precision,
                    )
                except Exception as exc:  # pragma: no cover - exercised via CLI tests
                    error_message = str(exc)
                    row_output["ERROR"] = error_message
                    errors.append(f"Row {index}: {error_message}")
                else:
                    for target in targets:
                        if target == "MGRS":
                            row_output["MGRS"] = results.get("MGRS")
                            continue
                        values = results.get(target)
                        if values:
                            columns = _target_columns(target)
                            for column, value in zip(columns, values):
                                if isinstance(value, float):
                                    decimals = 3 if column.endswith(("_X", "_Y", "_Z", "_H")) else 6
                                    row_output[column] = _format_value(value, decimals=decimals)
                                else:
                                    row_output[column] = value
                    if "HEIGHT" in results:
                        row_output[f"HEIGHT_{args.height}"] = _format_value(results["HEIGHT"][0], decimals=3)
                    if "HEIGHT_INFO" in results:
                        row_output["HEIGHT_INFO"] = _format_value(results["HEIGHT_INFO"][0], decimals=3)
                    if "HEIGHT_ERROR" in results:
                        row_output["ERROR"] = results["HEIGHT_ERROR"]
                writer.writerow(row_output)

    if errors:
        sys.stderr.write("\n".join(errors) + "\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_cli())
