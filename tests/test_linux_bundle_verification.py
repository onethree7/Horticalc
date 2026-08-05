from __future__ import annotations

import pytest

from scripts.packaging.verify_linux_bundle import inspect_linux_bundle, verify_linux_bundle


def touch(root, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def test_linux_bundle_accepts_python_and_wheel_owned_libraries(tmp_path) -> None:
    touch(tmp_path, "horticalc")
    touch(tmp_path, "_internal/libpython3.11.so.1.0")
    touch(tmp_path, "_internal/numpy.libs/libstdc++-wheel-owned.so.6")
    touch(tmp_path, "_internal/scipy.libs/libgfortran-wheel-owned.so.5")

    assert inspect_linux_bundle(tmp_path) == []
    verify_linux_bundle(tmp_path)


@pytest.mark.parametrize(
    "relative",
    [
        "_internal/libstdc++.so.6",
        "_internal/libglib-2.0.so.0",
        "_internal/libgtk-3.so.0",
        "_internal/libicuuc.so.70",
        "_internal/gi_typelibs/Gtk-3.0.typelib",
        "_internal/lib/gdk-pixbuf/loaders/libpixbufloader-svg.so",
        "_internal/share/glib-2.0/schemas/gschemas.compiled",
        "_internal/PySide6/QtWebEngineCore.abi3.so",
        "_internal/cefpython3/cefpython_py311.so",
    ],
)
def test_linux_bundle_rejects_mixed_native_gui_runtime(tmp_path, relative) -> None:
    touch(tmp_path, relative)

    violations = inspect_linux_bundle(tmp_path)

    assert len(violations) == 1
    assert relative in violations[0]
    with pytest.raises(RuntimeError, match="forbidden native runtime"):
        verify_linux_bundle(tmp_path)
