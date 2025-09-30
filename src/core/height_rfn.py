"""Placeholder RFN height model scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class RFNHeightUnavailable(RuntimeError):
    """Raised when RFN height constants are not configured."""


@dataclass
class RFNHeightModel:
    name: str = "RFN"
    reference_epoch: Optional[str] = None
    notes: str = (
        "RFN height transformation constants per LMV §3.9.3 are not yet published."
    )

    def orthometric_to_ellipsoidal(self, *_args, **_kwargs):  # pragma: no cover - placeholder
        raise RFNHeightUnavailable(self.notes)

    def ellipsoidal_to_orthometric(self, *_args, **_kwargs):  # pragma: no cover - placeholder
        raise RFNHeightUnavailable(self.notes)


DEFAULT_MODEL = RFNHeightModel()


__all__ = ["RFNHeightUnavailable", "RFNHeightModel", "DEFAULT_MODEL"]
