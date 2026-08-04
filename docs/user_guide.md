# User Guide

Status: `current-state`.

Horticalc can be used through a local browser GUI or the command line. Both use the same calculation core in `src/horticalc/`.

## Choose An Interface

- **GUI**: interactive work, editing fertilizers and water, building recipes, comparing results, and exploring solver targets.
- **CLI**: repeatable calculations, scripts, and automation. See [cli_reference.md](cli_reference.md) and [commands.md](commands.md).

## GUI Workflows

### Fertilizer Editor

Inspect, search, and edit fertilizer products and composition values in one continuous table. The final **Solver max / L** column optionally limits the dose the Solver may choose; leave it empty for no limit. Changes are saved to `user/fertilizers_overrides.csv` and `user/fertilizers_disabled.txt`. Source: `src/horticalc/data_io.py`.

### Water Values

Load, edit, save, and mix water profiles with reverse-osmosis water. The osmosis share is the percentage of the batch that is RO water (modelled as 0 mg/L). Source: `src/horticalc/core.py` and `frontend/app/water.js`.

### Calculator

1. Select a water profile or enter water values.
2. Select fertilizers and doses.
3. Click **Calculate**.
4. Inspect element totals, oxides, ions, ion balance, fertilizer-only and water-only contributions, EC, NPK metrics, and Sluijsmann.

The GUI supports German, English, Dutch, Spanish, and Simplified Chinese. The
language setting changes interface text but not recipe keys, element symbols,
CSV columns, or API fields.

### Solver

1. Load a target profile or enter target values.
2. Select the fertilizers the solver may use.
3. Add fixed doses if a fertilizer amount must remain unchanged.
4. Click **Calculate**.
5. Review target, achieved, and difference values. The `objective_elements` list shows what was actually optimized. Apply the result to the calculator or copy it.

When saving the target profile, enable **Save Solver setup** to retain the
batch volume, water profile and osmosis share, allowed fertilizers, fixed
amounts, urea mode, and Solver settings. Without this option, the profile keeps
only its nutrient targets. Horticalc warns before active fixed amounts or an
existing stored setup are omitted. **Save as fertilizer recipe** stores the
calculated doses for mixing; it does not store which doses were fixed Solver
inputs. Horticalc also asks before replacing any existing target profile. The
check uses the actual stored filename, so different entered names cannot
silently overwrite one another after filename cleanup.

Sulfur targets are report-only by default; enable the sulfur objective in the advanced solver settings if sulfur should affect the fit.

## UI Preferences, Units, Language, And Persistence

The **Configuration** card in `frontend/index.html` controls:

- batch volume and volume unit,
- solid dose unit,
- liquid dose unit,
- visual theme,
- language.

The theme selector includes the original Horticalc variants plus Solarized Light, Dracula, Gruvbox Dark, Catppuccin Mocha, Monokai Classic, Windows 95, Commodore 64, Nord / Arctic Workstation, and Amber CRT. Windows 95, Commodore 64, and Amber CRT are full visual skins; Nord is a restrained, high-readability editor palette. All preserve the same layout and interactions.

These are stored in `user/preferences.json` because the launcher's browser profiles are temporary. Theme, language, and display-unit choices are presentation-only; recipe, API, and solver inputs remain canonical. Source: `api/app.py`, `src/horticalc/data_io.py`, and `frontend/app/settings.js`.

Switching a display unit changes the shown number without changing the physical batch or canonical dose. Loading a recipe can temporarily override its own liters and solver config without rewriting user defaults.

## Persistence Notes

- Saved fertilizers, water profiles, nutrient-solution targets, and recipes are written to `user/`.
- Shipped defaults in `data/` and `recipes/` are layered underneath user overrides.
- Back up `user/` to preserve profiles and settings.

For command-line workflows, see [cli_reference.md](cli_reference.md) and [commands.md](commands.md).
