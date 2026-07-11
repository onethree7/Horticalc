# Development Guide

Status: `operation-guide`.

## Setup And Run From Source

See [commands.md](commands.md#install-and-run-from-source) for the exact venv and pip commands.

## Test Structure

- Calculation and unit tests: `tests/test_ec.py`, `tests/test_core.py`, `tests/test_units.py`.
- Solver tests: `tests/test_solver_*.py`.
- Frontend and UI tests: `tests/test_frontend_*.py`.
- API tests: `tests/test_api_*.py`.
- Packaging and launcher tests: `tests/test_portable_data_policy.py`, `tests/test_launcher_*.py`.
- Solver matrix tests: `tests/test_solver_matrix.py`.

Run the standard suite and focused examples: see [commands.md](commands.md#run-tests).

## Packaging And Release Entry Points

- Local PyInstaller build scripts: `scripts/packaging/build_linux.sh`, `scripts/packaging/build_windows.ps1`.
- CI release workflow: `.github/workflows/release.yml`.
- Release verification and checksum commands are in [commands.md](commands.md#release-verification).

## How To Update Docs

When you change an API route, output key, solver default, file path, launcher behavior, persistence rule, or UI workflow, update the matching doc in the same change. See [documentation_architecture.md](documentation_architecture.md#update-triggers) for the mapping.

## Node.js Requirement

The small executable vanilla-JavaScript tests use only Node.js built-in modules. No `npm install` or frontend bundler is required.

## Generated And Ignored Files

- `user/`: runtime overrides.
- `logs/`: launcher and solver-matrix logs.
- `dist/`, `build/`: packaging output.
- `_docs_backup/`: ignored documentation backups.

Do not commit generated runtime data unless the task explicitly asks for it.
