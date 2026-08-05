# Architecture

Status: `current-state`.

Horticalc has five runtime layers:

1. Static browser UI in `frontend/`.
2. FastAPI app in `api/app.py`.
3. Calculation core in `src/horticalc/`.
4. Solver in `src/horticalc/solver.py` and `src/horticalc/solver_config.py`.
5. Portable launcher and packaging in `src/horticalc/launcher.py`, `scripts/packaging/`, and `.github/workflows/release.yml`.

## Source Of Truth By Concern

| Concern | Source files | Notes |
| --- | --- | --- |
| Recipe calculation | `src/horticalc/core.py` | Converts fertilizer doses and water values into solution output. |
| EC | `src/horticalc/ec.py` | Computes ion-based EC at 18 C and 25 C. |
| NPK and ratios | `src/horticalc/metrics.py` | Formats NPK strings and summary ratios. |
| Sluijsmann | `src/horticalc/sluijsmann.py` | CaO-equivalent alkalinity/acidity metric. |
| Solver | `src/horticalc/solver.py`, `src/horticalc/priority_solver.py`, `src/horticalc/solver_config.py` | Solves target profiles through standard NNLS + tuning (`nnls_tuning`) or the experimental mass-NNLS and hierarchical models. |
| Unit definitions | `src/horticalc/units.py` | Canonical volume and dose conversions. |
| Data paths | `src/horticalc/paths.py` | AppRoot, shipped defaults, user overrides, logs, lockfile. |
| Target profile contract | `src/horticalc/nutrient_profiles.py` | Canonical normalization and Solver-setup presence rules shared by API and YAML persistence. |
| Solver history | `src/horticalc/solver_history.py` | Versioned JSONL snapshots, atomic writes, retention, summaries, and detail lookup. |
| Persistence IO | `src/horticalc/data_io.py` | Loads and saves CSV, YAML, and JSON. |
| API | `api/app.py` | JSON routes, YAML save support, and static frontend. |
| UI | `frontend/index.html`, `frontend/app/main.js`, controller modules, `frontend/styles/` | Native ES-module composition, feature-owned state, and workflows. |
| Launcher | `src/horticalc/launcher.py` | Starts API, waits for health, opens browser, manages lock and sessions. |
| Packaging | `scripts/packaging/*`, `.github/workflows/release.yml` | PyInstaller onedir builds and smoke tests. |

## Request Flows

### Calculator

1. UI converts the selected batch volume and doses to canonical units and posts to `/calculate`.
2. `api/app.py` validates allowed water keys and fertilizer names.
3. `compute_solution()` in `src/horticalc/core.py` applies osmosis, normalizes water forms, calculates elements, oxides, ions, ion balance, EC, NPK, Sluijsmann, and returns the output.

### Solver

1. UI posts target values, allowed fertilizers, optional fixed doses, water profile, and solver config to `/solve`.
2. `solve_recipe_data()` in `src/horticalc/solver.py` subtracts the water baseline, builds the fertilizer contribution matrix, excludes products with a zero per-liter Solver limit from variable dosing, dispatches to standard NNLS + tuning or the experimental mass-NNLS and SciPy HiGHS hierarchical-priority models, recomputes the achieved solution with `compute_solution()`, and returns solver errors plus model-specific audit metadata.
3. After a successful solve, `api/app.py` records the canonical setup, result,
   fertilizer forms, and printable calculation projection through
   `src/horticalc/solver_history.py`. Recording failures are non-fatal.

## AppRoot And Portable Data Layout

`app_root()` in `src/horticalc/paths.py` resolves to the repository root in development, the executable folder in PyInstaller releases, or the install prefix when the packaged assets are present.

```text
AppRoot/
  data/       shipped defaults
  recipes/    shipped defaults
  frontend/   static UI
  user/       user-created overrides, preferences, and solver_history.jsonl
  logs/       rotating launcher/server logs
```

`ensure_portable_layout()` creates `user/` and `logs/`, checks they are writable, and prunes redundant YAML copies from older releases. API resource lookup layers user YAML over shipped YAML by filename. The fertilizer catalog is shipped in `data/fertilizers.csv`; user edits are stored as `user/fertilizers_overrides.csv` and `user/fertilizers_disabled.txt`.

Solver history is independent of browser storage. The API reads compact
summaries at startup and full entries on demand; the frontend formats stored
canonical values using the currently selected locale and display units. Pin
metadata stays with each JSONL entry so retention and clearing remain atomic.
Recipe and target-profile favorite filenames use `user/preferences.json` and
never modify layered shipped YAML resources.

The launcher lock records the backend owner's PID. Each Chromium app window gets a session file under `user/launcher_sessions/`. The backend owner waits until all live sessions end, plus a short grace period, before stopping. Concurrent launchers wait for the winning owner's health endpoint. System-browser fallback keeps the server running until the launcher is stopped because tab closure cannot be observed reliably. Stale browser profiles are removed after a seven-day grace period.

## Current Boundaries

- The core does not know about HTTP or the DOM.
- The API owns request validation and persistence.
- The UI owns presentation, local browser state, and workflow navigation.
- `frontend/app/main.js` is the UI composition root. Feature controllers depend only on injected transport/services and shared pure helpers; `frontend/app/api.js` has no DOM dependency.
- Packaged releases use PyInstaller onedir.
