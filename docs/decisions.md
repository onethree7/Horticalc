# Decisions Log

Status: `decision-log`.

## Entry Template

- Date:
- Decision:
- Status: Proposed | Accepted | Deprecated
- Rationale:
- Source files:
- Links:

## License

- Horticalc is licensed under `GPL-3.0-or-later`.
- Source distributions and portable release archives include the canonical GPLv3 `LICENSE` text.
- The portable README identifies the copyright holder, warranty disclaimer, license, and corresponding-source location.

Source: `LICENSE`, `pyproject.toml`, `README.md`, `scripts/packaging/README.txt`.

## Packaging

- PyInstaller mode: onedir.
- Windows executable name: `Horticalc.exe`.
- Linux executable name: `horticalc`.
- Windows includes `tzdata` as a hidden import.
- Release artifacts include `frontend/`, `data/`, `recipes/`, the portable `README.txt`, and `LICENSE`.

Source: `scripts/packaging/horticalc.spec`, `scripts/packaging/build_windows.ps1`, `scripts/packaging/build_linux.sh`.

## Runtime And Networking

- Bind address: `127.0.0.1`.
- Port policy: scan `8000..8100`.
- Health endpoint: `/health`.
- Lockfile: `AppRoot/user/horticalc.lock.json`.
- App-window sessions: PID-backed files in `AppRoot/user/launcher_sessions/`.
- Logs: rotating `AppRoot/logs/launcher.log` files.
- Preferred browser: Edge, Chrome, or Chromium in app mode.
- Browser fallback: system default browser; the local server remains running.
- No-browser CI mode: `HORTICALC_NO_BROWSER=1`.

Source: `src/horticalc/launcher.py`.

## Portable Data

- AppRoot is the repo root in dev and the executable folder in release.
- Runtime writes stay under `AppRoot/user/` and `AppRoot/logs/`.
- The shipped fertilizer catalog remains in `data/fertilizers.csv`; user edits are stored as overrides and disabled names under `user/`.
- Shipped YAML defaults stay in place; user YAML overrides are layered by filename, and redundant copies from older releases are pruned on startup.

Source: `src/horticalc/paths.py`, `src/horticalc/data_io.py`.

## API And Frontend

- The backend serves the frontend from the same origin at `/`.
- API routes are registered before the static frontend mount.
- The frontend is a static Vanilla JS app with one native ES-module entrypoint, controller-owned feature state, and no production bundler.
- Batch volume is canonical liters in the core, API, CLI, and recipe files; the GUI can display L, US gal, Imp gal, or m³.
- The fertilizer dose contract remains `grams`: grams for solids, mL for liquids, with `weight_factor` as liquid density.
- `user/preferences.json` stores theme, default batch liters, volume and dose display units, UI-visible solver defaults, and the last directly loaded water profile.
- Frontend i18n is implemented without a bundler in `frontend/i18n/`; language selection is stored in `localStorage` and `user/preferences.json`.
- Numeric values use `.` as the decimal separator in output and persistence; GUI inputs accept `.` or `,`.
- Fertilizer physical state is stored as Boolean `liquid` and CSV `Liquid` (`0` solid, `1` liquid).

Source: `api/app.py`, `frontend/`, `src/horticalc/data_io.py`.

## Solver

- Default `solver_model`: `mass_nnls`; `legacy` remains an explicit
  compatibility option. Experimental molar goal policies are research-only.
- `mass_nnls` minimizes unweighted squared elemental residuals in canonical
  `mg/L`, uses `N_total` when present, and includes a non-zero `S` target.
- Fertilizer `SolverRole=fixed_only` prevents variable Solver dosing while
  preserving explicit fixed doses. The shipped HuminTech AMINO POWER and
  Fulvital products use this role; Fetrilon remains variable.
- Default `nitrogen_objective_mode`: `n_total_only`.
- Default `relative_weighting`: `false`.
- Default `singleton_supplier_enabled`: `false`.
- Default `singleton_underfill_enabled`: `true`.
- Report-only ignored target keys: `Na`, `Cl`. `S` is report-only unless `s_objective_enabled` is true.
- Solver matrix scoring follows `result.objective_elements`.

Source: `src/horticalc/solver_config.py`, `src/horticalc/solver.py`.

## CI/Release

- Release trigger: exact tag `v0.6.0` and manual workflow dispatch.
- CI OSes: `ubuntu-22.04` and `windows-latest`.
- CI Python: `3.11.9`.
- Release permissions: `contents: write`.
- Packaged binary smoke test uses `HORTICALC_NO_BROWSER=1`.

Source: `.github/workflows/release.yml`.
