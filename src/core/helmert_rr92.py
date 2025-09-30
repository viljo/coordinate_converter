"""RR92 (RFN) 7-parameter Helmert transformation."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Iterable, Tuple

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

    def as_vector(self) -> Tuple[float, float, float]:
        return (float(self.dx), float(self.dy), float(self.dz))


RR92_TO_SWEREF99 = HelmertParameters(
    dx=0.0048,
    dy=-0.0012,
    dz=0.0065,
    rx=-0.00083,
    ry=0.00143,
    rz=-0.00129,
    scale_ppm=-0.0012,
)


def _rotation_matrix(params: HelmertParameters) -> Tuple[Tuple[float, float, float], ...]:
    """Build a rotation matrix using exact sine/cosine values."""

    rx = radians(params.rx / 3600.0)
    ry = radians(params.ry / 3600.0)
    rz = radians(params.rz / 3600.0)

    cx, cy, cz = cos(rx), cos(ry), cos(rz)
    sx, sy, sz = sin(rx), sin(ry), sin(rz)

    return (
        (cy * cz, cz * sx * sy - cx * sz, sx * sz + cx * cz * sy),
        (cy * sz, cx * cz + sx * sy * sz, cx * sy * sz - cz * sx),
        (-sy, cy * sx, cx * cy),
    )


def _dot_row(row: Tuple[float, float, float], vector: Tuple[float, float, float]) -> float:
    return row[0] * vector[0] + row[1] * vector[1] + row[2] * vector[2]


def _matrix_transpose(matrix: Tuple[Tuple[float, float, float], ...]) -> Tuple[Tuple[float, float, float], ...]:
    return tuple(tuple(matrix[row][col] for row in range(3)) for col in range(3))


def _apply(
    params: HelmertParameters, xyz: Iterable[float], inverse: bool = False
) -> Tuple[float, float, float]:
    vector = tuple(float(component) for component in xyz)
    if len(vector) != 3:
        raise ValueError("Helmert transform expects 3D coordinates")

    translation = params.as_vector()
    rot = _rotation_matrix(params)
    scale = 1.0 + params.scale_ppm * 1e-6

    if inverse:
        scaled = tuple((vector[i] - translation[i]) / scale for i in range(3))
        rot_t = _matrix_transpose(rot)
        rotated = tuple(_dot_row(rot_t[row], scaled) for row in range(3))
    else:
        rotated_vec = tuple(_dot_row(rot[row], vector) for row in range(3))
        scaled = tuple(component * scale for component in rotated_vec)
        rotated = tuple(scaled[i] + translation[i] for i in range(3))
    return rotated


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
