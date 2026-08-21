# Command-line interface

The CLI runs calculator and Solver recipe files through the same core as the
desktop application and writes JSON to standard output. It is available after
the source installation in [Contributing](../CONTRIBUTING.md).

Activate that environment before using the examples:

Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If local policy prevents PowerShell activation, replace `python` below with
`.\.venv\Scripts\python.exe`. The remaining examples are single-line commands
that work in Bash and PowerShell after activation.

## Calculate a recipe

```bash
python -m horticalc recipes/reference_calcinit_1g_per_l.yml --pretty
```

The recipe may be positional or supplied with `--load-recipe`. Use
`--load-water` to override its water profile.

```bash
python -m horticalc --load-recipe recipes/reference_agrolution_313_1g_per_l.yml --load-water data/water_profiles/default.yml --out user/exports/result.json --pretty
```

## Solve targets

Solver recipes use the `solve` subcommand:

```bash
python -m horticalc solve user/recipes/example.yml --pretty
```

Override simple settings with their generated flags or any setting with a
repeatable `--solver-config KEY=VALUE` argument:

```bash
python -m horticalc solve user/recipes/example.yml --solver-model hierarchical --solver-config 'target_priorities={"N_total":{"under":1,"over":1}}' --pretty
```

`--solver-config-json JSON` merges a complete JSON object before explicit
`KEY=VALUE` overrides. Run `python -m horticalc solve --help` for the current
generated flags and [Solver](solver.md) for their meaning.

## Common options

| Option | Behavior |
| --- | --- |
| `--version` | Print the package version and exit. |
| `--load-recipe FILE` | Use this recipe instead of the positional path. |
| `--load-water FILE` | Override the water profile. |
| `--out FILE` | Write the same JSON result to a file. |
| `--pretty` | Indent JSON output. |

Input and output use the canonical units and keys in
[Data formats](data-formats.md). Success returns exit code `0`. Argument,
recipe-domain, and Solver-configuration errors return exit code `2`, write the
error to standard error, and do not write a JSON result.

The parser and option definitions are owned by `src/horticalc/__main__.py` and
`src/horticalc/solver_config.py`.
