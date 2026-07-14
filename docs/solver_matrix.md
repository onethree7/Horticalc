# Solver Matrix Benchmark

Status: `operation-guide`.

The schema-v2 solver matrix is a removable research harness in
`scripts/solver_matrix.py`. Product runtime does not import or call it.

## Purpose

The harness separates two questions that the old exponential subset search
mixed together:

1. **Solver settings:** every configuration is run against the same primary
   fertilizer portfolio and the same target corpus.
2. **Nutrient-portfolio mass barrage:** the canonical configuration is run
   against named recipe portfolios and deterministic leave-one-out variants.

This makes setting deltas paired and interpretable. Adding another fertilizer
does not multiply the setting matrix by every possible subset.

## Canonical Cases

`scripts/solver_matrix_cases.yml` is the data contract. It currently defines:

- Steiner Universal 1984;
- Bugbee Utah Cannabis 2022;
- Conn 2013 Arabidopsis (the requested CPMM/Conn case);
- Cooper NFT 1979;
- De La Rosa Lettuce T2;
- Hermans 2010 Arabidopsis;
- Hoagland and Arnon 1950 Solution 1;
- Long Ashton (LANS) nitrate type;
- the tracked augmented Saloner solver regression;
- the tracked golden solver regression.

The requested CPMM case resolves to the shipped `Conn_2013_Arabidopsis`
profile. Its source and elemental targets are recorded in
`data/nutrient_solutions/Conn_2013_Arabidopsis.yml`.

The primary 19-product portfolio is the explicit union of the allowed lists in
the on-disk 23-10-17 recipe, augmented Saloner recipe, and golden recipe. It
includes `HuminTech AMINO POWER Plus Liquid` and
`HuminTech Fulvital Plus Liquid`. The explicit snapshot keeps old benchmark
output reproducible if a user recipe later changes.

The cases file also tracks the two requested restricted portfolios: the
seven-product Blossom/Fetrilon/PeKacid/Spezial set and the six-product
313/Bittersalz/MKP set. Both use `Haifa MAG Magnesiumnitrat
11-0-0+16MgO`; they do not use Yara Magnitra-L.

Every canonical case fixes:

- `nitrogen_objective_mode: n_total_only`;
- `s_objective_enabled: true`.

`n_form_priority_weights` is not swept because it is inactive in
`n_total_only` mode.

## Setting Experiments

The YAML catalog owns all grids and confirmation variants. The runner expands
them generically. Current controlled groups cover:

- the complete Boolean factorial for relative weighting, singleton overshoot,
  singleton underfill, and the N-total governor;
- overshoot penalty and IRLS iteration interactions;
- relative-weighting scale epsilon;
- singleton overshoot share and maximum-regression tolerance, including
  `singleton_max_regress_pp: 10`;
- singleton underfill share and iteration count, including share `0`;
- N-total governor weight;
- explicit combined confirmation candidates.

Inactive numeric controls are not multiplied into redundant rows. For example,
singleton thresholds are varied only in configurations where that singleton
pass is enabled.

## Presets

- `quick`: canonical baseline only.
- `matrix`: the complete controlled setting catalog on the primary portfolio.
- `deep`: `matrix` plus named portfolios and primary-portfolio leave-one-out
  barrage cases.

Use `--primary-portfolio ID` to run the complete setting catalog against a
different named fertilizer portfolio without copying or editing the cases
file. The selected id is persisted in both the run manifest and summary.

`--max-runs` is a safety cap. Runs are configuration-first so a cap completes a
configuration across profiles before advancing, avoiding first-profile bias.
Use `0` to disable the cap.

## Output Contract

Each run directory contains:

- `run_manifest.json`: input checksum, resolved targets, portfolios, setting
  catalog, unresolved cases, and planned row count;
- `results.csv`: spreadsheet-friendly rows;
- `results.jsonl`: lossless streaming rows;
- `summary.json`: counts, best rows, and a preliminary setting ranking.

Every result row has stable `run_id`, `profile_id`, `portfolio_id`,
`experiment_id`, and `config_id` fields. JSON-valued columns retain the exact
solver configuration, allowed/used fertilizers, objective elements, achieved
concentrations, and errors.

`scripts/solver_matrix_analyze.py` writes:

- `analysis_summary.json`: paired setting effects, per-profile winners, named
  portfolio comparisons, and leave-one-out impacts;
- `analysis_report.md`: the same evidence in a readable report.

Analyzer rankings use paired percentage improvement from each profile's
canonical baseline. Raw average deltas are also retained.

## Scoring

The benchmark scores only `objective_elements` returned by
`solve_recipe_data()`. Elemental S is a macro score when the S objective is
enabled. Report-only values remain in `ignored_targets`.

For non-zero targets:

```text
abs((achieved - target) / target * 100)
```

For zero objective targets, an element-group absolute tolerance is used because
percent error is undefined.

```text
composite = 3.0 * macro_rms
          + 3.0 * nitrogen_form_rms
          + 1.5 * micro_rms
          + 0.5 * other_rms
```

Lower is better.

## Files And Removal

- `scripts/solver_matrix.py`: runner.
- `scripts/solver_matrix_cases.yml`: benchmark data and experiment grids.
- `scripts/solver_matrix_analyze.py`: paired analyzer and report writer.
- `tests/test_solver_matrix.py`: runner/data-contract tests.
- `tests/test_solver_matrix_analyze.py`: analysis-contract tests.
- `logs/solver_matrix/...`: generated, ignored results.

Deleting those scripts, cases, tests, generated output, and this docs link
removes the research harness without changing product runtime.

For exact commands, see [commands.md](commands.md#solver-matrix-harness).
