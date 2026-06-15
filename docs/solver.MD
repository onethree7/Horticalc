# Solver

Status: current-state.

The solver lives in `src/horticalc/solver.py`. It computes non-negative
fertilizer grams for target element concentrations in mg/L.

## Inputs

Solver recipes and `/solve` requests provide:

- `targets`: desired element targets in mg/L.
- `liters`: batch size.
- `water_profile`: optional water baseline and `osmosis_percent`.
- `fertilizers_allowed`: exact fertilizer names available to the solver.
- `fixed_grams`: optional fixed amounts by fertilizer name.
- `urea_as_nh4`: whether urea is represented as ammonium in the core output.
- `phosphate_species`: `H2PO4` by default, or `HPO4`.
- `solver_config`: optional advanced settings.

`solve_recipe_data()` validates these inputs before solving: `liters` must be
greater than zero, target keys must be in `ALLOWED_TARGET_KEYS`, target values
must be finite numbers, and `fixed_grams` must be finite, non-negative amounts
for fertilizers also listed in `fertilizers_allowed`.

## Objective Elements

`_objective_keys()` decides which target keys are optimized.

Current rules:

- Accepted target keys are defined by `ALLOWED_TARGET_KEYS` in
  `src/horticalc/solver.py`. Oxide/form aliases such as `K2O`, `P2O5`,
  lowercase keys, and unknown keys are rejected instead of becoming zero-column
  objectives.
- Numeric zero targets are skipped, except N-form zero targets in
  `n_forms_only` mode.
- `Na` and `Cl` are report-only and ignored as objectives.
- `S` is report-only by default. Set `solver_config.s_objective_enabled=true`
  to allow elemental sulfur as an objective. `SO4` is not a solver target key;
  it remains a fertilizer, water-profile, and ion-output form.
- Nitrogen form handling depends on `nitrogen_objective_mode`.

The output field `objective_elements` is the authoritative list. The solver
matrix benchmark also scores this list and does not invent its own objective
policy.

## Nitrogen Modes

`solver_config.nitrogen_objective_mode` supports:

- `as_targets`: legacy behavior; use non-zero N keys as provided.
- `n_total_only`: optimize `N_total` and exclude `N_NH4`, `N_NO3`, `N_UREA`.
- `n_forms_only`: optimize N forms, exclude `N_total`, and keep zero N-form
  targets when present.

Current default: `n_total_only`.

## Solver Config Defaults

The canonical defaults are in `src/horticalc/solver_config.py`.

| Key | Default |
| --- | --- |
| `relative_weighting` | `false` |
| `overshoot_penalty` | `1.0` |
| `irls_max_outer_iter` | `4` |
| `scale_eps_mg_per_l` | `1.0` |
| `singleton_supplier_enabled` | `false` |
| `singleton_share_threshold` | `0.85` |
| `singleton_max_regress_pp` | `0.25` |
| `singleton_underfill_enabled` | `true` |
| `singleton_underfill_share_threshold` | `0.85` |
| `singleton_underfill_max_iter` | `2` |
| `nitrogen_objective_mode` | `n_total_only` |
| `s_objective_enabled` | `false` |
| `n_total_governor_enabled` | `false` |
| `n_total_governor_weight` | `1.0` |

Note: the 2026-05-31 historical solver-matrix report recommended
`relative_weighting=true`, but the current implementation and tests default it
to `false`. Do not change docs to the historical recommendation unless the code
and tests change too.

## Optimization Model

The solver builds a contribution matrix:

- Rows are objective elements.
- Columns are allowed fertilizers.
- Values are mg/L contribution per gram for the current batch size.

Water baseline is computed with the same core calculation path and subtracted
from targets before solving. Fixed grams are also subtracted before optimizing
the remaining variable fertilizers.

`targets` or `targets_mg_per_l` are the only target sources. Calculation output
fields such as `water_elements_mg_per_l` are not treated as desired solver
targets.

The base solve is deterministic non-negative least squares:

```text
minimize || A x - b ||_2
subject to x >= 0
```

## Optional Behavior

Relative weighting scales rows by target/residual magnitude so small trace
targets can matter more. IRLS can increase weights for overshoot rows.

Singleton passes can reduce dominant-supplier overshoot or top up underfilled
dominant nutrients. The overshoot pass checks per-objective regression budgets;
the underfill pass keeps the broader max-error budget used by the default
portfolio behavior.

Legacy stage optimization and macro priority controls were removed from the
backend config after default-off matrix runs showed no current benefit.

The default portfolio path may compare a small set of candidate variants when
`nitrogen_objective_mode` is `n_total_only` and the config matches the default
portfolio.

## CLI

```bash
python -m horticalc solve recipes/solve_golden.yml --pretty
python -m horticalc solve recipes/solve_golden.yml --nitrogen-objective-mode n_forms_only --pretty
python -m horticalc solve recipes/solve_golden.yml --solver-config n_form_priority_weights='{"N_NO3": 3.0}'
```

## Verification

```bash
python scripts/test.py tests/test_solver_golden.py tests/test_solver_weighting.py -q
python scripts/test.py tests/test_solver_n_total_governor.py tests/test_cli_solver_config.py -q
python scripts/test.py tests/test_solver_matrix.py -q
```
