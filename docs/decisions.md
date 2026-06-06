# Decisions Log

Status: decision-log.

## Entry Template

- Date:
- Decision:
- Status: Proposed | Accepted | Deprecated
- Rationale:
- Source files:
- Links:

## Current Accepted Decisions

### Packaging

- PyInstaller mode: onedir.
- Windows executable name: `Horticalc.exe`.
- Linux executable name: `horticalc`.
- Windows includes `tzdata` as a hidden import.
- Release artifacts include `frontend/`, `data/`, and `recipes/`.

Source: `scripts/packaging/horticalc.spec`,
`scripts/packaging/build_windows.ps1`, `scripts/packaging/build_linux.sh`.

### Runtime And Networking

- Bind address: `127.0.0.1`.
- Port policy: scan `8000..8100`.
- Health endpoint: `/health`.
- Lockfile: `AppRoot/user/horticalc.lock.json`.
- Logs: `AppRoot/logs/launcher.log`.
- Preferred browser: Edge, Chrome, or Chromium in app mode.
- Browser fallback: system default browser.
- No-browser CI mode: `HORTICALC_NO_BROWSER=1`.
- Keep fallback server mode: `HORTICALC_KEEP_SERVER=1`.

Source: `src/horticalc/launcher.py`.

### Portable Data

- AppRoot is the repo root in development and the executable folder in release.
- Runtime writes stay under `AppRoot/user/` and `AppRoot/logs/`.
- The shipped fertilizer catalog remains in `data/fertilizers.csv`; user
  fertilizer edits are stored as overrides and disabled names under `user/`.
- Shipped YAML defaults are copied to user space on first run if missing.
- AppRoot must be writable; otherwise startup fails fast.

Source: `src/horticalc/paths.py`, `src/horticalc/data_io.py`.

### API And Frontend

- The backend serves the frontend from the same origin at `/`.
- API routes are registered before the static frontend mount.
- The frontend is a static Vanilla JS app.
- The visible workflow areas are `DUENGER-EDITOR`, `WASSERWERTE`,
  `RECHNER`, and `SOLVER`.
- The frontend fetches solver config schema from `/schema/solver-config`.
- Legacy macro/stage solver controls are removed from the backend config and UI.
- Frontend i18n is implemented without a bundler or external dependency in
  `frontend/i18n/`. German is the fallback catalog; English, Dutch, Spanish,
  and Simplified Chinese catalogs must keep the same keys. Language selection is
  stored in `localStorage` under `horticalc.locale` and only affects frontend
  presentation text.
- API keys, CSV fields, element symbols, units, persisted recipe fields, and
  solver config keys remain literal data contracts and are not translated.

Source: `api/app.py`, `frontend/`, `tests/test_frontend_solver_config_ui.py`,
`tests/test_frontend_i18n.py`.

### Solver

- Default `nitrogen_objective_mode`: `n_total_only`.
- Default `relative_weighting`: `false`.
- Default `singleton_supplier_enabled`: `false`.
- Default `singleton_underfill_enabled`: `true`.
- Report-only ignored target keys: `S`, `SO4`, `Na`, `Cl`.
- Solver matrix scoring follows `result.objective_elements`.

Source: `src/horticalc/solver_config.py`, `src/horticalc/solver.py`,
`tests/test_cli_solver_config.py`, `tests/test_solver_matrix.py`.

Historical note: the 2026-05-31 deep solver matrix report recommended
`relative_weighting=true`, but current code and tests default it to `false`.
The report is retained as historical evidence, not as the active default table.

### CI/Release

- Release trigger: tags matching `v*` and manual workflow dispatch.
- CI OSes: `ubuntu-22.04` and `windows-latest`.
- CI Python: `3.11.9`.
- Release permissions: `contents: write`.
- Packaged binary smoke test uses `HORTICALC_NO_BROWSER=1`.

Source: `.github/workflows/release.yml`.

## Maintenance Log

- 2026-06-01: Reworked documentation, added current architecture/API/data
  docs, deleted obsolete tracked plan/stub docs, and backed up old docs to
  `_docs_backup/2026-06-01-pre-docs-rework/`.
