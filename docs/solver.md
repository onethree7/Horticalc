# Solver

The Solver chooses non-negative fertilizer doses for elemental concentration
targets. Its standard optimization is non-negative least squares (NNLS). The
implementation is split between `src/horticalc/solver.py`, the configuration
contract in `src/horticalc/solver_config.py`, and the staged linear program in
`src/horticalc/priority_solver.py`.

## Inputs and constraints

A solve provides:

- elemental targets in `mg/L`;
- positive batch volume;
- the fertilizers available for variable dosing;
- optional fixed fertilizer amounts;
- optional water composition and RO-water proportion;
- urea handling and Solver configuration.

Target keys must belong to `ALLOWED_TARGET_KEYS` in
`src/horticalc/chemistry.py`. Values and fixed doses must be finite and
non-negative. Each allowed fertilizer name is unique, and every fixed-dose
fertilizer must also be allowed.

Water and fixed doses are calculated first and subtracted from the requested
targets. Variable doses respect `SolverMaxDosePerL`; a limit of `0` disables
variable dosing for that product while retaining an explicit fixed dose. All
models remove doses at or below `1e-10` canonical dose units before recomputing
the reported solution.

## Objective selection

`objective_elements` in the result is the authoritative list of targets that
affected a solve.

- Numeric zero targets are normally report-only.
- `Na` and `Cl` are always report-only.
- `nitrogen_objective_mode` selects provided nitrogen targets, total nitrogen
  only, or individual nitrogen forms only. The default is `n_total_only`.
- For the standard model, `S` is report-only unless
  `s_objective_enabled=true`; the two experimental models include a non-zero
  elemental `S` target.
- Hierarchical target directions at priority `0` are report-only.

`ignored_elements` remains part of accepted persisted/API data. The
hierarchical model interprets each listed element as priority `0` in both
directions; the GUI persists the canonical `target_priorities` representation.

## NNLS + tuning

`nnls_tuning` is the production default. Rows of the matrix are objective
elements, columns are allowed fertilizers, and each value is the contribution
in `mg/L` per canonical dose:

```text
minimize ||A x - b||₂
subject to 0 <= x <= per-product dose limit
```

The standard path can apply relative weighting, iterative reweighted least
squares (IRLS) overshoot penalties, an optional nitrogen-total governor, and
dominant-supplier correction passes. These controls affect only `nnls_tuning`.

## Mass NNLS (experimental)

`mass_nnls` minimizes unweighted squared residuals in elemental `mg/L`:

```text
minimize Σ(achieved_mg_per_l - target_mg_per_l)²
subject to fertilizer dose >= 0 and product dose limits
```

It does not apply relative weighting, IRLS, the nitrogen governor, or singleton
passes. Because the objective uses raw mass concentration, a residual of
`30 mg/L` contributes 10,000 times as much squared error as `0.3 mg/L`.

## Prioritized targets (experimental)

`hierarchical` uses SciPy HiGHS to solve directional priorities as a staged
linear program:

```text
achieved + under - over = target
```

Each target has separate under- and over-priorities:

| Priority | Meaning |
| ---: | --- |
| `1` | Must; solved first |
| `2` | Important |
| `3` | Normal; default |
| `4` | Flexible; solved last |
| `0` | Report only |

For each populated tier, the Solver first minimizes its largest directional
residual, then its total residual. Those optima become constraints for later
tiers, so a lower-priority improvement cannot worsen an earlier tier. A final
effective-product-mass minimization breaks equivalent ties. `priority_stages`
reports each retained tier optimum.

## Configuration and output

Use `GET /schema/solver-config` or, after activating the source environment as
described in [Command-line interface](cli.md),
`python -m horticalc solve --help` for current configuration keys, types,
defaults, and bounds. API/YAML values use native JSON types; CLI `KEY=VALUE`
overrides parse JSON when possible. Unknown keys, non-finite values, invalid
choices, and values outside declared bounds are rejected.

Every result identifies `solver_model`, proposed fertilizers,
`objective_elements`, targets, achieved concentrations, and residuals.
Hierarchical results also return resolved `target_priorities` and
`priority_stages`. See [Data formats](data-formats.md#results) for the ownership
of the exact output mapping.
