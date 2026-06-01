# Horticalc

Horticalc is a portable fertilizer calculator with a Python calculation core,
a FastAPI backend, and a static browser UI. It calculates nutrient solution
outputs from fertilizer recipes and can solve target nutrient profiles into
fertilizer grams.

## Quick Start

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`.

The launcher path starts the same local app and opens a browser window:

```bash
python -m horticalc.launcher
```

CLI examples:

```bash
python -m horticalc recipes/golden.yml --pretty
python -m horticalc solve recipes/solve_golden.yml --pretty
```

## Documentation

- Start here: [docs/index.md](docs/index.md)
- Contributor and automation guide: [AGENTS.md](AGENTS.md)
- Build and release guide: [docs/release_build.md](docs/release_build.md)
- Full docs audit from the 2026-06-01 rework: [docs/audit_2026_06_01.md](docs/audit_2026_06_01.md)

## Verify

```bash
python scripts/check_unicode_controls.py
python -m pytest -q
```
