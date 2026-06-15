# Solver Matrix Benchmark

Status: current-state.

The solver matrix is a removable research harness in `scripts/solver_matrix.py`.
It is not part of product runtime and is not called by the API, UI, core, or
launcher.

## Purpose

Use it to compare solver quality across:

- target profiles
- allowed fertilizer subsets
- nitrogen objective modes
- solver config toggles
- numeric refinement settings

The benchmark scores the same `objective_elements` returned by
`solve_recipe_data()`. It does not independently decide that report-only
targets such as `S`, `Na`, or `Cl` are optimization errors, and `SO4` is not an
accepted target key.

## Files

- `scripts/solver_matrix.py`: run matrix/deep benchmark.
- `scripts/solver_matrix_cases.yml`: default water, fertilizers, nitrogen
  modes, and custom profiles.
- `scripts/solver_matrix_analyze.py`: analyze a completed run.
- `logs/solver_matrix/...`: generated output, ignored by git.
- `tests/test_solver_matrix.py`: score, config, cap, and smoke tests.
- `tests/test_solver_matrix_analyze.py`: analysis tests.

## Current Defaults

The first boolean solver config starts from the implementation defaults in
`src/horticalc/solver_config.py`:

- `nitrogen_objective_mode: n_total_only`
- `relative_weighting: false`
- `singleton_supplier_enabled: false`
- `singleton_underfill_enabled: true`
- `n_total_governor_enabled: false`

Historical note: the 2026-05-31 deep run recommended a different default for
`relative_weighting`. Current code and tests default it to `false`.

## Presets

`quick`:

```bash
python scripts/solver_matrix.py --preset quick
```

- Uses the full fertilizer list as one subset.
- Runs the boolean config grid.
- Writes to `logs/solver_matrix/dev` unless `--out-dir` is set.

`matrix`:

```bash
python scripts/solver_matrix.py --preset matrix --max-runs 100000 --out-dir logs/solver_matrix/matrix_001
```

- Tests all non-empty subsets of the allowed fertilizers.
- Defaults to a `100000` attempted-row cap.
- Samples subsets across the full subset list when the cap is smaller than the
  full grid.

`deep`:

```bash
python scripts/solver_matrix.py --preset deep --seed 1337 --top-n 20 --max-runs 100000 --out-dir logs/solver_matrix/deep_001
```

- Starts from the matrix search.
- Keeps the best base rows per profile.
- Refines numeric settings around winners.
- Uses the same safety cap behavior as matrix.

Use `--max-runs 0` only for an intentionally uncapped research run.

## Common Commands

One-profile smoke:

```bash
python scripts/solver_matrix.py --preset quick --profiles Hoagland_Arnon_1950_Solution1_Nitrate --max-configs 2 --out-dir logs/solver_matrix/smoke
```

One nitrogen mode:

```bash
python scripts/solver_matrix.py --preset deep --nitrogen-modes n_total_only --seed 1337 --top-n 20 --max-runs 100000
```

Analyze a run:

```bash
python scripts/solver_matrix_analyze.py logs/solver_matrix/deep_001
```

Compare against a baseline:

```bash
python scripts/solver_matrix_analyze.py logs/solver_matrix/deep_001 --baseline-dir logs/solver_matrix/dev
```

## Output

Each run writes:

- `results.csv`: spreadsheet-friendly row output.
- `results.jsonl`: one JSON object per row.
- `summary.json`: aggregate counts, best rows, rankings, and metadata.

The analyzer writes:

- `analysis_summary.json`
- `analysis_report.md`

## Scoring

For non-zero targets:

```text
abs((achieved - target) / target * 100)
```

For zero targets included by `objective_elements`, the matrix uses absolute
tolerances by group because percent error is undefined.

Main score:

```text
3.0 * macro_score
+ 3.0 * n_form_score
+ 1.5 * micro_score
+ 0.5 * other_score
```

Lower is better. Ignored/report-only targets are written to ignored fields but
do not affect `composite_score`.

## Keep It Removable

Product code must not depend on the matrix. To remove it:

- Delete `scripts/solver_matrix.py`.
- Delete `scripts/solver_matrix_cases.yml`.
- Delete `scripts/solver_matrix_analyze.py` if no longer needed.
- Delete matrix tests.
- Remove docs links.
- Delete generated `logs/solver_matrix/...` output if desired.

## Verification

```bash
python scripts/test.py tests/test_solver_matrix.py tests/test_solver_matrix_analyze.py -q
```
