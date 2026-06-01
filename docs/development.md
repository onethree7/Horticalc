# Development Guide

## Setup

From the repository root:

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

On bash-like shells, replace `.\.venv\Scripts\python.exe` with the active
virtualenv's `python`.

## Run

API and UI:

```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Launcher:

```bash
python -m horticalc.launcher
```

CLI:

```bash
python -m horticalc recipes/golden.yml --pretty
python -m horticalc solve recipes/solve_golden.yml --pretty
```

## Tests

Standard verification:

```bash
python scripts/check_unicode_controls.py
python -m pytest -q
```

Focused examples:

```bash
python -m pytest tests/test_frontend_serving.py -q
python -m pytest tests/test_solver_golden.py tests/test_solver_weighting.py -q
python -m pytest tests/test_portable_data_policy.py tests/test_launcher_smoke.py -q
```

## Docs Checks

For documentation changes:

```bash
rg -n "TODO|UNDECIDED|Task [0-9]|Implementation Roadmap" docs README.md --glob "!**/development.md" --glob "!**/documentation_maintenance.md"
rg -n "GUI_PLAN|feature_osmosis|golden_example" docs README.md --glob "!**/audit_2026_06_01.md" --glob "!**/development.md" --glob "!**/documentation_maintenance.md"
python scripts/check_unicode_controls.py
```

The full test suite also protects frontend contracts, API schemas, portable
data policy, solver defaults, Unicode controls, and release-facing behavior.

## Generated And Ignored Files

- `user/`: editable runtime copies in development.
- `logs/`: launcher logs and solver-matrix output.
- `dist/`, `build/`: packaging output.
- `_docs_backup/`: ignored documentation backups.

Do not commit generated runtime data unless the task explicitly asks for it.
