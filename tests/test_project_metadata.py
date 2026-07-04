from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

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
    assert pyproject["project"]["license"] == "GPL-3.0-or-later"
    assert pyproject["project"]["license-files"] == ["LICENSE"]


def test_repository_contains_canonical_gplv3_license() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 29 June 2007" in license_text
    assert "Everyone is permitted to copy and distribute verbatim copies" in license_text


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
    assert "GNU General Public License" in readme
    assert "corresponding source code" in readme
    assert "Horticalc is an independent project" in readme
    assert "point-in-time snapshots" in readme
    assert "Those official documents always take precedence" in readme
    assert 'scripts/packaging/README.txt' in windows_build
    assert 'scripts/packaging/README.txt' in linux_build
    assert 'Join-Path $repoRoot "LICENSE"' in windows_build
    assert 'cp "$repo_root/LICENSE" "$app_root/LICENSE"' in linux_build
    assert 'app_root / "LICENSE"' in release_workflow
    assert 'legacy_fertilizers = user_dir / "fertilizers.csv"' in release_workflow
    assert 'Legacy Liquid,Flüssig,1.25,0.2' in release_workflow
    assert 'legacy_fertilizers.with_suffix(".csv.legacy-backup")' in release_workflow
    assert "Clean smoke-test runtime state" in release_workflow
    cleanup_index = release_workflow.index("Clean smoke-test runtime state")
    assert cleanup_index < release_workflow.index("Package artifact (Linux)")
    assert cleanup_index < release_workflow.index("Package artifact (Windows)")
