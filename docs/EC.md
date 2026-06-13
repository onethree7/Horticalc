# Electrical Conductivity

Status: current-state.

EC is computed in `src/horticalc/ec.py` from ion species in
`ions_mmol_per_l`. It is not a ppm/TDS-factor model.

## Model

Primary model:

- McCleskey et al. 2012 equations 7-9 and table 1.
- Temperature-dependent molal conductivity.
- Ionic-strength correction.

Fallback model:

- Vanysek/CRC limiting ionic conductivity at 25 C for ions not covered by the
  McCleskey table.
- Current fallback: `H2PO4-`.

Default temperatures:

- `18.0 C`
- `25.0 C`

Default density approximation:

- `1.0 kg/L`

## Input

`compute_ec()` accepts:

```python
compute_ec(ions_mmol_per_l)
```

`ions_mmol_per_l` comes from `core._compute_ions()`.

Recognized McCleskey ions:

- `K+`
- `Na+`
- `NH4+`
- `Ca2+`
- `Mg2+`
- `Cl-`
- `SO4^2-`
- `NO3-`
- `HCO3-`
- `CO3^2-`

Fallback ion:

- `H2PO4-`

Unknown ion labels are reported in `coverage.ignored_ions` and warnings.

## Output

`compute_ec()` returns:

- `method`
- `inputs`
- `ionic_strength_mol_per_kg`
- `ec_mS_per_cm`
- `ec_uS_per_cm`
- `contrib_mS_per_cm`
- `transport_numbers`
- `warnings`
- `coverage`
- `atc`

`CalcResult.to_dict()` exposes:

- `ec`: full solution EC.
- `ec_water`: water-only EC.
- `ec_fertilizer`: fertilizer-only EC.

## Assumptions

- Molality is approximated from mol/L using fixed density.
- Missing species such as H+, OH-, and complexes are not modelled.
- Phosphate species depend on the core-selected `phosphate_species`.
- Fallback ions do not get the McCleskey ionic-strength correction.

## Sources

- McCleskey RB, Nordstrom DK, Ryan JN, Ball JW. A new method of calculating
  electrical conductivity with applications to natural waters. Geochimica et
  Cosmochimica Acta 77 (2012) 369-382. DOI: 10.1016/j.gca.2011.10.031.
- Vanysek P. Ionic Conductivity and Diffusion at Infinite Dilution. CRC
  Handbook of Chemistry and Physics, 93rd Edition.

## Verification

```bash
python scripts/test.py tests/test_ec.py tests/test_ec_fertilizer_determinism.py -q
```
