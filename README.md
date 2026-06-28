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

## Getting Started

Horticalc includes an interactive browser GUI and a command-line interface.
Editable profiles and recipes are stored as YAML; API, GUI, CLI output, and
automation results use JSON. The **[user guide](docs/user_guide.md)** explains
when to use each interface, how to start the GUI on Windows or Linux, and how
to run calculator and solver recipes from the CLI.

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

## Technology

Horticalc uses Python, NumPy, PyYAML, FastAPI, uvicorn, and a Vanilla
JavaScript frontend. Portable Windows and Linux builds use PyInstaller.

## License

Copyright © 2026 Horticalc contributors.

Horticalc is free software licensed under the GNU General Public License,
version 3 or (at your option) any later version. See [LICENSE](LICENSE). The
corresponding source code and release build scripts are maintained in this
repository.

## Documentation

- [User guide](docs/user_guide.md)
- [Documentation map](docs/index.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api_reference.md)
- [Data model and units](docs/data_model.md)
- [Solver behavior](docs/solver.MD)
- [Security and release verification](SECURITY.md)
- [Contributor guide](AGENTS.md)
