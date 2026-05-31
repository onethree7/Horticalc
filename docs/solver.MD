# Horticalc Solver

This document describes how `horticalc` computes fertilizer grams to match a target nutrient profile (mg/L) given a water profile and an allowed fertilizer set.

## Problem statement

Given:

- `targets_mg_per_l`: desired element concentrations in mg/L
- water profile (mg/L), optionally mixed with osmosis water
- a set of allowed fertilizers, each with a composition and (optional) `weight_factor`
- optional fixed fertilizer grams

Find non-negative fertilizer grams that best match the targets, while keeping behavior deterministic and producing stable, realistic solutions.

## Allowed fertilizers in the UI

The solver UI maintains its allowed fertilizer list in the browser per context (localStorage key
prefix `last_fertilizers_allowed_context:`). Context is derived from the loaded recipe
(e.g., filename/profile name), so each recipe/profile keeps its own allowed set.

Current behavior:

- When the UI loads, it restores the stored list for the current context and filters it to known fertilizers.
- Migration path: if no context entry exists yet, the UI falls back to legacy global storage key
  `last_fertilizers_allowed` and writes the migrated value into the context key.
- When a recipe is loaded, the allowed list is initialized from the recipe context (not globally merged).
- Clicking **“Allowed aus Rezept übernehmen”** replaces the allowed list with the fertilizers
  currently selected in the recipe/calculator.
- Manual changes in the multi-select are persisted back to localStorage.

## Data model and units

- Targets and achieved values are expressed as mg/L of *elements* (e.g., `K`, `Ca`, `P`, `Fe`).
- Fertilizer composition is stored as fractions per product (e.g., N-forms, oxides, and other forms).
- Conversions:
  - oxide forms are converted to elemental mg using molar masses
  - N forms contribute to `N_total` and the specific form key (`N_NO3`, `N_NH4`, `N_UREA`)
- `weight_factor` scales a fertilizer’s effective contribution to match real dosing behavior (e.g., liquids with density / label basis differences). The solver uses the same scaling as the core “ground truth” compute path.

## Nitrogen objective modes

The solver supports three nitrogen objective modes through
`solver_config.nitrogen_objective_mode`:

- `as_targets`: legacy/default behavior. Use every non-zero target key, including
  `N_total` and any non-zero N forms that appear together.
- `n_total_only`: make `N_total` the single nitrogen objective. Exclude
  `N_NO3`, `N_NH4`, and `N_UREA` from the objective.
- `n_forms_only`: solve individual N forms. Exclude `N_total`, and include
  `N_NO3`, `N_NH4`, and `N_UREA` as objectives when they are present in the
  target profile, even if a form target is `0`.

The benchmark matrix uses this same solver setting. It does not emulate N-mode
behavior by changing targets on its own.

## Ignored targets

Some targets are excluded from the optimization objective (but still computed and reported in the output):

- `S`, `SO4`, `Na`, `Cl`

Rationale: these are frequently “forced” by the fertilizer set (especially sulfate) and are better treated as a reporting dimension or a later constraint layer rather than a hard fit objective.

Nitrogen objective handling is controlled separately by `nitrogen_objective_mode`.

## Linear model (A-matrix)

Let:

- `x` be the vector of fertilizer grams (decision variables), constrained to `x >= 0`
- `A` be the matrix of element contributions (mg/L per gram of fertilizer)
- `b` be the target residual after subtracting water baseline (mg/L)

For each objective element `i` and fertilizer `j`:

- `A[i,j] = (mg_per_g_of_element_i_from_fert_j) / liters`

Water baseline:

- The recipe’s water profile is converted to elemental mg/L and optionally mixed with osmosis water.
- The baseline is subtracted from targets:

`b = targets - water_baseline`

This means the solver decides only the additional nutrients required beyond the water.

## Core optimization: NNLS

The core solve is a non-negative least squares (NNLS) problem:

Minimize:

`|| A x - b ||_2`

Subject to:

`x >= 0`

NNLS is convex and deterministic under a fixed implementation, and it naturally enforces “no negative fertilizer amounts”.

If some fertilizer grams are fixed, their contribution is subtracted from `b` before solving, and only the remaining variables are optimized.

## Relative weighting (small targets vs large targets)

A pure least-squares objective is dominated by large-magnitude targets (e.g., `K`, `Ca`), which can systematically “sacrifice” small targets (e.g., trace elements).

To address this, the solver can use **relative weighting**, which scales each objective row to represent relative (percent-like) error.

Row scale per element:

- `scale_i = max(|target_i|, |b_i|, eps_mg_per_l)`

Base row weight:

- `base_w_i = 1 / scale_i`

This makes the solver care about proportional error, not absolute mg/L error, improving trace-element accuracy without requiring hard constraints.

## IRLS wrapper + overshoot penalty

Relative weighting is wrapped in a deterministic IRLS (iteratively re-weighted least squares) loop to discourage overshoot:

- Start with the base weights.
- Solve weighted NNLS.
- Compute residual `r = A x - b`.
- Increase the row weight when `r_i > 0` (overshoot), controlled by `overshoot_penalty`.
- Repeat for a small fixed number of iterations.

This reduces the tendency to exceed targets when a near-equal solution exists.

## Macro preference / priority groups (optional)

In nutrient solutions, the most important variables are typically macros:

1. `N` (N forms / total)
2. `K`
3. `P`
4. `Ca`
5. `Mg`

The solver can optionally apply a **macro preference** so that macro matching is “primary” while still keeping the advantages of relative weighting for traces.

This is done in two places:

1) **During optimization**  
Macro rows receive multiplicative weight factors (e.g., N weighted higher than trace rows), so the optimizer focuses on macros first.

2) **When selecting between candidate solutions**  
If the solver computes both a weighted and an unweighted candidate, it uses a lexicographic score:

- Compute `max_abs_percent_error` per priority group in order, plus a final “other” group.
- Compare score tuples lexicographically and pick the better candidate.
- This prevents tiny trace errors from dominating the solution choice when macros regress.

The same scoring can be used for post-pass accept/rollback decisions (see below).

## Post-solve candidate selection in `solve_recipe_data`

After solving, `solve_recipe_data` may compare two staged candidates:

- a **weighted** staged solve (relative weighting active), and
- an **unweighted** staged solve (absolute-fit baseline).

This comparison is intentionally narrow and is only performed when all of the following are true:

- `relative_weighting` is enabled
- `n_total_governor_enabled` is `false`
- `n_form_priority_weights` is empty

If any of those conditions is not met, the solver keeps the primary candidate without running this weighted-vs-unweighted tie-break.

Selection uses `_score_by_priority_groups` and compares score tuples **lexicographically**:

- earlier priority groups dominate later groups
- the final `other` bucket (the trace-heavy residual set) is compared last

Practical consequence: the selected solution can intentionally have a worse fit on trace-heavy `other` nutrients if that preserves better scores in earlier macro-priority groups. This behavior is by design: it protects macro targets first. To favor trace fit more strongly, adjust solver configuration (for example priority groups/weights or the features that disable this comparison path).

## Multi-stage optimization with regression budgets

To avoid “hardcoding” any specific nutrient while still honoring macro-first intent, the solver can
run a **staged (lexicographic) optimization**:

1) Stage 1 solves the highest-priority group (e.g., `N_total`, then N-forms, `K`, `P`, `Ca`, `Mg`).
2) Each subsequent stage adds the next priority group, **while anchoring all previously solved
   groups** to stay within a configurable **regression budget** of their achieved values.
3) The final stage includes all remaining objectives (“other” keys).

Anchors are implemented as additional soft rows that target the **previous stage’s achieved
mg/L**, with row scales derived from the regression budgets. This keeps earlier groups stable while
allowing later groups to improve without introducing any nutrient-specific hard rules.

Singleton-supplier post-passes can run at the end of each stage so that dominant-fertilizer
overshoots are corrected (and underfills can be topped up) before later stages refine
lower-priority nutrients.

## Singleton-supplier post-pass (optional)

Even with a good fit, the solver can produce “avoidable” overshoots when a single fertilizer supplies almost all of an element.

Example: a humic product used to supply nitrogen also carries large trace amounts, causing trace overshoot by orders of magnitude.

The singleton-supplier pass addresses this deterministically:

- For each objective element, compute each fertilizer’s share of that element’s achieved mg/L.
- If one fertilizer supplies more than `share_threshold` (e.g., 0.85) and the element is overshot:
  - reduce that fertilizer’s grams in closed form to remove the overshoot for that element
  - recompute achieved values using the core “ground truth” compute path
  - accept the change only if:
    - the overshoot is reduced (or not worsened), and
    - overall solution quality does not regress beyond configured limits, evaluated per
      priority-score tuple entry returned by `_score_by_priority_groups()`:
      - each configured priority group gets its own bound of `macro_regress_pp`
      - the trailing “other keys” group gets `max_regress_pp`
      - all tuple entries must satisfy `new_score_i <= old_score_i + tolerance_i`
        for the candidate to be accepted

This improves plausibility without hard constraints and preserves determinism.

## Determinism and reproducibility

The solver is designed to be deterministic:

- fixed iteration counts for IRLS
- deterministic ordering over objective keys and fertilizers
- deterministic accept/rollback logic for post-passes
- stable output schema and keys

This enables reliable regression testing and golden-file comparisons.

## Configuration (solver_config)

Recipes may supply `solver_config` to tune behavior. The GUI writes the same keys into recipe payloads, and the CLI can optionally override them for a single run.

Typical toggles:

- `relative_weighting`: enable relative scaling (default on)
- `overshoot_penalty`: overshoot discouragement strength
- `irls_max_outer_iter`: IRLS iterations (small fixed number)
- `scale_eps_mg_per_l`: epsilon for row scaling stability
- `singleton_supplier_enabled`: enable singleton post-pass
- `singleton_share_threshold`: dominant-supplier threshold
- `singleton_max_regress_pp`: rollback tolerance in percent points
- singleton underfill top-up (optional):
  - `singleton_underfill_enabled`: allow dominant-supplier underfill top-ups (default `true`)
  - `singleton_underfill_share_threshold`: dominant-supplier threshold for underfill (default = share threshold)
  - `singleton_underfill_max_iter`: iteration cap for underfill top-ups per stage (default `2`)
- staged optimization (optional):
  - `stage_optimization_enabled`: enable multi-stage solving (default `true`)
  - `stage_regression_pp`: max regression from a prior stage as percent of target (default `5.0`)
  - `stage_regression_mg_l`: absolute mg/L regression budget per stage (default `2.0`)
- macro priority (if implemented):
  - `macro_priority_enabled`
  - `priority_groups`, `priority_group_weights`
  - `macro_regress_pp`
- N-governor + N-form priority (optional):
  - `nitrogen_objective_mode` (`as_targets`, `n_total_only`, or `n_forms_only`)
  - `n_total_governor_enabled` (keep `N_total` in the objective and penalize only overshoot)
  - `n_total_governor_weight` (overshoot-only weight multiplier for `N_total`)
  - `n_form_priority_weights` (per-form multipliers like `{"N_NO3": 3.0, "N_UREA": 2.0, "N_NH4": 1.0}`)

CLI overrides:

- Use explicit switches for GUI-exposed primitives, e.g.:
  - `python -m horticalc solve recipes/solve_golden.yml --no-relative-weighting --overshoot-penalty 1.5`
  - `python -m horticalc solve recipes/solve_golden.yml --n-total-governor-enabled --n-total-governor-weight 0.05`
  - `python -m horticalc solve recipes/solve_golden.yml --nitrogen-objective-mode n_forms_only`
- Use `--solver-config KEY=VALUE` for advanced/structured keys, e.g.:
  - `python -m horticalc solve recipes/solve_golden.yml --solver-config n_form_priority_weights='{"N_NO3": 3.0}'`
- Use `--solver-config-json '{"priority_groups":[["N_total"],["K"]],"priority_group_weights":[3.5,2.5]}'` to merge a JSON object into `solver_config`.
- CLI values are optional overrides. If no switch is supplied, the recipe's `solver_config` is used unchanged.

## Verification

Recommended checks:

1) Run unit tests:
- `python -m pytest -q`

Success: all tests pass.

2) Compare a known recipe before/after changes:
- Ensure output keys are unchanged.
- Ensure ignored targets (`S`, `SO4`, `Na`, `Cl`) remain excluded from the fit but present in reporting.
- Validate macro fit and trace fit trade-offs are acceptable for your fertilizer set.
