# Development Guide

Status: `operation-guide`.

## Setup And Run From Source

See [commands.md](commands.md#install-and-run-from-source) for the exact venv and pip commands.

## Test Structure

- Calculation and unit tests: `tests/test_calculation_chemistry.py`,
  `tests/test_ec.py`, `tests/test_recipe_regressions.py`,
  `tests/test_units.py`, and `tests/test_water_profiles.py`.
- Solver tests: `tests/test_solver_*.py`.
- Frontend unit tests: `tests/frontend/*.test.mjs` using Node's built-in test runner.
- Frontend browser behavior: `tests/test_frontend_browser_smoke.py` and `scripts/frontend_smoke.cjs`.
- API tests: `tests/test_api_*.py`.
- Packaging and launcher tests: `tests/test_portable_data_policy.py`, `tests/test_launcher_*.py`.

Run the standard suite and focused examples: see [commands.md](commands.md#run-tests).

## Packaging And Release Entry Points

- Local PyInstaller build scripts: `scripts/packaging/build_linux.sh`, `scripts/packaging/build_windows.ps1`.
- CI release workflow: `.github/workflows/release.yml`.
- Release verification and checksum commands are in [commands.md](commands.md#release-verification).

## How To Update Docs

When you change an API route, output key, solver default, file path, launcher behavior, persistence rule, or UI workflow, update the matching doc in the same change. See [documentation_architecture.md](documentation_architecture.md#update-triggers) for the mapping.

## Frontend Test Requirement

The production frontend uses native ES modules and has no bundler or runtime
npm dependency. Development tooling is pinned to Ruff `0.16.1`, ESLint
`10.7.0`, Stylelint `17.14.0`, and `stylelint-config-standard` `40.0.0`.
`python scripts/test.py` installs missing development tools and runs Python
format/lint checks, frontend lint, Node unit tests, Playwright behavior tests,
and the Pytest suite. Use `--pytest-only` for a focused Pytest run without lint
or frontend checks. Every lint command fails on warnings.

For the Playwright test harness only, set `HORTICALC_BROWSER_PATH` when
Chrome/Chromium is installed outside the standard test locations, or set
`HORTICALC_TEST_URL` when running `node scripts/frontend_smoke.cjs` against an
already-running development server. The runtime launcher never locates or
starts Chrome/Chromium. Use
`HORTICALC_NO_GUI=1` for headless launcher and packaged-binary smoke tests.

## Generated And Ignored Files

- `user/`: runtime overrides.
- `logs/`: generated launcher and runtime logs.
- `dist/`, `build/`: packaging output.
- `node_modules/`: installed frontend test dependencies.
- `_docs_backup/`: ignored documentation backups.

Do not commit generated runtime data unless the task explicitly asks for it.
