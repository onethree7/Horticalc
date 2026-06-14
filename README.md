# Horticalc

> [!NOTE]
> **Horticalc is a work in progress.** Features, calculations, and data formats
> may still change. Check important recipes before using them on a real crop.

Horticalc is a local, open-source horticultural fertilizer calculator. It
combines fertilizer composition, water values, batch size, and optional
reverse-osmosis mixing to calculate the nutrient profile of a solution. Its
solver can also work backwards from nutrient targets and suggest fertilizer
doses.

"Horti" refers to horticulture. The goal is to make nutrient-solution planning
clear, inspectable, and useful for growers, researchers, students, and curious
plant people.

## Main Features

- Calculate elements, oxides, ions, NPK values, ratios, and EC.
- Include source-water nutrients and reverse-osmosis mixing.
- Compare fertilizer-only and water-only contributions.
- Check cation and anion balance.
- Solve nutrient targets into non-negative fertilizer doses.
- Store fertilizers, water profiles, targets, and recipes in editable files.
- Use the same calculation engine through the GUI, CLI, or API.

## GUI

The GUI is intended for interactive recipe work. It runs locally in a browser
window and includes four main areas:

- **Fertilizer editor:** inspect and edit fertilizer composition data.
- **Water values:** manage water profiles and RO-water mixing.
- **Calculator:** build recipes and inspect their nutrient results.
- **Solver:** enter target values and calculate matching fertilizer doses.

The GUI is useful when developing a recipe, comparing products, adjusting
water values, or exploring how each fertilizer changes the final solution. It
also supports German, English, Dutch, Spanish, and Simplified Chinese.

## Scientific Approach

Horticalc aims to keep its calculations transparent and reproducible. It uses:

- mass fractions, batch volume, and molar masses for nutrient conversions;
- element, oxide, mmol/L, and meq/L representations;
- ion-balance calculations for checking the modeled solution;
- an ion-based EC model with temperature and ionic-strength corrections;
- deterministic non-negative least squares for the fertilizer solver;
- automated tests for conversions, water handling, EC, solver behavior, and
  known recipes.

The result is a calculation model rather than a plant-growth simulation. It
does not currently model every chemical equilibrium, precipitation reaction,
or biological response. More detail is available in
[`docs/EC.md`](docs/EC.md), [`docs/solver.MD`](docs/solver.MD), and
[`docs/data_model.md`](docs/data_model.md).

## Start The GUI

Horticalc requires Python 3.10 or newer when running from source.

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

The launcher starts the local FastAPI server and opens Horticalc in Edge,
Chrome, Chromium, or the default browser. Packaged releases can instead be
started with `Horticalc.exe` on Windows or `./horticalc` on Linux.

## CLI

The CLI reads YAML recipes and writes JSON results. It is useful for scripts,
repeatable comparisons, automated experiments, and version-controlled recipes.

Calculate a recipe:

```bash
python -m horticalc recipes/golden.yml --pretty
```

Solve a target profile:

```bash
python -m horticalc solve recipes/solve_golden.yml --pretty
```

Use a different water profile:

```bash
python -m horticalc recipes/golden.yml --load-water 65936 --pretty
```

Write the result to a file:

```bash
python -m horticalc recipes/golden.yml \
  --out solutions/example_output.json --pretty
```

On Windows, use `.\.venv\Scripts\python.exe` in place of `python` when the
virtual environment is not activated. On Linux, use `./.venv/bin/python`.

## Technology

Horticalc uses Python, NumPy, PyYAML, FastAPI, uvicorn, and a Vanilla
JavaScript frontend. Portable Windows and Linux builds use PyInstaller.

## Documentation

- [User guide](docs/user_guide.md)
- [Documentation map](docs/index.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api_reference.md)
- [Data model and units](docs/data_model.md)
- [Solver behavior](docs/solver.MD)
- [Contributor guide](AGENTS.md)
