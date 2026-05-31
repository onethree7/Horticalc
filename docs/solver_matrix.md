# Solver Matrix Benchmark

The solver matrix is a removable analysis tool for testing Horticalc solver
quality across many target profiles, fertilizer subsets, and solver
configuration toggles.

It is intentionally kept outside the product UI and outside the normal solver
code path. Think of it as a solver laboratory: it generates data so we can see
which solver settings behave well, which profiles are hard to solve, and which
fertilizers matter most.

## Files

- `scripts/solver_matrix.py` runs the matrix and writes result files.
- `scripts/solver_matrix_cases.yml` defines the default water, fertilizers, and custom target profiles.
- `logs/solver_matrix/...` receives generated output. This folder is ignored by git.
- `tests/test_solver_matrix.py` covers the name validation, scoring rules, and CLI smoke path.

## Default Scenario

The default case file uses:

- Water profile: `65936`
- Osmosis: `66%`
- Liters: `10.0`
- Fertilizers:
  - `Compo Fetrilon Combi 1`
  - `Yara Magnitra-L Magnesiumnitrat`
  - `Yara Tera CALCINIT`
  - `HAIFA monokaliumphosphat MKP`
  - `YaraTera KRISTALON ROT CALCIUM`
  - `Agrolution Special 313 14-7-14+14CaO+TE`
  - `S3 Kaliwasser 28 Be`
  - `Peters Professional Combi Sol 6-18-36+3MgO+TE`

The matrix loads all shipped nutrient solution profiles from
`data/nutrient_solutions/*.yml` and also includes the custom profile
`saloner_bernstein_with_si_7` from `scripts/solver_matrix_cases.yml`.

Fertilizer names must match exactly after Horticalc loads them. The script
intentionally rejects surrounding whitespace and prints a hint if a name looks
close to an existing fertilizer.

## Presets

### quick

Use this for fast feedback while developing the solver or checking a branch.

```powershell
python scripts\solver_matrix.py --preset quick
```

Behavior:

- Uses the full fertilizer list as one subset.
- Runs the full boolean solver toggle grid.
- With the default case file, this is usually `10 profiles * 1 subset * 64 configs = 640 runs`.
- Writes results to `logs/solver_matrix/dev` unless `--out-dir` is provided.

### matrix

Use this when you want to test all fertilizer inclusion/exclusion combinations.

```powershell
python scripts\solver_matrix.py --preset matrix --out-dir logs\solver_matrix\matrix_001
```

Behavior:

- Tests every non-empty subset of the 8 allowed fertilizers.
- That is `2^8 - 1 = 255` fertilizer subsets.
- Runs the full boolean solver toggle grid for each subset.
- With the default case file, this is usually `10 profiles * 255 subsets * 64 configs = 163200 runs`.
- This is the main "with X, without Y/Z/A, with B" mode.

### deep

Use this for the biggest solver exploration pass.

```powershell
python scripts\solver_matrix.py --preset deep --seed 1337 --top-n 20 --out-dir logs\solver_matrix\deep_001
```

Behavior:

- Starts with the full `matrix` preset.
- Keeps the best `--top-n` base rows per profile.
- Adds numeric mutations around those winners.
- Uses `--seed` to make refinement ordering reproducible.

The deep refinement mutates numeric solver settings such as:

- `overshoot_penalty`
- `scale_eps_mg_per_l`
- `irls_max_outer_iter`
- `singleton_share_threshold`
- `singleton_underfill_share_threshold`
- `stage_regression_pp`
- `stage_regression_mg_l`
- `macro_regress_pp`
- `n_total_governor_weight`

This is intentionally not a blind billion-run brute force. The script first
finds promising boolean configurations, then tries numeric variations around
the strongest candidates.

## Useful Run Examples

Run the default quick matrix:

```powershell
python scripts\solver_matrix.py --preset quick
```

Run quick into a named output folder:

```powershell
python scripts\solver_matrix.py --preset quick --out-dir logs\solver_matrix\quick_2026_05_31
```

Run only one target profile:

```powershell
python scripts\solver_matrix.py --preset quick --profiles Hoagland_Arnon_1950_Solution1_Nitrate
```

Run two target profiles:

```powershell
python scripts\solver_matrix.py --preset quick --profiles Hoagland_Arnon_1950_Solution1_Nitrate,saloner_bernstein_with_si_7
```

Run all fertilizer subsets:

```powershell
python scripts\solver_matrix.py --preset matrix --out-dir logs\solver_matrix\all_subsets
```

Run a reproducible deep pass:

```powershell
python scripts\solver_matrix.py --preset deep --seed 1337 --top-n 20 --out-dir logs\solver_matrix\deep_1337
```

Run a small smoke pass for development:

```powershell
python scripts\solver_matrix.py --preset quick --max-profiles 1 --max-configs 2 --out-dir logs\solver_matrix\smoke
```

Run a small subset smoke pass:

```powershell
python scripts\solver_matrix.py --preset matrix --max-profiles 1 --max-subsets 5 --max-configs 4 --out-dir logs\solver_matrix\subset_smoke
```

Override water and osmosis from the command line:

```powershell
python scripts\solver_matrix.py --preset quick --water-profile 65936 --osmosis-percent 66
```

Use a different case file:

```powershell
python scripts\solver_matrix.py --preset quick --cases scripts\solver_matrix_cases.yml
```

On bash-like shells, use forward slashes:

```bash
python scripts/solver_matrix.py --preset quick --out-dir logs/solver_matrix/quick
```

## Output Files

Each run writes three files into the selected output directory.

### results.csv

This is the spreadsheet-friendly output. Each row is one solver run.

Important columns:

- `profile_id`: target profile id, usually the YAML stem.
- `profile_name`: human-readable profile name.
- `preset`: `quick`, `matrix`, or `deep`.
- `phase`: `base` for boolean grid runs, `refine` for deep numeric mutations.
- `subset_size`: number of allowed fertilizers in this run.
- `fertilizers_allowed`: JSON list of fertilizer names used by this run.
- `config_name`: readable summary of changed solver toggles.
- `solver_config`: JSON object passed into the solver.
- `status`: `ok` or `error`.
- `elapsed_seconds`: solver runtime for this row.
- `composite_score`: main quality score. Lower is better.
- `macro_score`: RMS normalized score for macro targets.
- `n_form_score`: RMS normalized score for nitrogen form targets.
- `micro_score`: RMS normalized score for trace element targets.
- `other_score`: RMS normalized score for other optimized/reportable targets.
- `ignored_score`: report-only score for ignored solver targets.
- `max_error_key`: worst non-ignored element by normalized score.
- `max_error_score`: score for `max_error_key`.
- `total_grams`: total grams of fertilizers in the generated solution.
- `used_fertilizer_count`: number of fertilizers with non-zero grams.
- `used_fertilizers`: JSON list of fertilizer grams.
- `achieved_elements_mg_per_l`: JSON object with final achieved element values.
- `errors_mg_per_l`: JSON object with achieved minus target for solver objective elements.
- `errors_percent`: JSON object with percent errors for solver objective elements.
- `ignored_targets`: JSON object for report-only targets.
- `error`: exception text if the run failed.

### results.jsonl

This contains the same row data as `results.csv`, but one JSON object per line.
Use it when writing follow-up analysis scripts.

Example:

```powershell
Get-Content logs\solver_matrix\dev\results.jsonl | Select-Object -First 3
```

### summary.json

This is the high-level report.

Important sections:

- `total_runs`: number of rows attempted.
- `failed_runs`: number of rows that captured an exception.
- `best_by_profile`: best row for each profile by `composite_score`.
- `global_config_ranking`: average score by `config_name` across successful runs.
- `fertilizer_omission_impact`: compares average score when a fertilizer is present vs absent.
- `allowed_fertilizers`: exact fertilizer names used.
- `profiles`: profile ids included in the run.
- `results_csv`: path to the CSV file.
- `results_jsonl`: path to the JSONL file.

Quickly inspect the top global configs:

```powershell
python -c "import json; s=json.load(open('logs/solver_matrix/dev/summary.json', encoding='utf-8')); print(*s['global_config_ranking'][:10], sep='\n')"
```

Inspect best profile winners:

```powershell
python -c "import json; s=json.load(open('logs/solver_matrix/dev/summary.json', encoding='utf-8')); print(*[(k, v['config_name'], v['composite_score']) for k, v in s['best_by_profile'].items()], sep='\n')"
```

## Scoring

The matrix is a quality benchmark first, not a speed benchmark.

For non-zero targets, the element score is absolute percent error:

```text
abs((achieved - target) / target * 100)
```

For zero targets, percent error would be meaningless, so the matrix uses an
absolute tolerance:

```text
abs(achieved - target) / tolerance * 100
```

Current zero-target tolerances:

- Micro targets: `0.05 mg/l`
- N form targets: `1.0 mg/l`
- Macro targets: `2.0 mg/l`
- Other targets: `1.0 mg/l`

Element groups:

- Macro: `N_total`, `P`, `K`, `Ca`, `Mg`, `Si`
- N forms: `N_NH4`, `N_NO3`, `N_UREA`
- Micro: `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`
- Ignored/report-only: `S`, `SO4`, `Na`, `Cl`
- Other: everything else, currently including `HCO3`

Group scores are RMS values. The main score is:

```text
3.0 * macro_score
+ 3.0 * n_form_score
+ 1.5 * micro_score
+ 0.5 * other_score
```

Lower is better.

Ignored/report-only targets are written to `ignored_score` and
`ignored_targets`, but they do not affect `composite_score`.

## Important Interpretation Notes

`S`, `SO4`, `Na`, and `Cl` are currently ignored as solver optimization
targets by `src/horticalc/solver.py`. The matrix reports them, but it does not
punish solver configs for them in the composite score.

`HCO3` is not currently in that ignored set. With water profile `65936`, a
target of `HCO3: 0` can create a large `other_score`, because the water itself
contributes bicarbonate. If the goal is to treat alkalinity as report-only too,
move `HCO3` into the report-only category in the matrix scoring rules or update
the solver policy deliberately.

The `quick` preset cannot calculate fertilizer omission impact, because every
run uses all allowed fertilizers. Use `matrix` or `deep` to populate meaningful
`avg_when_absent` and `omission_delta` values.

## How To Compare Solver Settings

Start with:

```powershell
python scripts\solver_matrix.py --preset quick --out-dir logs\solver_matrix\quick_baseline
```

Then inspect:

- `summary.json -> best_by_profile`
- `summary.json -> global_config_ranking`
- `results.csv -> max_error_key`
- `results.csv -> macro_score`
- `results.csv -> n_form_score`
- `results.csv -> micro_score`

If one profile is weird, isolate it:

```powershell
python scripts\solver_matrix.py --preset matrix --profiles saloner_bernstein_with_si_7 --out-dir logs\solver_matrix\saloner_matrix
```

If one config family looks promising, run deep:

```powershell
python scripts\solver_matrix.py --preset deep --seed 1337 --top-n 20 --profiles saloner_bernstein_with_si_7 --out-dir logs\solver_matrix\saloner_deep
```

Then compare `best_by_profile` between output folders.

## How To Add A Custom Profile

Add an entry under `custom_profiles` in `scripts/solver_matrix_cases.yml`:

```yaml
custom_profiles:
  - id: my_profile_id
    name: My Profile Name
    source: Short source note
    targets_mg_per_l:
      N_total: 160
      N_NH4: 32
      N_NO3: 128
      P: 30
      K: 100
      Ca: 120
      Mg: 35
      Fe: 1.5
```

Then run it by id:

```powershell
python scripts\solver_matrix.py --preset quick --profiles my_profile_id
```

## How To Change Fertilizers

Edit `allowed_fertilizers` in `scripts/solver_matrix_cases.yml`.

Use exact names from the loaded fertilizer CSV. If the script fails with an
invalid fertilizer error, read the suggestion carefully. It often means there is
extra whitespace or a slightly different product spelling.

To test one profile with all subsets of a changed fertilizer list:

```powershell
python scripts\solver_matrix.py --preset matrix --profiles Hoagland_Arnon_1950_Solution1_Nitrate --out-dir logs\solver_matrix\custom_ferts
```

## Development And Verification

Run focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_solver_matrix.py -q
```

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run a tiny CLI smoke test:

```powershell
.\.venv\Scripts\python.exe scripts\solver_matrix.py --preset quick --profiles Hoagland_Arnon_1950_Solution1_Nitrate --max-configs 2 --out-dir logs\solver_matrix\smoke
```

Run the normal quick lab:

```powershell
.\.venv\Scripts\python.exe scripts\solver_matrix.py --preset quick --out-dir logs\solver_matrix\dev
```

## Keeping It Removable

The solver matrix is designed so it can be removed later without touching core
solver behavior.

To remove it:

- Delete `scripts/solver_matrix.py`.
- Delete `scripts/solver_matrix_cases.yml`.
- Delete `tests/test_solver_matrix.py`.
- Remove the solver matrix link from `docs/index.md`.
- Delete any generated `logs/solver_matrix/...` folders if desired.

No product code depends on the matrix.
