# Data Model

Status: `current-state`.

## File Layout

Shipped defaults:

- `data/fertilizers.csv`
- `data/molar_masses.yml`
- `data/water_profiles/*.yml`
- `data/nutrient_solutions/*.yml`
- `recipes/*.yml`

Runtime user overrides:

- `user/fertilizers_overrides.csv`
- `user/fertilizers_disabled.txt`
- `user/preferences.json`
- `user/water_profiles/*.yml`
- `user/nutrient_solutions/*.yml`
- `user/recipes/*.yml`

`ensure_portable_layout()` in `src/horticalc/paths.py` creates writable runtime folders. Fertilizers are loaded by `load_fertilizers()` in `src/horticalc/data_io.py` from the shipped catalog first, then user overrides are applied, and names listed in `user/fertilizers_disabled.txt` are removed. Legacy `user/fertilizers.csv` snapshots are migrated once: custom names move into `user/fertilizers_overrides.csv`, and the original is retained as a `.legacy-backup`. Pre-`Liquid` catalogs map `Form=Flüssig` to liquid.

Water profiles, nutrient solutions, and recipes are read from shipped defaults with `user/` files layered on top by filename. Runtime edits are written only to `user/`; shipped files remain unchanged. Startup removes byte-identical copies and known untouched legacy nutrient-solution copies so existing installations migrate to the overlay model.

API list routes omit malformed or unreadable user YAML files and log a warning.
Water and target mappings must contain finite, non-negative numbers; API save
routes reject negatives, `NaN`, and infinity.

## Fertilizers CSV

Loaded by `load_fertilizers()` in `src/horticalc/data_io.py`.

Required columns:

- `Düngername` or `Duengername`
- `Liquid`
- `Gewicht`

Optional solver metadata:

- `SolverRole`: `variable` (default) lets the Solver choose a dose;
  `fixed_only` excludes the product from variable selection while still
  allowing an explicit recipe `fixed_grams` dose.
- `SolverMaxDosePerL`: non-negative maximum dose the Solver may choose per
  liter. Empty means unlimited; `0` excludes the product from variable Solver
  dosing. Explicit recipe `fixed_grams` overrides this maximum.

The shipped `data/fertilizers.csv` currently leaves `SolverMaxDosePerL` empty
for every product, so the shipped catalog defines no dose limits. HuminTech
AMINO POWER and Fulvital are shipped as `fixed_only`; all other shipped products
are `variable`. A user override can set either metadata field explicitly. An
older override file without a `SolverRole` column inherits the matching shipped
product's role, so upgrading cannot silently turn a fixed-only additive into a
variable Solver input.

All other numeric columns are interpreted as composition fractions. A value of
`0.14` means 14 percent by mass. `NR` or `Nr.` is accepted only for legacy CSV
compatibility and ignored during loading; newly written catalogs omit it.
New `fertilizers_overrides.csv` files use the stable shipped-catalog column
layout, with any user-defined composition columns appended. Empty values stay
empty rather than causing columns to disappear. Source: `save_fertilizers()` in
`src/horticalc/data_io.py`.

`load_fertilizers()` returns the fully merged shipped and user catalog sorted
by normalized fertilizer name. The API, GUI, solver, and CLI therefore share
the same default order. Source: `src/horticalc/data_io.py`.

Composition keys are defined by `COMP_COLS` in `src/horticalc/core.py`: `NO3`, `NH4`, `UREA`, `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O`, `SO4`, `Cl`, `CO3`, `HCO3`, `SiO2`, `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`.

`Liquid` is strictly `0` for a solid fertilizer or `1` for a liquid
fertilizer. It is exposed by the API as the Boolean field `liquid`; localized
labels are frontend presentation only. `Gewicht` is a `weight_factor` and
multiplies the fertilizer dose to effective product mass. It must be a finite
number greater than zero; invalid values are rejected instead of being silently
converted during persistence.
`SolverMaxDosePerL` uses the same canonical dose convention as Solver results:
g/L for solids and mL/L for liquids. It limits product dose, not nutrient
mg/L. The fertilizer editor exposes both solver metadata fields.

### Dose Units, Mass, And Liquid Fertilizers

Recipes and solver results use the `grams` field. In practice, the value is the user-facing dose:

- For solid fertilizers, enter grams.
- For liquid fertilizers, enter milliliters when `Liquid = 1` and `Gewicht` stores the product density in g/mL.

`compute_solution()` in `src/horticalc/core.py` converts the dose to effective product mass:

```text
effective product mass in g = dose * Gewicht
nutrient mg/L = dose * Gewicht * composition_fraction * 1000 / liters
```

The UI may present solid doses as g/kg/oz/lb and liquid doses as mL/L/US fl oz/Imp fl oz, but saved recipes, API payloads, solver output, and CLI output keep the canonical contract.

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

`load_water_profile_data()` in `src/horticalc/data_io.py` returns `name`, `source`, `osmosis_percent`, and numeric `mg_per_l`. `normalize_water_profile()` in `src/horticalc/core.py` converts helper keys into the forms used by the calculation core.

Osmosis behavior:

- `osmosis_percent` must be within `0..100`; out-of-range and non-finite values are rejected.
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
fertilizers:
  - name: Calcinit
    grams: 4.5
fertilizers_allowed:
  - Calcinit
solver_config: {}
```

The calculator uses `fertilizers`. The solver uses `targets`,
`fertilizers_allowed`, `fixed_grams`, and `solver_config`.
`fertilizers_allowed` stores exact fertilizer names and must not repeat the
same name within one recipe.
`solver_config.ignored_elements` may contain a duplicate-free list of target
keys to exclude from the optimization while retaining them in Solver output.
`liters` defaults to `10` only when omitted or null; an explicit zero, negative,
or non-finite value is invalid. Fertilizer `grams` values are finite and
non-negative.

## Nutrient Solution Target Profiles

Target profile YAML:

```yaml
name: Example Target
source: Example Author (2026)
targets_mg_per_l:
  N_total: 140
  P: 30
  K: 180
```

Targets are element mg/L. Accepted keys live in `ALLOWED_TARGET_KEYS` in `src/horticalc/solver.py`. Oxide aliases such as `K2O` and `P2O5` are fertilizer composition keys, not target keys. `S` is elemental sulfur; `SO4` is not a target key. `load_nutrient_solution_data()` returns only `name`, `source`, and `targets_mg_per_l`.

## Calculation Output

`CalcResult.to_dict()` in `src/horticalc/core.py` produces:

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

The three `ion_balance` objects contain `cations_meq_per_l`, `anions_meq_per_l`, `error_percent_signed`, `error_percent_abs`, `raw_cbe_percent_signed`, `raw_cbe_percent_abs`, `din_38402_62_percent_signed`, `din_38402_62_percent_abs`, and `balance_method`. The raw CBE is `(cations_sum - anions_sum) / (cations_sum + anions_sum) * 100`. The DIN formula is `(cations_sum - anions_sum) / (0.5 * (cations_sum + anions_sum)) * 100`.

The current ion set in `src/horticalc/core.py` is `NH4+`, `K+`, `Ca2+`, `Mg2+`, `Na+`, `NO3-`, `H2PO4-`, `SO4^2-`, `Cl-`, `HCO3-`, and `CO3^2-`. All phosphorus in the ion output is `H2PO4-`; pH-dependent speciation is not modelled.

`npk_metrics` is produced by `src/horticalc/metrics.py`. It includes `npk_ratios` and `npk_ratios_ion` mappings for dissolved mg/L comparisons such as `Ca:Mg`, `Ca:K`, `N:K`, `SO4:P`, and `P:K`.

## Solver Output

`SolveResult.to_dict()` in `src/horticalc/solver.py` produces:

1. `liters`
2. `solver_model`
3. `fertilizers`
4. `objective_elements`
5. `ignored_elements`
6. `targets_mg_per_l`
7. `achieved_elements_mg_per_l`
8. `errors_mg_per_l`
9. `errors_percent`

`solver_model` identifies the actual runtime path (`mass_nnls` or `legacy`).
`objective_elements` is the authoritative list of what
the solver optimized. The solver matrix benchmark scores this list.
`ignored_elements` records only explicit user exclusions. Ignored targets and
achieved values remain available for display and audit; error mappings contain
objective residuals only.
