# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

import sys
import os
from pathlib import Path


# PyInstaller exec() does not guarantee __file__ in CI; resolve root via env/cwd.
project_root_env = os.environ.get("HORTICALC_PROJECT_ROOT") or os.environ.get(
    "GITHUB_WORKSPACE"
)
project_root = Path(project_root_env).resolve() if project_root_env else Path.cwd().resolve()
app_name = "Horticalc" if sys.platform == "win32" else "horticalc"
entry_script = project_root / "src" / "horticalc" / "launcher.py"
show_console = sys.platform != "win32"
if sys.platform == "win32":
    hidden_imports = ["tzdata", "webview", "webview.platforms.edgechromium"]
else:
    hidden_imports = ["webview", "webview.platforms.gtk"]


a = Analysis(
    [str(entry_script)],
    pathex=[str(project_root), str(project_root / "src")],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=show_console,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)
