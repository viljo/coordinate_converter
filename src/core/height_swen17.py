"""SWEN17_RH2000 geoid wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple

from pyproj import Transformer
from pyproj.exceptions import ProjError

SWEN17_GRID = "swen17_rh2000_20170501.gtx"


class GeoidUnavailableError(RuntimeError):
    """Raised when the SWEN17 geoid grid is missing."""


@dataclass
class GeoidResult:
    height: float
    separation: float


@lru_cache(maxsize=1)
def _geoid_transformer() -> Transformer:
    pipeline = (
        "+proj=pipeline "
        "+step +proj=unitconvert +xy_in=deg +xy_out=rad "
        "+step +proj=unitconvert +z_in=m +z_out=m "
        f"+step +proj=vgridshift +grids={SWEN17_GRID} "
    )
    try:
        return Transformer.from_pipeline(pipeline)
    except ProjError as exc:  # pragma: no cover - tested indirectly
        raise GeoidUnavailableError(
            "SWEN17_RH2000 geoid grid is not available in the PROJ data directory"
        ) from exc


def orthometric_height(lat: float, lon: float, ellipsoidal_height: float) -> GeoidResult:
    """Compute orthometric height using the SWEN17 geoid."""

    transformer = _geoid_transformer()
    try:
        _, _, separation = transformer.transform(lon, lat, ellipsoidal_height)
    except ProjError as exc:
        raise GeoidUnavailableError("Failed to evaluate SWEN17 geoid") from exc
    orthometric = ellipsoidal_height - separation
    return GeoidResult(height=orthometric, separation=separation)


def ellipsoidal_height(lat: float, lon: float, orthometric_height: float) -> GeoidResult:
    """Convert orthometric height back to ellipsoidal height."""

    transformer = _geoid_transformer()
    try:
        _, _, separation = transformer.transform(lon, lat, 0.0)
    except ProjError as exc:
        raise GeoidUnavailableError("Failed to evaluate SWEN17 geoid") from exc
    ellipsoidal = orthometric_height + separation
    return GeoidResult(height=ellipsoidal, separation=separation)


__all__ = [
    "GeoidUnavailableError",
    "GeoidResult",
    "orthometric_height",
    "ellipsoidal_height",
]
