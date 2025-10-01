import pytest

from core import height_rfn


def test_rfn_height_unavailable():
    with pytest.raises(height_rfn.RFNHeightUnavailable):
        height_rfn.DEFAULT_MODEL.ellipsoidal_to_orthometric(59.3, 18.0, 45.0)


@pytest.mark.xfail(
    reason="Awaiting publication of RFN height parameters",
    raises=height_rfn.RFNHeightUnavailable,
)
def test_rfn_height_specific_value():
    height_rfn.DEFAULT_MODEL.orthometric_to_ellipsoidal(59.3, 18.0, 10.0)
