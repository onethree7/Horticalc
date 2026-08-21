# Electrical conductivity

Horticalc calculates electrical conductivity from the ion concentrations
produced by the chemistry core. It does not estimate EC from a ppm/TDS factor.
The implementation is `src/horticalc/ec.py`.

## Model

For covered ions, Horticalc applies McCleskey et al. (2012), equations 7–9 and
table 1: molal conductivity varies with temperature and is corrected for ionic
strength. `H2PO4-` uses its limiting conductivity at 25 °C from the CRC
reference because it is not covered by the primary table.

Default outputs are calculated at 18 °C and 25 °C with a density approximation
of `1.0 kg/L`.

The primary set is `K+`, `Na+`, `NH4+`, `Ca2+`, `Mg2+`, `Cl-`, `SO4^2-`,
`NO3-`, `HCO3-`, and `CO3^2-`. Ion-label aliases are normalized and accumulated.
Unsupported labels are listed in `coverage.ignored_ions` and produce a warning.

## Input and output

`compute_ec(ions_mmol_per_l)` accepts finite, non-negative ion concentrations.
Density must be finite and greater than zero.

The result contains method and input metadata, ionic strength, EC in `mS/cm`
and `uS/cm`, per-ion contributions, transport numbers, coverage, warnings, and
temperature-correction data. Calculator output exposes full-solution,
water-only, and fertilizer-only EC as `ec`, `ec_water`, and `ec_fertilizer`.

## Assumptions

- Molality is approximated from molarity using the configured fixed density.
- Missing species, including `H+`, `OH-`, and complexes, are not modelled.
- Phosphorus in the ion output is represented as `H2PO4-`; pH-dependent
  phosphate speciation is not modelled.
- The fallback ion does not receive the McCleskey ionic-strength correction.

## Sources

- McCleskey RB, Nordstrom DK, Ryan JN, Ball JW. *A new method of calculating
  electrical conductivity with applications to natural waters.* Geochimica et
  Cosmochimica Acta 77 (2012), 369–382. DOI: 10.1016/j.gca.2011.10.031.
- Vanysek P. *Ionic Conductivity and Diffusion at Infinite Dilution.* CRC
  Handbook of Chemistry and Physics, 93rd edition.
