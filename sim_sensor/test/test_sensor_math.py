import math

import pytest

pytest.importorskip('rclpy')

from sim_sensor.sensor_node import (MAX_RATE_HZ, MIN_RATE_HZ,  # noqa: E402
                                    depth_to_pressure, validate_rate)


def test_surface_is_atmospheric():
    assert depth_to_pressure(0.0) == pytest.approx(101325.0)


def test_ten_metres_is_about_two_atm():
    assert depth_to_pressure(10.0) == pytest.approx(201_800, rel=0.01)


@pytest.mark.parametrize('v', [MIN_RATE_HZ, 1, 10.0, MAX_RATE_HZ])
def test_valid_rates(v):
    assert validate_rate(v) == ''


@pytest.mark.parametrize('v', [0, -5.0, 0.01, 1000.0, math.nan, math.inf, 'fast', True])
def test_invalid_rates(v):
    assert validate_rate(v) != ''
