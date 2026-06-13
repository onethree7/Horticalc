"""Run the test suite with the repository virtual environment."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = REPO_ROOT / ".venv" / (
    "Scripts/python.exe" if os.name == "nt" else "bin/python"
)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    if not VENV_PYTHON.exists():
        print(f"[Horticalc] Creating virtual environment at {VENV_PYTHON.parent.parent}")
        run([sys.executable, "-m", "venv", str(VENV_PYTHON.parent.parent)])

    pytest_check = subprocess.run(
        [str(VENV_PYTHON), "-c", "import pytest"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if pytest_check.returncode != 0:
        print("[Horticalc] Installing development dependencies into .venv")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]"])

    pytest_args = sys.argv[1:] or ["-q"]
    return subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest", *pytest_args],
        cwd=REPO_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
