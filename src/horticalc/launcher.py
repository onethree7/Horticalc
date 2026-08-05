from __future__ import annotations

import atexit
import importlib
import logging
import logging.config
import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any, Protocol

import uvicorn

from horticalc.activation import (
    clear_activation_handler,
    configure_activation_handler,
    configure_activation_token,
)
from horticalc.paths import PORTABLE_WRITE_ERROR, app_root, ensure_portable_layout, logs_dir
from horticalc.single_instance import (
    HEALTH_TIMEOUT_SECONDS,
    PORT_RANGE,
    activate_existing_instance,
    claim_lockfile,
    health_ok,
    lockfile_path,
    remove_lockfile,
    wait_for_existing_server,
)

LOG_FILENAME = "launcher.log"
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 2
NO_GUI_ENV = "HORTICALC_NO_GUI"
WINDOW_TITLE = "Horticalc GUI"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 900
WINDOW_MIN_SIZE = (960, 640)
WEBVIEW_STORAGE_DIR = "webview"
WEBVIEW2_DOWNLOAD_URL = "https://developer.microsoft.com/microsoft-edge/webview2/"
LINUX_APT_WEBVIEW_COMMAND = "sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1"
LINUX_DNF_WEBVIEW_COMMAND = "sudo dnf install -y webkit2gtk4.1"
SOURCE_WEBVIEW_INSTALL_COMMAND = "python -m pip install -e ."


class RendererDependencyError(RuntimeError):
    """A known, actionable desktop-runtime dependency is unavailable."""


class WebviewWindow(Protocol):
    events: Any

    def restore(self) -> None: ...

    def show(self) -> None: ...


def _env_flag(name: str) -> bool:
    value = os.getenv(name, "")
    return value.strip().lower() in {"1", "true", "yes"}


def webview_storage_path(root: Path) -> Path:
    return root / "user" / WEBVIEW_STORAGE_DIR


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
    logging.config.dictConfig(_logging_config(log_file))
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

            ctypes.windll.user32.MessageBoxW(0, message, WINDOW_TITLE, 0x10)
        except Exception:
            logging.exception("Failed to display Windows message box.")
    raise SystemExit(1)


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


def stop_server(
    server: uvicorn.Server,
    server_thread: threading.Thread,
    lock_path: Path,
    timeout_seconds: float = 5.0,
) -> None:
    server.should_exit = True
    if server_thread is not threading.current_thread():
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


def selected_renderer(platform: str | None = None) -> str:
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        return "edgechromium"
    if platform.startswith("linux"):
        return "gtk"
    raise RuntimeError("Horticalc Desktop supports Windows 10/11 and Linux only.")


def linux_distribution_ids(os_release_path: Path | str = "/etc/os-release") -> set[str]:
    """Return normalized ID and ID_LIKE values without executing os-release."""

    try:
        lines = Path(os_release_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()

    values: set[str] = set()
    for line in lines:
        key, separator, raw_value = line.partition("=")
        if not separator or key not in {"ID", "ID_LIKE"}:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values.update(item.casefold() for item in value.split() if item)
    return values


def linux_webview_install_command(distribution_ids: set[str] | None = None) -> str | None:
    distribution_ids = linux_distribution_ids() if distribution_ids is None else distribution_ids
    if distribution_ids & {"debian", "ubuntu", "linuxmint"}:
        return LINUX_APT_WEBVIEW_COMMAND
    if distribution_ids & {"fedora", "rhel", "centos"}:
        return LINUX_DNF_WEBVIEW_COMMAND
    return None


def renderer_error_message(
    platform: str | None = None,
    distribution_ids: set[str] | None = None,
) -> str:
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        return (
            "Horticalc requires the Microsoft WebView2 Runtime. Install or repair it from "
            f"{WEBVIEW2_DOWNLOAD_URL} and start Horticalc again."
        )
    if platform.startswith("linux"):
        command = linux_webview_install_command(distribution_ids)
        requirement = "Horticalc requires the system GTK 3 and WebKitGTK 4.1 runtime."
        if command:
            return f"{requirement} Install it with: {command}"
        return f"{requirement} Install your distribution's WebKitGTK 4.1 package and start Horticalc again."
    return "Horticalc Desktop supports Windows 10/11 and Linux only."


def gui_initialization_error_message(log_file: Path) -> str:
    return f"Horticalc could not initialize its native desktop window. See {log_file} for technical details."


def ensure_renderer_available(platform: str | None = None) -> None:
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        try:
            winforms = importlib.import_module("webview.platforms.winforms")
            if getattr(winforms, "renderer", None) != "edgechromium":
                raise RendererDependencyError(renderer_error_message(platform))
        except (ImportError, ValueError) as exc:
            raise RendererDependencyError(renderer_error_message(platform)) from exc
        return
    if platform.startswith("linux"):
        try:
            gi = importlib.import_module("gi")
        except ImportError as exc:
            raise RendererDependencyError(
                "Horticalc's Python desktop dependencies are missing. Install this source checkout with: "
                f"{SOURCE_WEBVIEW_INSTALL_COMMAND}"
            ) from exc
        try:
            gi.require_version("Gtk", "3.0")
            gi.require_version("WebKit2", "4.1")
        except ValueError as exc:
            raise RendererDependencyError(renderer_error_message(platform)) from exc

        # Import errors here can be ABI/loader failures rather than missing packages.
        # Let the caller report a neutral initialization failure with the traceback in the log.
        importlib.import_module("webview.platforms.gtk")
        return
    raise RendererDependencyError(renderer_error_message(platform))


def focus_window(window: WebviewWindow, platform: str | None = None) -> bool:
    platform = sys.platform if platform is None else platform
    try:
        window.restore()
        if platform == "win32":
            window.show()
    except Exception:
        logging.getLogger("horticalc.launcher").exception("Failed to restore the Horticalc window.")
        return False
    return True


def load_webview() -> Any:
    try:
        return importlib.import_module("webview")
    except ModuleNotFoundError as exc:
        if exc.name != "webview":
            raise
        raise RendererDependencyError(
            f"pywebview is not installed. Install this source checkout with: {SOURCE_WEBVIEW_INSTALL_COMMAND}"
        ) from exc


def run_webview(url: str, storage_path: Path, server: uvicorn.Server) -> None:
    webview = load_webview()

    ensure_renderer_available()
    webview.settings["ALLOW_DOWNLOADS"] = False
    webview.settings["ALLOW_FILE_URLS"] = False
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
    webview.settings["REMOTE_DEBUGGING_PORT"] = None

    window = webview.create_window(
        WINDOW_TITLE,
        url=url,
        js_api=None,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=WINDOW_MIN_SIZE,
        resizable=True,
        background_color="#08110d",
        text_select=True,
        zoomable=False,
    )
    configure_activation_handler(focus_window, window)
    window.events.closed += lambda: setattr(server, "should_exit", True)
    webview.start(
        gui=selected_renderer(),
        debug=False,
        private_mode=False,
        storage_path=str(storage_path),
    )


def main() -> None:
    root = app_root()
    try:
        ensure_portable_layout(root)
        logs_path = logs_dir(root)
    except RuntimeError as exc:
        fail_fast(str(exc) or PORTABLE_WRITE_ERROR)

    log_file = setup_logging(logs_path)
    logger = logging.getLogger("horticalc.launcher")
    logger.info("AppRoot resolved to %s", root)
    no_gui = _env_flag(NO_GUI_ENV)

    from api.app import app

    lock_path = lockfile_path(root)
    while True:
        try:
            existing = wait_for_existing_server(lock_path)
        except RuntimeError as exc:
            fail_fast(str(exc), log_file)
        if existing is not None:
            logger.info("Existing server detected on port %s.", existing.port)
            if no_gui:
                logger.info("%s is set; leaving the existing server unchanged.", NO_GUI_ENV)
                return
            if activate_existing_instance(existing):
                logger.info("Activated the existing Horticalc window.")
                return
            fail_fast("Horticalc is running, but its window could not be activated.", log_file)

        port = find_free_port()
        if port is None:
            fail_fast("No free port found in the 8000-8100 range.", log_file)
        activation_token = secrets.token_urlsafe(32)
        if claim_lockfile(lock_path, port, activation_token):
            configure_activation_token(activation_token)
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
    server_thread = threading.Thread(target=server.run, name="uvicorn-server", daemon=True)
    server_thread.start()

    def cleanup() -> None:
        clear_activation_handler()
        stop_server(server, server_thread, lock_path)

    atexit.register(cleanup)
    try:
        require_server_health(server, server_thread, lock_path, port, log_file)
        if no_gui:
            logger.info("%s is set; running the local server without a desktop window.", NO_GUI_ENV)
            server_thread.join()
            return

        storage_path = webview_storage_path(root)
        storage_path.mkdir(parents=True, exist_ok=True)
        url = f"http://127.0.0.1:{port}/"
        logger.info("Opening native desktop window with %s.", selected_renderer())
        try:
            run_webview(url, storage_path, server)
        except RendererDependencyError as exc:
            logger.exception("The native desktop runtime is unavailable.")
            fail_fast(str(exc), log_file)
        except Exception:
            logger.exception("Failed to initialize the native desktop window.")
            fail_fast(gui_initialization_error_message(log_file), log_file)
        logger.info("Desktop window closed; stopping local server.")
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    finally:
        cleanup()
        atexit.unregister(cleanup)


if __name__ == "__main__":
    main()
