# Firmware testing with pytest and Wokwi

An experimental project demonstrating how to integrate a firmware emulator into
the pytest framework. Tests exercise ESP32 firmware through its serial command
interface, while pytest fixtures manage the build, emulator startup, and shutdown.
The same device client can also communicate with a physical ESP32.

## How it works

```text
pytest → Device client → PySerial / RFC2217 → Wokwi → ESP32 firmware
```

When a test first requests the device, a session fixture:

1. Checks the Wokwi CLI, API token, PlatformIO, and availability of port 4000.
2. Builds the firmware in `firmware-emu/` with `pio run`.
3. Starts Wokwi CLI and waits for the firmware's JSON `READY` message.
4. Provides the emulator's serial endpoint to the device tests.
5. Stops the emulator at session teardown, including when tests fail.

Each device test opens its own serial connection at 115200 baud with a two-second
response timeout. After the test, its fixture attempts `RESET` and closes the
connection. The emulator is shared across the session.

## Setup

Use Python 3.10 or later. From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in
PowerShell.

Install a current [Wokwi CLI](https://docs.wokwi.com/wokwi-ci/cli-installation)
with RFC2217 support and make sure `wokwi-cli` is on your `PATH`. Obtain an API
token from the [Wokwi CI dashboard](https://wokwi.com/dashboard/ci).

## Run against the emulator

Set the token in your shell and run pytest:

```sh
export WOKWI_CLI_TOKEN='<your-token>'
python -m pytest -v
```

In PowerShell, set the token with `$env:WOKWI_CLI_TOKEN = '<your-token>'`.
Keep tokens out of source control. The test setup reads environment variables
directly; it does not load `.env` files.

No manual simulator startup or `DEVICE_PORT` setting is required. The default
endpoint is `rfc2217://localhost:4000`, matching `firmware-emu/wokwi.toml`.
Firmware builds have a 180-second deadline and emulator startup has a 60-second
deadline. Missing prerequisites and startup failures appear as test setup errors.

To run only the emulator lifecycle tests, without hardware, Wokwi CLI, or a token:

```sh
python -m pytest tests/test_emulator.py -v
```

## Use an external device

For a physical board, build and upload the firmware using PlatformIO, close any
serial monitor, and set its serial port:

```sh
export DEVICE_PORT=/dev/ttyUSB0  # For example, COM5 on Windows
python -m pytest -v
```

For an already running Wokwi simulation:

```sh
export DEVICE_PORT=rfc2217://localhost:4000
python -m pytest -v --external-device
```

The default localhost endpoint and `rfc2217://127.0.0.1:4000` use automatic
emulator management unless `--external-device` is supplied. Other explicit
`DEVICE_PORT` values bypass automatic management. External devices are neither
built nor started or stopped by pytest.

## Project structure

| Path | Purpose |
| --- | --- |
| `device.py` | Serial command client, JSON decoding, and response timeouts |
| `emulator.py` | Firmware build and Wokwi process lifecycle |
| `conftest.py` | Session and per-test device fixtures |
| `assertions.py` | Shared assertions for structured error responses |
| `tests/` | Device behavior and emulator lifecycle tests |
| `firmware-emu/src/main.cpp` | PlatformIO firmware entry point |
| `firmware-emu/sketch.ino` | Arduino sketch version of the firmware |
| `firmware-emu/diagram.json` | Simulated ESP32, LED, and DHT22 circuit |
| `firmware-emu/wokwi.toml` | Firmware paths and RFC2217 configuration |
| `firmware-emu/platformio.ini` | ESP32 build configuration and dependencies |

The device protocol uses newline-terminated commands and JSON responses. Tests
cover `PING`, `STATUS`, `GET TEMP`, LED control, PWM boundaries, invalid inputs,
reset behavior, and an intentionally silent `NO_RESPONSE` command for timeouts.
