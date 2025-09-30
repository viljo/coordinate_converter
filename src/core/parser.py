"""Robust free-text coordinate parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence, Tuple

from mgrs import MGRS

from .crs_registry import CRSCode


class ParseError(ValueError):
    """Raised when a string cannot be parsed into coordinates."""


@dataclass
class ParsedCoordinate:
    crs: CRSCode
    values: Tuple[float, ...]
    source_format: str
    height: Optional[float] = None
    height_system: str = "ELLIPSOIDAL"
    warnings: list[str] = field(default_factory=list)


_MGRS = MGRS()
_COORD_PATTERN = re.compile(
    r"""
    (?P<coord>
        [+-]?\d+(?:[\.,]\d+)?              # degrees or X component
        (?:
            [^0-9A-Za-z]+[+-]?\d+(?:[\.,]\d+)?
        ){0,2}
        \s*[NSEW]?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
_HEIGHT_PATTERN = re.compile(
    r"(?:H|HEIGHT|ALT|ELEV|Z)\s*[:=]?\s*([+-]?\d+(?:[\.,]\d+)?)",
    re.IGNORECASE,
)
_LABELLED_AXIS_PATTERN = re.compile(
    r"\b([XYZ]|LAT|LON|LONG|LATITUDE|LONGITUDE|NORTHING|EASTING|N|E)\s*[:=]\s*([+-]?\d+(?:[\.,]\d+)?)",
    re.IGNORECASE,
)


def _clean_number(text: str) -> float:
    return float(text.replace(",", "."))


def _parse_angle(token: str) -> float:
    token_upper = token.upper().strip()
    sign = -1.0 if any(h in token_upper for h in ("S", "W")) else 1.0
    if token_upper.startswith("-"):
        sign = -1.0
    numbers = [
        _clean_number(match)
        for match in re.findall(r"[+-]?\d+(?:[\.,]\d+)?", token_upper)
    ]
    if not numbers:
        raise ParseError(f"No numeric tokens in angle '{token}'")

    if any(sym in token_upper for sym in ("°", "D", "º", "'", "\"")) and len(numbers) >= 2:
        degrees = numbers[0]
        minutes = numbers[1] if len(numbers) > 1 else 0.0
        seconds = numbers[2] if len(numbers) > 2 else 0.0
        decimal = degrees + minutes / 60.0 + seconds / 3600.0
    elif len(numbers) >= 2 and any(sym in token_upper for sym in ("M", "'")):
        decimal = numbers[0] + numbers[1] / 60.0
    elif len(numbers) >= 3 and not any(sym in token_upper for sym in ("°", "D", "º")):
        # Allow space-separated DMS without explicit symbols
        decimal = numbers[0] + numbers[1] / 60.0 + numbers[2] / 3600.0
    else:
        decimal = numbers[0]
    return sign * decimal


def _parse_latlon(text: str) -> Tuple[float, float, Optional[float], str, list[str]]:
    warnings: list[str] = []
    coords = [coord.strip() for coord in _COORD_PATTERN.findall(text)]
    if len(coords) < 2:
        decimal_only = re.fullmatch(r"[0-9\s+\-\.,]+", text)
        if decimal_only:
            numbers = [
                _clean_number(match)
                for match in re.findall(r"[+-]?\d+(?:[\.,]\d+)?", text)
            ]
            if len(numbers) >= 2:
                height = numbers[2] if len(numbers) > 2 else None
                return numbers[0], numbers[1], height, "DD", warnings
        raise ParseError("Could not identify latitude/longitude pairs")

    lat_token, lon_token = coords[0], coords[1]
    lat = _parse_angle(lat_token)
    lon = _parse_angle(lon_token)
    fmt = "DD"
    if any(sym in lat_token for sym in "°º'") or any(sym in lon_token for sym in "°º'"):
        fmt = "DMS"
    elif len(re.findall(r"\d+(?:[\.,]\d+)?", lat_token)) >= 2 or len(
        re.findall(r"\d+(?:[\.,]\d+)?", lon_token)
    ) >= 2:
        fmt = "DDM"

    height = None
    if len(coords) >= 3:
        try:
            height = _clean_number(re.findall(r"[+-]?\d+(?:[\.,]\d+)?", coords[2])[0])
        except IndexError:
            warnings.append("Third token ignored: could not parse height")
    else:
        height_match = _HEIGHT_PATTERN.search(text)
        if height_match:
            height = _clean_number(height_match.group(1))

    return lat, lon, height, fmt, warnings


def parse(text: str, default_crs: CRSCode = CRSCode.SWEREF99_GEO) -> ParsedCoordinate:
    """Parse a string into a coordinate."""

    raw = text.strip()
    if not raw:
        raise ParseError("Empty coordinate string")

    upper = raw.upper()

    mgrs_candidate = re.sub(r"\s+", "", raw)
    if re.fullmatch(r"\d{1,2}[C-HJ-NP-X][A-Z]{2}\d{2,10}", mgrs_candidate.upper()):
        try:
            lat, lon = _MGRS.toLatLon(mgrs_candidate)
        except Exception as exc:  # pragma: no cover - library specific
            raise ParseError("Invalid MGRS string") from exc
        return ParsedCoordinate(
            crs=CRSCode.WGS84_GEO,
            values=(lat, lon),
            source_format="MGRS",
            warnings=["Parsed as MGRS (WGS84 grid)"],
        )

    labelled = {match.group(1).upper(): _clean_number(match.group(2)) for match in _LABELLED_AXIS_PATTERN.finditer(raw)}
    if {"X", "Y", "Z"}.issubset(labelled.keys()) or {"LAT", "LON", "HEIGHT"}.issubset(labelled.keys()):
        if {"X", "Y", "Z"}.issubset(labelled.keys()):
            values = (labelled["X"], labelled["Y"], labelled["Z"])
            source_format = "RR92_XYZ" if "RR92" in upper or "RFN" in upper else "XYZ"
            crs = CRSCode.RR92_XYZ if source_format == "RR92_XYZ" else CRSCode.WGS84_XYZ
            return ParsedCoordinate(crs=crs, values=values, source_format=source_format)

    numeric_tokens = [
        _clean_number(match)
        for match in re.findall(r"[+-]?\d+(?:[\.,]\d+)?", raw)
    ]
    if ("RR92" in upper or "RFN" in upper) and len(numeric_tokens) >= 3:
        return ParsedCoordinate(
            crs=CRSCode.RR92_XYZ,
            values=tuple(numeric_tokens[:3]),
            source_format="RR92_XYZ",
        )
    if "XYZ" in upper and len(numeric_tokens) >= 3:
        return ParsedCoordinate(
            crs=CRSCode.WGS84_XYZ,
            values=tuple(numeric_tokens[:3]),
            source_format="XYZ",
        )

    if len(numeric_tokens) >= 3 and all(abs(val) > 1000 for val in numeric_tokens[:3]):
        source_format = "RR92_XYZ" if "RR92" in upper or "RFN" in upper else "XYZ"
        crs = CRSCode.RR92_XYZ if source_format == "RR92_XYZ" else CRSCode.WGS84_XYZ
        return ParsedCoordinate(
            crs=crs,
            values=tuple(numeric_tokens[:3]),
            source_format=source_format,
        )

    if len(numeric_tokens) >= 2 and any(abs(val) > 100000 for val in numeric_tokens[:2]):
        return ParsedCoordinate(
            crs=CRSCode.RT90_3021,
            values=tuple(numeric_tokens[:2]),
            source_format="RT90",
        )

    lat, lon, height, fmt, warnings = _parse_latlon(raw)
    crs = default_crs if "SWEREF" in upper else CRSCode.WGS84_GEO if "WGS" in upper else default_crs
    return ParsedCoordinate(
        crs=crs,
        values=(lat, lon) if height is None else (lat, lon, height),
        source_format=fmt,
        height=height,
        warnings=warnings,
    )


__all__ = ["ParseError", "ParsedCoordinate", "parse"]
