from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
BUILD_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "packaging" / "build_windows.ps1"
INSTALLER_SCRIPT = BUILD_SCRIPT.with_name("build_windows_installer.ps1")


@pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is required")
@pytest.mark.parametrize(
    "failed_command, message",
    [(1, "Version discovery failed"), (2, "Version resource generation failed"), (3, "PyInstaller failed")],
)
def test_windows_build_stops_before_touching_stale_output(tmp_path: Path, failed_command: int, message: str) -> None:
    script = tmp_path / "scripts" / "packaging" / "build_windows.ps1"
    script.parent.mkdir(parents=True)
    shutil.copyfile(BUILD_SCRIPT, script)
    output = tmp_path / "dist" / "Horticalc"
    output.mkdir(parents=True)
    binary = output / "Horticalc.exe"
    binary.write_text("previous binary", encoding="utf-8")
    for name in ("frontend", "data", "recipes"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "sentinel").write_text("new asset", encoding="utf-8")
        (output / name).mkdir()
        (output / name / "sentinel").write_text("previous asset", encoding="utf-8")
    (script.parent / "README.txt").write_text("readme", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("license", encoding="utf-8")
    python_path = sys.executable.replace("'", "''")
    script_path = str(script).replace("'", "''")
    command = f"""
$ErrorActionPreference = 'Stop'
$global:buildProbeCalls = 0
function python {{
    $global:buildProbeCalls++
    if ($global:buildProbeCalls -eq {failed_command}) {{
        & '{python_path}' -c "import sys; print('0.6.7'); sys.exit(7)"
    }} else {{
        & '{python_path}' -c "print('0.6.7')"
    }}
}}
& '{script_path}'
"""
    environment = {key: value for key, value in os.environ.items() if key != "HORTICALC_VERSION"}
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode != 0
    assert message in result.stderr
    assert binary.read_text(encoding="utf-8") == "previous binary"
    for name in ("frontend", "data", "recipes"):
        assert (output / name / "sentinel").read_text(encoding="utf-8") == "previous asset"


@pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is required")
@pytest.mark.parametrize("version_output", ["0.6.7", ""])
def test_installer_stops_before_compilation_when_version_discovery_fails(tmp_path: Path, version_output: str) -> None:
    script = tmp_path / "scripts" / "packaging" / "build_windows_installer.ps1"
    script.parent.mkdir(parents=True)
    shutil.copyfile(INSTALLER_SCRIPT, script)
    for name in (
        "dist/Horticalc/Horticalc.exe",
        "dist/Horticalc/_internal/pythonnet/runtime/Python.Runtime.dll",
        "dist/Horticalc/frontend/index.html",
        "dist/Horticalc/LICENSE",
        "assets/horticalc.ico",
        "scripts/packaging/horticalc.iss",
        "horticalc-v0.6.7-windows-setup.exe",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("previous output", encoding="utf-8")
    marker = tmp_path / "compiler-called"
    compiler = tmp_path / "fake-iscc.ps1"
    marker_path = str(marker).replace("'", "''")
    compiler.write_text(f"Set-Content -LiteralPath '{marker_path}' -Value 'called'\n", encoding="utf-8")
    python_path = sys.executable.replace("'", "''")
    script_path = str(script).replace("'", "''")
    compiler_path = str(compiler).replace("'", "''")
    command = f"""
function python {{
    & '{python_path}' -c "import sys; sys.stdout.write('{version_output}'); sys.exit(7)"
}}
& '{script_path}' -IsccPath '{compiler_path}'
"""
    environment = {key: value for key, value in os.environ.items() if key != "HORTICALC_VERSION"}
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode != 0
    assert "Version discovery failed with exit code 7" in result.stderr
    assert not marker.exists()
    assert (tmp_path / "dist/Horticalc/Horticalc.exe").read_text(encoding="utf-8") == "previous output"
    assert (tmp_path / "horticalc-v0.6.7-windows-setup.exe").read_text(encoding="utf-8") == "previous output"
