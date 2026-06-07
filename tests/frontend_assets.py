from __future__ import annotations

from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def frontend_path(name: str) -> Path:
    return FRONTEND_DIR / name


def read_frontend_file(name: str) -> str:
    return frontend_path(name).read_text(encoding="utf-8")
