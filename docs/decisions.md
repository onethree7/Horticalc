# Decisions Checklist (Portable Releases)

Each decision is marked **DEFAULT** or **UNDECIDED** explicitly.

## Build & Packaging
- **Linux build baseline runner version:** DEFAULT — `ubuntu-22.04`.
- **Packaging mode:** DEFAULT — PyInstaller **onedir** (not onefile).

## Runtime & Networking
- **Bind address:** DEFAULT — `127.0.0.1` only.
- **Port policy:** DEFAULT — fixed-range scan on `127.0.0.1` (suggested range `8000–8100`).
- **Lockfile path/name:** DEFAULT — `AppRoot/user/horticalc.lock.json`.

## UI Routing
- **SPA fallback needed?:** UNDECIDED — verify during Task 1 (frontend currently has no client-side routing).

## Data & Persistence
- **AppRoot definition:** DEFAULT — packaged executable directory; in dev, repo root.
- **First-run copy behavior:** DEFAULT — copy shipped defaults from `AppRoot/data/` to `AppRoot/user/` when user copies are missing.

## CI/Release
- **Release trigger:** DEFAULT — tags matching `v*` plus manual workflow dispatch.
