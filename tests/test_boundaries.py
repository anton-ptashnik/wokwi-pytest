import pytest
from assertions import assert_error

@pytest.mark.parametrize("value", [
    0,
    1,
    50,
    99,
    pytest.param(
        100,
        marks=pytest.mark.xfail(reason="Value 100 is not accepted for SET PWM"),
    ),
])
def test_pwm_valid_boundaries(device, value):
    r = device.command(f"SET PWM {value}")
    assert r["status"] == "OK"
    assert r["pwm"] == value

@pytest.mark.parametrize("value", [-1, 101, 999])
def test_pwm_invalid_boundaries(device, value):
    r = device.command(f"SET PWM {value}")
    assert_error(r, "INVALID_VALUE")
