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
- `user/solver_history.jsonl`
- `user/water_profiles/*.yml`
- `user/nutrient_solutions/*.yml`
- `user/recipes/*.yml`

`ensure_portable_layout()` in `src/horticalc/paths.py` creates writable runtime folders. Fertilizers are loaded by `load_fertilizers()` in `src/horticalc/data_io.py` from the shipped catalog first, then user overrides are applied, and names listed in `user/fertilizers_disabled.txt` are removed. Legacy `user/fertilizers.csv` snapshots are migrated once: custom names move into `user/fertilizers_overrides.csv`, and the original is retained as a `.legacy-backup`. Pre-`Liquid` catalogs map `Form=Flüssig` to liquid.

Water profiles, nutrient solutions, and recipes are read from shipped defaults with `user/` files layered on top by filename. Runtime edits are written only to `user/`; shipped files remain unchanged. Startup removes byte-identical copies and known untouched legacy nutrient-solution copies so existing installations migrate to the overlay model.
Deleting a recipe or nutrient-solution target removes only its file under
`user/`. If that file overrode a shipped resource with the same filename, the
shipped resource becomes effective again.

The shipped calculator recipes are reference calculations. `default.yml` is
empty. Every non-default reference recipe uses `osmosis_percent: 100` and 1
g/L of each listed product, so its fertilizer-form concentrations follow from
the declared catalog fractions. Solver and regression fixtures live outside
`recipes/` and are never listed as user recipes.

API list routes omit malformed or unreadable user YAML files and log a warning.
Water and target mappings must contain finite, non-negative numbers; API save
routes reject negatives, `NaN`, and infinity.

## Solver History JSONL

`src/horticalc/solver_history.py` owns `user/solver_history.jsonl`. Each line
is a schema-versioned object containing a UUID, UTC timestamp, canonical Solver
setup, unchanged `SolveResult` mapping, fertilizer solid/liquid kinds, optional
Boolean `pinned` metadata, and the
EC/NPK/element projection needed by the printable UI output. The setup embeds
the actual water composition and RO-water proportion rather than depending on a mutable
water-profile filename.

Entries are stored oldest first. Summaries return pinned entries first and
newest first within the pinned and unpinned groups. Existing entries without
`pinned` are unpinned. The effective retention default is `1000`, bounded to
`0..10000`, and applies only to unpinned entries. Reducing it removes the oldest
unpinned entries immediately; `0` retains only pins and disables new normal
entries. The clear operation also retains pins. Writes are serialized and
atomic. Malformed lines are logged and skipped so valid history remains readable.

## Fertilizers CSV

Loaded by `load_fertilizers()` in `src/horticalc/data_io.py`.

### Schema

The canonical catalog requires:

- `Düngername` or the legacy-compatible `Duengername`
- `Liquid` (`0` for solid, `1` for liquid)
- `Gewicht` (a positive weight factor)

The optional `SolverMaxDosePerL` column limits variable solver dosing in the
product's canonical dose unit. Empty means no limit; `0` excludes the product
from variable dosing. An explicit `fixed_grams` entry remains available for a
fixed recipe dose.

All other numeric columns are composition fractions. A value of `0.14`
means 14% by mass. Legacy `NR`/`Nr.` columns are ignored. User override
catalogs use the shipped column layout and may append composition columns.

### Composition and dose conversion

Composition keys are defined by `COMP_COLS` in `src/horticalc/core.py`:

```text
NO3  NH4  UREA  P2O5  K2O  CaO  MgO  Na2O
SO4  Cl   CO3   HCO3  SiO2
Fe   Mn   Cu   Zn   B    Mo
```

Fertilizer `NH4`, `NO3`, and `UREA` values are elemental nitrogen
fractions. Oxide and salt forms are converted to elemental values using the
molar masses in `data/molar_masses.yml`.

Recipes and solver results use `grams` as the canonical dose field. The
fertilizer's `Gewicht` converts that dose to effective product mass:

```text
effective product mass (g) = grams × Gewicht
nutrient concentration (mg/L) = grams × Gewicht × fraction × 1000 / liters
```

For liquid products, the UI may display a volume dose; `Gewicht` stores the
density used for the conversion. Saved recipe and solver payloads retain the
canonical dose contract. The source of this calculation is
`compute_solution()` in `src/horticalc/core.py`.

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
- Mixed water concentrations are multiplied by `1 - osmosis_percent / 100`.
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
`solver_config.target_priorities` may map target keys to integer `under` and
`over` priorities in `0..4`. `ignored_elements` remains a duplicate-free
compatibility input; the hierarchical model treats each listed key as
priority `0` in both directions.
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
solver_config:
  solver_model: hierarchical
  target_priorities:
    N_total: {under: 1, over: 1}
    Ca: {under: 2, over: 3}
```

Targets are element mg/L. Accepted keys live in `ALLOWED_TARGET_KEYS` in
`src/horticalc/chemistry.py`. Oxide aliases such as `K2O` and `P2O5` are
fertilizer composition keys, not target keys. `S` is elemental sulfur; `SO4`
is not a target key. `solver_config` is optional and uses the same validated
contract as a recipe. `load_nutrient_solution_data()` returns `name`, `source`,
and `targets_mg_per_l`, plus every optional Solver-setup field present in the
YAML.

Target profiles saved with **Save/load Solver setup** may additionally contain the
current Solver inputs:

```yaml
liters: 10
water_profile: default
osmosis_percent: 0
fertilizers_allowed:
  - Compo Fetrilon Combi 1
  - ICL Nova PeKacid 0-60-20
fixed_grams:
  Compo Fetrilon Combi 1: 2
  ICL Nova PeKacid 0-60-20: 6
urea_as_nh4: false
solver_config:
  solver_model: mass_nnls
```

These fields are optional as a group in the GUI and remain individually
optional for older files and API clients. `liters` is positive,
`osmosis_percent` is within `0..100`, allowed fertilizer names are unique,
and every finite non-negative `fixed_grams` entry must also occur in
`fertilizers_allowed`. Fixed amounts are canonical batch totals and scale
proportionally when the GUI batch volume changes. Both API payloads and YAML
files use the normalizer in `src/horticalc/nutrient_profiles.py`; persistence
is owned by `src/horticalc/data_io.py`.

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
6. `target_priorities`
7. `priority_stages`
8. `targets_mg_per_l`
9. `achieved_elements_mg_per_l`
10. `errors_mg_per_l`
11. `errors_percent`

`solver_model` identifies the actual runtime path (`mass_nnls`, `hierarchical`,
or `nnls_tuning`).
`objective_elements` is the authoritative list of what the solver optimized.
`target_priorities` contains the resolved directional tiers used by a
hierarchical solve and is empty for the other models. `priority_stages`
contains the retained maximum and total `mg/L` residual for each populated
tier. `ignored_elements` remains a compatibility view of targets with both
directions at priority `0`. Report-only target and achieved values remain
available for display and audit; error mappings contain objective residuals
only.
