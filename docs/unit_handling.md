# Unit Handling

Status: `current-state`.

## Canonical Vs Display Units

Horticalc uses canonical units for calculation and persistence. Selecting a GUI unit changes presentation and input interpretation, not the stored physical quantity.

| Quantity | Canonical contract | Configurable presentation |
| --- | --- | --- |
| Batch volume | liters | L, US gal, Imp gal, m³ |
| Solid fertilizer dose | `grams` field in grams | g, kg, oz, lb |
| Liquid fertilizer dose | `grams` field interpreted as mL through density | mL, L, US fl oz, Imp fl oz |
| Element and water concentration | mg/L | water entry can also show mmol/L |
| Ion amount concentration | mmol/L and meq/L output | not configurable |
| EC | mS/cm at 18 °C and 25 °C | not configurable |

`src/horticalc/units.py` owns volume, mass, and liquid-volume definitions. `GET /schema/units` in `api/app.py` exposes those definitions to the frontend. `frontend/app/units.js` converts the selected display value to liters before building calculator, solver, or recipe payloads. API fields, CLI results, and recipe YAML continue to use `liters` and `grams` without a migration.

The supported gallon units are deliberately named `us_gallon` and `imperial_gallon`; an ambiguous `gallon` key is rejected. One US liquid gallon is 3.785411784 L and one Imperial gallon is 4.54609 L. A unit switch alone does not rescale fertilizer doses or recalculate the solution; editing the converted volume does rescale the active batch.

## Volume, Solid Dose, Liquid Dose, Concentration, EC

- Volume is stored in liters. `volume_to_liters()` and `liters_to_volume()` convert at the boundary.
- Solid doses are stored in grams. `mass_to_grams()` and `grams_to_mass()` convert at the boundary.
- Liquid doses are stored in milliliters. `liquid_volume_to_milliliters()` and `milliliters_to_liquid_volume()` convert at the boundary.
- Element, oxide, and water concentrations are mg/L.
- Ion output is mmol/L and meq/L.
- EC is mS/cm and uS/cm at 18 °C and 25 °C.

## Extension Rule

Add future units from the core outward:

1. Define the canonical quantity and exact conversion in `src/horticalc/units.py`.
2. Add conversion and round-trip tests.
3. Expose the definition through `GET /schema/units` and validate preferences.
4. Convert only at UI or future explicit API boundaries; keep chemistry, recipes, and solver inputs canonical.
5. Update GUI labels, clipboard output, persistence docs, and rendered tests.
6. Compare canonical outputs before and after switching display units.

This rule prevents display preferences from changing chemistry results.
