from __future__ import annotations

import atexit
import json
import logging
import logging.config
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn

from horticalc.paths import PORTABLE_WRITE_ERROR, app_root, ensure_portable_layout, logs_dir


PORT_RANGE = range(8000, 8101)
HEALTH_ENDPOINT = "/health"
HEALTH_TIMEOUT_SECONDS = 30.0
LOCKFILE_NAME = "horticalc.lock.json"
LOG_FILENAME = "launcher.log"
NO_BROWSER_ENV = "HORTICALC_NO_BROWSER"


def _env_flag(name: str) -> bool:
    value = os.getenv(name, "")
    return value.strip().lower() in {"1", "true", "yes"}


def lockfile_path(root: Path) -> Path:
    return root / "user" / LOCKFILE_NAME


def _logging_config(log_file: Path) -> dict[str, Any]:
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": log_format}},
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "level": "INFO",
                "filename": str(log_file),
                "encoding": "utf-8",
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
        },
        "loggers": {
            "": {"handlers": ["file", "console"], "level": "INFO"},
            "uvicorn": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
        },
    }


def setup_logging(logs_path: Path) -> Path:
    log_file = logs_path / LOG_FILENAME
    config = _logging_config(log_file)
    logging.config.dictConfig(config)
    return log_file


def fail_fast(message: str, log_file: Path | None = None) -> None:
    if log_file:
        logging.error("%s (see %s)", message, log_file)
    else:
        logging.error("%s", message)
    print(message, file=sys.stderr)
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "Horticalc", 0x10)
        except Exception:
            logging.exception("Failed to display Windows message box.")
    sys.exit(1)


def find_free_port() -> int | None:
    for port in PORT_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    return None


def _health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}{HEALTH_ENDPOINT}"


def health_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(_health_url(port), timeout=1) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, ValueError):
        return False


def read_lockfile(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    port = payload.get("port")
    if not isinstance(port, int):
        return None
    return payload


def write_lockfile(path: Path, port: int, pid: int | None = None) -> None:
    payload = {
        "pid": pid or os.getpid(),
        "port": port,
        "started_at": time.time(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def remove_lockfile(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logging.exception("Failed to remove lockfile: %s", path)


def open_browser_when_ready(
    port: int,
    timeout_seconds: float,
    ready_event: threading.Event,
    error_event: threading.Event,
    error_holder: dict[str, str],
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if health_ok(port):
            url = f"http://127.0.0.1:{port}/"
            webbrowser.open(url)
            ready_event.set()
            return
        time.sleep(0.5)
    error_holder["message"] = (
        "Server failed to become healthy within 30 seconds. "
        "See the log file for details."
    )
    error_event.set()


def wait_for_health(
    port: int,
    timeout_seconds: float,
    ready_event: threading.Event,
    error_event: threading.Event,
    error_holder: dict[str, str],
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if health_ok(port):
            ready_event.set()
            return
        time.sleep(0.5)
    error_holder["message"] = (
        "Server failed to become healthy within 30 seconds. "
        "See the log file for details."
    )
    error_event.set()


def main() -> None:
    root = app_root()
    try:
        ensure_portable_layout(root)
        logs_path = logs_dir(root)
    except RuntimeError as exc:
        message = str(exc) or PORTABLE_WRITE_ERROR
        fail_fast(message)
        return

    log_file = setup_logging(logs_path)
    logger = logging.getLogger("horticalc.launcher")
    logger.info("AppRoot resolved to %s", root)
    no_browser = _env_flag(NO_BROWSER_ENV)

    from api.app import app

    lock_path = lockfile_path(root)
    lock_data = read_lockfile(lock_path)
    if lock_data and health_ok(lock_data["port"]):
        url = f"http://127.0.0.1:{lock_data['port']}/"
        logger.info("Existing server detected on port %s.", lock_data["port"])
        if no_browser:
            logger.info("%s is set; skipping browser launch.", NO_BROWSER_ENV)
            return
        logger.info("Opening browser for existing server.")
        webbrowser.open(url)
        return
    if lock_path.exists():
        logger.info("Stale lockfile detected; removing %s.", lock_path)
        remove_lockfile(lock_path)

    port = find_free_port()
    if port is None:
        fail_fast("No free port found in the 8000-8100 range.", log_file)
        return

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_config=_logging_config(log_file),
        access_log=True,
    )
    server = uvicorn.Server(config)

    write_lockfile(lock_path, port)
    atexit.register(remove_lockfile, lock_path)
    server_thread = threading.Thread(target=server.run, name="uvicorn-server", daemon=True)
    server_thread.start()

    ready_event = threading.Event()
    error_event = threading.Event()
    error_holder: dict[str, str] = {}
    if no_browser:
        logger.info("%s is set; waiting for /health without launching a browser.", NO_BROWSER_ENV)
        wait_for_health(port, HEALTH_TIMEOUT_SECONDS, ready_event, error_event, error_holder)
    else:
        browser_thread = threading.Thread(
            target=open_browser_when_ready,
            args=(port, HEALTH_TIMEOUT_SECONDS, ready_event, error_event, error_holder),
            name="browser-launcher",
            daemon=True,
        )
        browser_thread.start()

    try:
        while True:
            if error_event.is_set():
                server.should_exit = True
                server_thread.join(timeout=5)
                remove_lockfile(lock_path)
                fail_fast(error_holder.get("message", "Server failed to start."), log_file)
                return
            if ready_event.is_set():
                break
            if not server_thread.is_alive():
                remove_lockfile(lock_path)
                fail_fast("Server stopped unexpectedly. See the log file for details.", log_file)
                return
            time.sleep(0.1)

        server_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
        server.should_exit = True
        server_thread.join(timeout=5)
        remove_lockfile(lock_path)


if __name__ == "__main__":
    main()
