from __future__ import annotations

import sys
from pathlib import Path

from .data_io import repo_root


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return repo_root()


def user_dir(root: Path | None = None) -> Path:
    base = root or app_root()
    return base / "user"


def logs_dir(root: Path | None = None) -> Path:
    base = root or app_root()
    return base / "logs"
