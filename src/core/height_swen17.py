"""SWEN17_RH2000 geoid wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Tuple

try:
    from pyproj import Transformer  # type: ignore
    from pyproj.exceptions import ProjError  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - graceful fallback when pyproj is absent
    Transformer = None  # type: ignore

    class ProjError(Exception):
        pass

from . import artifacts
from .artifacts import ArtifactDownloadError

SWEN17_ARTIFACT_NAME = "SWEN17_RH2000.gtx"

_SWEN17_PATH: Path | None = None


class GeoidUnavailableError(RuntimeError):
    """Raised when the SWEN17 geoid grid is missing."""


@dataclass
class GeoidResult:
    height: float
    separation: float


def _swen17_grid_path() -> Path:
    global _SWEN17_PATH
    if _SWEN17_PATH is not None:
        return _SWEN17_PATH
    try:
        path = artifacts.ensure_artifact(SWEN17_ARTIFACT_NAME)
    except (ArtifactDownloadError, KeyError) as exc:
        raise GeoidUnavailableError(
            "SWEN17_RH2000 geoid grid could not be downloaded. "
            "Set COORDINATE_ARTIFACTS_OFFLINE=0 or provide the file manually."
        ) from exc
    artifacts.register_with_pyproj([path.parent])
    _SWEN17_PATH = path
    return path


@lru_cache(maxsize=1)
def _geoid_transformer() -> Transformer:
    if Transformer is None:
        raise GeoidUnavailableError("pyproj is required to evaluate the SWEN17_RH2000 geoid")
    grid_path = _swen17_grid_path()
    pipeline = (
        "+proj=pipeline "
        "+step +proj=unitconvert +xy_in=deg +xy_out=rad "
        "+step +proj=unitconvert +z_in=m +z_out=m "
        f"+step +proj=vgridshift +grids=@{grid_path.as_posix()} "
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
        _, _, transformed_height = transformer.transform(lon, lat, ellipsoidal_height)
        separation = transformed_height - ellipsoidal_height
    except ProjError as exc:
        raise GeoidUnavailableError("Failed to evaluate SWEN17 geoid") from exc
    orthometric = ellipsoidal_height - separation
    return GeoidResult(height=orthometric, separation=separation)


def ellipsoidal_height(lat: float, lon: float, orthometric_height: float) -> GeoidResult:
    """Convert orthometric height back to ellipsoidal height."""

    transformer = _geoid_transformer()
    try:
        # Get geoid separation by transforming a reference height
        _, _, transformed_ref = transformer.transform(lon, lat, 0.0)
        separation = transformed_ref - 0.0  # This gives us the geoid separation
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
