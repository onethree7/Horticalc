# Decisions log

## Decision entry template

- **Date:** YYYY-MM-DD
- **Decision:**
- **Status:** Proposed | Accepted | Deprecated
- **Rationale:**
- **Links:** (PRs, issues, docs)

## Current decisions (defaults)

Each decision is marked **DEFAULT** or **UNDECIDED** explicitly.

### Build & Packaging
- **Linux build baseline runner version:** DEFAULT — `ubuntu-22.04`.
- **Packaging mode:** DEFAULT — PyInstaller **onedir** (not onefile).
- **Windows tzdata bundling:** DEFAULT — include `tzdata` via PyInstaller hidden import to satisfy `zoneinfo` on Windows.

### Runtime & Networking
- **Bind address:** DEFAULT — `127.0.0.1` only.
- **Port policy:** DEFAULT — fixed-range scan on `127.0.0.1` (suggested range `8000–8100`). Confirmed in Task 2.
- **Lockfile path/name:** DEFAULT — `AppRoot/user/horticalc.lock.json`. Confirmed in Task 2.
- **App-window browser policy:** DEFAULT — prefer Chromium-based browsers (Edge/Chrome/Chromium) launched in app mode with `AppRoot/user/browser_profiles/` profiles; fallback to system default browser with a short grace period unless `HORTICALC_KEEP_SERVER=1` is set.
- **Browser profile cleanup:** DEFAULT — remove per-launch profile directories via `shutil.rmtree(..., ignore_errors=True)` without try/except.
- **Linux browser requirement (runtime):** DEFAULT — for best UX, a Chromium-based browser should be installed; fallback uses the system default browser.
- **Linux runtime validation:** DEFAULT — validated on Debian/Ubuntu; other distros expected to work if Chromium is installed.

### UI Routing
- **SPA fallback needed?:** UNDECIDED — verify during Task 1 (frontend currently has no client-side routing).

### Data & Persistence
- **AppRoot definition:** DEFAULT — packaged executable directory; in dev, repo root.
- **First-run copy behavior:** DEFAULT — copy shipped defaults from `AppRoot/data/` to `AppRoot/user/` when user copies are missing.

### Solver
- **Default nitrogen objective mode:** DEFAULT — use `n_total_only` for normal calculator solving. Confirmed by the 2026-05-31 deep solver matrix run, where `n_total_only` won 10/10 best-profile rows.
- **Default solver weighting:** DEFAULT — keep `relative_weighting=true`. The same deep run showed substantially worse averages when relative weighting was disabled.
- **Macro priority:** DEFAULT — keep `macro_priority_enabled=false`. Treat the feature as a deprecation/removal candidate after one more confirmation run because it was the strongest harmful boolean in the 2026-05-31 matrix.
- **Stage optimization:** DEFAULT — keep `stage_optimization_enabled=false`. Treat as a lower-priority removal candidate if it remains neutral or harmful after macro-priority cleanup.
- **Solver matrix scoring law:** DEFAULT — benchmark scoring must follow `result.objective_elements` from `solver.py` 1:1. The benchmark must not independently decide that report-only targets such as `HCO3`, `S`, `SO4`, `Na`, or `Cl` are optimization errors.

### CI/Release
- **Release trigger:** DEFAULT — tags matching `v*` plus manual workflow dispatch.
- **CI runner OSes:** DEFAULT — `ubuntu-22.04` and `windows-latest`.
- **CI Python version:** DEFAULT — `3.11.9`.
- **Release workflow permissions:** DEFAULT — `contents: write` for attaching assets to GitHub Releases.

## Maintenance log (non-decision updates)
- 2026-01-28: Removed unused `load_water_profile` helper from `src/horticalc/data_io.py`.
- 2026-01-28: Centralized request payload parsing and filename sanitization helpers in `api/app.py` (no behavior change).
- 2026-01-28: Code hygiene cleanup (launcher browser lookup, health timeout message, request parsing, and minor simplifications).
- 2026-01-28: Aligned fertilizer selection and calculator table column widths with the PR74 layout for consistent UI alignment.
