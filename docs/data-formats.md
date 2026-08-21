# Data formats

Horticalc calculates and persists canonical quantities. Display units and UI
language never rename stored keys or change the physical value.

## Data layout

Shipped data is read from:

- `data/fertilizers.csv` and `data/molar_masses.yml`;
- `data/water_profiles/*.yml` and `data/nutrient_solutions/*.yml`;
- `recipes/*.yml`.

User edits are written below `user/`: fertilizer overrides and disabled names,
preferences, Solver history, water profiles, target profiles, and recipes. A
user YAML file overrides a shipped file with the same filename. Deleting that
user file reveals the shipped version again.

Path resolution and portable-directory creation are owned by
`src/horticalc/paths.py`; CSV/YAML loading and saving are owned by
`src/horticalc/data_io.py`.

## Canonical units

| Quantity | Stored contract | UI alternatives |
| --- | --- | --- |
| Batch volume | liters | L, US gal, Imp gal, m³ |
| Solid dose | `grams` in g | g, kg, oz, lb |
| Liquid dose | `grams` interpreted as mL | mL, L, US fl oz, Imp fl oz |
| Element, oxide, and water concentration | `mg/L` | water input may show `mmol/L` |
| Ion concentration | `mmol/L` and `meq/L` | fixed |
| EC | `mS/cm` and `uS/cm` | fixed |

Exact conversion factors come from `src/horticalc/units.py` and are exposed to
the UI by `GET /schema/units`.

## Fertilizer CSV

The catalogue begins with these fields:

| Column | Meaning |
| --- | --- |
| `Düngername` | Unique product name |
| `Liquid` | `0` for solid, `1` for liquid |
| `Gewicht` | Positive weight factor; density for liquids |
| `SolverMaxDosePerL` | Optional non-negative variable Solver limit |

Remaining numeric columns are composition mass fractions. Supported forms are
defined by `COMP_COLS` in `src/horticalc/chemistry.py`: nitrogen forms, common
oxides and salts, and trace elements. For example, `0.14` is 14% by mass.

For a canonical dose:

```text
effective product mass (g) = grams × Gewicht
nutrient concentration (mg/L) = grams × Gewicht × fraction × 1000 / liters
```

An empty `SolverMaxDosePerL` is unlimited; `0` excludes a product from variable
Solver dosing but not from an explicit fixed dose.

## Water profiles

```yaml
name: Example water
source: Laboratory report, 2026-01-15
osmosis_percent: 0
mg_per_l:
  Ca: 80
  Mg: 20
  HCO3: 120
```

`osmosis_percent` is between `0` and `100`. Horticalc multiplies every source-
water concentration by `1 - osmosis_percent / 100`; RO water is modelled as
`0 mg/L`. Accepted water keys are `ALLOWED_WATER_KEYS` in
`src/horticalc/chemistry.py`.

## Calculator recipes

```yaml
name: Example recipe
liters: 10
water_profile: default
osmosis_percent: 0
urea_as_nh4: false
fertilizers:
  - name: Yara Tera CALCINIT
    grams: 10
```

`liters` must be positive. Fertilizer amounts are finite and non-negative. The
shipped `default.yml` contains no fertilizer; other shipped recipes are
zero-water reference calculations rather than crop recommendations.

## Nutrient target profiles

```yaml
name: Example target
source: Example Author (2026)
targets_mg_per_l:
  N_total: 140
  P: 30
  K: 180
solver_config:
  solver_model: hierarchical
  target_priorities:
    N_total: {under: 1, over: 1}
```

Targets are elemental `mg/L`; accepted keys are `ALLOWED_TARGET_KEYS` in
`src/horticalc/chemistry.py`. `K2O`, `P2O5`, and `SO4` are composition forms,
not target aliases. `S` means elemental sulfur.

A target profile may also store a complete Solver setup: `liters`,
`water_profile`, `osmosis_percent`, `fertilizers_allowed`, `fixed_grams`,
`urea_as_nh4`, and `solver_config`. The normalization contract shared by API
and YAML is in `src/horticalc/nutrient_profiles.py`.

## Sulfur conversion and profile sources

When a source reports sulfate or sulfur trioxide, convert it to elemental
sulfur before storing a target:

```text
S mg/L = SO4 mg/L × molar_mass(S) / molar_mass(SO4)
S mg/L = SO3 mg/L × molar_mass(S) / molar_mass(SO3)
```

Each shipped target YAML contains its own concise provenance and any required
conversion note. That file, rather than a second catalogue in the docs, owns
the source for its values.

## Results

Calculator JSON groups the full solution, fertilizer-only contribution, and
water-only contribution into elemental, oxide, ion, ion-balance, and EC data.
It also returns NPK metrics, Sluijsmann, batch liters, and RO-water proportion.
The authoritative mapping is `CalcResult.to_dict()` in `src/horticalc/core.py`.

Solver JSON returns the actual solver model, fertilizer doses,
`objective_elements`, target and achieved concentrations, residuals, and
priority audit data. `SolveResult.to_dict()` in `src/horticalc/solver.py` owns
the authoritative mapping. The HTTP representations are available in generated
OpenAPI as described in [HTTP API](api.md).
