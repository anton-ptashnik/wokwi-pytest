"""Lifecycle tests that do not need Wokwi credentials or hardware."""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

import emulator


@pytest.fixture
def runtime(monkeypatch):
    monkeypatch.setenv("WOKWI_CLI_TOKEN", "test-token")
    with patch.object(emulator.shutil, "which", side_effect=lambda name: name), \
         patch.object(emulator.socket, "socket") as socket_mock, \
         patch.object(emulator.socket, "create_connection"), \
         patch.object(emulator.subprocess, "run") as build, \
         patch.object(emulator.subprocess, "Popen") as start:
        socket_mock.return_value.__enter__.return_value.connect_ex.return_value = 1
        build.return_value.returncode = 0
        process = MagicMock()
        process.poll.return_value = None

        def launch(*args, **kwargs):
            kwargs["stdout"].write(b'{"status":"READY"}\n')
            kwargs["stdout"].flush()
            return process

        start.side_effect = launch
        yield process, build, start, socket_mock


def test_session_starts_and_stops_even_when_test_fails(runtime):
    process, build, start, _ = runtime
    with pytest.raises(ValueError, match="test failed"):
        with emulator.running_emulator() as port:
            assert port == emulator.EMULATOR_PORT
            process.terminate.assert_not_called()
            raise ValueError("test failed")
    build.assert_called_once()
    assert start.call_args.args[0][-2:] == ["--timeout", "0"]
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)


def test_early_exit_reports_error(runtime):
    process, *_ = runtime
    process.poll.return_value = 1
    process.returncode = 1
    with pytest.raises(RuntimeError, match="exited during startup"):
        with emulator.running_emulator():
            pytest.fail("Must not yield an exited emulator")


def test_startup_timeout_stops_process(runtime):
    process, _, start, _ = runtime
    start.side_effect = None
    start.return_value = process
    with pytest.raises(RuntimeError, match="did not become ready"):
        with emulator.running_emulator(startup_timeout=0):
            pytest.fail("Must not yield before READY")
    process.terminate.assert_called_once()


def test_busy_port_does_not_start_or_stop_emulator(runtime):
    process, build, start, socket_mock = runtime
    socket_mock.return_value.__enter__.return_value.connect_ex.return_value = 0
    with pytest.raises(RuntimeError, match="already in use"):
        with emulator.running_emulator():
            pytest.fail("Must not reuse an existing emulator")
    build.assert_not_called()
    start.assert_not_called()
    process.terminate.assert_not_called()


def test_failed_build_does_not_start_emulator(runtime):
    _, build, start, _ = runtime
    build.return_value.returncode = 1
    with pytest.raises(RuntimeError, match="Firmware build failed"):
        with emulator.running_emulator():
            pytest.fail("Must not run a stale build")
    start.assert_not_called()


def test_shutdown_kills_process_that_ignores_termination():
    process = MagicMock()
    process.poll.return_value = None
    process.wait.side_effect = [subprocess.TimeoutExpired("wokwi-cli", 5), 0]
    emulator.stop_process(process)
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
