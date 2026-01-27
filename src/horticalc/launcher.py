from __future__ import annotations

import atexit
import json
import logging
import logging.config
import os
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import uvicorn

from horticalc.paths import PORTABLE_WRITE_ERROR, app_root, ensure_portable_layout, logs_dir


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


def start_server(app: Any, log_file: Path) -> tuple[uvicorn.Server, threading.Thread, int]:
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=0,
        log_config=_logging_config(log_file),
        access_log=True,
    )
    server = uvicorn.Server(config)
    sock = config.bind_socket()
    port = sock.getsockname()[1]
    server_thread = threading.Thread(
        target=server.run,
        kwargs={"sockets": [sock]},
        name="uvicorn-server",
        daemon=True,
    )
    server_thread.start()
    return server, server_thread, port


def _close_window(window: Any, logger: logging.Logger, webview_module: Any) -> None:
    for method_name in ("destroy", "close"):
        method = getattr(window, method_name, None)
        if callable(method):
            try:
                method()
                return
            except Exception:
                logger.exception("Failed to close webview window.")
                return
    destroy_window = getattr(webview_module, "destroy_window", None)
    if callable(destroy_window):
        try:
            destroy_window()
        except Exception:
            logger.exception("Failed to close webview window via module helper.")


def open_webview(url: str, logger: logging.Logger) -> None:
    import webview

    window = webview.create_window("Horticalc", url)

    def _on_closed() -> None:
        logger.info("Webview window closed.")

    try:
        window.events.closed += _on_closed
    except Exception:
        logger.exception("Failed to register window close handler.")

    def _handle_signal(signum: int, _frame: Any) -> None:
        logger.info("Shutdown requested (signal %s).", signum)
        _close_window(window, logger, webview)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_signal)

    webview.start()


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

    from api.app import create_app

    lock_path = lockfile_path(root)
    lock_data = read_lockfile(lock_path)
    if lock_data and health_ok(lock_data["port"]):
        url = f"http://127.0.0.1:{lock_data['port']}/"
        logger.info("Existing server detected on port %s.", lock_data["port"])
        if no_browser:
            logger.info("%s is set; skipping UI launch.", NO_BROWSER_ENV)
            return
        logger.info("Opening embedded window for existing server.")
        open_webview(url, logger)
        return
    if lock_path.exists():
        logger.info("Stale lockfile detected; removing %s.", lock_path)
        remove_lockfile(lock_path)

    app = create_app()
    server, server_thread, port = start_server(app, log_file)
    write_lockfile(lock_path, port)
    atexit.register(remove_lockfile, lock_path)

    ready_event = threading.Event()
    error_event = threading.Event()
    error_holder: dict[str, str] = {}
    logger.info("Waiting for /health before showing UI.")
    wait_for_health(port, HEALTH_TIMEOUT_SECONDS, ready_event, error_event, error_holder)
    if error_event.is_set():
        server.should_exit = True
        server_thread.join(timeout=5)
        remove_lockfile(lock_path)
        fail_fast(error_holder.get("message", "Server failed to start."), log_file)
        return
    if not server_thread.is_alive():
        remove_lockfile(lock_path)
        fail_fast("Server stopped unexpectedly. See the log file for details.", log_file)
        return

    try:
        if no_browser:
            logger.info("%s is set; keeping server running without UI.", NO_BROWSER_ENV)
            server_thread.join()
            return
        url = f"http://127.0.0.1:{port}/"
        open_webview(url, logger)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)
        remove_lockfile(lock_path)


if __name__ == "__main__":
    main()
