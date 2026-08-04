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
- In `hierarchical`, each active target has separate `under` and `over`
  priorities from `solver_config.target_priorities`. Direction priority `0`
  is report-only; a target is absent from the objective only when both
  directions are `0`.
- The older `solver_config.ignored_elements` input remains accepted for API,
  recipe, and preference compatibility. In `hierarchical` it migrates to
  `{under: 0, over: 0}`. The GUI writes only `target_priorities`.
- `mass_nnls` and `hierarchical` always include a non-zero elemental `S` target. In `nnls_tuning`,
  `S` is report-only unless `solver_config.s_objective_enabled=true`. `SO4` is
  not a solver target key.
- Nitrogen form handling depends on `nitrogen_objective_mode`.

The output field `objective_elements` is the authoritative list.
`target_priorities` contains the resolved directional priorities used by a
hierarchical solve. `ignored_elements` is retained as a compatibility field
and lists targets for which both directions are report-only. A solve is
rejected when no objective remains. Before returning, every solver model uses
the same result validation and rejects non-finite values or negative fertilizer
doses.

## Nitrogen Modes

`solver_config.nitrogen_objective_mode` supports:

- `as_targets`: original behavior; use non-zero N keys as provided.
- `n_total_only`: optimize `N_total` and exclude `N_NH4`, `N_NO3`, `N_UREA`.
- `n_forms_only`: optimize N forms, exclude `N_total`, and keep zero N-form targets when present.

Current default: `n_total_only`.

## Solver Config Defaults And Validation

The canonical defaults are in `src/horticalc/solver_config.py`:

| Key | Default | Bounds |
| --- | --- | --- |
| `solver_model` | `nnls_tuning` | `mass_nnls`, `hierarchical`, `nnls_tuning` |
| `ignored_elements` | `[]` | Unique target-key strings |
| `target_priorities` | `{}` | Target keys mapped to optional integer `under`/`over` priorities in `0..4`; omitted directions resolve to `3` |
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
list of accepted target keys. `target_priorities` rejects unknown target or
direction keys, non-integer priorities, and values outside `0..4`. The CLI's `KEY=VALUE` form is the only boundary
that converts text values; for example,
`--solver-config target_priorities='{"N_total":{"under":1,"over":1},"Ca":{"under":2,"over":3}}'`.
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

`solver_model` selects one of three runtime paths:

- `nnls_tuning` is the production default. It is the standard NNLS + tuning
  model and contains
  the configurable NNLS/IRLS/singleton implementation and all tuning fields
  below.
- `mass_nnls` is experimental. It minimizes raw elemental squared
  error in canonical `mg/L`, uses `N_total` whenever that target is present,
  and includes a non-zero `S` target. Relative weighting, IRLS, governor, and
  singleton fields do not affect this model.
- `hierarchical` is experimental. It uses strict directional priority tiers in
  raw `mg/L`, with the same N-total and sulfur objective selection as
  `mass_nnls`, but without tuning weights or post-passes.

The selected model is returned as `solver_model` in every solve response.

### Mass NNLS model (experimental)

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

The compatibility-only `ignored_elements` list is a transparent objective
projection, not a hidden weight or safety rule. It can intentionally allow a
large error in an excluded element, so ignored concentrations are always
calculated and reported. The default is empty: Horticalc does not hardcode Cu,
B, Ca, Mg, or any other user-selectable element as biologically unimportant.

`SolverMaxDosePerL` bounds the dose chosen for each allowed fertilizer. A value
of `0` excludes the product from variable dose selection while still allowing
an explicit `fixed_grams` dose. The shipped HuminTech AMINO POWER and Fulvital
products use this zero limit so they cannot act as unconstrained nutrient
concentrates.

### Hierarchical directional-priority model (experimental)

`src/horticalc/priority_solver.py` formulates the fertilizer matrix as a
linear program and solves it with SciPy HiGHS. Every active element has two
non-negative residuals:

```text
achieved + under - over = target
```

Priorities have these product meanings:

| Value | UI label | Meaning |
| ---: | --- | --- |
| `1` | Must | Solved first |
| `2` | Important | Solved after every priority-1 direction is fixed |
| `3` | Normal | Default for an omitted direction |
| `4` | Flexible | Last optimized tier |
| `0` | Report only | Direction is calculated but does not affect doses |

For each non-empty tier, the solver first minimizes that tier's largest
directional residual in `mg/L`, then minimizes its sum of residuals without
worsening the first optimum. Both optima become constraints for all later
tiers. A final effective-product-mass minimization only breaks chemically
equivalent ties and cannot worsen any nutrient tier.

This is lexicographic goal programming, not weighted least squares. There is
no numeric multiplier through which many lower-priority improvements can
compensate for one higher-priority error. There are also no nutrient
concentration bounds, macro/micro classes, learned biological severities, or
hardcoded element priorities. The user or saved target profile supplies the
directional order. Raw `mg/L` inside each tier ensures that, for example,
`N -30 mg/L` is not numerically equated with `Cu +0.3 mg/L` merely because
both may have a similar percentage error.

Fixed fertilizer doses, per-product `SolverMaxDosePerL`, water subtraction, and
liquid density have the same meaning as in the other runtime models.
`priority_stages` in the solve response exposes each tier's retained maximum
and total residual for audit.

### NNLS + tuning model (standard; `nnls_tuning`)

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

- The settings below apply only to `nnls_tuning`; `mass_nnls` and `hierarchical`
  deliberately ignore them.
- `relative_weighting` scales rows by target/residual magnitude.
- `overshoot_penalty` and IRLS increase weights for overshoot rows.
- Singleton passes can reduce dominant-supplier overshoot or top up underfilled dominant nutrients.
- The default portfolio path may compare a small set of candidate variants when `nitrogen_objective_mode` is `n_total_only` and the config matches the default portfolio.

## CLI Examples

For copy/paste solver commands, see [commands.md](commands.md#cli-recipes).
