# Release Builds

Status: operation-guide.

Horticalc releases use PyInstaller onedir builds. The packaged executable
starts the local API, serves the frontend, opens a browser window, and writes
only inside the extracted app folder.

## Runtime Model

1. The launcher executable starts a FastAPI/uvicorn server on `127.0.0.1`.
2. The server exposes API routes and serves `frontend/` at `/`.
3. The launcher waits for `/health`.
4. The launcher prefers Edge, Chrome, or Chromium in app-window mode.
5. If the app is already running, the lockfile points to the active port and a
   second launch opens the existing server instead of starting another one.
6. Runtime writes go to `AppRoot/user/` and `AppRoot/logs/`.
7. Browser profiles are created under `AppRoot/user/browser_profiles/` and
   removed after the app window closes.

## AppRoot Layout

Windows:

```text
dist/Horticalc/
  Horticalc.exe
  _internal/
  frontend/
  data/
  recipes/
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
  user/      created at runtime
  logs/      created at runtime
```

## Build Locally

Install build requirements:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

Windows PowerShell:

```powershell
.\scripts\packaging\build_windows.ps1
```

Linux:

```bash
chmod +x scripts/packaging/build_linux.sh
./scripts/packaging/build_linux.sh
```

The build scripts run PyInstaller with
`scripts/packaging/horticalc.spec`, then copy `frontend/`, `data/`, and
`recipes/` into the onedir app root.

## CI Release Workflow

`.github/workflows/release.yml` runs on:

- manual workflow dispatch
- pushed tags matching `v*`

Matrix:

- `ubuntu-22.04`
- `windows-latest`
- Python `3.11.9`

The workflow:

1. Installs requirements and PyInstaller.
2. Builds the platform package.
3. Starts the packaged binary with `HORTICALC_NO_BROWSER=1`.
4. Reads `AppRoot/user/horticalc.lock.json`.
5. Polls `/health`.
6. Checks that `frontend/`, `data/`, `recipes/`, and `logs/` exist.
7. Uploads artifacts.
8. Attaches release assets for `v*` tags.

## Cut A Release

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

GitHub Actions builds and publishes:

- `horticalc-vX.Y.Z-linux.tar.gz`
- `horticalc-vX.Y.Z-windows.zip`

## Portable Data Policy

`src/horticalc/paths.py` owns this policy:

- AppRoot is the repo root in dev and the executable folder in release.
- Shipped defaults live in `data/` and `recipes/`.
- Editable runtime copies live in `user/`.
- Logs live in `logs/`.
- If AppRoot is not writable, startup fails with:

```text
Extract to a writable folder (e.g. Desktop/Downloads). Do not run from Program Files.
```

Do not introduce writes to OS user directories, the registry, XDG paths,
`%APPDATA%`, or `%LOCALAPPDATA%`.

## Verification

Standard:

```bash
python -m pytest -q
```

Packaging smoke:

```bash
python -m horticalc.launcher
```

CI-style no-browser smoke:

```bash
set HORTICALC_NO_BROWSER=1
python -m horticalc.launcher
```

Stop the process after `/health` is confirmed.
