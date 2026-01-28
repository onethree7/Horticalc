# Decisions Checklist (Portable Releases)

Each decision is marked **DEFAULT** or **UNDECIDED** explicitly.

## Build & Packaging
- **Linux build baseline runner version:** DEFAULT — `ubuntu-22.04`.
- **Packaging mode:** DEFAULT — PyInstaller **onedir** (not onefile).
- **Windows tzdata bundling:** DEFAULT — include `tzdata` via PyInstaller hidden import to satisfy `zoneinfo` on Windows.

## Runtime & Networking
- **Bind address:** DEFAULT — `127.0.0.1` only.
- **Port policy:** DEFAULT — fixed-range scan on `127.0.0.1` (suggested range `8000–8100`). Confirmed in Task 2.
- **Lockfile path/name:** DEFAULT — `AppRoot/user/horticalc.lock.json`. Confirmed in Task 2.
- **App-window browser policy:** DEFAULT — prefer Chromium-based browsers (Edge/Chrome/Chromium) launched in app mode with `AppRoot/user/browser_profiles/` profiles; fallback to system default browser with a short grace period unless `HORTICALC_KEEP_SERVER=1` is set.
- **Linux browser requirement (runtime):** DEFAULT — for best UX, a Chromium-based browser should be installed; fallback uses the system default browser.
- **Linux runtime validation:** DEFAULT — validated on Debian/Ubuntu; other distros expected to work if Chromium is installed.

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
