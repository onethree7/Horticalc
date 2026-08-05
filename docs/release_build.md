# Release Builds

Status: `operation-guide`.

Horticalc releases use PyInstaller onedir builds. The packaged executable starts
the local API, serves the frontend, opens a native pywebview window, and writes
only inside the extracted app folder.

## Runtime Model

1. The launcher starts a FastAPI/uvicorn server on `127.0.0.1`.
2. The server exposes API routes and serves `frontend/` at `/`.
3. The launcher waits for `/health`.
4. The launcher opens one native pywebview window using WebView2 on Windows or GTK/WebKitGTK on Linux.
5. If the app is already running, a second launch restores and focuses the existing window.
6. Runtime writes go to `AppRoot/user/` and `AppRoot/logs/`.
7. Persistent WebView state is stored under `AppRoot/user/webview/`.
8. Runtime logs rotate at 2 MiB with two backups.

Lock ownership is claimed exclusively before uvicorn starts. Concurrent launches
wait for the owner to become healthy. Dead, malformed, or obsolete locks are
removed safely. The lock contains a random per-run token used only by the local
`/_launcher/activate` endpoint. Native window close is the lifecycle source for
server shutdown; there is no external-browser fallback.

`pyproject.toml` owns runtime dependency declarations. `constraints-release.txt` pins the complete release build environment used by CI and local release builds.
`pywebview` is pinned to `6.2.1`. The PyInstaller spec includes only the selected
platform backend and excludes Qt, PySide, CEF, MSHTML, and backends for other
operating systems.
Source installations are constrained to Python 3.10 through 3.13 because the
GTK dependency pinned by pywebview 6.2.1 does not support Python 3.14. Release
artifacts continue to use Python 3.11.9.

## Platform Requirements

- Windows 10/11: system-installed Microsoft WebView2 Runtime. Horticalc forces
  `edgechromium` and does not fall back to MSHTML or an external browser.
- Ubuntu 22.04: `python3-gi`, `python3-gi-cairo`, `gir1.2-gtk-3.0`, and
  `gir1.2-webkit2-4.1`. CI installs the matching build headers before packaging.
- Other Linux distributions: best effort with compatible GTK 3, PyGObject, and
  WebKitGTK 4.1 packages.
- Windows 7/8/8.1 and macOS: not supported by the desktop release.

## AppRoot Layout

Windows:

```text
dist/Horticalc/
  Horticalc.exe
  _internal/
  frontend/
  data/
  recipes/
  README.txt
  LICENSE
  user/      created at runtime
    webview/ persistent WebView state
  logs/      created at runtime
```

Linux:

```text
dist/horticalc/
  horticalc
  _internal/
  frontend/
  data/
  recipes/
  README.txt
  LICENSE
  user/      created at runtime
    webview/ persistent WebView state
  logs/      created at runtime
```

## Build Locally

Install build requirements with the release constraints, then run the platform build script.

For the exact commands, see [commands.md](commands.md#release-build-pyinstaller).

The build scripts run PyInstaller with `scripts/packaging/horticalc.spec`, then copy `frontend/`, `data/`, and `recipes/` into the onedir app root and add the portable `README.txt` and GPLv3 `LICENSE`. The portable README states that Horticalc is independent from named manufacturers and data sources, and that bundled product data are point-in-time snapshots without warranty.

On Windows, `scripts/packaging/build_windows.ps1` also generates a version
resource with `scripts/packaging/write_windows_version_info.py`. CI passes the
canonical package version through `HORTICALC_VERSION`; local builds derive it
from `horticalc.__version__` unless the environment variable is explicit.

## CI Release Workflow

`.github/workflows/release.yml` runs on:

- manual workflow dispatch
- the exact release tag `v0.6.1`

Matrix:

- `ubuntu-22.04`
- `windows-latest`
- Python `3.11.9`

`scripts/check_release_version.py` rejects a tag that does not exactly match
`v` plus `horticalc.__version__`. Manual workflow builds retain short-commit
artifact names. Tagged builds use `v0.6.1`.

## Release Verification

`.github/workflows/release.yml` owns release archive checksums and GitHub Artifact Attestations. These prove file integrity and GitHub Actions build provenance; they are not Windows Authenticode signatures and do not make Windows show a verified publisher for `Horticalc.exe`.

For the exact checksum and attestation commands, see [commands.md](commands.md#release-verification).

## Portable Data Policy

`src/horticalc/paths.py` owns this policy:

- AppRoot is the repo root in dev and the executable folder in release.
- Shipped defaults live in `data/` and `recipes/`.
- User-created and edited overrides live in `user/`.
- Rotating logs live in `logs/`.
- If AppRoot is not writable, startup fails fast with:

```text
Extract to a writable folder (e.g. Desktop/Downloads). Do not run from Program Files.
```

Do not introduce Horticalc application-data writes to OS user directories, the
registry, XDG paths, `%APPDATA%`, or `%LOCALAPPDATA%`. WebView state is directed
explicitly to `AppRoot/user/webview/`.

## Verification

Standard tests, packaging smoke, and headless smoke are in [commands.md](commands.md#run-tests) and [commands.md](commands.md#release-build-pyinstaller).

Before publishing a desktop release, run the packaged GUI on a clean Windows
10 VM, a clean Windows 11 VM, and Ubuntu 22.04. On each platform verify first
start, Calculator, Solver, clipboard, scrolling, persisted preferences, a second
launch restoring the existing window, and window close removing the server and
lock. On Windows also test with Chrome absent and before Edge has ever been
opened. Test a missing WebView2 or WebKitGTK runtime separately and require the
documented error without an MSHTML, Qt, or external-browser fallback. Compare
the printed artifact size with the previous equivalent build and investigate
an increase above 25 percent.
