from __future__ import annotations

import sys
import threading
import types

import pytest

from horticalc.launcher import (
    active_launcher_sessions,
    create_launcher_session,
    fail_fast,
    lockfile_path,
    read_lockfile,
    remove_lockfile,
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


def test_lockfile_removal_is_owner_aware(tmp_path) -> None:
    path = lockfile_path(tmp_path)
    path.parent.mkdir()
    write_lockfile(path, port=8000, pid=1234)

    remove_lockfile(path, expected_pid=5678)
    assert path.exists()

    remove_lockfile(path, expected_pid=1234)
    assert not path.exists()


def test_launcher_sessions_keep_live_processes_and_remove_stale_ones(tmp_path, monkeypatch) -> None:
    live = create_launcher_session(tmp_path, pid=1234)
    stale = create_launcher_session(tmp_path, pid=5678)
    monkeypatch.setattr("horticalc.launcher._pid_is_running", lambda pid: pid == 1234)

    assert active_launcher_sessions(tmp_path) == [live]
    assert live.exists()
    assert not stale.exists()


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

def test_fail_fast_exits(monkeypatch) -> None:
    if sys.platform.startswith("win"):
        fake_ctypes = types.SimpleNamespace(
            windll=types.SimpleNamespace(user32=types.SimpleNamespace(MessageBoxW=lambda *args, **kwargs: 0))
        )
        monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)

    with pytest.raises(SystemExit) as exc_info:
        fail_fast("boom")

    assert exc_info.value.code == 1
