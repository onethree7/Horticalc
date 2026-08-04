"""Run the test suite with the repository virtual environment."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = REPO_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
SUITES = ("product", "research", "all")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--suite", choices=SUITES, default="product")
    parser.add_argument("--pytest-only", action="store_true")
    return parser.parse_known_args(argv)


def ensure_python_dependencies(*, needs_ruff: bool) -> None:
    if not VENV_PYTHON.exists():
        print(f"[Horticalc] Creating virtual environment at {VENV_PYTHON.parent.parent}")
        run([sys.executable, "-m", "venv", str(VENV_PYTHON.parent.parent)])

    required_modules = ["httpx2", "pytest"]
    if needs_ruff:
        required_modules.append("ruff")
    dependency_check = subprocess.run(
        [str(VENV_PYTHON), "-c", "; ".join(f"import {module}" for module in required_modules)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if dependency_check.returncode != 0:
        print("[Horticalc] Installing development dependencies into .venv")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]"])


def ensure_frontend_dependencies() -> str:
    npm = shutil.which("npm")
    if not npm:
        print("[Horticalc] Node.js/npm is required for frontend tests and linting")
        raise RuntimeError("Node.js/npm is unavailable")
    required_node_packages = ("eslint", "playwright", "stylelint")
    if any(not (REPO_ROOT / "node_modules" / package / "package.json").exists() for package in required_node_packages):
        print("[Horticalc] Installing frontend test dependencies")
        run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"])
    return npm


def run_python_checks() -> None:
    run([str(VENV_PYTHON), "-m", "ruff", "format", "--check", "api", "scripts", "src", "tests"])
    run([str(VENV_PYTHON), "-m", "ruff", "check", "api", "scripts", "src", "tests"])


def run_frontend_checks(npm: str) -> None:
    run([npm, "run", "lint"])
    run([npm, "run", "test:unit"])


def apply_suite_marker(pytest_args: list[str], suite: str) -> list[str]:
    suite_expression = {"product": "not research", "research": "research", "all": None}[suite]
    if suite_expression is None:
        return pytest_args

    remaining: list[str] = []
    existing_expression: str | None = None
    index = 0
    while index < len(pytest_args):
        argument = pytest_args[index]
        if argument == "-m":
            if index + 1 >= len(pytest_args):
                raise ValueError("pytest -m requires an expression")
            existing_expression = pytest_args[index + 1]
            index += 2
            continue
        remaining.append(argument)
        index += 1

    marker_expression = suite_expression
    if existing_expression:
        marker_expression = f"({suite_expression}) and ({existing_expression})"
    return [*remaining, "-m", marker_expression]


def main(argv: list[str] | None = None) -> int:
    runner_args, pytest_args = parse_args(sys.argv[1:] if argv is None else argv)
    run_checks = not runner_args.pytest_only
    run_frontend = run_checks and runner_args.suite in {"product", "all"}

    ensure_python_dependencies(needs_ruff=run_checks)
    npm: str | None = None
    if run_frontend:
        try:
            npm = ensure_frontend_dependencies()
        except RuntimeError:
            return 1

    if run_checks:
        run_python_checks()
    if npm is not None:
        run_frontend_checks(npm)

    pytest_args = pytest_args or ["-q"]
    try:
        pytest_args = apply_suite_marker(pytest_args, runner_args.suite)
    except ValueError as exc:
        print(f"[Horticalc] {exc}")
        return 2
    return subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest", *pytest_args],
        cwd=REPO_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
