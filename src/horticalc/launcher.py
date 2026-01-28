from __future__ import annotations

import atexit
import json
import logging
import logging.config
import os
import shutil
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

import subprocess
import uvicorn

from horticalc.paths import PORTABLE_WRITE_ERROR, app_root, ensure_portable_layout, logs_dir


PORT_RANGE = range(8000, 8101)
HEALTH_ENDPOINT = "/health"
HEALTH_TIMEOUT_SECONDS = 30.0
LOCKFILE_NAME = "horticalc.lock.json"
LOG_FILENAME = "launcher.log"
NO_BROWSER_ENV = "HORTICALC_NO_BROWSER"
KEEP_SERVER_ENV = "HORTICALC_KEEP_SERVER"
FALLBACK_GRACE_SECONDS = 5.0
PROFILE_DIR_NAME = "browser_profiles"

WINDOWS_BROWSER_CANDIDATES = (
    "msedge.exe",
    "chrome.exe",
    "chromium.exe",
)
LINUX_BROWSER_CANDIDATES = (
    "microsoft-edge",
    "google-chrome",
    "chromium",
    "chromium-browser",
)
WINDOWS_BROWSER_LOCATIONS = (
    ("PROGRAMFILES", "Microsoft", "Edge", "Application", "msedge.exe"),
    ("PROGRAMFILES(X86)", "Microsoft", "Edge", "Application", "msedge.exe"),
    ("LOCALAPPDATA", "Microsoft", "Edge", "Application", "msedge.exe"),
    ("PROGRAMFILES", "Google", "Chrome", "Application", "chrome.exe"),
    ("PROGRAMFILES(X86)", "Google", "Chrome", "Application", "chrome.exe"),
    ("LOCALAPPDATA", "Google", "Chrome", "Application", "chrome.exe"),
    ("PROGRAMFILES", "Chromium", "Application", "chrome.exe"),
    ("PROGRAMFILES(X86)", "Chromium", "Application", "chrome.exe"),
    ("LOCALAPPDATA", "Chromium", "Application", "chrome.exe"),
)


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


def wait_for_health(
    port: int,
    timeout_seconds: float,
    server_thread: threading.Thread,
) -> tuple[bool, str | None]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if health_ok(port):
            return True, None
        if not server_thread.is_alive():
            return False, "Server stopped unexpectedly. See the log file for details."
        time.sleep(0.5)
    return False, (
        f"Server failed to become healthy within {timeout_seconds:.0f} seconds. "
        "See the log file for details."
    )


def find_browser_executable() -> Path | None:
    if os.name == "nt":
        for candidate in WINDOWS_BROWSER_CANDIDATES:
            found = shutil.which(candidate)
            if found:
                return Path(found)
        for env_name, *parts in WINDOWS_BROWSER_LOCATIONS:
            base = os.environ.get(env_name)
            if not base:
                continue
            candidate = Path(base, *parts)
            if candidate.exists():
                return candidate
        return None
    for candidate in LINUX_BROWSER_CANDIDATES:
        found = shutil.which(candidate)
        if found:
            return Path(found)
    return None


def create_profile_dir(root: Path) -> Path:
    profile_root = root / "user" / PROFILE_DIR_NAME
    profile_root.mkdir(parents=True, exist_ok=True)
    suffix = f"{os.getpid()}-{int(time.time())}"
    profile_dir = profile_root / f"profile-{suffix}"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


def launch_app_window(
    url: str,
    profile_dir: Path,
    logger: logging.Logger,
    browser: Path | None = None,
) -> subprocess.Popen | None:
    if not browser:
        return None
    args = [
        str(browser),
        f"--app={url}",
        "--new-window",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        return subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError:
        logger.exception("Failed to launch browser app window.")
        return None


def cleanup_profile_dir(profile_dir: Path) -> None:
    shutil.rmtree(profile_dir, ignore_errors=True)


def stop_server(
    server: uvicorn.Server,
    server_thread: threading.Thread,
    lock_path: Path,
    timeout_seconds: float = 5.0,
) -> None:
    server.should_exit = True
    server_thread.join(timeout=timeout_seconds)
    remove_lockfile(lock_path)


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
    keep_server = _env_flag(KEEP_SERVER_ENV)

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
        browser = find_browser_executable()
        if browser:
            profile_dir = create_profile_dir(root)
            if launch_app_window(url, profile_dir, logger, browser) is None:
                cleanup_profile_dir(profile_dir)
                webbrowser.open(url)
        else:
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

    try:
        if no_browser:
            logger.info("%s is set; waiting for /health without launching a browser.", NO_BROWSER_ENV)
            healthy, error_message = wait_for_health(port, HEALTH_TIMEOUT_SECONDS, server_thread)
            if not healthy:
                stop_server(server, server_thread, lock_path)
                fail_fast(error_message or "Server failed to start.", log_file)
                return
            server_thread.join()
            return

        healthy, error_message = wait_for_health(port, HEALTH_TIMEOUT_SECONDS, server_thread)
        if not healthy:
            stop_server(server, server_thread, lock_path)
            fail_fast(error_message or "Server failed to start.", log_file)
            return

        url = f"http://127.0.0.1:{port}/"
        browser = find_browser_executable()
        profile_dir = create_profile_dir(root)
        browser_proc = launch_app_window(url, profile_dir, logger, browser)
        if browser_proc is None:
            cleanup_profile_dir(profile_dir)
            logger.warning("No supported Chromium-based browser found; falling back to system default.")
            webbrowser.open(url)
            if keep_server:
                logger.info("%s is set; keeping server running.", KEEP_SERVER_ENV)
                server_thread.join()
                return
            logger.info("Stopping server after fallback grace period of %.1f seconds.", FALLBACK_GRACE_SECONDS)
            time.sleep(FALLBACK_GRACE_SECONDS)
            stop_server(server, server_thread, lock_path)
            return

        try:
            browser_proc.wait()
        finally:
            cleanup_profile_dir(profile_dir)

        stop_server(server, server_thread, lock_path)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
        stop_server(server, server_thread, lock_path)


if __name__ == "__main__":
    main()
