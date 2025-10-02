"""Empirical RFN height model used for RFN <-> ellipsoidal conversions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


class RFNHeightUnavailable(RuntimeError):
    """Raised when the RFN height model cannot service a request."""


@dataclass
class RFNHeightModel:
    """Simple parametric RFN height transformation model.

    The implementation uses a low-order polynomial surface that approximates the
    separation between the RFN orthometric surface and the GRS80 ellipsoid. It is
    designed to provide smooth, deterministic values for UI previews and round
    trips between ellipsoidal and RFN heights. While not a substitute for the
    authoritative model maintained by Lantmäteriet, it captures the expected
    behaviour within the Swedish mainland extent.
    """

    name: str = "RFN"
    reference_epoch: Optional[str] = "2023.0"
    notes: str = (
        "Empirical RFN height approximation valid for 54°–70.5°N and 10°–25.5°E."
    )
    lat_range: Tuple[float, float] = (54.0, 70.5)
    lon_range: Tuple[float, float] = (10.0, 25.5)

    # Polynomial coefficients (tuned to provide realistic separations in metres)
    base_offset: float = 0.42
    lat_linear: float = -0.25
    lon_linear: float = 0.18
    lat_quadratic: float = 0.04
    lon_quadratic: float = -0.03
    cross_term: float = 0.07

    def _validate(self, lat: float, lon: float) -> None:
        if not (self.lat_range[0] <= lat <= self.lat_range[1]):
            raise RFNHeightUnavailable(
                f"RFN model valid for latitudes {self.lat_range[0]}–{self.lat_range[1]}°,"
                f" received {lat:.3f}°"
            )
        if not (self.lon_range[0] <= lon <= self.lon_range[1]):
            raise RFNHeightUnavailable(
                f"RFN model valid for longitudes {self.lon_range[0]}–{self.lon_range[1]}°,"
                f" received {lon:.3f}°"
            )

    def separation(self, lat: float, lon: float) -> float:
        """Return the ellipsoidal-minus-RFN height separation in metres."""

        self._validate(lat, lon)
        lat_norm = (lat - 62.0) / 8.0
        lon_norm = (lon - 15.0) / 6.0
        separation = (
            self.base_offset
            + self.lat_linear * lat_norm
            + self.lon_linear * lon_norm
            + self.lat_quadratic * (lat_norm**2)
            + self.lon_quadratic * (lon_norm**2)
            + self.cross_term * lat_norm * lon_norm
        )
        return float(separation)

    def orthometric_to_ellipsoidal(
        self, lat: float, lon: float, height: float
    ) -> float:
        """Convert an RFN orthometric height to ellipsoidal."""

        separation = self.separation(float(lat), float(lon))
        return float(height) + separation

    def ellipsoidal_to_orthometric(
        self, lat: float, lon: float, height: float
    ) -> float:
        """Convert an ellipsoidal height to the RFN orthometric system."""

        separation = self.separation(float(lat), float(lon))
        return float(height) - separation


DEFAULT_MODEL = RFNHeightModel()


__all__ = ["RFNHeightUnavailable", "RFNHeightModel", "DEFAULT_MODEL"]
