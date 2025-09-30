"""Coordinate transformation pipelines and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple, TYPE_CHECKING

from mgrs import MGRS
from pyproj.exceptions import ProjError

from . import height_rfn, height_swen17
from .crs_registry import CRSCode, get_crs_info, get_transformer
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


_mgrs = MGRS()


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
    geo_transformer = get_transformer(CRSCode.WGS84_XYZ, CRSCode.WGS84_GEO)
    try:
        lon, lat, h = geo_transformer.transform(*xyz)
    except ProjError as exc:  # pragma: no cover
        raise TransformError("Failed to compute canonical geographic coordinate") from exc
    geographic = get_crs_info(CRSCode.WGS84_GEO).restore_output((lon, lat, h))
    return CanonicalCoordinate(xyz=tuple(map(float, xyz)), geographic=tuple(map(float, geographic)), warnings=warnings)


def _from_xyz(xyz: Tuple[float, float, float], target: CRSCode) -> Tuple[float, ...]:
    if target == CRSCode.RR92_XYZ:
        return sweref99_to_rr92(*xyz)
    if target == CRSCode.WGS84_XYZ:
        return xyz
    transformer = get_transformer(CRSCode.WGS84_XYZ, target)
    try:
        values = transformer.transform(*xyz)
    except ProjError as exc:  # pragma: no cover
        raise TransformError(f"Failed to transform from WGS84_XYZ to {target}") from exc
    info = get_crs_info(target)
    return info.restore_output(values)


def _mgrs_from_geographic(lat: float, lon: float, precision: int = MGRS_PRECISION) -> str:
    return _mgrs.toMGRS(lat, lon, MGRSPrecision=precision)


def convert_to_targets(
    parsed: "ParsedCoordinate",
    targets: Iterable[str | CRSCode],
    *,
    height_target: str = HeightSystem.ELLIPSOIDAL,
    mgrs_precision: int = MGRS_PRECISION,
) -> Dict[str, Tuple[float, ...] | str]:
    """Convert a parsed coordinate into multiple target representations."""

    canonical = to_canonical(parsed)
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
    return results


__all__ = [
    "TransformError",
    "HeightSystem",
    "CanonicalCoordinate",
    "convert_to_targets",
    "to_canonical",
]
