from __future__ import annotations

import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from horticalc import __version__
from scripts.check_release_version import expected_release_tag, validate_release_tag

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

    assert {"fastapi", "pydantic", "uvicorn", "pyyaml", "numpy", "scipy", "pywebview"} <= dependency_names
    assert sum(dependency.startswith("pywebview") for dependency in pyproject["project"]["dependencies"]) == 2
    assert pyproject["project"]["requires-python"] == ">=3.10,<3.14"
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
    assert "frontend/app.js" not in data_files["frontend"]
    assert data_files["frontend/app"] == ["frontend/app/*.js"]
    assert "frontend/i18n/*.js" in data_files["frontend/i18n"]
    assert data_files["frontend/styles"] == ["frontend/styles/*.css"]
    assert "data/*.csv" in data_files["data"]
    assert "data/water_profiles/*.yml" in data_files["data/water_profiles"]
    assert "data/nutrient_solutions/*.yml" in data_files["data/nutrient_solutions"]
    assert "recipes/*.yml" in data_files["recipes"]


def test_release_builds_include_readme_and_clean_smoke_state() -> None:
    readme = (ROOT / "scripts" / "packaging" / "README.txt").read_text(encoding="utf-8")
    windows_build = (ROOT / "scripts" / "packaging" / "build_windows.ps1").read_text(encoding="utf-8")
    installer_build = (ROOT / "scripts" / "packaging" / "build_windows_installer.ps1").read_text(encoding="utf-8")
    installer_script = (ROOT / "scripts" / "packaging" / "horticalc.iss").read_text(encoding="utf-8")
    installer_smoke = (ROOT / "scripts" / "packaging" / "smoke_windows_installer.ps1").read_text(encoding="utf-8")
    linux_build = (ROOT / "scripts" / "packaging" / "build_linux.sh").read_text(encoding="utf-8")
    release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "Back up user/" in readme
    assert "logs/launcher.log" in readme
    assert "GNU General Public License" in readme
    assert "corresponding source code" in readme
    assert "Horticalc is an independent project" in readme
    assert "point-in-time snapshots" in readme
    assert "Those official documents always take precedence" in readme
    assert "Microsoft WebView2 Runtime" in readme
    assert "does not require or control an installed" in readme
    assert "scripts/packaging/README.txt" in windows_build
    assert "scripts/packaging/README.txt" in linux_build
    assert 'Join-Path $repoRoot "LICENSE"' in windows_build
    assert 'cp "$repo_root/LICENSE" "$app_root/LICENSE"' in linux_build
    assert "50DF7813-DAE5-4976-8B13-6D677CF44660" in installer_script
    assert "DefaultDirName={localappdata}\\Programs\\Horticalc" in installer_script
    assert "PrivilegesRequired=lowest" in installer_script
    assert "CloseApplications=yes" in installer_script
    assert "RestartApplications=no" in installer_script
    assert "postinstall skipifsilent" in installer_script
    assert 'Name: "{app}\\user"; Flags: uninsneveruninstall' in installer_script
    assert 'Name: "{app}\\logs"' in installer_script
    assert 'Name: "{group}\\Horticalc"' in installer_script
    install_delete = installer_script.split("[InstallDelete]", 1)[1].split("[Files]", 1)[0]
    assert '"{app}\\user"' not in install_delete
    assert "ISCC_PATH" in installer_build
    assert "Inno Setup 6 compiler" in installer_build
    assert "Runtime state found in installer input" in installer_build
    assert "Zone.Identifier" in installer_smoke
    assert "UseShellExecute = $false" in installer_smoke
    assert "Installer update removed user data" in installer_smoke
    assert "Uninstaller did not remove logs" in installer_smoke
    assert 'app_root / "LICENSE"' in release_workflow
    assert 'legacy_fertilizers = user_dir / "fertilizers.csv"' in release_workflow
    assert "Legacy Liquid,Flüssig,1.25,0.2" in release_workflow
    assert 'legacy_fertilizers.with_suffix(".csv.legacy-backup")' in release_workflow
    assert "csv.DictReader(handle)" in release_workflow
    assert "Clean smoke-test runtime state" in release_workflow
    assert "Build Windows installer" in release_workflow
    assert "Smoke test Windows installer" in release_workflow
    assert "Attest Windows installer" in release_workflow
    assert "Upload Windows installer artifact" in release_workflow
    assert "release-assets/*.exe" in release_workflow
    assert "release-assets/*.exe.sha256" in release_workflow
    assert "HORTICALC_NO_GUI" in release_workflow
    assert "HORTICALC_NO_BROWSER" not in release_workflow
    assert "gir1.2-webkit2-4.1" in release_workflow
    assert "Unexpected bundled renderer" in release_workflow
    assert "verify_linux_bundle.py" in linux_build
    assert "verify_linux_bundle.py" in release_workflow
    assert "smoke_linux_gui.py" in release_workflow
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1" in release_workflow
    for supported_linux in ("ubuntu:22.04", "ubuntu:24.04", "debian:13", "fedora:44"):
        assert supported_linux in release_workflow
    assert "sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1" in release_workflow
    assert "sudo dnf install -y webkit2gtk4.1" in release_workflow
    assert "needs:\n      - build\n      - linux-compatibility" in release_workflow
    assert '- "v*"' in release_workflow
    assert "if: startsWith(github.ref, 'refs/tags/v')" in release_workflow
    assert "Compute release metadata" in release_workflow
    assert 'notes_path=".github/release-notes/${GITHUB_REF_NAME}.md"' in release_workflow
    assert "name: ${{ steps.release.outputs.name }}" in release_workflow
    assert "body_path: ${{ steps.release.outputs.notes_path }}" in release_workflow
    cleanup_index = release_workflow.index("Clean smoke-test runtime state")
    assert cleanup_index < release_workflow.index("Package artifact (Linux)")
    assert cleanup_index < release_workflow.index("Package artifact (Windows)")
    assert cleanup_index < release_workflow.index("Build Windows installer")


def test_ci_resolves_release_constraints() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "Release dependency resolution" in workflow
    assert "PIP_CONSTRAINT: constraints-release.txt" in workflow
    assert "python -m pip install --dry-run . pyinstaller" in workflow
    assert "gir1.2-webkit2-4.1" in workflow


def test_pyinstaller_selects_one_native_webview_backend() -> None:
    spec = (ROOT / "scripts" / "packaging" / "horticalc.spec").read_text(encoding="utf-8")

    assert '"webview.platforms.edgechromium"' in spec
    assert '"webview.platforms.gtk"' in spec
    assert 'collect_submodules("scipy._external.array_api_compat.numpy")' in spec
    assert "support Windows and Linux only" in spec
    assert "a.exclude_system_libraries()" in spec
    for hook in ("pyi_rth_gtk.py", "pyi_rth_gdkpixbuf.py", "pyi_rth_gio.py", "pyi_rth_glib.py", "pyi_rth_gi.py"):
        assert f'"{hook}"' in spec
    for system_data in ("gi_typelibs/", "lib/gdk-pixbuf/", "share/glib-2.0/", "share/icons/"):
        assert f'"{system_data}"' in spec
    for excluded in ("PyQt5", "PyQt6", "PySide2", "PySide6", "cefpython3", "webview.platforms.mshtml"):
        assert f'"{excluded}"' in spec


def test_windows_packaging_uses_the_horticalc_leaf_icon() -> None:
    spec = (ROOT / "scripts" / "packaging" / "horticalc.spec").read_text(encoding="utf-8")
    installer = (ROOT / "scripts" / "packaging" / "horticalc.iss").read_text(encoding="utf-8")
    installer_build = (ROOT / "scripts" / "packaging" / "build_windows_installer.ps1").read_text(encoding="utf-8")

    assert (ROOT / "assets" / "horticalc.ico").is_file()
    assert '"assets" / "horticalc.ico"' in spec
    assert 'icon=str(icon_path) if sys.platform == "win32" else None' in spec
    assert "SetupIconFile={#SourceDir}\\..\\..\\assets\\horticalc.ico" in installer
    assert 'Join-Path $repoRoot "assets/horticalc.ico"' in installer_build


def test_linux_runtime_commands_have_user_and_offline_owners() -> None:
    for path in (ROOT / "README.md", ROOT / "scripts" / "packaging" / "README.txt"):
        text = path.read_text(encoding="utf-8")
        assert "sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1" in text
        assert "sudo dnf install -y webkit2gtk4.1" in text


def test_windows_release_docs_have_clear_owners() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = (ROOT / "RELEASE.md").read_text(encoding="utf-8")
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")
    portable_readme = (ROOT / "scripts" / "packaging" / "README.txt").read_text(encoding="utf-8")

    for text in (readme, release, portable_readme):
        assert "windows-setup.exe" in text
    for text in (release, portable_readme):
        assert "%LocalAppData%\\Programs\\Horticalc" in text
    for text in (readme, usage, portable_readme):
        normalized = text.casefold()
        assert "unblock" in normalized
        assert "delete" in normalized
        assert "extract" in normalized
        assert "Zulassen" not in text
    assert "windows-setup.exe" in portable_readme
    assert "%LocalAppData%\\Programs\\Horticalc" in portable_readme
    assert "not Authenticode-signed" in portable_readme
    assert "build_windows_installer.ps1" in release
    assert "windows-setup.exe.sha256" in release


def test_runtime_package_api_and_cli_versions_match(api_client: TestClient) -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
    assert version("horticalc") == __version__
    assert api_client.get("/health").json()["version"] == __version__
    assert api_client.get("/openapi.json").json()["info"]["version"] == __version__
    result = subprocess.run(
        [sys.executable, "-m", "horticalc", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == __version__


def test_release_tag_must_match_the_single_version_literal() -> None:
    release_tag = f"v{__version__}"
    assert expected_release_tag() == release_tag
    validate_release_tag(release_tag)
    with pytest.raises(ValueError, match=rf"must be exactly {re.escape(release_tag)}"):
        validate_release_tag("v4.1")


def test_current_version_has_release_notes() -> None:
    notes = (ROOT / ".github" / "release-notes" / f"v{__version__}.md").read_text(encoding="utf-8")

    assert __version__ in notes
