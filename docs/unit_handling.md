# Unit Handling

This document records the current unit architecture, the HydroBuddy comparison
that informed it, and the safe path for adding more units. It describes
implemented behavior unless a section is explicitly labelled as deferred.

## Current Contract

Horticalc uses canonical units for calculation and persistence. Selecting a GUI
unit changes presentation and input interpretation, not the stored physical
quantity.

| Quantity | Canonical contract | Configurable presentation |
| --- | --- | --- |
| Batch volume | liters | L, US gal, Imp gal, m³ |
| Solid fertilizer dose | `grams` field in grams | g, kg, oz, lb |
| Liquid fertilizer dose | `grams` field interpreted as mL through density | mL, L, US fl oz, Imp fl oz |
| Element and water concentration | mg/L | water entry can also show mmol/L |
| Ion amount concentration | mmol/L and meq/L output fields | not configurable |
| EC | mS/cm at 18 °C and 25 °C | not configurable |

`src/horticalc/units.py` owns volume, mass, and liquid-volume definitions. The
FastAPI route `GET /schema/units` exposes those definitions to the frontend.
`frontend/app.js` converts the selected display value to liters before building
calculator, solver, or recipe payloads. Fertilizer display values are likewise
converted back to canonical grams for solids or canonical milliliters for
liquids before payload construction. API fields, CLI results, and recipe YAML
therefore continue to use the literal `liters` and `grams` fields without a
migration or a second dose contract.

The supported gallon units are deliberately named `us_gallon` and
`imperial_gallon`; an ambiguous `gallon` key is rejected. One US liquid gallon
is 3.785411784 L and one Imperial gallon is 4.54609 L. A unit switch alone does
not rescale fertilizer doses or recalculate the solution because the physical
batch is unchanged. Editing the converted volume does rescale the active batch,
matching the existing liters workflow.

The selected `volume_unit`, `solid_dose_unit`, and `liquid_dose_unit` are
presentation preferences. Canonical `default_liters`, recipe doses, Solver
fixed values, and result objects remain unchanged. Switching a display unit
therefore does not rewrite a recipe or accumulate conversion rounding.

## HydroBuddy Comparison (Research)

The compared fork and the upstream HydroBuddy repository shared commit
`a1e63b32dcee9f92e34c9c281e090820dfc49def` at the time of review.

HydroBuddy accepts liters, US gallons, or cubic meters and immediately converts
the input to cubic meters, its calculation unit for `ppm = g/m³`. It separately
uses a display factor for grams or ounces and always labels liquid products in
mL. Its radio-button selections are persisted in `settings.ini`.

Relevant source:

- [volume and mass conversion in `hb_main.pas`](https://github.com/onethree7/hydrobuddy_fk/blob/a1e63b32dcee9f92e34c9c281e090820dfc49def/hb_main.pas#L726-L753)
- [result unit selection in `hb_main.pas`](https://github.com/onethree7/hydrobuddy_fk/blob/a1e63b32dcee9f92e34c9c281e090820dfc49def/hb_main.pas#L1761-L1794)
- [settings persistence in `hb_main.pas`](https://github.com/onethree7/hydrobuddy_fk/blob/a1e63b32dcee9f92e34c9c281e090820dfc49def/hb_main.pas#L3581-L3636)
- [HydroBuddy feature overview](https://scienceinhydroponics.com/2016/03/the-first-free-hydroponic-nutrient-calculator-program-o.html?print=print)

Horticalc follows the same useful principle—convert at the boundary and keep
one calculation unit—but centralizes definitions outside the UI and exposes
them through an API schema. This avoids HydroBuddy's repeated UI-bound
conversion branches.

## Existing Dose Contract

The fertilizer catalog already owns the physical distinction through `Liquid`.
Horticalc intentionally keeps the existing compact recipe/API contract:

- `grams` means grams when the referenced fertilizer is solid;
- `grams` means milliliters when the referenced fertilizer is liquid;
- `Gewicht`/`weight_factor` is the liquid density in g/mL and converts the
  canonical mL dose to product mass for chemistry.

The GUI labels each row with its actual display unit. This avoids a duplicated
quantity object while keeping old recipes, API clients, Solver output, and CLI
output compatible.

## Deferred Concentration Units

Water-entry mg/L ↔ mmol/L conversion already depends on substance-specific
molar masses. A general `ppm` selector would be misleading unless its basis is
defined; in dilute water mg/L is often treated as ppm, but they are not a
universally interchangeable unit contract. Any future concentration unit must
identify whether it represents element, ion, oxide, mass, molarity, or
equivalents.

## Extension Rule

Add future units from the core outward:

1. Define the canonical quantity and exact factor or quantity-specific
   conversion in `src/horticalc/units.py`.
2. Add conversion and round-trip tests.
3. Expose the definition through `GET /schema/units` and validate preferences.
4. Convert only at UI or future explicit API boundaries; keep chemistry, stored
   recipes, and solver inputs
   canonical.
5. Update GUI labels, clipboard output, persistence docs, and rendered tests.
6. Compare canonical outputs before and after switching display units.

This rule prevents display preferences from changing chemistry results.
