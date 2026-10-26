# PlatformIO / VS Code project

## Build and upload
1. Install Visual Studio Code and the PlatformIO IDE extension.
2. Open this folder (the one containing `platformio.ini`) in VS Code.
3. Connect an ESP32 DevKit board over USB and select its COM port if needed.
4. In the PlatformIO sidebar, run **Build**. For a physical board, run **Upload**.
5. Open **Monitor** at 115200 baud. Close Serial Monitor before running Python tests against the same COM port.

## Wokwi
The project includes `diagram.json` and `wokwi.toml` for use with the Wokwi VS Code extension. Build the project first, then start the Wokwi simulation. The DHT22 is connected to GPIO15 (`esp:D15`); the LED is connected to GPIO2 (`esp:D2`).

## Python automation
The Python tests in the parent `automation/` folder automatically build the firmware,
start one Wokwi CLI simulation for the test session, wait for the firmware's `READY`
message, and stop the simulation after all tests finish (including failures).
The configured RFC2217 port is `localhost:4000`; stop any manually running simulation
before starting the tests.

One-time setup:

1. Install the Python dependencies: `python -m pip install -r requirements.txt`.
2. Install PlatformIO: `python -m pip install platformio`.
3. Install a current [Wokwi CLI](https://docs.wokwi.com/wokwi-ci/cli-installation)
   with RFC2217 support and put `wokwi-cli` on your `PATH`.
4. Get a token from the [Wokwi CI dashboard](https://wokwi.com/dashboard/ci)
   and set the `WOKWI_CLI_TOKEN` environment variable. Keep the token out of source control.

From `automation/`, run:

```sh
export WOKWI_CLI_TOKEN='<your-token>'
python -m pytest -v
```

No `DEVICE_PORT` setting is needed for automatic simulation. Setting it to
`rfc2217://localhost:4000` or `rfc2217://127.0.0.1:4000` also uses automatic simulation.
Startup has a 60-second deadline; firmware builds have a 180-second deadline.
Missing prerequisites, build failures, occupied ports, and simulator startup errors
are reported as setup errors.

For a physical ESP32, set `DEVICE_PORT` to its serial port (115200 baud):

```sh
DEVICE_PORT=/dev/ttyUSB0 python -m pytest -v
```

To use an already running Wokwi simulation without managing its lifecycle:

```sh
DEVICE_PORT=rfc2217://localhost:4000 python -m pytest -v --external-device
```

Other explicitly configured `DEVICE_PORT` values also bypass automatic simulation.
The hardware-free lifecycle tests can be run separately:

```sh
python -m pytest tests/test_emulator.py -v
```
