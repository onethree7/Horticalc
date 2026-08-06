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
    hidden_imports = [
        "tzdata",
        "webview.platforms.edgechromium",
        "webview.platforms.win32",
        "webview.platforms.winforms",
    ]
    excluded_renderers = [
        "gi",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "cefpython3",
        "webview.platforms.android",
        "webview.platforms.cef",
        "webview.platforms.cocoa",
        "webview.platforms.gtk",
        "webview.platforms.mshtml",
        "webview.platforms.qt",
    ]
elif sys.platform.startswith("linux"):
    hidden_imports = ["webview.platforms.gtk"]
    excluded_renderers = [
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "cefpython3",
        "clr",
        "pythonnet",
        "webview.platforms.android",
        "webview.platforms.cef",
        "webview.platforms.cocoa",
        "webview.platforms.edgechromium",
        "webview.platforms.mshtml",
        "webview.platforms.qt",
        "webview.platforms.win32",
        "webview.platforms.winforms",
    ]
else:
    raise SystemExit("Horticalc desktop packages support Windows and Linux only")
version_file = os.environ.get("HORTICALC_VERSION_FILE") if sys.platform == "win32" else None


a = Analysis(
    [str(entry_script)],
    pathex=[str(project_root), str(project_root / "src")],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_renderers,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Linux desktop libraries must be one coherent system stack. Bundling selected
# Ubuntu GTK/GLib/C++ libraries while loading WebKitGTK from the target host
# creates ABI conflicts on newer distributions.
if sys.platform.startswith("linux"):
    a.exclude_system_libraries()

    system_gui_data_prefixes = (
        "gi_typelibs/",
        "gio_modules/",
        "lib/gdk-pixbuf/",
        "share/glib-2.0/",
        "share/icons/",
        "share/locale/",
        "share/themes/",
    )
    forced_internal_runtime_hooks = {
        "pyi_rth_gdkpixbuf.py",
        "pyi_rth_gi.py",
        "pyi_rth_gio.py",
        "pyi_rth_glib.py",
        "pyi_rth_gtk.py",
    }

    def normalized_destination(entry):
        return str(entry[0]).replace("\\", "/").lstrip("./")

    def is_system_gui_data(entry):
        destination = normalized_destination(entry)
        return any(
            destination == prefix.rstrip("/") or destination.startswith(prefix)
            for prefix in system_gui_data_prefixes
        )

    def is_forced_internal_runtime_hook(entry):
        destination_name = Path(str(entry[0])).name
        source_name = Path(str(entry[1])).name if len(entry) > 1 else ""
        return destination_name in forced_internal_runtime_hooks or source_name in forced_internal_runtime_hooks

    a.scripts = [entry for entry in a.scripts if not is_forced_internal_runtime_hook(entry)]
    a.binaries = [entry for entry in a.binaries if not is_system_gui_data(entry)]
    a.datas = [entry for entry in a.datas if not is_system_gui_data(entry)]

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
    version=version_file,
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
