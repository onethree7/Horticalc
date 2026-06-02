# Data Model

## File Layout

Shipped defaults:

- `data/fertilizers.csv`
- `data/molar_masses.yml`
- `data/water_profiles/*.yml`
- `data/nutrient_solutions/*.yml`
- `recipes/*.yml`

Runtime user copies:

- `user/fertilizers_overrides.csv`
- `user/fertilizers_disabled.txt`
- `user/water_profiles/*.yml`
- `user/nutrient_solutions/*.yml`
- `user/recipes/*.yml`

`ensure_portable_layout()` creates writable runtime folders. Fertilizers are
loaded by `load_fertilizers()` in `src/horticalc/data_io.py` from the shipped
catalog first, then user overrides are applied, and names listed in
`user/fertilizers_disabled.txt` are removed. Legacy `user/fertilizers.csv`
snapshots are migrated once: custom names move into
`user/fertilizers_overrides.csv`, and the original file is retained as a
`.legacy-backup`.

Water profiles, nutrient solutions, and recipes still copy shipped defaults
into `user/` when a user copy is missing. Runtime edits are written to `user/`,
not to shipped defaults.

## Fertilizers CSV

Loaded by `load_fertilizers()` in `src/horticalc/data_io.py`.

Required columns:

- `Düngername` or `Duengername`
- `Form`
- `Gewicht`

All other numeric columns are interpreted as composition fractions. A value of
`0.14` means 14 percent by mass. The field named `NR` or `Nr.` is treated as a
row number and ignored during loading.

Composition keys are defined by `COMP_COLS` in `src/horticalc/core.py`:

- `NO3`, `NH4`, `UREA`
- `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O`
- `SO4`, `Cl`, `CO3`, `HCO3`, `SiO2`
- `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`

`Gewicht` is a `weight_factor` and multiplies effective fertilizer grams.

## Water Profiles

Water profile YAML:

```yaml
name: default
source: ""
osmosis_percent: 0
mg_per_l:
  Ca: 80
  Mg: 20
  HCO3: 120
```

Accepted input keys include direct forms, element helpers, oxide helpers, and
carbonate helpers. `normalize_water_profile()` converts helper keys into the
forms used by the calculation core.

Osmosis behavior:

- `osmosis_percent` is clamped to `0..100`.
- Mixed water values are multiplied by `1 - osmosis_percent / 100`.
- RO water is modelled as `0 mg/L` for every input.

## Recipes

Calculator recipe YAML:

```yaml
name: Example
liters: 10
water_profile: default
osmosis_percent: 0
urea_as_nh4: false
phosphate_species: H2PO4
fertilizers:
  - name: Calcinit
    grams: 4.5
fertilizers_allowed:
  - Calcinit
solver_config: {}
```

The calculator uses `fertilizers`. The solver uses `targets`,
`fertilizers_allowed`, `fixed_grams`, and `solver_config`.

## Nutrient Solution Target Profiles

Target profile YAML:

```yaml
name: Example Target
source: ""
targets_mg_per_l:
  N_total: 160
  P: 30
  K: 180
```

Targets are element mg/L. Some keys may be reported but ignored by the solver
objective; see [Solver](solver.MD).

## Calculation Output

`CalcResult.to_dict()` in `src/horticalc/core.py` is the canonical output
schema:

1. `liters`
2. `elements_mg_per_l`
3. `oxides_mg_per_l`
4. `ions_mmol_per_l`
5. `ions_meq_per_l`
6. `ion_balance`
7. `fertilizer_elements_mg_per_l`
8. `fertilizer_oxides_mg_per_l`
9. `fertilizer_ions_mmol_per_l`
10. `fertilizer_ions_meq_per_l`
11. `fertilizer_ion_balance`
12. `ec_fertilizer`
13. `water_elements_mg_per_l`
14. `water_oxides_mg_per_l`
15. `water_ions_mmol_per_l`
16. `water_ions_meq_per_l`
17. `water_ion_balance`
18. `ec`
19. `ec_water`
20. `npk_metrics`
21. `sluijsmann`
22. `osmosis_percent`

`ion_balance`, `fertilizer_ion_balance`, and `water_ion_balance` are produced
by `src/horticalc/core.py`. They contain `cations_meq_per_l`,
`anions_meq_per_l`, legacy compatibility fields `error_percent_signed` and
`error_percent_abs`, explicit raw CBE fields `raw_cbe_percent_signed` and
`raw_cbe_percent_abs`, DIN formula fields `din_38402_62_percent_signed` and
`din_38402_62_percent_abs`, and `balance_method`.

`error_percent_signed` and `error_percent_abs` remain aliases for the raw CBE:
`(cations_sum - anions_sum) / (cations_sum + anions_sum) * 100`. The DIN value
shown as "Ionenbilanzabweichung nach DIN 38402-62 Formel" uses
`(cations_sum - anions_sum) / (0.5 * (cations_sum + anions_sum)) * 100`.

Die Ionenbilanzabweichung wird mit der DIN-38402-62-Formel berechnet.
HortiCalc berücksichtigt dabei nur die im Modell vorhandenen analytischen
Ionensummen; fehlende Wasseranalyse-Ionen werden nicht rekonstruiert, geraten
oder durch stilles Wunschdenken ergänzt.

The current ion set in `src/horticalc/core.py` is NH4+, K+, Ca2+, Mg2+, Na+,
NO3-, phosphate as the configured H2PO4-/HPO4^2- species, SO4^2-, Cl-, HCO3-,
and CO3^2-. Trace nutrients are not included in the ion balance unless they are
explicitly modelled as charged species.

`npk_metrics` is produced by `src/horticalc/metrics.py`. It includes the
existing oxide/form ratios in `npk_ratios` and a separate `npk_ratios_ion`
mapping for dissolved mg/L element or form comparisons such as `Ca:Mg`,
`Ca:K`, `N:K`, `SO4:P`, and `P:K`.

## Solver Output

`SolveResult.to_dict()` in `src/horticalc/solver.py` is the canonical solver
schema:

1. `liters`
2. `fertilizers`
3. `objective_elements`
4. `targets_mg_per_l`
5. `achieved_elements_mg_per_l`
6. `errors_mg_per_l`
7. `errors_percent`

`objective_elements` is important: it is the list actually optimized by the
solver and by the solver matrix score.
