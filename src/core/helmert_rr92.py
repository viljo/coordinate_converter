"""RR92 (RFN) 7-parameter Helmert transformation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np

# Parameters adapted from Lantmäteriet technical guidance for the
# transformation between RR92 (RFN) and SWEREF99/SWEREF93.
# Units: translations in metres, rotations in arc-seconds, scale in ppm.


@dataclass(frozen=True)
class HelmertParameters:
    dx: float
    dy: float
    dz: float
    rx: float
    ry: float
    rz: float
    scale_ppm: float

    def as_vector(self) -> np.ndarray:
        return np.array([self.dx, self.dy, self.dz], dtype=float)


RR92_TO_SWEREF99 = HelmertParameters(
    dx=0.0048,
    dy=-0.0012,
    dz=0.0065,
    rx=-0.00083,
    ry=0.00143,
    rz=-0.00129,
    scale_ppm=-0.0012,
)


def _rotation_matrix(params: HelmertParameters) -> np.ndarray:
    """Build a rotation matrix using exact sine/cosine values."""

    rad = np.deg2rad(np.array([params.rx, params.ry, params.rz]) / 3600.0)
    rx, ry, rz = rad
    cx, cy, cz = np.cos([rx, ry, rz])
    sx, sy, sz = np.sin([rx, ry, rz])

    return np.array(
        [
            [cy * cz, cz * sx * sy - cx * sz, sx * sz + cx * cz * sy],
            [cy * sz, cx * cz + sx * sy * sz, cx * sy * sz - cz * sx],
            [-sy, cy * sx, cx * cy],
        ],
        dtype=float,
    )


def _apply(params: HelmertParameters, xyz: Iterable[float], inverse: bool = False) -> Tuple[float, float, float]:
    vector = np.array(tuple(xyz), dtype=float)
    if vector.shape != (3,):
        raise ValueError("Helmert transform expects 3D coordinates")

    translation = params.as_vector()
    rot = _rotation_matrix(params)
    scale = 1.0 + params.scale_ppm * 1e-6

    if inverse:
        scaled = (vector - translation) / scale
        rotated = rot.T @ scaled
    else:
        rotated = rot @ vector
        rotated = rotated * scale
        rotated = rotated + translation
    return tuple(float(c) for c in rotated)


def rr92_to_sweref99(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Transform RR92 geocentric coordinates into SWEREF99."""

    return _apply(RR92_TO_SWEREF99, (x, y, z), inverse=False)


def sweref99_to_rr92(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Transform SWEREF99 geocentric coordinates into RR92."""

    return _apply(RR92_TO_SWEREF99, (x, y, z), inverse=True)


__all__ = [
    "HelmertParameters",
    "RR92_TO_SWEREF99",
    "rr92_to_sweref99",
    "sweref99_to_rr92",
]
