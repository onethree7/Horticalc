# User Guide

## TL;DR Quick Start

Download the latest release, extract the archive, and start Horticalc:

- **Windows:** run `Horticalc.exe`.
- **Linux:** run `./horticalc`.

The app opens in your browser. That's it.

Horticalc can be used through its local browser GUI or from the command line.
Both interfaces use the same calculation core.

## Choose An Interface

Use the **GUI** for interactive work: editing fertilizers and water values,
building recipes, comparing results, and exploring solver targets.

Use the **CLI** for repeatable calculations, scripts, automated comparisons,
and recipes stored in version control. Editable profiles and recipes are YAML;
CLI output, API payloads, GUI data exchange, and automation results are JSON.

## Start The GUI

Running from source requires Python 3.10 or newer and a writable checkout of
the repository.

### Windows

From PowerShell in the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m horticalc.launcher
```

### Linux

From a terminal in the repository root:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m horticalc.launcher
```

The launcher starts a server on `127.0.0.1`, waits for its health check, and
opens Horticalc in Edge, Chrome, or Chromium when available. Otherwise, it uses
the system browser.

For a packaged release, extract the complete archive to a writable folder and
run `Horticalc.exe` on Windows or `./horticalc` on Linux. Keep the executable
beside the included `_internal/`, `frontend/`, `data/`, and `recipes/` folders.
The packaged `README.txt` explains backup, reset, and troubleshooting. Back up
`user/` to preserve saved profiles and settings; shipped defaults remain in
`data/` and `recipes/` and are not duplicated into `user/`.

### Development Server

To run the server directly instead of using the launcher:

```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/`.

## GUI Areas

- **Fertilizer editor:** inspect, search, and edit fertilizer products and
  composition values in one continuous table. The final **Solver max / L**
  column optionally limits the dose the Solver may choose; leave it empty for
  no limit.
- **Water values:** load, edit, save, and mix water profiles with reverse-
  osmosis water.
- **Calculator:** select fertilizers and doses, calculate a recipe, and inspect
  its nutrient, ion, ratio, balance, and EC results.
- **Solver:** enter a nutrient target and calculate matching fertilizer doses.

The GUI supports German, English, Dutch, Spanish, and Simplified Chinese. The
language setting changes interface text but not recipe keys, element symbols,
CSV columns, or API fields.

## Calculator Workflow

1. Load or edit the fertilizer list if needed.
2. Select a water profile or enter water values.
3. Load a recipe or select fertilizers manually.
4. Open the compact **Settings** disclosure in Configuration to choose the
   batch-volume, solid-dose, and liquid-dose display units, then enter the
   always-visible batch amount and fertilizer doses. The closed disclosure
   summarizes the active units, and every calculator row shows its actual unit
   according to the fertilizer's solid/liquid type.
5. Calculate and inspect the result tables and summary sidebar.

Horticalc remembers the directly selected water profile, batch volume, and
volume and dose display units as startup defaults. Switching a unit converts
the shown number without changing the physical batch or canonical dose. API and
recipe data remain liters plus grams-for-solids/mL-for-liquids. Loading a recipe can temporarily override its own liters,
water profile, and Solver configuration without changing those user defaults.

Results include element and oxide totals, ions, ion balance, fertilizer-only
and water-only contributions, EC, NPK metrics, nutrient ratios, and Sluijsmann.

## Solver Workflow

1. Load a target profile or enter target values.
2. Select the fertilizers the solver may use.
3. Add fixed doses only when a fertilizer amount must remain unchanged.
4. Calculate the solution.
5. Review target, achieved, and difference values, then copy the result or
   apply it to the calculator.

The solver only optimizes the nutrients listed in `objective_elements` in its
result. Other displayed nutrients show side effects of the proposed recipe.
Sulfur targets are report-only by default; enable the sulfur objective in the
advanced solver settings when sulfur should affect the fit.

## CLI

Run these examples from the repository root after installing Horticalc. If the
virtual environment is not active, replace `python` with
`.\.venv\Scripts\python.exe` on Windows or `./.venv/bin/python` on Linux.

Calculate a recipe:

```bash
python -m horticalc recipes/golden.yml --pretty
```

Solve a target recipe:

```bash
python -m horticalc solve recipes/solve_golden.yml --pretty
```

Override the recipe's water profile:

```bash
python -m horticalc recipes/golden.yml --load-water 65936 --pretty
```

Write JSON output to a file:

```bash
python -m horticalc recipes/golden.yml \
  --out solutions/example_output.json --pretty
```

Override a solver setting for one run:

```bash
python -m horticalc solve recipes/solve_golden.yml \
  --nitrogen-objective-mode n_forms_only --pretty
```

Use `python -m horticalc --help` or `python -m horticalc solve --help` for all
available options. Recipe fields, units, and output keys are documented in the
[data model](data_model.md), with solver behavior covered in
[solver.MD](solver.MD).
