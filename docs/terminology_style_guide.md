# Nutrient Solution / Solver / Recipe Terminology & Formatting Guide

## Purpose
Provide a single, canonical source of truth for terms and output formatting so **core.py**,
solver, CLI, API, docs, and UI all use the same wording, layout, and naming.

## Scope
This guide applies to:
- Core output contract from `src/horticalc/core.py` (`CalcResult.to_dict`).
- Solver inputs/outputs in `src/horticalc/solver.py`.
- CLI strings in `src/horticalc/__main__.py`.
- Any docs/UI that describe nutrient solutions, recipes, or solver behavior.

## Canonical Terms (must be used verbatim)
- **Recipe**: Input YAML used to compute a nutrient solution (non-solver).
- **Solver Recipe**: Input YAML used by the solver (targets/fixed constraints).
- **Nutrient Solution**: The computed result of a recipe (the solution itself).
- **Solution Output**: The structured JSON output produced by the core.
- **Water Baseline**: Water profile contributions before fertilizers.
- **Fertilizer Contributions**: Fertilizer-only contributions.

## Core Output Contract (authoritative keys)
These keys are defined in `CalcResult.to_dict()` and MUST be referenced exactly in all
wording, layout, and API/docs labels. Do not invent alternate names or synonyms.

### Top-level keys and required order
Order is part of the contract for documentation and pretty output:

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

### Naming rules (strict)
- **snake_case** only.
- Units must be encoded in the key (`mg_per_l`, `mmol_per_l`, `mS_per_cm`, etc.).
- Use **exact** key names from the list above in any docs/UI label text
  (e.g., “elements_mg_per_l”, not “elements (mg/L)”).

### Terminology alignment for core outputs
When describing a key in docs/UI, use the following precise terms:
- `elements_mg_per_l`: **Nutrient Solution elements** (total solution, mg/L).
- `oxides_mg_per_l`: **Nutrient Solution oxides** (total solution, mg/L).
- `ions_mmol_per_l`: **Nutrient Solution ions** (total solution, mmol/L).
- `ions_meq_per_l`: **Nutrient Solution ions** (total solution, meq/L).
- `ion_balance`: **Nutrient Solution ion balance**.

- `fertilizer_*`: **Fertilizer Contributions** only (not total solution).
- `water_*`: **Water Baseline** only (not total solution).

- `ec`: **Nutrient Solution EC** (total solution EC from ions).
- `ec_fertilizer`: **Fertilizer Contributions EC**.
- `ec_water`: **Water Baseline EC**.

- `npk_metrics`: **NPK metrics for the Nutrient Solution**.
- `sluijsmann`: **Sluijsmann metrics for the Nutrient Solution**.
- `osmosis_percent`: **Applied osmosis percent** used for the water baseline.

## Recipe vs Solver Recipe (inputs)
- A **Recipe** is used by the core to compute a Nutrient Solution.
- A **Solver Recipe** is used to compute **fertilizer grams** that achieve targets
  and then passes through the core to produce the Nutrient Solution.
- Use “recipe” only for input YAMLs. Use “solution output” for JSON outputs.

## CLI/Docs/UI string consistency
- CLI help text should use:
  - “Recipe” for `horticalc`.
  - “Solver Recipe” for `horticalc solve`.
- Avoid “result”, “output”, or “solution” unless explicitly using **Solution Output**.

## Example labels (approved)
- “Recipe file”
- “Solver Recipe file”
- “Nutrient Solution Output”
- “Fertilizer Contributions (fertilizer_*)”
- “Water Baseline (water_*)”

## Example labels (not allowed)
- “Solution Recipe”
- “Result JSON” (use **Solution Output**)
- “Elements (mg/L)” (use **elements_mg_per_l**)

## Alignment checklist (must pass)
- All docs/UI references match the **Canonical Terms**.
- All key names match the **Core Output Contract**.
- Any reformatting preserves the **required order**.
- No synonyms or localized variants for canonical terms in English docs.
