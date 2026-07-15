from __future__ import annotations

import atexit
import json
import logging
import logging.config
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from contextlib import suppress
from pathlib import Path
from typing import Any

import uvicorn

from horticalc.paths import PORTABLE_WRITE_ERROR, app_root, ensure_portable_layout, logs_dir

PORT_RANGE = range(8000, 8101)
HEALTH_ENDPOINT = "/health"
HEALTH_TIMEOUT_SECONDS = 30.0
LOCKFILE_NAME = "horticalc.lock.json"
LOG_FILENAME = "launcher.log"
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 2
NO_BROWSER_ENV = "HORTICALC_NO_BROWSER"
KEEP_SERVER_ENV = "HORTICALC_KEEP_SERVER"
FALLBACK_GRACE_SECONDS = 5.0
LOCK_READ_GRACE_SECONDS = 0.5
STALE_PROFILE_AGE_SECONDS = 7 * 24 * 60 * 60
PROFILE_DIR_NAME = "browser_profiles"
SESSION_DIR_NAME = "launcher_sessions"
PROFILE_DIR_PATTERN = re.compile(r"^profile-(\d+)-(?:(\d+)-.+|\d+)$")

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


def _logging_config(log_file: Path, *, packaged: bool | None = None) -> dict[str, Any]:
    packaged = bool(getattr(sys, "frozen", False)) if packaged is None else packaged
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": log_format}},
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "level": "INFO",
                "filename": str(log_file),
                "encoding": "utf-8",
                "maxBytes": LOG_MAX_BYTES,
                "backupCount": LOG_BACKUP_COUNT,
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
            "uvicorn.access": {
                "handlers": ["file", "console"],
                "level": "WARNING" if packaged else "INFO",
                "propagate": False,
            },
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


def _write_json_stream(handle, payload: dict[str, Any]) -> None:
    json.dump(payload, handle, indent=2)
    handle.flush()
    os.fsync(handle.fileno())


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.tmp-",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            _write_json_stream(temp_file, payload)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            with suppress(OSError):
                temp_path.unlink(missing_ok=True)


def _lock_payload(port: int, pid: int | None = None) -> dict[str, Any]:
    return {
        "pid": pid or os.getpid(),
        "port": port,
        "started_at": time.time(),
    }


def read_lockfile(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    port = payload.get("port")
    pid = payload.get("pid")
    if not isinstance(port, int) or port not in PORT_RANGE:
        return None
    if not isinstance(pid, int) or pid <= 0:
        return None
    return payload


def write_lockfile(path: Path, port: int, pid: int | None = None) -> None:
    _atomic_write_json(path, _lock_payload(port, pid))


def claim_lockfile(path: Path, port: int, pid: int | None = None) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return False
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            _write_json_stream(handle, _lock_payload(port, pid))
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return True


def remove_lockfile(path: Path, expected_pid: int | None = None) -> None:
    if expected_pid is not None:
        payload = read_lockfile(path)
        if payload is None or payload.get("pid") != expected_pid:
            return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logging.exception("Failed to remove lockfile: %s", path)


def wait_for_existing_server(
    lock_path: Path,
    timeout_seconds: float = HEALTH_TIMEOUT_SECONDS,
    malformed_grace_seconds: float = LOCK_READ_GRACE_SECONDS,
) -> int | None:
    health_deadline = time.monotonic() + timeout_seconds
    malformed_deadline = time.monotonic() + malformed_grace_seconds
    while lock_path.exists():
        payload = read_lockfile(lock_path)
        if payload is None:
            if time.monotonic() < malformed_deadline:
                time.sleep(0.05)
                continue
            remove_lockfile(lock_path)
            return None

        port = payload["port"]
        owner_pid = payload["pid"]
        if health_ok(port):
            return port
        if not _pid_is_running(owner_pid):
            remove_lockfile(lock_path, expected_pid=owner_pid)
            return None
        if time.monotonic() >= health_deadline:
            raise RuntimeError(f"Existing Horticalc process {owner_pid} did not become healthy.")
        time.sleep(0.1)
    return None


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
        f"Server failed to become healthy within {timeout_seconds:.0f} seconds. See the log file for details."
    )


def _which_first(candidates: tuple[str, ...]) -> Path | None:
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return Path(found)
    return None


def find_browser_executable() -> Path | None:
    if os.name == "nt":
        browser = _which_first(WINDOWS_BROWSER_CANDIDATES)
        if browser:
            return browser
        for env_name, *parts in WINDOWS_BROWSER_LOCATIONS:
            base = os.environ.get(env_name)
            if not base:
                continue
            candidate = Path(base, *parts)
            if candidate.exists():
                return candidate
        return None
    return _which_first(LINUX_BROWSER_CANDIDATES)


def _process_identity(pid: int) -> int | None:
    if pid <= 0:
        return None
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not process:
                return None
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            try:
                if not ctypes.windll.kernel32.GetProcessTimes(
                    process,
                    ctypes.byref(creation),
                    ctypes.byref(exit_time),
                    ctypes.byref(kernel),
                    ctypes.byref(user),
                ):
                    return None
                return (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            finally:
                ctypes.windll.kernel32.CloseHandle(process)
        except (AttributeError, OSError):
            return None
    try:
        return (Path("/proc") / str(pid)).stat().st_ctime_ns
    except OSError:
        return None


def create_profile_dir(root: Path) -> Path:
    profile_root = root / "user" / PROFILE_DIR_NAME
    profile_root.mkdir(parents=True, exist_ok=True)
    owner_pid = os.getpid()
    identity = _process_identity(owner_pid) or 0
    return Path(
        tempfile.mkdtemp(
            prefix=f"profile-{owner_pid}-{identity}-",
            dir=profile_root,
        )
    )


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


def launcher_session_dir(root: Path) -> Path:
    path = root / "user" / SESSION_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_launcher_session(root: Path, pid: int | None = None) -> Path:
    owner_pid = pid or os.getpid()
    path = launcher_session_dir(root) / f"session-{owner_pid}-{time.time_ns()}.json"
    _atomic_write_json(
        path,
        {
            "pid": owner_pid,
            "process_identity": _process_identity(owner_pid),
        },
    )
    return path


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not process:
                return False
            ctypes.windll.kernel32.CloseHandle(process)
            return True
        except (AttributeError, OSError):
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def active_launcher_sessions(root: Path) -> list[Path]:
    active: list[Path] = []
    for path in launcher_session_dir(root).glob("session-*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            pid = payload.get("pid")
            expected_identity = payload.get("process_identity")
        except (OSError, json.JSONDecodeError):
            pid = None
            expected_identity = None
        current_identity = _process_identity(pid) if isinstance(pid, int) else None
        identity_matches = (
            expected_identity is None or current_identity is None or expected_identity == current_identity
        )
        if isinstance(pid, int) and _pid_is_running(pid) and identity_matches:
            active.append(path)
        else:
            path.unlink(missing_ok=True)
    return active


def cleanup_stale_profile_dirs(root: Path, now: float | None = None) -> None:
    profile_root = root / "user" / PROFILE_DIR_NAME
    if not profile_root.exists():
        return
    current_time = time.time() if now is None else now
    for profile_dir in profile_root.glob("profile-*"):
        match = PROFILE_DIR_PATTERN.match(profile_dir.name)
        if not match or not profile_dir.is_dir():
            continue
        owner_pid = int(match.group(1))
        expected_identity = int(match.group(2)) if match.group(2) else None
        try:
            old_enough = current_time - profile_dir.stat().st_mtime >= STALE_PROFILE_AGE_SECONDS
        except OSError:
            continue
        current_identity = _process_identity(owner_pid)
        owner_matches = _pid_is_running(owner_pid) and (
            expected_identity is None or current_identity is None or expected_identity == current_identity
        )
        if old_enough and not owner_matches:
            cleanup_profile_dir(profile_dir)


def wait_for_launcher_sessions(root: Path, grace_seconds: float = FALLBACK_GRACE_SECONDS) -> None:
    empty_since: float | None = None
    while empty_since is None or time.monotonic() - empty_since < grace_seconds:
        if active_launcher_sessions(root):
            empty_since = None
        elif empty_since is None:
            empty_since = time.monotonic()
        time.sleep(0.1)


def wait_for_app_window(
    url: str,
    root: Path,
    profile_dir: Path,
    logger: logging.Logger,
    browser: Path,
) -> bool:
    session_path = create_launcher_session(root)
    browser_proc = launch_app_window(url, profile_dir, logger, browser)
    if browser_proc is None:
        remove_lockfile(session_path)
        return False
    try:
        browser_proc.wait()
    finally:
        remove_lockfile(session_path)
        cleanup_profile_dir(profile_dir)
    return True


def stop_server(
    server: uvicorn.Server,
    server_thread: threading.Thread,
    lock_path: Path,
    timeout_seconds: float = 5.0,
) -> None:
    server.should_exit = True
    server_thread.join(timeout=timeout_seconds)
    remove_lockfile(lock_path, expected_pid=os.getpid())


def require_server_health(
    server: uvicorn.Server,
    server_thread: threading.Thread,
    lock_path: Path,
    port: int,
    log_file: Path,
) -> None:
    healthy, error_message = wait_for_health(port, HEALTH_TIMEOUT_SECONDS, server_thread)
    if healthy:
        return
    stop_server(server, server_thread, lock_path)
    fail_fast(error_message or "Server failed to start.", log_file)


def wait_for_fallback_shutdown(
    server_thread: threading.Thread,
    logger: logging.Logger,
    compatibility_flag_set: bool,
) -> None:
    if compatibility_flag_set:
        logger.info("%s is set; fallback server remains running.", KEEP_SERVER_ENV)
    else:
        logger.info("System-browser fallback keeps the local server running.")
    server_thread.join()


def wait_for_existing_server_fallback(root: Path, logger: logging.Logger) -> None:
    session_path = create_launcher_session(root)
    logger.info("System-browser fallback keeps this launcher session active.")
    try:
        while True:
            time.sleep(3600)
    finally:
        remove_lockfile(session_path)


def main() -> None:
    root = app_root()
    try:
        ensure_portable_layout(root)
        cleanup_stale_profile_dirs(root)
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
    while True:
        try:
            existing_port = wait_for_existing_server(lock_path)
        except RuntimeError as exc:
            fail_fast(str(exc), log_file)
            return
        if existing_port is not None:
            url = f"http://127.0.0.1:{existing_port}/"
            logger.info("Existing server detected on port %s.", existing_port)
            if no_browser:
                logger.info("%s is set; skipping browser launch.", NO_BROWSER_ENV)
                return
            logger.info("Opening browser for existing server.")
            browser = find_browser_executable()
            if browser:
                profile_dir = create_profile_dir(root)
                if not wait_for_app_window(url, root, profile_dir, logger, browser):
                    cleanup_profile_dir(profile_dir)
                    webbrowser.open(url)
                    wait_for_existing_server_fallback(root, logger)
            else:
                webbrowser.open(url)
                wait_for_existing_server_fallback(root, logger)
            return

        port = find_free_port()
        if port is None:
            fail_fast("No free port found in the 8000-8100 range.", log_file)
            return
        if claim_lockfile(lock_path, port):
            break
        logger.info("Another launcher claimed the server lock; waiting for it.")

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_config=_logging_config(log_file),
        access_log=not bool(getattr(sys, "frozen", False)),
    )
    server = uvicorn.Server(config)

    atexit.register(remove_lockfile, lock_path, os.getpid())
    server_thread = threading.Thread(target=server.run, name="uvicorn-server", daemon=True)
    server_thread.start()

    try:
        if no_browser:
            logger.info("%s is set; waiting for /health without launching a browser.", NO_BROWSER_ENV)
            require_server_health(server, server_thread, lock_path, port, log_file)
            server_thread.join()
            return

        require_server_health(server, server_thread, lock_path, port, log_file)

        url = f"http://127.0.0.1:{port}/"
        browser = find_browser_executable()
        profile_dir = create_profile_dir(root)
        if browser is None or not wait_for_app_window(url, root, profile_dir, logger, browser):
            cleanup_profile_dir(profile_dir)
            logger.warning("No supported Chromium-based browser found; falling back to system default.")
            webbrowser.open(url)
            wait_for_fallback_shutdown(server_thread, logger, keep_server)
            return

        logger.info("App window closed; waiting for other launcher sessions.")
        wait_for_launcher_sessions(root)
        stop_server(server, server_thread, lock_path)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
        stop_server(server, server_thread, lock_path)


if __name__ == "__main__":
    main()
