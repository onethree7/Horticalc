from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import repo_root
from horticalc.launcher import fail_fast, lockfile_path, read_lockfile, write_lockfile
from horticalc.paths import app_root


def test_app_root_matches_repo_root_in_dev() -> None:
    assert app_root() == repo_root()


def test_lockfile_roundtrip(tmp_path) -> None:
    root = tmp_path
    (root / "user").mkdir()
    path = lockfile_path(root)
    write_lockfile(path, port=8000, pid=1234)
    payload = read_lockfile(path)
    assert payload is not None
    assert payload["port"] == 8000
    assert payload["pid"] == 1234


def test_fail_fast_exits(monkeypatch) -> None:
    if sys.platform.startswith("win"):
        fake_ctypes = types.SimpleNamespace(
            windll=types.SimpleNamespace(user32=types.SimpleNamespace(MessageBoxW=lambda *args, **kwargs: 0))
        )
        monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)

    with pytest.raises(SystemExit) as exc_info:
        fail_fast("boom")

    assert exc_info.value.code == 1
