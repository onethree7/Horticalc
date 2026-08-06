# CLI Reference

Status: `current-state`.

The CLI is implemented in `src/horticalc/__main__.py`. It runs calculator or solver recipes from YAML and prints JSON.

## Commands

### Calculate a recipe

```bash
python -m horticalc recipes/<file>.yml
```

### Solve a target recipe

```bash
python -m horticalc solve user/recipes/<solver-recipe>.yml
```

## Global Options

- `--version`: print the canonical Horticalc version and exit.
- `--load-recipe <file>`: load a recipe file explicitly (overrides the positional argument).
- `--load-water <file>`: load a water profile file.
- `--out <file>`: write the JSON result to a file.
- `--pretty`: pretty-print the JSON output.
- `--solver-config KEY=VALUE ...`: override any solver config key in solve mode.
- `--nitrogen-objective-mode <mode>`: override the solver nitrogen mode.

All solver config keys are also available as `--key-name` flags. Run `python -m horticalc solve --help` for the full list.

For copy/paste examples, see [commands.md](commands.md).

## Exit Codes

- `0`: success.
- `2`: command-line, recipe-domain, or solver-configuration error.

Error output is printed to `stderr` and the JSON output is not written.

## Output Format

- Calculator output follows `CalcResult.to_dict()` in `src/horticalc/core.py`.
- Solver output follows `SolveResult.to_dict()` in `src/horticalc/solver.py`.

See [data_model.md](data_model.md) for the key reference.
