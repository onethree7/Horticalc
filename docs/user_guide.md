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

Use `Sprache` in the `Konfiguration` card to switch the frontend between
German, English, Dutch, Spanish, and Simplified Chinese. The selection is stored
in the browser as `horticalc.locale`. It changes visible UI text only; files,
API keys, CSV headers, element symbols, and saved recipes keep their original
data names.

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
   Use `Alle` to allow every fertilizer, `Nur aktive` to temporarily show only
   selected fertilizers, and `Auswahl leeren` to reset the allowed list.
3. Leave `Override / fixe Menge (g, optional)` collapsed unless a fertilizer
   must be held at a fixed gram amount.
4. Keep `Auto übernehmen` enabled in the lower action row when the calculator
   and live sidebar should update after each solve.
5. Click `Solver berechnen`.
6. Copy the result or use `Im Rechner ansehen` to switch to the calculator. The
   clipboard text includes batch liters, osmosis percent, fertilizer grams, NPK,
   EC, Solver target/achieved/delta values, and ion mg/L values. It is compact
   space-aligned text for monospace copy/paste code blocks.
7. Adjust the bottom `Erweitert` solver config, including urea, phosphate
   handling, and optional `S als Solver-Ziel`, only when needed.

The solver optimizes only `objective_elements`, but the Solver result table
still shows the standard nutrient rows. Rows that were not active targets are
muted so collateral nutrient changes remain visible.

`S`/`SO4` targets are visible in reports but ignored by default. Enable
`S als Solver-Ziel` in `Erweitert` when sulfur demand should actively influence
the fertilizer selection.

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
