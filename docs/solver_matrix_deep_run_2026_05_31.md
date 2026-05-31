# Solver Matrix Deep Run Report - 2026-05-31

This report records the interpretation of the large local solver-matrix run in `logs/solver_matrix/dev`. It is intentionally evidence-heavy because the purpose of this benchmark is to decide solver behavior, not just to find a nice-looking single recipe.

## Source Run

| Item | Value |
|---|---:|
| Total rows | 2,624,392 |
| Failed rows | 0 |
| Base rows | 2,620,160 |
| Refine rows | 4,232 |
| Profiles | 10 |
| Fertilizers | 11 |
| CSV size | 8.71 GiB |
| JSONL size | 9.82 GiB |
| Analysis pass | 207.7 s |

Run command:

```powershell
python scripts\solver_matrix.py --preset deep --seed 1337 --top-n 20
```

## Executive Verdict

- The correct calculator default is the simple model: `n_total_only`, `relative_weighting=true`, `macro_priority_enabled=false`, `stage_optimization_enabled=false`, `singleton_supplier_enabled=true`, `singleton_underfill_enabled=true`, `n_total_governor_enabled=false`.
- `n_total_only` won every best-profile row: 10 out of 10. No best row used `n_forms_only`.
- `relative_weighting` is a keeper. Turning it off made the base average much worse in both nitrogen modes.
- `macro_priority_enabled` is the strongest malicious-detractor candidate. It more than doubled average error under `n_total_only` and almost doubled it under `n_forms_only`.
- `stage_optimization_enabled` is not proven useful as a default. With macro priority off it is mostly redundant; in aggregate it worsened the run. Keep it off and treat it as a later removal candidate after macro-priority cleanup.
- `n_forms_only` is scientifically valid as an explicit expert mode, but it should not be the default for this fertilizer catalog. It creates artificial pressure on N forms that the allowed products cannot independently satisfy.
- The main remaining quality limit is not NPK math. It is trace-element controllability: Cu, B, Mn, Zn, Fe, and Mo dominate worst-error keys.
- HCO3, S, SO4, Na, and Cl should remain report-only until the product deliberately implements them as objective elements. The matrix must continue scoring only `result.objective_elements`.

## Nitrogen Mode Result

| Mode | Rows | Avg score | Median | P95 | Best | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| `n_total_only` | 1,314,312 | 1637.925 | 311.946 | 10617.002 | 0.000 | Default winner |
| `n_forms_only` | 1,310,080 | 2989.279 | 744.293 | 12014.431 | 95.243 | Expert-only, not default |

`n_forms_only` had an average score 1.83x the `n_total_only` average and a median score 2.39x the `n_total_only` median. That is not noise. It is a structural signal.

Why this happened: most fertilizer products carry N forms as coupled passengers. If the objective demands exact N_NH4/N_NO3/N_UREA shape, the solver has to satisfy a form-ratio problem with products that were not designed as independent pure controls. `N_total` is the agronomic boss in the normal calculator path; form details should be reported or handled by a dedicated expert profile, not silently treated as equally binding targets.

## Best Rows By Profile

| Profile | Score | Mode | Phase | Subset | Macro | Micro | Worst key | Worst score |
|---|---:|---|---|---:|---:|---:|---|---:|
| `Abram_Steiner_Hydrokultur_Naehrloesung` | 74.824 | `n_total_only` | `refine` | 8 | 0.083 | 49.716 | `B` | 92.647 |
| `Bugbee_Utah_Hydroponic_Cannabis_2022` | 141.525 | `n_total_only` | `base` | 4 | 17.391 | 59.568 | `Cu` | 72.225 |
| `Hoagland_Arnon_1950_Solution1_Nitrate` | 92.341 | `n_total_only` | `refine` | 5 | 1.928 | 57.706 | `B` | 93.968 |
| `Hoagland_Arnon_1950_Solution2_AmmoniumPhosphate` | 113.300 | `n_total_only` | `refine` | 7 | 8.890 | 57.754 | `B` | 93.936 |
| `Knop_1861_Standard` | 0.000 | `n_total_only` | `base` | 5 | 0.000 | 0.000 | `Mg` | 0.000 |
| `Long_Ashton_Nutrient_Solution_LANS_NitrateType` | 74.795 | `n_total_only` | `refine` | 7 | 0.031 | 49.800 | `B` | 76.431 |
| `Murashige_Skoog_MS_1962_FullStrength` | 245.815 | `n_total_only` | `base` | 5 | 38.821 | 86.235 | `Mn` | 99.712 |
| `Saloner_Bernstein_Cannabis_NPK_Target_Optimization` | 78.850 | `n_total_only` | `refine` | 6 | 0.048 | 52.471 | `Zn` | 81.924 |
| `Yoshida_Rice_Solution_1976_CommonVariant` | 103.574 | `n_total_only` | `refine` | 6 | 1.521 | 66.007 | `Fe` | 98.657 |
| `saloner_bernstein_with_si_7` | 83.121 | `n_total_only` | `refine` | 7 | 0.120 | 55.173 | `Zn` | 83.061 |

Every winner used `n_total_only`. Seven winners came from numeric refinement and three were already best in the base grid. The best subset sizes were 4 to 8 fertilizers, not all 11, which means more products are not automatically better. Extra coupled nutrients often add constraints and side effects.

## Improvement Versus Previous 8-Fertilizer HCO3-Fixed Run

| Profile | Old score | New score | Improvement |
|---|---:|---:|---:|
| `Abram_Steiner_Hydrokultur_Naehrloesung` | 107.260 | 74.824 | 30.2% |
| `Bugbee_Utah_Hydroponic_Cannabis_2022` | 169.995 | 141.525 | 16.7% |
| `Hoagland_Arnon_1950_Solution1_Nitrate` | 118.643 | 92.341 | 22.2% |
| `Hoagland_Arnon_1950_Solution2_AmmoniumPhosphate` | 205.747 | 113.300 | 44.9% |
| `Knop_1861_Standard` | 10.166 | 0.000 | 100.0% |
| `Long_Ashton_Nutrient_Solution_LANS_NitrateType` | 90.607 | 74.795 | 17.5% |
| `Murashige_Skoog_MS_1962_FullStrength` | 511.207 | 245.815 | 51.9% |
| `Saloner_Bernstein_Cannabis_NPK_Target_Optimization` | 284.983 | 78.850 | 72.3% |
| `Yoshida_Rice_Solution_1976_CommonVariant` | 395.109 | 103.574 | 73.8% |
| `saloner_bernstein_with_si_7` | 281.136 | 83.121 | 70.4% |

Average best-row improvement was 50.0%. The expanded fertilizer list helped materially, especially on Saloner, Yoshida, Murashige, and Hoagland2.

## Boolean Feature Effects

These values compare base-grid rows only, so each boolean state has equal coverage.

### `n_total_only`

| Feature | False avg | True avg | Better state | Delta | Decision |
|---|---:|---:|---|---:|---|
| `relative_weighting` | 2352.092 | 933.661 | `true` | 1418.431 | Keep on |
| `macro_priority_enabled` | 1037.142 | 2248.611 | `false` | 1211.469 | Default off, removal candidate |
| `stage_optimization_enabled` | 1524.171 | 1761.582 | `false` | 237.410 | Default off, removal candidate |
| `singleton_supplier_enabled` | 1936.093 | 1349.660 | `true` | 586.433 | Keep on |
| `singleton_underfill_enabled` | 1643.307 | 1642.447 | `true` | 0.860 | Keep optional |
| `n_total_governor_enabled` | 1798.880 | 1486.874 | `true` | 312.006 | Optional safety, not default |

### `n_forms_only`

| Feature | False avg | True avg | Better state | Delta | Decision |
|---|---:|---:|---|---:|---|
| `relative_weighting` | 4221.943 | 1756.615 | `true` | 2465.328 | Keep on |
| `macro_priority_enabled` | 2088.024 | 3890.535 | `false` | 1802.511 | Default off, removal candidate |
| `stage_optimization_enabled` | 2859.298 | 3119.260 | `false` | 259.962 | Default off, removal candidate |
| `singleton_supplier_enabled` | 3481.544 | 2497.015 | `true` | 984.529 | Keep on |
| `singleton_underfill_enabled` | 2932.747 | 3045.812 | `false` | 113.065 | Keep optional |
| `n_total_governor_enabled` | 3416.048 | 2562.510 | `true` | 853.538 | Optional safety, not default |

The important interaction is not just individual flags. The best fair base configurations were all `n_total_only` with `macro_priority_enabled=false`. `stage_optimization_enabled=true` and `false` tied when macro priority was already off, so stage is not carrying useful independent signal in the winning regime.

## Top Fair Base Configurations

| Rank | Avg score | Config |
|---:|---:|---|
| 1 | 319.700 | `n_mode=n_total_only,macro_priority_enabled=false` |
| 2 | 319.700 | `n_mode=n_total_only,macro_priority_enabled=false,stage_optimization_enabled=false` |
| 3 | 320.395 | `n_mode=n_total_only,macro_priority_enabled=false,singleton_underfill_enabled=false` |
| 4 | 320.395 | `n_mode=n_total_only,macro_priority_enabled=false,stage_optimization_enabled=false,singleton_underfill_enabled=false` |
| 5 | 405.996 | `n_mode=n_total_only,macro_priority_enabled=false,n_total_governor_enabled=true` |
| 6 | 405.996 | `n_mode=n_total_only,macro_priority_enabled=false,stage_optimization_enabled=false,n_total_governor_enabled=true` |
| 7 | 406.506 | `n_mode=n_total_only,macro_priority_enabled=false,singleton_underfill_enabled=false,n_total_governor_enabled=true` |
| 8 | 406.506 | `n_mode=n_total_only,macro_priority_enabled=false,stage_optimization_enabled=false,singleton_underfill_enabled=false,n_total_governor_enabled=true` |
| 9 | 526.190 | `n_mode=n_total_only,macro_priority_enabled=false,singleton_supplier_enabled=false,singleton_underfill_enabled=false` |
| 10 | 526.190 | `n_mode=n_total_only,macro_priority_enabled=false,stage_optimization_enabled=false,singleton_supplier_enabled=false,singleton_underfill_enabled=false` |

This is the core evidence for the default change. The top rows are not exotic. They are the simple weighted solve, N_total objective, macro priority disabled. The simple model wins.

## Numeric Refinement Effects

| Mutation | Avg score | Count | Interpretation |
|---|---:|---:|---|
| `irls_max_outer_iter=8` | 102.600 | 200 | Useful but small; more outer iterations can polish winners. |
| `stage_regression_mg_l=0.5` | 102.600 | 200 | Mostly irrelevant while the winning path avoids relying on stage/macro behavior. |
| `stage_regression_pp=1.0` | 102.600 | 200 | Mostly irrelevant while the winning path avoids relying on stage/macro behavior. |
| `macro_regress_pp=1.0` | 102.605 | 200 | Mostly irrelevant while the winning path avoids relying on stage/macro behavior. |
| `singleton_share_threshold=0.95` | 102.605 | 200 | Threshold tuning is minor compared with mode and weighting. |
| `singleton_underfill_share_threshold=0.95` | 102.605 | 200 | Threshold tuning is minor compared with mode and weighting. |
| `stage_regression_pp=10.0` | 102.612 | 200 | Mostly irrelevant while the winning path avoids relying on stage/macro behavior. |
| `stage_regression_mg_l=5.0` | 102.618 | 200 | Mostly irrelevant while the winning path avoids relying on stage/macro behavior. |
| `macro_regress_pp=0.0` | 102.624 | 200 | Mostly irrelevant while the winning path avoids relying on stage/macro behavior. |
| `n_total_governor_weight=0.01` | 102.627 | 144 | Governor weight has low sensitivity around winners. |
| `n_total_governor_weight=0.1` | 102.627 | 144 | Governor weight has low sensitivity around winners. |
| `n_total_governor_weight=5.0` | 102.628 | 144 | Governor weight has low sensitivity around winners. |

Numeric refinement matters for best-profile rows, but it did not overturn the structural decisions. Boolean objective design mattered more than magic numeric constants.

## Fertilizer Effectivity

Positive omission delta means the average score got worse when the fertilizer was absent, so the product was useful across random subsets. Negative omission delta means rows containing it were worse on average. That is not the same as saying the fertilizer is bad; trace products can be vital in narrow contexts and harmful in broad averages.

### Base omission impact under `n_total_only`

| Fertilizer | Omission delta | Present avg | Absent avg | Best-profile uses | Interpretation |
|---|---:|---:|---:|---:|---|
| `K+S EPSO Top Bittersalz 16-39` | 1089.579 | 1098.353 | 2187.932 | 4 | Core control product |
| `Yara Magnitra-L Magnesiumnitrat` | 922.337 | 1181.934 | 2104.270 | 8 | Core control product |
| `S3 Kaliwasser 28 Be` | 143.518 | 1571.153 | 1714.671 | 8 | Often useful |
| `Yara Tera CALCINIT` | 139.353 | 1573.234 | 1712.587 | 9 | Often useful |
| `Peters Professional Combi Sol 6-18-36+3MgO+TE` | 117.000 | 1584.405 | 1701.405 | 2 | Often useful |
| `YaraTera KRISTALON ROT CALCIUM` | 38.069 | 1623.851 | 1661.920 | 4 | Mild positive average |
| `HAIFA monokaliumphosphat MKP` | 17.615 | 1634.074 | 1651.688 | 9 | Mild positive average |
| `Compo Hakaphos Soft16-8-22(+3) Spezial` | 5.761 | 1639.998 | 1645.758 | 4 | Mild positive average |
| `Agrolution Special 313 14-7-14+14CaO+TE` | -60.752 | 1673.238 | 1612.486 | 7 | Context medicine, not broad food |
| `Compo Hakaphos Blau 15-10-15(+2)` | -133.752 | 1709.720 | 1575.968 | 0 | Likely red-herring for this test set |
| `Compo Fetrilon Combi 1` | -1535.702 | 2410.353 | 874.650 | 5 | Context medicine, not broad food |

Reading by product:

- `K+S EPSO Top Bittersalz 16-39` and `Yara Magnitra-L Magnesiumnitrat` are the strongest broad enablers. They give independent Mg/S and nitrate/Mg leverage that removes a lot of impossible geometry.
- `Yara Tera CALCINIT`, `HAIFA monokaliumphosphat MKP`, and `S3 Kaliwasser 28 Be` appear in most winners because they provide the basic Ca, P, and K levers.
- `Compo Fetrilon Combi 1` has a very negative average omission effect, but still appears in 5 of 10 winners. This is exactly a trace-medicine pattern: powerful when a profile needs a trace package, harmful when random subsets force it into profiles that cannot absorb its coupled trace ratios.
- `Compo Hakaphos Blau 15-10-15(+2)` did not appear in any best-profile winner. For this benchmark set it behaves like a red-herring fertilizer.
- `Agrolution Special 313` appears in 7 winners despite a negative average. It is useful as a contextual bundled product, but bad as a universal assumption.

## Nutrient-Level Interpretation

| Mode | Worst-key ranking signal | Meaning |
|---|---|---|
| `n_total_only` | `Cu` 635,478, `B` 146,404, `Mn` 122,720, `Zn` 98,562, `Fe` 66,014, `Ca` 62,248, `Mo` 61,466, `P` 52,880 | Once total N is the boss, remaining failures are mostly trace controllability, not macro math. |
| `n_forms_only` | `Cu` 520,863, `N_NH4` 276,431, `N_UREA` 159,924, `Zn` 65,300, `B` 56,944, `P` 49,488, `Mn` 47,932, `Fe` 39,652 | N form targets become artificial blockers alongside trace elements. |

The macro stack is mostly solvable with the allowed products. K and N_total are rarely the worst key under `n_total_only`. The hard part is trace ratio geometry: one chelate or compound product can move Fe, Mn, Cu, Zn, B, and Mo together when profiles often need them separately. That is why a future industry-grade improvement should focus on target semantics and trace controls before inventing more global solver heuristics.

## Zero Targets, HCO3, And The `-` Question

The run confirms the database semantics problem: numeric `0` and missing target are not the same concept. A numeric zero can mean "I require this to be zero". A missing value, YAML `null`, or a deliberate `-` marker means "do not optimize this element". The solver historically skipped zero targets, which made `0` behave like ignore in many places. That was convenient, but it hides intent.

Recommended semantic model:

- Missing key or YAML `null`: unknown / not a target / ignore.
- Numeric value above zero: optimize if the solver supports that objective key.
- Numeric `0`: explicit zero target, but only optimize it if the objective policy says this key is controllable and should be included.
- UI display `-`: presentation for ignore/null, not a numeric value saved as `0`.

For now, the benchmark is correct because it follows `result.objective_elements` 1:1. `HCO3: 0` is report-only today because the solver does not include it as an objective. If a future solver supports HCO3 optimization, the benchmark will automatically score it when the solver includes it.

## Feature Decision Matrix

| Feature | Current decision | Evidence | Next action |
|---|---|---|---|
| `nitrogen_objective_mode=n_total_only` | Default | 10/10 profile winners, much better mean and median | Keep as calculator default |
| `relative_weighting=true` | Keep | Best rel/macro/stage families all use it; false greatly worsened averages | Do not remove |
| `macro_priority_enabled` | Default off | Worst major boolean; true doubled n_total average | Treat as deprecated, remove after one more confirmation run |
| `stage_optimization_enabled` | Default off | Aggregate worse; no independent benefit with macro off | Keep only as legacy toggle for now |
| `singleton_supplier_enabled` | Keep on | True improved both modes materially | Keep |
| `singleton_underfill_enabled` | Keep optional | Almost neutral under n_total; mild help under forms when false | Keep, not a priority |
| `n_total_governor_enabled` | Optional, default off | Helps bad configs, but best fair default did not need it | Keep as explicit expert/safety toggle |
| `n_forms_only` | Expert mode | Valid chemistry question, poor default geometry | Keep for explicit N-form recipes, not normal calculator default |

## What To Code Out Later

Do not delete everything at once. The industry-grade path is staged:

1. Already done in the PR branch: set the production defaults to the winning simple model and make the benchmark defaults start from the same model.
2. Next confirmation run: rerun deep on the new defaults into a fresh folder and compare against this report.
3. If the signal repeats, deprecate and remove `macro_priority_enabled` first. It is the clearest malicious detractor.
4. After macro priority is gone, reassess `stage_optimization_enabled`. If it remains neutral or harmful, remove it too. It currently looks like complexity without independent value.
5. Keep N mode selection, relative weighting, and singleton supplier behavior. Those are objective semantics or genuine solver mechanisms, not random heuristics.

## Recommended Next Run

After merging or testing the PR branch with the data-backed defaults, run:

```powershell
python scripts\solver_matrix.py --preset deep --seed 1337 --top-n 20 --out-dir logs\solver_matrix\after_n_total_default
```

Then compare:

- best rows per profile
- global fair base configs
- macro-priority on/off delta
- stage on/off delta after macro priority is already off
- worst nutrient keys under `n_total_only`

If this second run confirms the same shape, the next solver-quality PR should remove or hard-deprecate macro priority instead of adding more knobs.
