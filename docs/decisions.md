# Decisions Checklist (Portable Releases)

Each decision is marked **DEFAULT** or **UNDECIDED** explicitly.

## Build & Packaging
- **Linux build baseline runner version:** DEFAULT — `ubuntu-22.04`.
- **Packaging mode:** DEFAULT — PyInstaller **onedir** (not onefile).
- **Windows tzdata bundling:** DEFAULT — include `tzdata` via PyInstaller hidden import to satisfy `zoneinfo` on Windows.

## Runtime & Networking
- **Bind address:** DEFAULT — `127.0.0.1` only.
- **Port policy:** DEFAULT — bind with `port=0` so the OS selects a free port. Confirmed in embedded UI launcher.
- **Lockfile path/name:** DEFAULT — `AppRoot/user/horticalc.lock.json`. Confirmed in Task 2.
- **Embedded UI window:** DEFAULT — `pywebview` (Edge WebView2 on Windows, GTK/WebKit on Linux).

## UI Routing
- **SPA fallback needed?:** UNDECIDED — verify during Task 1 (frontend currently has no client-side routing).

## Data & Persistence
- **AppRoot definition:** DEFAULT — packaged executable directory; in dev, repo root.
- **First-run copy behavior:** DEFAULT — copy shipped defaults from `AppRoot/data/` to `AppRoot/user/` when user copies are missing.

## CI/Release
- **Release trigger:** DEFAULT — tags matching `v*` plus manual workflow dispatch.
- **CI runner OSes:** DEFAULT — `ubuntu-22.04` and `windows-latest`.
- **CI Python version:** DEFAULT — `3.11.9`.
- **Release workflow permissions:** DEFAULT — `contents: write` for attaching assets to GitHub Releases.
