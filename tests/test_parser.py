import math

import pytest

from core import parser
from core.crs_registry import CRSCode


def test_parse_decimal_defaults_to_sweref():
    parsed = parser.parse("59.3293 18.0686")
    assert parsed.crs == CRSCode.SWEREF99_GEO
    lat, lon = parsed.values[:2]
    assert math.isclose(lat, 59.3293)
    assert math.isclose(lon, 18.0686)


def test_parse_dms_with_height():
    parsed = parser.parse("59°19'45\"N 18°04'30\"E h=12.3", default_crs=CRSCode.WGS84_GEO)
    assert parsed.crs == CRSCode.WGS84_GEO
    lat, lon, height = parsed.values
    assert math.isclose(lat, 59 + 19 / 60 + 45 / 3600)
    assert math.isclose(lon, 18 + 4 / 60 + 30 / 3600)
    assert math.isclose(height, 12.3)


def test_parse_mgrs():
    mgrs_module = pytest.importorskip("mgrs")
    MGRS = mgrs_module.MGRS
    mgrs_string = MGRS().toMGRS(59.3293, 18.0686, MGRSPrecision=5)
    parsed = parser.parse(mgrs_string)
    assert parsed.source_format == "MGRS"
    assert parsed.crs == CRSCode.WGS84_GEO
    assert len(parsed.values) == 2


def test_parse_rt90():
    parsed = parser.parse("6583052 1627548")
    assert parsed.crs == CRSCode.RT90_3021
    assert parsed.values == (6583052.0, 1627548.0)


def test_parse_rr92_xyz():
    parsed = parser.parse("RR92 X=3660000 Y=132000 Z=5205000")
    assert parsed.crs == CRSCode.RR92_XYZ
    assert parsed.values == (3660000.0, 132000.0, 5205000.0)


def test_parse_ddm():
    parsed = parser.parse("59°19.750' N 18°3.200' E")
    lat, lon = parsed.values[:2]
    assert math.isclose(lat, 59 + 19.75 / 60)
    assert math.isclose(lon, 18 + 3.2 / 60)
