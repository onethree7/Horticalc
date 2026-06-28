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

Lock ownership is claimed exclusively before uvicorn starts. Concurrent
launches wait for that owner to become healthy, while dead or malformed locks
are removed safely. Lock and launcher-session records use durable replacement
writes. Browser profile directories are collision-proof. When no supported
app-mode browser is available, the system-browser fallback keeps the backend
running until the launcher process is stopped; later launches reuse it.
Fallback launchers connected to an existing backend keep their own session
record alive, preventing the owner from stopping while the fallback tab is in
use. Session records include process identity to detect PID reuse, and stale
browser profiles are cleaned only after seven days.

`pyproject.toml` owns runtime dependency declarations.
`constraints-release.txt` pins the complete release build environment used by
CI and local release builds.

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

```powershell
$env:PIP_CONSTRAINT = "constraints-release.txt"
python -m pip install . pyinstaller
```

On Linux, use `PIP_CONSTRAINT=constraints-release.txt python -m pip install . pyinstaller`.

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

On Windows, `scripts/packaging/build_windows.ps1` also generates a PyInstaller
version resource with `scripts/packaging/write_windows_version_info.py`. CI
passes the Git tag or short commit through `HORTICALC_VERSION`; local builds
can set the same environment variable before running the script.

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
2. Resolves the release version from the tag or current commit.
3. Builds the platform package.
4. Starts the packaged binary with `HORTICALC_NO_BROWSER=1`.
5. Reads `AppRoot/user/horticalc.lock.json`.
6. Polls `/health`.
7. Checks that `frontend/`, `data/`, `recipes/`, and `logs/` exist.
8. Computes a SHA-256 checksum file for each platform archive.
9. Creates GitHub Artifact Attestations for each archive and checksum file.
10. Uploads artifacts.
11. Attaches release assets for `v*` tags.

## Cut A Release

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

GitHub Actions builds and publishes:

- `horticalc-vX.Y.Z-linux.tar.gz`
- `horticalc-vX.Y.Z-linux.tar.gz.sha256`
- `horticalc-vX.Y.Z-windows.zip`
- `horticalc-vX.Y.Z-windows.zip.sha256`

## Release Verification

`.github/workflows/release.yml` owns release archive checksums and GitHub
Artifact Attestations. These prove file integrity and GitHub Actions build
provenance; they are not Windows Authenticode signatures and do not make
Windows show a verified publisher for `Horticalc.exe`.

Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 .\horticalc-vX.Y.Z-windows.zip
Get-Content .\horticalc-vX.Y.Z-windows.zip.sha256
```

Linux:

```bash
sha256sum -c horticalc-vX.Y.Z-linux.tar.gz.sha256
```

With the GitHub CLI:

```bash
gh attestation verify horticalc-vX.Y.Z-windows.zip --repo onethree7/Horticalc
gh attestation verify horticalc-vX.Y.Z-linux.tar.gz --repo onethree7/Horticalc
```

For security reporting and antivirus false-positive notes, see
[SECURITY.md](../SECURITY.md).

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
python scripts/test.py
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
