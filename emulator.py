"""Manage the Wokwi CLI process used by device tests."""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import socket
import subprocess
import tempfile
import time

PROJECT = Path(__file__).resolve().parent / "firmware-emu"
EMULATOR_PORT = "rfc2217://localhost:4000"


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@contextmanager
def running_emulator(startup_timeout=60):
    cli = shutil.which("wokwi-cli")
    if not cli:
        raise RuntimeError("Install wokwi-cli and set WOKWI_CLI_TOKEN to run the emulator.")
    if not os.environ.get("WOKWI_CLI_TOKEN"):
        raise RuntimeError("Set WOKWI_CLI_TOKEN to your Wokwi CLI API token.")
    pio = shutil.which("pio")
    if not pio:
        raise RuntimeError("Install PlatformIO (pip install platformio) to build the firmware.")
    with socket.socket() as probe:
        if probe.connect_ex(("localhost", 4000)) == 0:
            raise RuntimeError("Port 4000 is already in use. Stop the existing emulator or use --external-device.")
    with tempfile.TemporaryDirectory(prefix="wokwi-") as log_dir, open(
        Path(log_dir) / "emulator.log", "w+b"
    ) as log:
        build = subprocess.run([pio, "run"], cwd=PROJECT, stdout=log,
                               stderr=subprocess.STDOUT, timeout=180)
        if build.returncode:
            log.seek(0)
            raise RuntimeError("Firmware build failed:\n" + log.read().decode(errors="replace"))
        log.seek(0)
        log.truncate()
        process = subprocess.Popen([cli, ".", "--timeout", "0"], cwd=PROJECT,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + startup_timeout
            while True:
                output = Path(log.name).read_text(errors="replace")
                if process.poll() is not None:
                    raise RuntimeError(f"Wokwi exited during startup ({process.returncode}):\n{output}")
                if '"status":"READY"' in output:
                    with socket.create_connection(("localhost", 4000), timeout=1):
                        pass
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Wokwi did not become ready within {startup_timeout}s:\n{output}")
                time.sleep(0.1)
            yield EMULATOR_PORT
        finally:
            stop_process(process)
