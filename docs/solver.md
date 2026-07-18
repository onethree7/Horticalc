# Solver

Status: `current-state`.

The solver lives in `src/horticalc/solver.py` and `src/horticalc/solver_config.py`. It computes non-negative fertilizer doses for target element concentrations in mg/L.

## Inputs

Solver recipes and `/solve` requests provide:

- `targets`: desired element targets in mg/L.
- `liters`: batch size.
- `water_profile`: optional water baseline and `osmosis_percent`.
- `fertilizers_allowed`: exact fertilizer names available to the solver.
- `fixed_grams`: optional fixed amounts by fertilizer name.
- `urea_as_nh4`: whether urea is represented as ammonium in the core output.
- `solver_config`: optional advanced settings.

`solve_recipe_data()` validates these inputs before solving: `liters` must be
finite and greater than zero, osmosis must be within `0..100`, target keys must
be in `ALLOWED_TARGET_KEYS`, target values must be finite and non-negative, and
`fixed_grams` must be finite, non-negative amounts
for fertilizers also listed in `fertilizers_allowed`. The
`fertilizers_allowed` list must not contain duplicates.

## Objective Elements

`_objective_keys()` in `src/horticalc/solver.py` decides which target keys are optimized:

- Accepted target keys are in `ALLOWED_TARGET_KEYS` in `src/horticalc/solver.py`. Oxide/form aliases such as `K2O`, `P2O5`, lowercase keys, and unknown keys are rejected.
- Numeric zero targets are skipped, except N-form zero targets in `n_forms_only` mode.
- `Na` and `Cl` are report-only and ignored as objectives.
- Keys listed in `solver_config.ignored_elements` are removed from the
  objective at the user's request. Their targets and achieved concentrations
  remain in the response, but their residuals cannot change the selected
  fertilizer doses.
- `mass_nnls` always includes a non-zero elemental `S` target. In `legacy`,
  `S` is report-only unless `solver_config.s_objective_enabled=true`. `SO4` is
  not a solver target key.
- Nitrogen form handling depends on `nitrogen_objective_mode`.

The output field `objective_elements` is the authoritative list. The solver
matrix benchmark scores this list. `ignored_elements` records the explicit
user exclusions separately. A solve is rejected when no objective remains.

## Nitrogen Modes

`solver_config.nitrogen_objective_mode` supports:

- `as_targets`: legacy behavior; use non-zero N keys as provided.
- `n_total_only`: optimize `N_total` and exclude `N_NH4`, `N_NO3`, `N_UREA`.
- `n_forms_only`: optimize N forms, exclude `N_total`, and keep zero N-form targets when present.

Current default: `n_total_only`.

## Solver Config Defaults And Validation

The canonical defaults are in `src/horticalc/solver_config.py`:

| Key | Default | Bounds |
| --- | --- | --- |
| `solver_model` | `mass_nnls` | `mass_nnls`, `legacy` |
| `ignored_elements` | `[]` | Unique target-key strings |
| `relative_weighting` | `false` | Boolean |
| `overshoot_penalty` | `1.0` | `>= 0` |
| `irls_max_outer_iter` | `4` | `1..12` |
| `scale_eps_mg_per_l` | `1.0` | `> 0` |
| `singleton_supplier_enabled` | `false` |
| `singleton_share_threshold` | `0.85` | `0..1` |
| `singleton_max_regress_pp` | `0.25` | `>= 0` |
| `singleton_underfill_enabled` | `true` |
| `singleton_underfill_share_threshold` | `0.85` | `0..1` |
| `singleton_underfill_max_iter` | `2` | `1..8` |
| `nitrogen_objective_mode` | `n_total_only` |
| `s_objective_enabled` | `false` |
| `n_total_governor_enabled` | `false` |
| `n_total_governor_weight` | `1.0` | `>= 0` |
| `n_form_priority_weights` | `{}` |

Solver configuration has one validation contract in
`src/horticalc/solver_config.py`. API and YAML values must use their native
Boolean, numeric, integer, string, list, or mapping types; numeric values must
be finite, unknown keys are rejected, and `nitrogen_objective_mode` must be one
of the three documented modes. `ignored_elements` must be a duplicate-free
list of accepted target keys. The CLI's `KEY=VALUE` form is the only boundary
that converts text values; for example,
`--solver-config ignored_elements='["Cu","B"]'`.
`n_form_priority_weights` remains an advanced
mapping for `N_NH4`, `N_NO3`, and `N_UREA` with finite, non-negative weights.
It is accepted in recipes and direct solve inputs, but not in UI preferences.
Iteration count `1` performs the initial pass. Refinements are disabled through
their separate `*_enabled` flags, not by setting an iteration count to zero.

Note: the 2026-05-31 historical solver-matrix report recommended
`relative_weighting=true`, but the current implementation and tests default it
to `false`. Do not change docs to the historical recommendation unless the code
and tests change too.

## Optimization Model

`solver_model` selects one of two runtime paths:

- `mass_nnls` is the production default. It minimizes raw elemental squared
  error in canonical `mg/L`, uses `N_total` whenever that target is present,
  and includes a non-zero `S` target. Relative weighting, IRLS, governor, and
  singleton fields do not affect this model.
- `legacy` retains the existing NNLS/IRLS/singleton implementation and all of
  the tuning fields below as a compatibility option.

The selected model is returned as `solver_model` in every solve response.

### Mass NNLS model

The solver builds the contribution matrix in elemental `mg/L` and solves:

```text
minimize sum((achieved_mg_per_l - target_mg_per_l)^2)
subject to fertilizer dose >= 0
```

There is no percentage normalization, molar conversion, macro/micro class,
biological severity table, IRLS reweighting, or singleton post-pass in this
objective. Consequently, an `N -30 mg/L` residual contributes `900`, while a
`Cu +0.3 mg/L` residual contributes `0.09`. This is a physical mass-error
criterion, not a claim that all biological trade-offs are known.

The optional `ignored_elements` list is a transparent objective projection,
not a hidden weight or safety rule. It can intentionally allow a large error in
an excluded element, so ignored concentrations are always calculated and
reported. The default is empty: Horticalc does not hardcode Cu, B, Ca, Mg, or
any other user-selectable element as biologically unimportant.

Allowed fertilizers with `SolverRole=fixed_only` are excluded from variable
dose selection. They still contribute normally when the recipe supplies an
explicit `fixed_grams` dose. This prevents additive products such as shipped
HuminTech AMINO POWER and Fulvital from being used as unconstrained nutrient
concentrates. It is product capability metadata, not a nutrient upper bound.

### Legacy model

The solver builds a contribution matrix: rows are objective elements, columns are allowed fertilizers, and values are mg/L contribution per gram for the current batch size. Water baseline is computed with `compute_solution()` and subtracted from targets before solving. Fixed grams are subtracted before optimizing the remaining variable fertilizers.

The base solve is deterministic non-negative least squares:

```text
minimize || A x - b ||_2
subject to 0 <= x <= product maximum * liters
```

The upper bound comes from optional fertilizer CSV field
`SolverMaxDosePerL`. An empty field is unlimited and therefore follows the
original NNLS path exactly. Explicit `fixed_grams` are user instructions and
override a product maximum. Relative weighting, IRLS, and singleton underfill
passes use the same upper bounds.

## Optional Behavior

- The settings below apply only to `legacy`; `mass_nnls` deliberately ignores
  them.
- `relative_weighting` scales rows by target/residual magnitude.
- `overshoot_penalty` and IRLS increase weights for overshoot rows.
- Singleton passes can reduce dominant-supplier overshoot or top up underfilled dominant nutrients.
- The default portfolio path may compare a small set of candidate variants when `nitrogen_objective_mode` is `n_total_only` and the config matches the default portfolio.

## CLI Examples

For copy/paste solver commands, see [commands.md](commands.md#cli-recipes).
