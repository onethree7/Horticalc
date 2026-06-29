# Data Model

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

`ensure_portable_layout()` creates writable runtime folders. Fertilizers are
loaded by `load_fertilizers()` in `src/horticalc/data_io.py` from the shipped
catalog first, then user overrides are applied, and names listed in
`user/fertilizers_disabled.txt` are removed. Legacy `user/fertilizers.csv`
snapshots are migrated once: custom names move into
`user/fertilizers_overrides.csv`, and the original file is retained as a
`.legacy-backup`.

Water profiles, nutrient solutions, and recipes are read from shipped defaults
with `user/` files layered on top by filename. Runtime edits are written only
to `user/`; shipped files remain unchanged. Startup removes byte-identical
copied defaults and known untouched legacy nutrient-solution copies so existing
installations migrate to the overlay model without losing edits.

API list routes omit malformed or unreadable user YAML files and log a warning,
allowing the remaining valid profiles to stay available. Numeric mappings must
contain finite numbers; API save routes reject `NaN` and infinity rather than
persisting them. Runtime liters, fertilizer grams, Solver fixed grams, and
osmosis percentages must also be finite.

Persistence writes for YAML, preferences JSON, fertilizer CSV, and disabled
fertilizer names use a temporary file followed by an atomic replacement. A
failed replacement therefore leaves the previous file intact. YAML files must
contain a top-level mapping, and YAML/JSON/CSV persistence rejects non-finite
numbers. Invalid preferences are logged and retain the empty-preferences
fallback; invalid resource YAML remains visible to API logging and is skipped
from resource lists.

Explicitly malformed profile fields are not treated as missing defaults:
numeric mappings must be mappings, osmosis percentages must be numeric, and
fertilizer CSV names must remain unique after whitespace and case
normalization. All incoming fertilizers are validated before shipped/user
overlay differences are calculated. Preference writers require a JSON object.

The fertilizer override CSV and disabled-name file form one logical update.
If the final disabled-name write fails, persistence restores the previous
override CSV so a failed save cannot leave a partially updated overlay.

`user/preferences.json` is a JSON object containing optional `theme`, `locale`,
`default_liters`, `solver_config`, and `last_water_profile` fields. The API
validates partial updates and preserves JSON types. Preference `solver_config`
contains only UI-visible Solver defaults; advanced settings marked `ui: false`
remain recipe or direct solve inputs. Source: `load_user_preferences()` in
`src/horticalc/data_io.py` and `/preferences` in `api/app.py`.

## Fertilizers CSV

Loaded by `load_fertilizers()` in `src/horticalc/data_io.py`.

Required columns:

- `Düngername` or `Duengername`
- `Liquid`
- `Gewicht`

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

Composition keys are defined by `COMP_COLS` in `src/horticalc/core.py`:

- `NO3`, `NH4`, `UREA`
- `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O`
- `SO4`, `Cl`, `CO3`, `HCO3`, `SiO2`
- `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`

`Liquid` is strictly `0` for a solid fertilizer or `1` for a liquid
fertilizer. It is exposed by the API as the Boolean field `liquid`; localized
labels are frontend presentation only. `Gewicht` is a `weight_factor` and
multiplies the fertilizer dose to effective product mass. It must be a finite
number greater than zero; invalid values are rejected instead of being silently
converted during persistence.

### Dose Units, Mass, And Liquid Fertilizers

Recipes and solver results use the API field `grams` because this is the
canonical field name in `api/app.py`, `src/horticalc/core.py`, and
`src/horticalc/solver.py`. In practice, the value is the user-facing fertilizer
dose:

- For solid fertilizers, enter and measure the value as grams.
- For liquid fertilizers, enter and measure the value as milliliters when
  `Liquid = 1` and `Gewicht` stores the product density in `g/mL`.

The calculation core in `compute_solution()` converts the dose to effective
product mass before applying composition fractions:

```text
effective product mass in g = dose * Gewicht
nutrient mg/L = dose * Gewicht * composition_fraction * 1000 / liters
```

Composition fractions are mass fractions for the product. For example, `0.04`
means four percent by product mass. A liquid fertilizer with `Gewicht = 1.136`
therefore turns a solver result of `10` into `10 mL` in practice, while the
calculation uses `10 * 1.136 = 11.36 g` product mass internally. If dosing the
same liquid by scale instead of volume, weigh `dose * Gewicht` grams.

This means the UI/API label `grams` is literal for solids and historical for
liquids. The chemistry remains mass-normalized because the density factor is
applied before nutrient contributions are computed.

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

Shipped water profiles may include optional source metadata such as `region`,
`zone`, `year`, `pdf_url`, `source_url`, `source_quality`, `ph`, `ec_us_cm`,
`hardness_dh`, `limit_policy`, and `raw_mg_per_l`. These fields document the
published analysis source and detection-limit handling. `load_water_profile_data()`
in `src/horticalc/data_io.py` returns only `name`, `source`, `osmosis_percent`,
and numeric `mg_per_l` for runtime calculation.

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
source: Example Author (2026), table 1, DOI 10.example/example
note: Elemental mg/L calculated from source mmol/L values.
targets_mg_per_l:
  N_total: 140.067
  N_NO3: 140.067
  S: 64.13
```

Targets are element mg/L. The accepted solver target keys live in
`ALLOWED_TARGET_KEYS` in `src/horticalc/solver.py`; oxide aliases such as
`K2O` and `P2O5` are fertilizer composition keys, not target keys. Some target
keys may be reported but ignored by the solver objective; see
[Solver](solver.MD).

Shipped scientific profiles keep a short citation and, only when conversion
was required, one concise `note`. They do not duplicate the source table.
`load_nutrient_solution_data()` deliberately returns only `name`, `source`,
and `targets_mg_per_l`; the note is provenance text rather than solver input.
Unknown nutrients are omitted instead of being encoded as zero. See
[Nutrient solution profiles](nutrient_solution_profiles.md).

Nutrient-solution target profiles are not fertilizer recipes. They must not
contain compound quantities, stock-solution instructions, or substance masses.
Those belong to calculator recipes or fertilizer data. Scientific target YAMLs
retain only a concise citation and reported elemental or ionic concentrations.

The target key `S` is elemental sulfur. A source value reported as sulfate or
`SO3` must be converted toward elemental `S` using molar masses. `SO4` remains
a fertilizer composition, water-profile, and ion-output form; it is not an
accepted solver target key.

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

The ion-balance deviation is calculated with the DIN 38402-62 formula.
Horticalc includes only the analytical ion totals represented by the model;
missing water-analysis ions are not reconstructed, guessed, or silently
invented.

The current ion set in `src/horticalc/core.py` is NH4+, K+, Ca2+, Mg2+, Na+,
NO3-, H2PO4-, SO4^2-, Cl-, HCO3-, and CO3^2-. All phosphorus in the ion output
is represented as H2PO4-; pH-dependent phosphate speciation is not modelled.
Trace nutrients are not included in the ion balance unless they are explicitly
modelled as charged species.

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
