from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import repo_root
from horticalc.launcher import lockfile_path, read_lockfile, write_lockfile
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
