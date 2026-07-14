"""Run the test suite with the repository virtual environment."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
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

    dependency_check = subprocess.run(
        [str(VENV_PYTHON), "-c", "import httpx2, pytest"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if dependency_check.returncode != 0:
        print("[Horticalc] Installing development dependencies into .venv")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]"])

    if not (REPO_ROOT / "node_modules" / "playwright" / "package.json").exists():
        npm = shutil.which("npm")
        if not npm:
            print("[Horticalc] Node.js/npm is required for frontend browser tests")
            return 1
        print("[Horticalc] Installing frontend test dependencies")
        run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"])

    pytest_args = sys.argv[1:] or ["-q"]
    return subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest", *pytest_args],
        cwd=REPO_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
