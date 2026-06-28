from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _dependency_names(dependencies: list[str]) -> set[str]:
    names = set()
    for dependency in dependencies:
        match = re.match(r"([A-Za-z0-9_.-]+)", dependency)
        if match:
            names.add(match.group(1).casefold())
    return names

def test_pyproject_declares_runtime_dependencies_used_by_entrypoints() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependency_names = _dependency_names(pyproject["project"]["dependencies"])

    assert {"fastapi", "pydantic", "uvicorn", "pyyaml", "numpy"} <= dependency_names


def test_pyproject_packages_app_assets_for_wheel_installs() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    data_files = pyproject["tool"]["setuptools"]["data-files"]

    assert "frontend/index.html" in data_files["frontend"]
    assert "frontend/i18n/*.js" in data_files["frontend/i18n"]
    assert "data/*.csv" in data_files["data"]
    assert "data/water_profiles/*.yml" in data_files["data/water_profiles"]
    assert "data/nutrient_solutions/*.yml" in data_files["data/nutrient_solutions"]
    assert "recipes/*.yml" in data_files["recipes"]


def test_release_builds_include_readme_and_clean_smoke_state() -> None:
    readme = (ROOT / "scripts" / "packaging" / "README.txt").read_text(encoding="utf-8")
    windows_build = (ROOT / "scripts" / "packaging" / "build_windows.ps1").read_text(
        encoding="utf-8"
    )
    linux_build = (ROOT / "scripts" / "packaging" / "build_linux.sh").read_text(
        encoding="utf-8"
    )
    release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert "Back up user/" in readme
    assert "logs/launcher.log" in readme
    assert 'scripts/packaging/README.txt' in windows_build
    assert 'scripts/packaging/README.txt' in linux_build
    assert "Clean smoke-test runtime state" in release_workflow
    cleanup_index = release_workflow.index("Clean smoke-test runtime state")
    assert cleanup_index < release_workflow.index("Package artifact (Linux)")
    assert cleanup_index < release_workflow.index("Package artifact (Windows)")
