import pytest

from core import height_rfn


def test_rfn_separation_stockholm():
    model = height_rfn.DEFAULT_MODEL
    separation = model.separation(59.3293, 18.0686)
    assert separation == pytest.approx(0.58018, abs=1e-5)


def test_rfn_round_trip():
    model = height_rfn.DEFAULT_MODEL
    ellipsoidal_height = 50.0
    orthometric_height = model.ellipsoidal_to_orthometric(
        59.3293, 18.0686, ellipsoidal_height
    )
    assert orthometric_height == pytest.approx(49.41982, abs=1e-5)

    restored = model.orthometric_to_ellipsoidal(59.3293, 18.0686, orthometric_height)
    assert restored == pytest.approx(ellipsoidal_height, abs=1e-5)


def test_rfn_out_of_bounds():
    model = height_rfn.DEFAULT_MODEL
    with pytest.raises(height_rfn.RFNHeightUnavailable):
        model.separation(72.0, 18.0)
