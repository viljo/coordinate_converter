"""Coordinate transformation pipelines and helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple, TYPE_CHECKING

try:
    from mgrs import MGRS  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - provide graceful degradation
    MGRS = None

try:
    from pyproj.exceptions import ProjError  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - align with crs_registry fallback
    class ProjError(Exception):
        pass

from . import height_rfn, height_swen17
from .crs_registry import CRSCode, HAVE_PYPROJ, get_crs_info, get_transformer
from .helmert_rr92 import rr92_to_sweref99, sweref99_to_rr92

MGRS_PRECISION = 5

if TYPE_CHECKING:  # pragma: no cover
    from .parser import ParsedCoordinate


class TransformError(RuntimeError):
    """Raised when a transformation fails."""


class HeightSystem(str):
    ELLIPSOIDAL = "ELLIPSOIDAL"
    RH2000 = "RH2000"
    RFN = "RFN"


@dataclass
class CanonicalCoordinate:
    xyz: Tuple[float, float, float]
    geographic: Tuple[float, float, float]
    warnings: List[str] = field(default_factory=list)


_mgrs = MGRS() if MGRS is not None else None
_HAVE_MGRS = _mgrs is not None

WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)


def _geodetic_to_ecef(lat_deg: float, lon_deg: float, height: float) -> Tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    cos_lon = math.cos(lon)
    sin_lon = math.sin(lon)
    N = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat * sin_lat)
    x = (N + height) * cos_lat * cos_lon
    y = (N + height) * cos_lat * sin_lon
    z = (N * (1 - WGS84_E2) + height) * sin_lat
    return float(x), float(y), float(z)


def _ecef_to_geodetic(x: float, y: float, z: float) -> Tuple[float, float, float]:
    b = WGS84_A * (1 - WGS84_F)
    ep2 = (WGS84_A ** 2 - b ** 2) / (b ** 2)
    p = math.hypot(x, y)
    lon = math.atan2(y, x)
    if p == 0:
        lat = math.copysign(math.pi / 2, z)
        h = abs(z) - b
        return math.degrees(lat), math.degrees(lon), float(h)
    theta = math.atan2(z * WGS84_A, p * b)
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)
    lat = math.atan2(z + ep2 * b * sin_theta ** 3, p - WGS84_E2 * WGS84_A * cos_theta ** 3)
    sin_lat = math.sin(lat)
    N = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat * sin_lat)
    h = p / math.cos(lat) - N
    return math.degrees(lat), math.degrees(lon), float(h)


def _ensure_tuple(values: Iterable[float], length: int) -> Tuple[float, ...]:
    seq = tuple(values)
    if len(seq) >= length:
        return seq[:length]
    padded = list(seq)
    while len(padded) < length:
        padded.append(0.0)
    return tuple(padded)


def _to_xyz(parsed_values: Sequence[float], crs: CRSCode) -> Tuple[float, float, float]:
    info = get_crs_info(crs)
    prepared = info.prepare_input(parsed_values)
    if len(prepared) == 2:
        prepared = (*prepared, 0.0)
    if not HAVE_PYPROJ:
        if crs in {CRSCode.WGS84_GEO, CRSCode.SWEREF99_GEO}:
            lon, lat, h = prepared
            return _geodetic_to_ecef(lat, lon, h)
        if crs == CRSCode.WGS84_XYZ:
            return tuple(map(float, prepared[:3]))
        raise TransformError(f"pyproj is required to transform coordinates from {crs}")
    transformer = get_transformer(crs, CRSCode.WGS84_XYZ)
    try:
        x, y, z = transformer.transform(*prepared)
    except ProjError as exc:  # pragma: no cover - exercised via unit tests
        raise TransformError(f"Failed to transform from {crs} to WGS84_XYZ") from exc
    return float(x), float(y), float(z)


def to_canonical(parsed: "ParsedCoordinate") -> CanonicalCoordinate:
    """Convert a parsed coordinate to canonical geocentric/geographic caches."""

    warnings: List[str] = []
    if parsed.crs == CRSCode.RR92_XYZ:
        xyz = rr92_to_sweref99(*_ensure_tuple(parsed.values, 3))
    else:
        xyz = _to_xyz(parsed.values, parsed.crs)
    if HAVE_PYPROJ:
        geo_transformer = get_transformer(CRSCode.WGS84_XYZ, CRSCode.WGS84_GEO)
        try:
            lon, lat, h = geo_transformer.transform(*xyz)
        except ProjError as exc:  # pragma: no cover
            raise TransformError("Failed to compute canonical geographic coordinate") from exc
        geographic = get_crs_info(CRSCode.WGS84_GEO).restore_output((lon, lat, h))
    else:
        lat, lon, h = _ecef_to_geodetic(*xyz)
        geographic = (lat, lon, h)
    return CanonicalCoordinate(xyz=tuple(map(float, xyz)), geographic=tuple(map(float, geographic)), warnings=warnings)


def _from_xyz(xyz: Tuple[float, float, float], target: CRSCode) -> Tuple[float, ...]:
    if target == CRSCode.RR92_XYZ:
        return sweref99_to_rr92(*xyz)
    if target == CRSCode.WGS84_XYZ:
        return xyz
    if not HAVE_PYPROJ:
        if target == CRSCode.WGS84_GEO:
            lat, lon, h = _ecef_to_geodetic(*xyz)
            return (lat, lon, h)
        if target == CRSCode.SWEREF99_GEO:
            lat, lon, h = _ecef_to_geodetic(*xyz)
            return (lat, lon)
        raise TransformError(f"pyproj is required to transform coordinates to {target}")
    transformer = get_transformer(CRSCode.WGS84_XYZ, target)
    try:
        values = transformer.transform(*xyz)
    except ProjError as exc:  # pragma: no cover
        raise TransformError(f"Failed to transform from WGS84_XYZ to {target}") from exc
    info = get_crs_info(target)
    return info.restore_output(values)


def _mgrs_from_geographic(lat: float, lon: float, precision: int = MGRS_PRECISION) -> str:
    if _HAVE_MGRS:
        return _mgrs.toMGRS(lat, lon, MGRSPrecision=precision)
    # Fallback: provide a readable placeholder when mgrs is unavailable.
    return f"LAT{lat:.5f}_LON{lon:.5f}"


def convert_to_targets(
    parsed: "ParsedCoordinate",
    targets: Iterable[str | CRSCode],
    *,
    height_target: str = HeightSystem.ELLIPSOIDAL,
    mgrs_precision: int = MGRS_PRECISION,
) -> Dict[str, Tuple[float, ...] | str]:
    """Convert a parsed coordinate into multiple target representations."""

    canonical = to_canonical(parsed)
    lat, lon, ellipsoidal = canonical.geographic
    height_source = parsed.height
    if height_source is not None:
        if parsed.height_system == HeightSystem.RH2000:
            try:
                res = height_swen17.ellipsoidal_height(lat, lon, height_source)
            except height_swen17.GeoidUnavailableError as exc:
                canonical.warnings.append(str(exc))
            else:
                ellipsoidal = res.height
                canonical.geographic = (lat, lon, ellipsoidal)
                canonical.xyz = _geodetic_to_ecef(lat, lon, ellipsoidal)
                parsed.height = ellipsoidal
        elif parsed.height_system == HeightSystem.RFN:
            try:
                ellipsoidal_height = height_rfn.DEFAULT_MODEL.orthometric_to_ellipsoidal(
                    lat, lon, height_source
                )
            except height_rfn.RFNHeightUnavailable as exc:
                canonical.warnings.append(str(exc))
            else:  # pragma: no cover - future extension
                ellipsoidal = float(ellipsoidal_height)
                canonical.geographic = (lat, lon, ellipsoidal)
                canonical.xyz = _geodetic_to_ecef(lat, lon, ellipsoidal)
                parsed.height = ellipsoidal

    results: Dict[str, Tuple[float, ...] | str] = {}

    for target in targets:
        if str(target).upper() == "MGRS":
            lat, lon, _ = canonical.geographic
            results[str(target).upper()] = _mgrs_from_geographic(lat, lon, precision=mgrs_precision)
            continue
        target_code = CRSCode(str(target))
        values = _from_xyz(canonical.xyz, target_code)
        results[target_code.value] = values

    # Height conversion
    ellipsoidal = canonical.geographic[2]
    lat, lon = canonical.geographic[0], canonical.geographic[1]
    height_value = parsed.height if parsed.height is not None else ellipsoidal
    if height_target == HeightSystem.ELLIPSOIDAL:
        results["HEIGHT"] = (float(ellipsoidal),)
    elif height_target == HeightSystem.RH2000:
        try:
            res = height_swen17.orthometric_height(lat, lon, height_value)
        except height_swen17.GeoidUnavailableError as exc:
            results["HEIGHT_ERROR"] = str(exc)
        else:
            results["HEIGHT"] = (res.height,)
            results["HEIGHT_INFO"] = (res.separation,)
    elif height_target == HeightSystem.RFN:
        try:
            height = height_rfn.DEFAULT_MODEL.ellipsoidal_to_orthometric(lat, lon, height_value)
        except height_rfn.RFNHeightUnavailable as exc:
            results["HEIGHT_ERROR"] = str(exc)
        else:  # pragma: no cover - future extension
            results["HEIGHT"] = (height,)
    if canonical.warnings:
        results["WARNINGS"] = tuple(canonical.warnings)
    return results


__all__ = [
    "TransformError",
    "HeightSystem",
    "CanonicalCoordinate",
    "convert_to_targets",
    "to_canonical",
]
