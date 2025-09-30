"""Central registry of supported coordinate reference systems."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Iterable, Tuple

try:
    from pyproj import CRS, Transformer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    class CRS:  # type: ignore
        """Lightweight stand-in used when pyproj is unavailable."""

        def __init__(self, identifier: str) -> None:
            self.identifier = identifier

        @classmethod
        def from_epsg(cls, code: int) -> "CRS":
            return cls(f"EPSG:{code}")

        @classmethod
        def from_proj4(cls, proj4: str) -> "CRS":
            return cls(proj4)

    class Transformer:  # type: ignore
        """Minimal transformer that only records the requested CRS pair."""

        def __init__(self, src: CRS, dst: CRS) -> None:
            self.src = src
            self.dst = dst

        @classmethod
        def from_crs(cls, src: CRS, dst: CRS, always_xy: bool = True) -> "Transformer":
            return cls(src, dst)

        def transform(self, *args: float):  # pragma: no cover - should be handled upstream
            raise RuntimeError("pyproj is required for this transformation")

    HAVE_PYPROJ = False
else:
    HAVE_PYPROJ = True


class AxisOrder(Enum):
    """Semantic axis orders for user-facing values."""

    LAT_LON = "latlon"
    LON_LAT = "lonlat"
    XY = "xy"
    XYZ = "xyz"


class CRSCode(str, Enum):
    """Enumerates the supported CRS codes used across the application."""

    WGS84_GEO = "WGS84_GEO"
    SWEREF99_GEO = "SWEREF99_GEO"
    RT90_3021 = "RT90_3021"
    WGS84_XYZ = "WGS84_XYZ"
    RR92_XYZ = "RR92_XYZ"


@dataclass(frozen=True)
class CRSInfo:
    code: CRSCode
    crs: CRS
    axis_order: AxisOrder
    dimensionality: int
    description: str

    def prepare_input(self, values: Iterable[float]) -> Tuple[float, ...]:
        """Reorders values into the axis order expected by pyproj."""

        vals = tuple(values)
        if self.axis_order is AxisOrder.LAT_LON:
            if len(vals) == 2:
                lat, lon = vals
                return lon, lat
            if len(vals) >= 3:
                lat, lon, h = vals[:3]
                return lon, lat, h
        if self.axis_order is AxisOrder.XY:
            if len(vals) == 2:
                return vals
            if len(vals) >= 3:
                return vals[:3]
        if self.axis_order is AxisOrder.XYZ:
            if len(vals) >= 3:
                return vals[:3]
        if self.axis_order is AxisOrder.LON_LAT:
            if len(vals) == 2:
                return vals[0], vals[1]
            if len(vals) >= 3:
                return vals[:3]
        # Default behaviour: pad to dimensionality with zeros
        padded = list(vals)
        while len(padded) < self.dimensionality:
            padded.append(0.0)
        return tuple(padded[: self.dimensionality])

    def restore_output(self, values: Iterable[float]) -> Tuple[float, ...]:
        """Restores pyproj outputs to the user-facing order."""

        vals = tuple(values)
        if self.axis_order is AxisOrder.LAT_LON:
            if len(vals) == 2:
                lon, lat = vals
                return lat, lon
            if len(vals) >= 3:
                lon, lat, h = vals[:3]
                return lat, lon, h
        if self.axis_order in {AxisOrder.XY, AxisOrder.XYZ, AxisOrder.LON_LAT}:
            return vals[: self.dimensionality]
        return vals


def _build_registry() -> dict[CRSCode, CRSInfo]:
    registry: dict[CRSCode, CRSInfo] = {}

    registry[CRSCode.WGS84_GEO] = CRSInfo(
        code=CRSCode.WGS84_GEO,
        crs=CRS.from_epsg(4979),
        axis_order=AxisOrder.LAT_LON,
        dimensionality=3,
        description="WGS84 geographic 3D",
    )
    registry[CRSCode.SWEREF99_GEO] = CRSInfo(
        code=CRSCode.SWEREF99_GEO,
        crs=CRS.from_epsg(4619),
        axis_order=AxisOrder.LAT_LON,
        dimensionality=2,
        description="SWEREF99 geographic",
    )
    registry[CRSCode.RT90_3021] = CRSInfo(
        code=CRSCode.RT90_3021,
        crs=CRS.from_epsg(3021),
        axis_order=AxisOrder.XY,
        dimensionality=2,
        description="RT90 2.5 gon V projected",
    )
    registry[CRSCode.WGS84_XYZ] = CRSInfo(
        code=CRSCode.WGS84_XYZ,
        crs=CRS.from_epsg(4978),
        axis_order=AxisOrder.XYZ,
        dimensionality=3,
        description="WGS84 geocentric",
    )
    registry[CRSCode.RR92_XYZ] = CRSInfo(
        code=CRSCode.RR92_XYZ,
        crs=CRS.from_proj4("+proj=geocent +ellps=GRS80 +units=m +no_defs"),
        axis_order=AxisOrder.XYZ,
        dimensionality=3,
        description="RR92 geocentric",
    )
    return registry


_REGISTRY = _build_registry()


def get_crs_info(code: CRSCode | str) -> CRSInfo:
    """Return CRS metadata by code."""

    key = CRSCode(code)
    return _REGISTRY[key]


@lru_cache(maxsize=None)
def get_transformer(src: CRSCode | str, dst: CRSCode | str) -> Transformer:
    """Get a cached pyproj Transformer between CRS codes."""

    if not HAVE_PYPROJ:
        raise RuntimeError("pyproj is required to build coordinate transformers")
    src_info = get_crs_info(src)
    dst_info = get_crs_info(dst)
    return Transformer.from_crs(src_info.crs, dst_info.crs, always_xy=True)


def list_supported_codes() -> Tuple[CRSCode, ...]:
    return tuple(_REGISTRY.keys())


__all__ = [
    "AxisOrder",
    "CRSCode",
    "CRSInfo",
    "HAVE_PYPROJ",
    "get_crs_info",
    "get_transformer",
    "list_supported_codes",
]
