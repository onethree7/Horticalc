from __future__ import annotations

import sys
import types
import urllib.error

import pytest

import horticalc.launcher as launcher
import horticalc.single_instance as single_instance
from horticalc.launcher import (
    LOG_BACKUP_COUNT,
    LOG_MAX_BYTES,
    RendererDependencyError,
    _logging_config,
    ensure_renderer_available,
    fail_fast,
    focus_window,
    gui_initialization_error_message,
    linux_distribution_ids,
    linux_webview_install_command,
    load_webview,
    renderer_error_message,
    run_webview,
    selected_renderer,
    stop_server,
    webview_storage_path,
)
from horticalc.paths import _first_app_root_with_assets, app_root, repo_root
from horticalc.single_instance import (
    ExistingInstance,
    activate_existing_instance,
    claim_lockfile,
    lockfile_path,
    read_lockfile,
    remove_lockfile,
    wait_for_existing_server,
    write_lockfile,
)

TOKEN = "t" * 43


def test_app_root_matches_repo_root_in_dev() -> None:
    assert app_root() == repo_root()


def test_app_root_candidate_requires_frontend_data_and_recipe(tmp_path) -> None:
    empty_root = tmp_path / "empty"
    installed_root = tmp_path / "installed"
    for relative in ("frontend/index.html", "data/fertilizers.csv", "recipes/default.yml"):
        path = installed_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")

    assert _first_app_root_with_assets((empty_root, installed_root)) == installed_root.resolve()


def test_lockfile_roundtrip_includes_activation_token(tmp_path) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, port=8000, activation_token=TOKEN, pid=1234)

    payload = read_lockfile(path)

    assert payload is not None
    assert payload["port"] == 8000
    assert payload["pid"] == 1234
    assert payload["activation_token"] == TOKEN


def test_lockfile_rejects_obsolete_schema(tmp_path) -> None:
    path = lockfile_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text('{"pid": 1234, "port": 8000}', encoding="utf-8")

    assert read_lockfile(path) is None


def test_packaged_logging_rotates_and_suppresses_access_noise(tmp_path) -> None:
    config = _logging_config(tmp_path / "launcher.log", packaged=True)

    assert config["handlers"]["file"]["class"] == "logging.handlers.RotatingFileHandler"
    assert config["handlers"]["file"]["maxBytes"] == LOG_MAX_BYTES
    assert config["handlers"]["file"]["backupCount"] == LOG_BACKUP_COUNT
    assert config["loggers"]["uvicorn.access"]["level"] == "WARNING"
    assert _logging_config(tmp_path / "dev.log", packaged=False)["loggers"]["uvicorn.access"]["level"] == "INFO"


def test_lockfile_removal_is_owner_aware(tmp_path) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, port=8000, activation_token=TOKEN, pid=1234)

    remove_lockfile(path, expected_pid=5678)
    assert path.exists()

    remove_lockfile(path, expected_pid=1234)
    assert not path.exists()


def test_lockfile_write_is_atomic_on_replace_failure(tmp_path, monkeypatch) -> None:
    path = lockfile_path(tmp_path)
    path.parent.mkdir(parents=True)
    original = '{"pid": 1234, "port": 8000}'
    path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        single_instance.os,
        "replace",
        lambda *_args: (_ for _ in ()).throw(OSError("replace failed")),
    )

    with pytest.raises(OSError, match="replace failed"):
        write_lockfile(path, port=8001, activation_token=TOKEN, pid=5678)

    assert path.read_text(encoding="utf-8") == original
    assert list(path.parent.glob(f".{path.name}.tmp-*")) == []


def test_exclusive_lockfile_claim_has_single_winner(tmp_path) -> None:
    path = lockfile_path(tmp_path)

    assert claim_lockfile(path, port=8000, activation_token=TOKEN, pid=1234) is True
    assert claim_lockfile(path, port=8001, activation_token="x" * 43, pid=5678) is False
    assert read_lockfile(path)["pid"] == 1234


def test_existing_server_waits_for_live_owner_health(tmp_path, monkeypatch) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, port=8000, activation_token=TOKEN, pid=1234)
    health_results = iter([False, True])
    monkeypatch.setattr(single_instance, "health_ok", lambda _port: next(health_results))
    monkeypatch.setattr(single_instance, "_pid_is_running", lambda _pid: True)

    assert wait_for_existing_server(path, timeout_seconds=1) == ExistingInstance(1234, 8000, TOKEN)


def test_existing_server_removes_dead_or_malformed_locks(tmp_path, monkeypatch) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, port=8000, activation_token=TOKEN, pid=1234)
    monkeypatch.setattr(single_instance, "health_ok", lambda _port: False)
    monkeypatch.setattr(single_instance, "_pid_is_running", lambda _pid: False)

    assert wait_for_existing_server(path, timeout_seconds=0) is None
    assert not path.exists()

    path.write_text("{broken", encoding="utf-8")
    assert wait_for_existing_server(path, malformed_grace_seconds=0) is None
    assert not path.exists()


def test_existing_instance_activation_uses_token_header(monkeypatch) -> None:
    observed = {}

    class Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def open_request(request, timeout):
        observed["url"] = request.full_url
        headers = {name.lower(): value for name, value in request.header_items()}
        observed["token"] = headers[single_instance.ACTIVATION_HEADER.lower()]
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr(single_instance.urllib.request, "urlopen", open_request)

    assert activate_existing_instance(ExistingInstance(1234, 8000, TOKEN)) is True
    assert observed == {
        "url": "http://127.0.0.1:8000/_launcher/activate",
        "token": TOKEN,
        "timeout": 1,
    }


def test_existing_instance_activation_retries_while_window_is_unavailable(monkeypatch) -> None:
    calls = []

    def unavailable(*_args, **_kwargs):
        calls.append(True)
        raise urllib.error.HTTPError("url", 503, "not ready", {}, None)

    monkeypatch.setattr(single_instance.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr(single_instance.time, "sleep", lambda _seconds: None)
    times = iter([0.0, 0.0, 1.0])
    monkeypatch.setattr(single_instance.time, "monotonic", lambda: next(times))

    assert activate_existing_instance(ExistingInstance(1234, 8000, TOKEN), timeout_seconds=0.5) is False
    assert calls == [True]


@pytest.mark.parametrize(("platform", "renderer"), [("win32", "edgechromium"), ("linux", "gtk")])
def test_renderer_is_explicit(platform, renderer) -> None:
    assert selected_renderer(platform) == renderer


def test_unsupported_desktop_platform_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="Windows 10/11 and Linux only"):
        selected_renderer("darwin")


def test_renderer_errors_name_actionable_runtime_requirement() -> None:
    assert "WebView2 Runtime" in renderer_error_message("win32")
    assert launcher.WEBVIEW2_DOWNLOAD_URL in renderer_error_message("win32")
    assert "gir1.2-webkit2-4.1" in renderer_error_message("linux", {"debian"})
    assert "webkit2gtk4.1" in renderer_error_message("linux", {"fedora"})


def test_linux_distribution_detection_uses_id_and_id_like(tmp_path) -> None:
    os_release = tmp_path / "os-release"
    os_release.write_text('NAME="Test"\nID=linuxmint\nID_LIKE="ubuntu debian"\n', encoding="utf-8")

    assert linux_distribution_ids(os_release) == {"linuxmint", "ubuntu", "debian"}
    assert linux_distribution_ids(tmp_path / "missing") == set()


@pytest.mark.parametrize(
    ("distribution_ids", "command"),
    [
        ({"ubuntu"}, launcher.LINUX_APT_WEBVIEW_COMMAND),
        ({"debian"}, launcher.LINUX_APT_WEBVIEW_COMMAND),
        ({"linuxmint", "ubuntu"}, launcher.LINUX_APT_WEBVIEW_COMMAND),
        ({"fedora"}, launcher.LINUX_DNF_WEBVIEW_COMMAND),
        ({"arch"}, None),
    ],
)
def test_linux_webview_command_matches_distribution(distribution_ids, command) -> None:
    assert linux_webview_install_command(distribution_ids) == command


def test_windows_renderer_preflight_rejects_mshtml(monkeypatch) -> None:
    monkeypatch.setattr(
        launcher.importlib,
        "import_module",
        lambda _name: types.SimpleNamespace(renderer="mshtml"),
    )

    with pytest.raises(RuntimeError, match="WebView2 Runtime"):
        ensure_renderer_available("win32")


def test_linux_renderer_preflight_does_not_fall_back_to_qt(monkeypatch) -> None:
    gi = types.SimpleNamespace(
        require_version=lambda namespace, _version: (
            (_ for _ in ()).throw(ValueError("namespace missing")) if namespace == "WebKit2" else None
        )
    )
    monkeypatch.setattr(launcher.importlib, "import_module", lambda _name: gi)

    with pytest.raises(RendererDependencyError, match="WebKitGTK 4.1"):
        ensure_renderer_available("linux")


def test_linux_renderer_abi_error_is_not_misreported_as_missing_package(monkeypatch) -> None:
    gi = types.SimpleNamespace(require_version=lambda *_args: None)

    def import_module(name):
        if name == "gi":
            return gi
        raise ImportError("undefined symbol: g_once_init_enter_pointer")

    monkeypatch.setattr(launcher.importlib, "import_module", import_module)

    with pytest.raises(ImportError, match="undefined symbol"):
        ensure_renderer_available("linux")


def test_missing_pywebview_source_dependency_has_install_command(monkeypatch) -> None:
    missing = ModuleNotFoundError("No module named 'webview'", name="webview")
    monkeypatch.setattr(launcher.importlib, "import_module", lambda _name: (_ for _ in ()).throw(missing))

    with pytest.raises(RendererDependencyError, match=r"python -m pip install -e \."):
        load_webview()


def test_unexpected_gui_failure_message_is_neutral(tmp_path) -> None:
    message = gui_initialization_error_message(tmp_path / "launcher.log")

    assert "could not initialize" in message
    assert "launcher.log" in message
    assert "WebKitGTK" not in message
    assert "WebView2" not in message


def test_webview_storage_stays_in_portable_user_directory(tmp_path) -> None:
    assert webview_storage_path(tmp_path) == tmp_path / "user" / "webview"


def test_focus_window_restores_linux_window_through_pywebview() -> None:
    calls = []
    window = types.SimpleNamespace(
        restore=lambda: calls.append("restore"),
        show=lambda: calls.append("show"),
    )

    assert focus_window(window, "linux") is True
    assert calls == ["restore"]


def test_focus_window_restores_and_shows_windows_window_through_pywebview() -> None:
    calls = []
    window = types.SimpleNamespace(
        restore=lambda: calls.append("restore"),
        show=lambda: calls.append("show"),
    )

    assert focus_window(window, "win32") is True
    assert calls == ["restore", "show"]


def test_focus_window_reports_pywebview_activation_failure() -> None:
    window = types.SimpleNamespace(
        restore=lambda: (_ for _ in ()).throw(RuntimeError("failed")),
        show=lambda: None,
    )

    assert focus_window(window, "linux") is False


def test_run_webview_uses_native_window_without_js_bridge(tmp_path, monkeypatch) -> None:
    class Event:
        def __init__(self):
            self.handlers = []

        def __iadd__(self, handler):
            self.handlers.append(handler)
            return self

    closed = Event()
    window = types.SimpleNamespace(
        events=types.SimpleNamespace(closed=closed),
        native=None,
        restore=lambda: None,
        show=lambda: None,
    )
    observed = {}

    def create_window(*args, **kwargs):
        observed["window_args"] = args
        observed["window_kwargs"] = kwargs
        return window

    def start(**kwargs):
        observed["start_kwargs"] = kwargs
        for handler in closed.handlers:
            handler()

    fake_webview = types.SimpleNamespace(settings={}, create_window=create_window, start=start)
    monkeypatch.setitem(sys.modules, "webview", fake_webview)
    monkeypatch.setattr(launcher, "selected_renderer", lambda: "edgechromium")
    monkeypatch.setattr(launcher, "ensure_renderer_available", lambda: None)
    server = types.SimpleNamespace(should_exit=False)

    run_webview("http://127.0.0.1:8000/", tmp_path, server)

    assert observed["window_kwargs"]["js_api"] is None
    assert observed["start_kwargs"] == {
        "gui": "edgechromium",
        "debug": False,
        "private_mode": False,
        "storage_path": str(tmp_path),
    }
    assert fake_webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] is False
    assert fake_webview.settings["ALLOW_DOWNLOADS"] is False
    assert server.should_exit is True


def test_stop_server_is_idempotent(tmp_path) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, 8000, TOKEN, pid=launcher.os.getpid())
    joins = []
    server = types.SimpleNamespace(should_exit=False)
    thread = types.SimpleNamespace(join=lambda timeout: joins.append(timeout))

    stop_server(server, thread, path)
    stop_server(server, thread, path)

    assert server.should_exit is True
    assert joins == [5.0, 5.0]
    assert not path.exists()


def test_obsolete_browser_launcher_identifiers_are_removed() -> None:
    source = (repo_root() / "src" / "horticalc" / "launcher.py").read_text(encoding="utf-8")
    for obsolete in (
        "HORTICALC_NO_BROWSER",
        "HORTICALC_KEEP_SERVER",
        "launcher_sessions",
        "browser_profiles",
        "webbrowser",
        "--app",
    ):
        assert obsolete not in source


def test_fail_fast_exits(monkeypatch) -> None:
    if sys.platform.startswith("win"):
        fake_ctypes = types.SimpleNamespace(
            windll=types.SimpleNamespace(user32=types.SimpleNamespace(MessageBoxW=lambda *args: 0))
        )
        monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)

    with pytest.raises(SystemExit) as exc_info:
        fail_fast("boom")

    assert exc_info.value.code == 1
