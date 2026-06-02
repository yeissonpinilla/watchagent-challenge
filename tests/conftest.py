import pytest
from types import SimpleNamespace


@pytest.fixture
def baseline():
    return SimpleNamespace(
        temp_mean=15.0,
        temp_std=3.0,
        temp_p5=10.0,
        temp_p95=20.0,
        temp_min=10.0,
        temp_max=20.0,
        wind_mean=10.0,
        wind_std=2.0,
        precip_mean=0.5,
    )


@pytest.fixture
def reading():
    return SimpleNamespace(
        city="Toronto",
        timestamp="2026-05-01T12:00",
        temperature_2m=16.0,
        wind_speed_10m=10.0,
        precipitation=0.0,
    )
