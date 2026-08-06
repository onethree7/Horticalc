#!/usr/bin/env python3
"""Reject native GUI/system runtimes that must not ship in the Linux bundle."""

from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path

FORBIDDEN_SYSTEM_LIBRARY_PATTERNS = (
    "libatk-*.so*",
    "libatspi.so*",
    "libcairo*.so*",
    "libepoxy.so*",
    "libffi.so*",
    "libfontconfig.so*",
    "libfreetype.so*",
    "libgcc_s.so*",
    "libgdk-*.so*",
    "libgdk_pixbuf-*.so*",
    "libgio-*.so*",
    "libgirepository-*.so*",
    "libglib-*.so*",
    "libgmodule-*.so*",
    "libgobject-*.so*",
    "libgtk-*.so*",
    "libharfbuzz.so*",
    "libicu*.so*",
    "libpango*.so*",
    "libstdc++.so*",
    "libwayland-*.so*",
    "libX11.so*",
)
FORBIDDEN_DATA_PREFIXES = (
    "_internal/gi_typelibs/",
    "_internal/gio_modules/",
    "_internal/lib/gdk-pixbuf/",
    "_internal/share/glib-2.0/",
    "_internal/share/icons/",
    "_internal/share/locale/",
    "_internal/share/themes/",
)
FORBIDDEN_RENDERER_FRAGMENTS = (
    "cefpython",
    "chromium",
    "pyside",
    "pyqt",
    "qtwebengine",
)


def inspect_linux_bundle(app_root: Path) -> list[str]:
    app_root = app_root.resolve()
    if not app_root.is_dir():
        return [f"application directory does not exist: {app_root}"]

    violations: list[str] = []
    for path in sorted(app_root.rglob("*")):
        relative = path.relative_to(app_root)
        relative_posix = relative.as_posix()
        relative_folded = relative_posix.casefold()

        if not path.is_file() and not path.is_symlink():
            continue
        if any(
            relative_folded == prefix.rstrip("/").casefold() or relative_folded.startswith(prefix.casefold())
            for prefix in FORBIDDEN_DATA_PREFIXES
        ):
            violations.append(f"bundled system GUI data: {relative_posix}")
            continue

        if any(fragment in relative_folded for fragment in FORBIDDEN_RENDERER_FRAGMENTS):
            violations.append(f"unexpected renderer: {relative_posix}")
            continue

        if any(part.casefold().endswith(".libs") for part in relative.parts):
            # NumPy/SciPy wheel-owned native dependencies intentionally remain bundled.
            continue
        if any(fnmatch.fnmatchcase(path.name, pattern) for pattern in FORBIDDEN_SYSTEM_LIBRARY_PATTERNS):
            violations.append(f"bundled system library: {relative_posix}")

    return violations


def verify_linux_bundle(app_root: Path) -> None:
    violations = inspect_linux_bundle(app_root)
    if violations:
        shown = violations[:50]
        details = "\n".join(f"  - {violation}" for violation in shown)
        omitted = len(violations) - len(shown)
        suffix = f"\n  ... and {omitted} more" if omitted else ""
        raise RuntimeError(f"Linux bundle contains forbidden native runtime files:\n{details}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app_root", type=Path, help="PyInstaller onedir application root")
    args = parser.parse_args()
    try:
        verify_linux_bundle(args.app_root)
    except RuntimeError as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Linux bundle verification passed: {args.app_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
