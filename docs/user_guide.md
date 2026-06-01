# User Guide

## Start The App

Development server:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`.

Launcher:

```bash
python -m horticalc.launcher
```

The launcher starts the local server on `127.0.0.1`, waits for `/health`, and
opens a Chromium-based app window when possible. If no supported browser is
found, it falls back to the system default browser.

## UI Areas

- `DUENGER-EDITOR`: edit fertilizer products and composition values.
- `WASSERWERTE`: load, edit, save, and reset water profiles; set osmosis
  percent; view mg/L or mmol/L helper values.
- `RECHNER`: calculate a nutrient solution from selected fertilizers and grams.
- `SOLVER`: solve target nutrient profiles into fertilizer grams.

## Calculator Workflow

1. Load or edit the fertilizer list if needed.
2. Choose or enter water values.
3. Choose a recipe profile or select fertilizer rows manually.
4. Set grams and liters.
5. Click `Berechnen` or let auto-recalculate refresh the output.

The calculator output includes element totals, oxide totals, ions, ion balance,
fertilizer-only contribution, water-only contribution, EC, NPK metrics,
Sluijsmann, and the active `osmosis_percent`.

## Solver Workflow

1. Load a nutrient solution target profile or enter target values manually.
2. Search and tick allowed fertilizers in the Solver picker, or use
   `Aus Rechner übernehmen` to add the current calculator fertilizer selection.
3. Optionally set `Fixe Menge (g, optional)` values for specific fertilizers.
4. Keep `Solver-Ergebnis automatisch im Rechner übernehmen` enabled when the
   calculator and live sidebar should update after each solve.
5. Adjust `Erweitert` solver config only when needed.
6. Click `Solver berechnen`.
7. Copy the result or use `Im Rechner ansehen` to switch to the calculator.

The solver optimizes only `objective_elements`. Some reported targets, such as
`S`, `SO4`, `Na`, and `Cl`, are intentionally not objectives in the current
solver.

## CLI

Calculate a recipe:

```bash
python -m horticalc recipes/golden.yml --pretty
```

Solve a target recipe:

```bash
python -m horticalc solve recipes/solve_golden.yml --pretty
```

Use a water profile:

```bash
python -m horticalc recipes/golden.yml --load-water 65936 --pretty
```

Write JSON output:

```bash
python -m horticalc recipes/golden.yml --out solutions/example_output.json --pretty
```

Override solver config for one CLI run:

```bash
python -m horticalc solve recipes/solve_golden.yml --nitrogen-objective-mode n_forms_only --pretty
```
