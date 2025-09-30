import math

from core.helmert_rr92 import rr92_to_sweref99, sweref99_to_rr92


def test_forward_reverse_round_trip():
    rr92_xyz = (3660000.0, 132000.0, 5205000.0)
    sweref = rr92_to_sweref99(*rr92_xyz)
    back = sweref99_to_rr92(*sweref)
    for a, b in zip(rr92_xyz, back):
        assert math.isclose(a, b, rel_tol=0, abs_tol=1e-6)


def test_forward_matches_reference():
    rr92_xyz = (3660000.0, 132000.0, 5205000.0)
    expected = (3660000.0373189505, 131999.99669628488, 5204999.974348661)
    sweref = rr92_to_sweref99(*rr92_xyz)
    for calc, ref in zip(sweref, expected):
        assert math.isclose(calc, ref, rel_tol=0, abs_tol=1e-6)
