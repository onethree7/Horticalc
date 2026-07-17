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

The primary portfolio is the explicit 22-product union of the real recipe
pools. It contains no HuminTech product. The matrix marks every portfolio as
either `selection` or `diagnostic`: only `selection` cases may determine a
winner. `HuminTech AMINO POWER Plus Liquid` and `HuminTech Fulvital Plus
Liquid` occur only in the two diagnostic honeypots
`augmented_saloner_humin_honeypot` and `solve_golden_humin_honeypot`. Those
cases are still solved and reported, but are excluded from lexicographic
ranking, behavioral deduplication, holdouts, and bootstrap sampling.

The named selection portfolios additionally include the six supplied
handcrafted product sets. Products whose supplied reference amount was zero
are absent. Positive source amounts are retained as machine-readable
`reference_amounts` provenance in the run manifest, but never constrain or
seed the solver:

| Portfolio id | Nonzero products |
|---|---:|
| `solve_golden` | 4 |
| `blossom_calcinit_epso_313` | 4 |
| `kristalon_epso_313` | 3 |
| `epso_313_s3` | 3 |
| `plagron_ca_edta_basis3_epso_313` | 5 |
| `plagron_ghe_tripart` | 4 |

The Golden target remains a real handcrafted regression profile. Its former
synthetic `S: 999` target has been replaced at the owning fixture
`recipes/solve_golden.yml` by the recipe-derived `85.79586471044226 mg/L S`.
That value reproduces the original 10 L Golden recipe with its historical
66.6666666667% osmosis-water mix, so S remains a real objective instead of
disappearing.
The normal and Humin honeypot executions use the same corrected target and
differ only in allowed products. Augmented Saloner is treated the same way.
Bugbee remains a scientific nutrient-solution target; no dedicated Bugbee
fertilizer pool is invented because the cited profile specifies elemental
targets, not a product recipe.

The cases file also tracks the two requested restricted portfolios: the
seven-product Blossom/Fetrilon/PeKacid/Spezial set and the six-product
313/Bittersalz/MKP set. Both use `Haifa MAG Magnesiumnitrat
11-0-0+16MgO`; they do not use Yara Magnitra-L.

Every canonical case fixes:

- `nitrogen_objective_mode: n_total_only`;
- `s_objective_enabled: true`.

`n_form_priority_weights` is not swept because it is inactive in
`n_total_only` mode.

### Portfolio and calibration scope

Additional portfolios are useful when they remove a genuinely different
source of an element or couple elements differently; arbitrary product subsets
mostly duplicate existing cases and overweight one catalog. The present set
therefore keeps the supplied real pools, the two earlier restricted pools, and
leave-one-out variants of the Humin-free union.

An artificial nutrient profile should not enter biological winner selection:
it has no ground truth and would silently encode the author’s preferences. A
useful synthetic check is instead a separate round-trip calibration generated
from a known non-Humin fertilizer mixture. Its pass condition is near-zero
residual on the generated vector, not recovery of the same doses (multiple
recipes can be chemically equivalent). That calibration belongs in a distinct
diagnostic phase before it is added; it must never be averaged into scientific
or handcrafted-profile rankings.

## Runtime Mass NNLS And Research Controls

Status: `current-state runtime plus research comparison`.

Production `mass_nnls` lives only in `src/horticalc/solver.py`. It minimizes
the unweighted sum of squared elemental residuals in canonical `mg/L`, subject
to non-negative fertilizer doses. It uses `N_total` whenever present and
always includes a non-zero elemental S target. It has no percentage or molar
normalization, macro/micro class, element severity table, IRLS pass, singleton
pass, or learned biological preference. For scale, `N -30 mg/L` contributes
`900` to the objective and `Cu +0.3 mg/L` contributes `0.09`.

The product catalog supplies a separate capability rule. A fertilizer with
`SolverRole=fixed_only` is not a variable Solver column, but its explicitly
supplied `fixed_grams` dose still contributes normally. The shipped HuminTech
AMINO POWER and Fulvital products are fixed-only; Fetrilon remains variable.
The two diagnostic Humin portfolios explicitly override that role inside the
research harness so the failure mode remains observable. Selection portfolios
use the shipped catalog exactly as production does.

The former deterministic goal implementation now lives only in
`scripts/solver_goal_model.py`. It remains useful as a research control for
molar/mg minimax and global underfill hypotheses, but product runtime and UI do
not import or expose it. `scripts/solver_model_matrix.py` compares eight
policies:

- production `mass_nnls`;
- legacy canonical and historical config `34191`;
- symmetric mmol/L minimax;
- mmol/L minimax with global underfill factors `2`, `4`, and `10`;
- symmetric mg/L minimax.

The matrix contains 10 profiles x 35 portfolios plus seven matched recipe
roundtrips, or 357 cases per policy and 2,856 result rows. The 33 selection
portfolios determine quality gates; the two force-variable Humin portfolios
contribute 20 diagnostic cases per policy without influencing acceptance.
Evidence is stored as compressed `model_matrix_rows.jsonl.gz`;
`model_matrix_summary.json` contains the gates and research rankings.

### Mass-NNLS runtime result (2026-07-17)

Status: `accepted implementation result; quality gate passed`.

The corrected complete run finished 2,856/2,856 rows without failure in
20.29 seconds. Production Mass NNLS had zero dominated selection cases,
round-tripped all seven reference mixtures to numerical precision, returned
finite non-negative doses, and never produced a larger raw mg/L squared-error
sum than canonical Legacy in any of the 330 selection cases.

| Policy | Role | Mean squared error (mg/L)^2 | Worst N error mg/L | Dominated cases |
|---|---|---:|---:|---:|
| `mass_nnls` | production | 448.129 | 51.150 | 0 |
| `goal_mmol_symmetric` | research | 564.522 | 30.943 | 0 |
| `goal_mg_symmetric` | research | 562.633 | 66.932 | 0 |
| `goal_mmol_under_x2` | research | 595.587 | 57.739 | 0 |
| `goal_mmol_under_x4` | research | 727.446 | 101.827 | 0 |
| `goal_mmol_under_x10` | research | 1056.474 | 187.926 | 0 |
| `legacy_34191` | legacy | 1948.114 | 103.721 | 0 |
| `legacy_canonical` | legacy | 539.125 | 59.818 | 7 |

The mean raw squared error is 16.9% below canonical Legacy. The summary's
separate historical lexicographic mmol ranking still places
`goal_mmol_symmetric` first; that answers a different research question and is
not used to choose the product model. No single scalar metric is presented as
biological ground truth.

On the matched augmented Saloner portfolio, Mass NNLS uses unbounded Fetrilon
at `0.172435 g/10 L`, hits every macro plus Si within `0.0022 mg/L`, and returns
`N_total -0.0013`, `Fe -0.1629`, and `Cu +0.2979 mg/L`. Merely adding the two
fixed-only Humin products to the production allowed list leaves that solution
unchanged and selects neither product. On Bugbee with the same fertilizer
pool, achieved Fe is `1.3039 mg/L`, Mn `1.1186 mg/L`, and Cu `0.1111 mg/L`;
the toxic `Fe 21.55 mg/L` regression is not reproduced.

The force-variable diagnostics remain intentionally harsher. They show what
the mathematical optimizer would do if additive capability metadata were
removed, without tainting the production portfolio or inventing dose limits.

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
- `deep`: `matrix` plus named selection and diagnostic portfolios and
  primary-portfolio leave-one-out barrage cases. Diagnostic cases are reported
  separately and cannot change the winner.

Use `--primary-portfolio ID` to run the complete setting catalog against a
different named fertilizer portfolio without copying or editing the cases
file. The selected id is persisted in both the run manifest and summary.

`--max-runs` is a safety cap. Runs are configuration-first so a cap completes a
configuration across profiles before advancing, avoiding first-profile bias.
Use `0` to disable the cap.

## Exhaustive Interaction Runner

Status: `current-state`.

`scripts/solver_matrix_exhaustive.py` runs the full interaction search. It
derives every parameter domain from the controlled YAML catalog, then removes
combinations whose differing values cannot affect the active solver path. For
example, IRLS controls are fixed while relative weighting is disabled and a
singleton pass's thresholds are fixed while that pass is disabled.

The current catalog resolves to exactly 354,523 effective configurations and
3,545,230 solves across the ten canonical profiles. The retained combinations
include the requested unweighted configuration with S enabled, N-total-only,
both singleton passes enabled, overshoot share `0.85`, underfill share `0`,
underfill iterations `2`, and maximum regression `10`. A blind product which
retained inactive values would produce about 36.9 million solves.

An in-memory concurrency probe was run on 2026-07-16 on Windows with an AMD
Ryzen 9 3900X (12 cores, 24 logical processors) and 128 GB RAM. BLAS thread
counts were fixed to one per worker. The probe used the shipped read-only data,
discarded result payloads, and measured the following throughput:

| Execution | Solves/second |
|---|---:|
| Serial | 309 |
| 6 processes | 1,978 |
| 12 processes | 3,079 |
| 24 processes, 4,096 tasks | 3,644 |
| 24 processes, 10,000 tasks | 4,189 |
| 36 processes | 3,442 |
| 48 processes | 3,159 |
| 60 processes | 2,916 |
| 1,024 threads | 222 |

These measurements support a large queued task batch, not thousands of active
workers. On the measured host, `--workers 24 --queue-depth 10000` is the KISS
starting point. At the measured compute-only rate, 3.5 million solves take
about 14 minutes and the blind 36.9-million-row product takes about 2.45 hours.
Result aggregation and persistence add overhead, so these projections are not
end-to-end guarantees. `--workers 0` uses the logical CPU count; an explicit
worker count is preferred for a reproducible production run.

The parent process loads and validates all fertilizer, profile, water, and
molar-mass data once. Persistent workers receive that immutable payload, so
they do not race through `ensure_portable_layout()`. BLAS thread counts are
fixed to one per worker.

One writer stores normalized records in SQLite. Configurations, profiles,
portfolios, and exact achieved-element vectors are stored once; achieved
vectors are deduplicated by SHA-256 and referenced by integer ids from compact
run rows. Full solver JSON is rerun deterministically and zlib-compressed only
for the selected Pareto/utopia finalists and the legacy-composite comparison.
Input and source hashes form a run signature. Reusing the same output directory
resumes missing configurations; differing inputs are rejected instead of being
mixed into an existing database.

`--max-configs` supports smoke tests, `--skip-analysis` separates generation
from analysis, and `--analyze-only` reprocesses a completed matching database.

## Completed Exhaustive Benchmark: 2026-07-16

Status: `research-result`.

The complete interaction matrix was run against all ten canonical profiles on
the measured Ryzen 9 3900X host. The generated evidence remains under
`logs/solver_matrix/exhaustive_001/` and has input signature
`7412582f02bb8124b32db1605086420d389dbf05b4cf0707e9faa2699a43d8f6`.

| Measurement | Result |
|---|---:|
| Effective configurations | 354,523 |
| Solver runs | 3,545,230 |
| Successful / failed | 3,545,230 / 0 |
| Processes / queue depth | 24 / 10,000 |
| Compute and persistence time | 1,612.44 seconds |
| Exact unique achieved vectors | 19,170 |
| Deduplicated result repetition | 99.459% |
| SQLite size | 1,346,404,352 bytes |
| Pareto solutions | 13,935 |
| Compressed detailed finalists | 280 |

The all-objective data-normalized utopia selection was not macro-safe enough
for a general default: it produced `N_total -23.04%` and `K -22.79%` for
Bugbee and `N_total -15.41%` for augmented Saloner. A read-only re-evaluation
therefore ranked every complete configuration by equal percentage RMS over
only the macro objectives `N_total`, `P`, `K`, `Ca`, `Mg`, and `S`. Micros did
not participate in this ranking.

| Selection | Macro RMS | Rank of 354,523 |
|---|---:|---:|
| Macro configuration `69630` | **11.7418%** | **1** |
| All-objective normalized utopia | 12.7758% | 172,374 |
| Legacy composite winner | 14.6392% | 330,977 |
| Mode-like local-knee consensus | 15.4682% | 344,815 |

Configuration `69630`, hash
`7d01f2730b85fb46e4d059b77fa98a5b29778e2153a28cdcb96a834b45b7b263`,
is:

```yaml
relative_weighting: true
overshoot_penalty: 0.0
irls_max_outer_iter: 4
scale_eps_mg_per_l: 5.0
singleton_supplier_enabled: true
singleton_share_threshold: 0.95
singleton_max_regress_pp: 0.25
singleton_underfill_enabled: false
singleton_underfill_share_threshold: 0.85  # inactive while disabled
singleton_underfill_max_iter: 2            # inactive while disabled
nitrogen_objective_mode: n_total_only
s_objective_enabled: true
n_total_governor_enabled: true
n_total_governor_weight: 5.0
n_form_priority_weights: {}
```

Its largest macro percentage deviations by profile were:

| Profile | Largest macro deviation |
|---|---:|
| Steiner | `S -3.69%` |
| Bugbee | `K -11.94%` (`N_total -7.82%`) |
| Conn | `P +0.41%` |
| Cooper NFT | `P +3.55%` |
| De La Rosa Lettuce T2 | `P +0.06%` |
| Hermans | `K -0.04%` |
| Hoagland and Arnon Solution 1 | `N_total -0.15%` |
| Long Ashton LANS | `K +0.57%` |
| Augmented Saloner | `N_total -0.14%` |
| Golden regression | `S -87.89%` |

The Golden S target remains a material portfolio trade-off: another setting
can reduce its isolated S deficit, but not while retaining the best aggregate
macro result across the complete corpus. Configuration `69630` is a research
candidate, not a hardcoded runtime default, proof of biological severity, or a
hard limit. The raw achieved vectors remain available for future scoring
policies without rerunning the solver.

## Learned Preference Selection

Status: `current-state research-infrastructure`.

`scripts/solver_preference.py` performs the later policy selection without
changing the product solver or hardcoding a biological severity table. It
reads the completed exhaustive SQLite database in read-only mode and provides
four operations:

1. `pairs` samples nondominated solutions which improve different elements and
   emits deterministic A/B conflicts. The initial batch is balanced across all
   ten profiles. Once a model exists, `--model ... --append` prioritizes pairs
   nearest the model's 50/50 decision boundary and excludes pairs already
   emitted or labelled.
2. `label` records only `A`, `B`, or `SKIP` together with the pair id, profile,
   and matrix signature. It displays nutrients in the calculator's canonical
   order with target, achieved concentration, signed mg/L difference, and
   percentage for A and B in one table. Labels never alter solver settings.
3. `train` fits a projected non-negative Bradley-Terry logistic model with L1
   shrinkage and L2 regularization. Non-negative coefficients guarantee that
   increasing any error cannot improve a solution. Underfill and overshoot are
   independent features for every element.
4. `rank` re-scores all 354,523 complete settings from deduplicated achieved
   vectors, so no solver rerun is required.

Each element direction supplies three physical views of the same error:

- absolute error in mg/L;
- error relative to that profile's non-zero target;
- error relative to the improvement span observed on that profile's Pareto
  set.

The robust 90th-percentile feature scales are fitted from the labelled
solutions and the features use `log1p`, giving diminishing marginal influence
without a fixed upper/lower limit. Target-relative features distinguish a
large percentage on a trace element, while mg/L and reachable-span features
retain the physical difference between, for example, `N -30 mg/L` and
`Cu +0.15 mg/L`. Unused effects can shrink exactly to zero. Leave-one-profile-
out validation refits both feature scales and coefficients using only the
training profiles.

The default `grouped` feature structure learns one severity per element and
direction. Its monotone input is the mean of the independently scaled/logged
mg/L, relative-target, and reachable-span views. This retains all three views
while preventing nearly collinear columns for one error from exchanging
arbitrary coefficients. The legacy `independent` structure remains available
as a research comparator. Model JSON records matrix rank, condition number,
learned grouped severities, training metrics, and profile holdouts.

The final ordering is deliberately non-compensating and lexicographic:

1. lowest worst learned element penalty across all profiles;
2. lowest worst total profile cost;
3. lowest mean total profile cost;
4. configuration id as a deterministic tie break.

Consequently, ten perfect micros cannot numerically cancel a catastrophic N
error. Pareto filtering still determines which trade-offs are worth asking
about; the user labels supply the preference information which Pareto
dominance cannot infer. Until A/B labels exist, this workflow intentionally
does not claim an objective biological winner.

Default generated artifacts beside the exhaustive database are:

- `preference_pairs.jsonl`: complete, replayable conflicts including targets,
  achieved values, signed errors, solver configs, and reachability context;
- `preference_labels.jsonl`: replaceable-by-id decisions;
- `preference_model.json`: fitted scales, non-negative coefficients, training
  metrics, and profile holdouts;
- `preference_ranking.json`: the non-compensating top-200 shortlist, including
  the worst element and profile for each setting.

## Preference Portfolio Barrage

Status: `current-state research-infrastructure`.

`scripts/solver_preference_barrage.py` validates the learned top shortlist on
fertilizer sets which were not part of the primary setting search. With the
canonical defaults it executes:

```text
200 shortlisted configurations x 25 portfolios x 10 profiles = 50,000 solves
```

The two historical references `69630` and `207711` are always appended when
they are not already shortlisted. The current default therefore executes at
most 50,500 solves and retains a direct comparison even when either reference
ranks poorly on the primary portfolio.

The 25 portfolios are the six named cases plus the 19 deterministic
leave-one-fertilizer-out variants of the primary portfolio. Tasks are one
configuration/portfolio pair containing all ten profiles. The measured-host
defaults remain 24 worker processes and a queue depth of 10,000; the queue is
not a worker count.

The barrage uses the same normalized SQLite design as the exhaustive run:
configuration, profile, portfolio, and exact achieved vectors are stored once;
run rows reference deduplicated solution ids. Its input signature includes the
learned model, shortlist, profile and fertilizer contracts, water, molar
masses, and solver inputs. Matching runs resume; mismatched evidence is
rejected.

`barrage_ranking.json` orders candidates by worst learned element penalty,
worst profile/portfolio case, and mean case cost. It additionally records:

- leave-one-profile-out ranks;
- leave-one-portfolio-out ranks;
- the separately identified worst profile and worst case;
- deterministic bootstrap median rank, 90th-percentile rank, top-ten share,
  and win share;
- the winner's score margin to the runner-up.

Exact score ties use shared competition ranks (`1, 1, 3`) instead of an
arbitrary configuration-id order. Holdout and bootstrap ranks count distinct
solver behaviors rather than redundant settings. Behaviors are deduplicated
by their full sequence of achieved solution vectors across all 250 cases;
equivalent configuration ids remain visible but cannot inflate ranks.

The first lexicographic row is reported as the `leader`, not automatically as
a validated winner. Validation is deliberately strict and preference-free: a
winner must be unique, retain shared rank 1 in every leave-one-profile and
leave-one-portfolio analysis, and have bootstrap 90th-percentile rank 1. If
any condition fails, the JSON and CLI state that no winner has been validated
and retain the complete stability evidence instead of silently relaxing the
criterion.

This does not manufacture biological ground truth. It tests whether the
preference learned from labelled trade-offs generalizes and whether a setting
collapses when the fertilizer portfolio changes.

## Exhaustive Stress Screening

Status: `current-state research-infrastructure`.

The primary top-200 shortlist can miss settings which generalize to restricted
fertilizer portfolios. `scripts/solver_preference_screen.py` therefore runs
every one of the 354,523 exhaustive configurations on three stress portfolios
which exposed distinct failures in the first barrage:

- `solve_golden`;
- `restricted_blossom_fetrilon_pekacid_spezial`;
- `restricted_313_bittersalz_mkp`.

Across all ten profiles this is 10,635,690 screening solves. The runner uses
the same 24-process/10,000-queue execution model and normalized, resumable,
SHA-256-deduplicated SQLite storage. It reads configurations from the original
exhaustive database instead of serializing the complete configuration catalog
into a giant intermediate JSON file.

`screening_ranking.json` is a union rather than a single-score cutoff. By
default it retains candidates from:

- the best 10,000 non-compensating lexicographic results;
- the best 5,000 worst-case results;
- the best 5,000 mean-case results;
- the best 2,000 results for each screening portfolio;
- the best 1,000 results for each profile;
- the best 2,000 results after leaving out each profile;
- the best 2,000 results after leaving out each screening portfolio;
- historical references `69630` and `207711`.

Overlaps are stored once and every retained configuration records all reasons
for its inclusion. The union is then passed to the complete configured
portfolio barrage. This is a successive-halving search: it covers the full
solver-setting space on the known stress axes, while reserving the complete
portfolio matrix for a broad evidence-backed finalist set. The final barrage
still applies the same strict holdout and bootstrap winner validation.

`--include-ranking` makes successive screens a strict shortlist union.
`--analysis-model` can rescore stored solutions with another compatible model,
and `--analysis-out` preserves both reports. The barrage supports the same
model-only rescoring. `--extend-shortlist` permits a stored barrage to grow
only when every old configuration and all semantic solver inputs still match;
it then computes only the new configurations.

## Broad Preference Research Result (2026-07-17)

Status: `research-result; no validated winner`.

The completed broad search used two full-configuration screens and one
successively extended barrage:

- 354,523 configurations x 10 profiles x the three primary stress portfolios
  = 10,635,690 solves;
- the same configuration/profile space on `loo_02`, `loo_18`, and
  `augmented_saloner` = another 10,635,690 solves;
- the union of both screens and both preference structures retained 55,065
  configurations;
- 55,065 x 10 profiles x 25 portfolios = 13,766,250 complete barrage rows,
  representing 9,785 exact solver behaviors.

No runtime solver default was changed. Generated SQLite/JSON evidence stays
under ignored `logs/solver_matrix/` paths.

The independent model's full-matrix leader is config `152177`; it is not
validated (worst profile holdout behavior rank 4,943, worst portfolio holdout
rank 465, bootstrap p90 rank 586). The grouped model's leader is config `22403`;
it is also not validated (7,467, 2,014, and 2,681.4 respectively). Choosing
either leader as the product default would overstate the evidence.

A minimax comparison of stability ranks across both model structures identifies
configs `34191` and `34219` as tied cross-model robustness leaders. Their
stability ranks are 1 under the independent model and 5 under the grouped
model, but their worst holdout behavior ranks still reach 1,857 and 2,247.
They are research finalists, not proven biological defaults. Both use total-N
only, S enabled, relative weighting enabled, IRLS 2, scale epsilon 5 mg/L,
overshoot penalty 1, singleton supplier enabled, singleton underfill disabled,
singleton max regress 0 percentage points, and underfill share 0.85; they differ
only in singleton supplier share (0 for `34191`, 0.65 for `34219`).

Configuration multiplicity therefore no longer distorts ranks, restricted
portfolios are covered broadly, and model dependence is explicit. The 120
labels still do not identify a unique biological trade-off policy strongly
enough for one universal configuration to survive every holdout.

## Controlled-Runner Output Contract

Each run directory contains:

- `run_manifest.json`: input checksum, resolved targets, portfolios, setting
  catalog, unresolved cases, and planned row count;
- `results.csv`: spreadsheet-friendly rows;
- `results.jsonl`: lossless streaming rows;
- `summary.json`: counts, best rows, and a preliminary setting ranking.

Every result row has stable `run_id`, `profile_id`, `portfolio_id`,
`portfolio_role`, `experiment_id`, and `config_id` fields. JSON-valued columns
retain the exact solver configuration, allowed/used fertilizers, objective
elements, achieved concentrations, and errors. Portfolio
`reference_amounts` live in the manifest because they are provenance rather
than per-run solver inputs.

`scripts/solver_matrix_analyze.py` writes:

- `analysis_summary.json`: paired setting effects, per-profile winners, named
  selection-portfolio comparisons, separately labelled diagnostic honeypots,
  and leave-one-out impacts;
- `analysis_report.md`: the same evidence in a readable report.

Analyzer rankings use paired percentage improvement from each profile's
canonical baseline. Raw average deltas are also retained.

## Exhaustive-Runner Output Contract

The exhaustive output directory contains:

- `exhaustive.sqlite3`: normalized, resumable raw search data, configuration
  hashes, exact achieved vectors, Pareto membership, and compressed finalists;
- `exhaustive_summary.json`: run counts, signature, execution settings, timing,
  and resume status;
- `pareto_analysis.json`: per-profile candidate/Pareto counts, the selected
  data-normalized utopia points, signed element errors, the one configuration
  that performs best across the complete corpus, and legacy winners.

The SQLite `meta.manifest` value records resolved targets, allowed fertilizers,
water, molar masses, parameter domains, source hashes, element order, and the
planned row count. This is the self-contained evidence needed to reprocess a
run without parsing repeated result text.

## Controlled Legacy Scoring

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

The exhaustive winner selection does not use this composite score. The score
is retained only to compare the new selection with historical results.

## Exhaustive Pareto Selection

For every objective element, the exhaustive analyzer calculates the absolute
error in mg/L. A solution is removed only when another solution is no worse on
every objective and strictly better on at least one. No macro/micro grouping,
percentage error, element weight, severity constant, or under/over preference
participates in this dominance test. Rescaling a single element's units by a
positive constant therefore cannot change Pareto membership.

Because a Pareto set can contain many valid trade-offs, the analyzer also emits
one deterministic default: it min/max normalizes each element's errors over
the Pareto set and selects the lowest RMS distance to the per-element ideal.
This gives every observed objective dimension one normalized coordinate but is
not presented as biological truth. The complete Pareto set remains stored, so
a later user policy can select a different point without rerunning the solver.
Underfill and overshoot remain symmetric in this evaluation; any directional
preference must be an explicit later policy, not a hidden solver benchmark
constant.

For the single configuration intended to work best across the whole benchmark
corpus, each `(profile, element)` error is normalized independently over all
complete configurations and the lowest overall RMS distance is selected. This
prevents profiles or elements with naturally larger mg/L magnitudes from
winning merely because of their units. `pareto_analysis.json` reports that
global configuration, its per-profile normalized RMS, and every signed error.

## Files And Removal

- `scripts/solver_matrix.py`: runner.
- `scripts/solver_matrix_exhaustive.py`: parallel exhaustive runner and Pareto
  analyzer.
- `scripts/solver_matrix_cases.yml`: benchmark data and experiment grids.
- `scripts/solver_matrix_analyze.py`: paired analyzer and report writer.
- `scripts/solver_preference.py`: conflict generation, labels, monotone model,
  and non-compensating shortlist ranking.
- `scripts/solver_preference_barrage.py`: deduplicated shortlist barrage and
  holdout/bootstrap stability analysis.
- `scripts/solver_preference_screen.py`: exhaustive stress-portfolio screen and
  multi-view shortlist construction.
- `tests/test_solver_matrix.py`: runner/data-contract tests.
- `tests/test_solver_matrix_exhaustive.py`: exhaustive enumeration, Pareto,
  compact-storage, and resume tests.
- `tests/test_solver_matrix_analyze.py`: analysis-contract tests.
- `tests/test_solver_preference.py`: feature direction, monotonicity,
  non-compensation, compact barrage, resume, and holdout tests.
- `logs/solver_matrix/...`: generated, ignored results.

Deleting those scripts, cases, tests, generated output, and this docs link
removes the research harness without changing product runtime.

For exact commands, see [commands.md](commands.md#solver-matrix-harness).
