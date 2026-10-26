import os
import warnings

import pytest
from device import Device
from emulator import EMULATOR_PORT, running_emulator


def pytest_addoption(parser):
    parser.addoption("--external-device", action="store_true",
                     help="Use DEVICE_PORT without starting or stopping Wokwi")


@pytest.fixture(scope="session")
def device_port(request):
    port = os.getenv("DEVICE_PORT", EMULATOR_PORT)
    if request.config.getoption("--external-device") or port not in {
        EMULATOR_PORT, "rfc2217://127.0.0.1:4000"
    }:
        yield port
        return
    with running_emulator() as emulator_port:
        yield emulator_port

@pytest.fixture
def device(device_port):
    dev = Device(device_port, timeout=2.0)
    yield dev
    try:
        dev.command("RESET")
    except (TimeoutError, AssertionError) as exc:
        warnings.warn(f"Device RESET during teardown failed: {exc}", RuntimeWarning)
    finally:
        dev.close()
