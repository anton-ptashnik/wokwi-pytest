import pytest
from assertions import assert_error


def test_status_values(device):
    r = device.command("STATUS")
    assert r["status"] == "OK"
    assert "heap" in r
    assert "pwm" in r

    heap = r["heap"]
    pwm = r["pwm"]

    assert isinstance(heap, int)
    assert isinstance(pwm, int)
    assert heap >= 0
    assert pwm >= 0


@pytest.mark.parametrize("value", ["INVALID_COMMAND", "SETPWM 55", "SET LED ON OFF"])
def test_invalid_command(device, value):
    r = device.command(value)
    assert_error(r, "UNKNOWN_COMMAND")


@pytest.mark.parametrize("value", ["SET LED NO", "SET LED 1", "SET LED YES", "SET LED "])
def test_invalid_led_value(device, value):
    r = device.command(value)
    assert_error(r, "INVALID_VALUE")


@pytest.mark.parametrize("value", ["SET PWM high", "SET PWM low", "SET PWM 10a", "SET PWM a10", "SET PWM "])
def test_invalid_pwm_value(device, value):
    r = device.command(value)
    assert_error(r, "INVALID_VALUE")
