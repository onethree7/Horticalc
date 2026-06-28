from __future__ import annotations

import sys
import threading
import types

import pytest

import horticalc.launcher as launcher
from horticalc.launcher import (
    LOG_BACKUP_COUNT,
    LOG_MAX_BYTES,
    _logging_config,
    active_launcher_sessions,
    claim_lockfile,
    cleanup_stale_profile_dirs,
    create_profile_dir,
    create_launcher_session,
    fail_fast,
    lockfile_path,
    read_lockfile,
    remove_lockfile,
    wait_for_existing_server,
    wait_for_existing_server_fallback,
    wait_for_fallback_shutdown,
    wait_for_launcher_sessions,
    write_lockfile,
)
from horticalc.paths import _first_app_root_with_assets, app_root, repo_root

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


def test_lockfile_roundtrip(tmp_path) -> None:
    root = tmp_path
    (root / "user").mkdir()
    path = lockfile_path(root)
    write_lockfile(path, port=8000, pid=1234)
    payload = read_lockfile(path)
    assert payload is not None
    assert payload["port"] == 8000
    assert payload["pid"] == 1234


def test_packaged_logging_rotates_and_suppresses_access_noise(tmp_path) -> None:
    config = _logging_config(tmp_path / "launcher.log", packaged=True)

    assert config["handlers"]["file"]["class"] == "logging.handlers.RotatingFileHandler"
    assert config["handlers"]["file"]["maxBytes"] == LOG_MAX_BYTES
    assert config["handlers"]["file"]["backupCount"] == LOG_BACKUP_COUNT
    assert config["loggers"]["uvicorn.access"]["level"] == "WARNING"
    dev_config = _logging_config(tmp_path / "dev.log", packaged=False)
    assert dev_config["loggers"]["uvicorn.access"]["level"] == "INFO"


def test_lockfile_removal_is_owner_aware(tmp_path) -> None:
    path = lockfile_path(tmp_path)
    path.parent.mkdir()
    write_lockfile(path, port=8000, pid=1234)

    remove_lockfile(path, expected_pid=5678)
    assert path.exists()

    remove_lockfile(path, expected_pid=1234)
    assert not path.exists()


def test_lockfile_write_is_atomic_on_replace_failure(tmp_path, monkeypatch) -> None:
    path = lockfile_path(tmp_path)
    path.parent.mkdir()
    original = '{"pid": 1234, "port": 8000}'
    path.write_text(original, encoding="utf-8")

    def fail_replace(_source, _destination) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(launcher.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        write_lockfile(path, port=8001, pid=5678)

    assert path.read_text(encoding="utf-8") == original
    assert list(path.parent.glob(f".{path.name}.tmp-*")) == []


def test_exclusive_lockfile_claim_has_single_winner(tmp_path) -> None:
    path = lockfile_path(tmp_path)

    assert claim_lockfile(path, port=8000, pid=1234) is True
    assert claim_lockfile(path, port=8001, pid=5678) is False
    assert read_lockfile(path)["pid"] == 1234


def test_existing_server_waits_for_live_owner_health(tmp_path, monkeypatch) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, port=8000, pid=1234)
    health_results = iter([False, True])
    monkeypatch.setattr(launcher, "health_ok", lambda _port: next(health_results))
    monkeypatch.setattr(launcher, "_pid_is_running", lambda _pid: True)

    assert wait_for_existing_server(path, timeout_seconds=1) == 8000


def test_existing_server_removes_dead_or_malformed_locks(tmp_path, monkeypatch) -> None:
    path = lockfile_path(tmp_path)
    write_lockfile(path, port=8000, pid=1234)
    monkeypatch.setattr(launcher, "health_ok", lambda _port: False)
    monkeypatch.setattr(launcher, "_pid_is_running", lambda _pid: False)

    assert wait_for_existing_server(path, timeout_seconds=0) is None
    assert not path.exists()

    path.write_text("{broken", encoding="utf-8")
    assert wait_for_existing_server(path, malformed_grace_seconds=0) is None
    assert not path.exists()


def test_launcher_sessions_keep_live_processes_and_remove_stale_ones(tmp_path, monkeypatch) -> None:
    live = create_launcher_session(tmp_path, pid=1234)
    stale = create_launcher_session(tmp_path, pid=5678)
    monkeypatch.setattr("horticalc.launcher._pid_is_running", lambda pid: pid == 1234)

    assert active_launcher_sessions(tmp_path) == [live]
    assert live.exists()
    assert not stale.exists()


def test_launcher_sessions_reject_reused_pid_identity(tmp_path, monkeypatch) -> None:
    identity = {1234: 111}
    monkeypatch.setattr(launcher, "_process_identity", lambda pid: identity.get(pid))
    session = create_launcher_session(tmp_path, pid=1234)
    monkeypatch.setattr(launcher, "_pid_is_running", lambda _pid: True)
    identity[1234] = 222

    assert active_launcher_sessions(tmp_path) == []
    assert not session.exists()


def test_live_launcher_session_delays_server_shutdown(tmp_path, monkeypatch) -> None:
    session = create_launcher_session(tmp_path)
    monkeypatch.setattr("horticalc.launcher._pid_is_running", lambda pid: session.exists())
    waiter = threading.Thread(
        target=wait_for_launcher_sessions,
        args=(tmp_path,),
        kwargs={"grace_seconds": 0.05},
        daemon=True,
    )
    waiter.start()

    waiter.join(timeout=0.15)
    assert waiter.is_alive()

    session.unlink()
    waiter.join(timeout=0.5)
    assert not waiter.is_alive()


def test_launcher_session_write_cleans_up_after_replace_failure(tmp_path, monkeypatch) -> None:
    def fail_replace(_source, _destination) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(launcher.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        create_launcher_session(tmp_path, pid=1234)

    session_dir = launcher.launcher_session_dir(tmp_path)
    assert list(session_dir.iterdir()) == []


def test_browser_profile_directories_are_unique(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(launcher.os, "getpid", lambda: 1234)

    first = create_profile_dir(tmp_path)
    second = create_profile_dir(tmp_path)

    assert first != second
    assert first.exists()
    assert second.exists()


def test_stale_profile_cleanup_handles_dead_or_reused_owner(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(launcher.os, "getpid", lambda: 1234)
    monkeypatch.setattr(launcher, "_process_identity", lambda _pid: 111)
    profile = create_profile_dir(tmp_path)
    old_time = 1_000.0
    launcher.os.utime(profile, (old_time, old_time))
    monkeypatch.setattr(launcher, "_pid_is_running", lambda _pid: True)
    monkeypatch.setattr(launcher, "_process_identity", lambda _pid: 222)

    cleanup_stale_profile_dirs(
        tmp_path,
        now=old_time + launcher.STALE_PROFILE_AGE_SECONDS,
    )

    assert not profile.exists()


def test_stale_profile_cleanup_removes_legacy_dead_owner_profile(tmp_path, monkeypatch) -> None:
    profile = tmp_path / "user" / launcher.PROFILE_DIR_NAME / "profile-1234-1700000000"
    profile.mkdir(parents=True)
    old_time = 1_000.0
    launcher.os.utime(profile, (old_time, old_time))
    monkeypatch.setattr(launcher, "_pid_is_running", lambda _pid: False)

    cleanup_stale_profile_dirs(
        tmp_path,
        now=old_time + launcher.STALE_PROFILE_AGE_SECONDS,
    )

    assert not profile.exists()


def test_existing_server_fallback_session_is_removed_on_exit(tmp_path, monkeypatch) -> None:
    logger = types.SimpleNamespace(info=lambda *_args: None)

    def stop_waiting(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(launcher.time, "sleep", stop_waiting)

    with pytest.raises(KeyboardInterrupt):
        wait_for_existing_server_fallback(tmp_path, logger)

    assert list(launcher.launcher_session_dir(tmp_path).iterdir()) == []


def test_system_browser_fallback_waits_for_server_shutdown() -> None:
    joined = []
    server_thread = types.SimpleNamespace(join=lambda: joined.append(True))
    logger = types.SimpleNamespace(info=lambda *_args: None)

    wait_for_fallback_shutdown(server_thread, logger, compatibility_flag_set=False)

    assert joined == [True]

def test_fail_fast_exits(monkeypatch) -> None:
    if sys.platform.startswith("win"):
        fake_ctypes = types.SimpleNamespace(
            windll=types.SimpleNamespace(user32=types.SimpleNamespace(MessageBoxW=lambda *args: 0))
        )
        monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)

    with pytest.raises(SystemExit) as exc_info:
        fail_fast("boom")

    assert exc_info.value.code == 1
