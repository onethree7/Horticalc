"""Run the test suite with the repository virtual environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = REPO_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    if not VENV_PYTHON.exists():
        print(f"[Horticalc] Creating virtual environment at {VENV_PYTHON.parent.parent}")
        run([sys.executable, "-m", "venv", str(VENV_PYTHON.parent.parent)])

    dependency_check = subprocess.run(
        [str(VENV_PYTHON), "-c", "import httpx2, pytest, ruff"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if dependency_check.returncode != 0:
        print("[Horticalc] Installing development dependencies into .venv")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]"])

    npm = shutil.which("npm")
    if not npm:
        print("[Horticalc] Node.js/npm is required for frontend tests and linting")
        return 1
    required_node_packages = ("eslint", "playwright", "stylelint")
    if any(not (REPO_ROOT / "node_modules" / package / "package.json").exists() for package in required_node_packages):
        print("[Horticalc] Installing frontend test dependencies")
        run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"])

    run([str(VENV_PYTHON), "-m", "ruff", "format", "--check", "api", "scripts", "src", "tests"])
    run([str(VENV_PYTHON), "-m", "ruff", "check", "api", "scripts", "src", "tests"])
    run([npm, "run", "lint"])
    run([npm, "run", "test:unit"])

    pytest_args = sys.argv[1:] or ["-q"]
    return subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest", *pytest_args],
        cwd=REPO_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
