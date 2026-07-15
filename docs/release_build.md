# Release Builds

Status: `operation-guide`.

Horticalc releases use PyInstaller onedir builds. The packaged executable starts the local API, serves the frontend, opens a browser window, and writes only inside the extracted app folder.

## Runtime Model

1. The launcher starts a FastAPI/uvicorn server on `127.0.0.1`.
2. The server exposes API routes and serves `frontend/` at `/`.
3. The launcher waits for `/health`.
4. The launcher prefers Edge, Chrome, or Chromium in app-window mode.
5. If the app is already running, the lockfile points to the active port and a second launch opens the existing server.
6. Runtime writes go to `AppRoot/user/` and `AppRoot/logs/`.
7. Browser profiles are created under `AppRoot/user/browser_profiles/` and removed after the app window closes.
8. Runtime logs rotate at 2 MiB with two backups.

Lock ownership is claimed exclusively before uvicorn starts. Concurrent launches wait for the owner to become healthy. Dead or malformed locks are removed safely. Lock and session records use durable replacement writes. Browser profile directories are collision-proof. System-browser fallback keeps the backend running until the launcher is stopped because tab closure cannot be observed reliably. Stale browser profiles are removed after seven days.

`pyproject.toml` owns runtime dependency declarations. `constraints-release.txt` pins the complete release build environment used by CI and local release builds.

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
- the exact release tag `v0.6.0`

Matrix:

- `ubuntu-22.04`
- `windows-latest`
- Python `3.11.9`

`scripts/check_release_version.py` rejects a tag that does not exactly match
`v` plus `horticalc.__version__`. Manual workflow builds retain short-commit
artifact names. Tagged builds use `v0.6.0`.

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

Do not introduce writes to OS user directories, the registry, XDG paths, `%APPDATA%`, or `%LOCALAPPDATA%`.

## Verification

Standard test suite, packaging smoke, and no-browser smoke are in [commands.md](commands.md#run-tests) and [commands.md](commands.md#release-build-pyinstaller).
