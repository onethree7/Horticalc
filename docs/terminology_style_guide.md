# Terminology & Formatting Guide (Core-Aligned)

This guide defines the **single source of truth** for wording, layout, and naming used for
nutrient solutions, solver recipes, and recipes. It is **100% aligned with the core terms**
and output keys defined in `src/horticalc/core.py`.

## 1) Canonical Terms (use exact wording)

| Term | Definition | Scope |
| --- | --- | --- |
| **Recipe** | Input YAML that defines a nutrient solution. | CLI, API, UI, docs |
| **Solver Recipe** | Input YAML for the solver (targets/constraints). | CLI, API, UI, docs |
| **Nutrient Solution** | The computed result of a Recipe. | CLI, API, UI, docs |
| **Solution Output** | The JSON output of the Nutrient Solution. | CLI, API, UI, docs |

**Rules**
- Do **not** use alternative terms (e.g., “result”, “output”, “solution recipe”) unless the
  canonical term above applies.
- Use the same capitalization in user-facing strings (e.g., “Solver Recipe”).

## 2) Core-Aligned Output Keys (source: `CalcResult.to_dict`)

The following keys are the **canonical field names**. Do not rename or paraphrase them in
UI labels, docs, or API specs.

**Primary Nutrient Solution output (order matters):**
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

**Key formatting rules**
- Use `snake_case` with units in the key suffix (e.g., `mg_per_l`, `mmol_per_l`).
- Always use the exact key names above when describing output fields.

## 3) Core Terms Must Be Reflected Everywhere

When documenting or labeling output:
- Use **Nutrient Solution** to describe computed results.
- Use **Solution Output** to describe JSON output fields.
- When referencing individual fields, **use the exact key name** shown above.

## 4) CLI / UI / Docs Alignment

All user-facing strings must use the canonical terms:
- “Load Recipe”
- “Load Solver Recipe”
- “Nutrient Solution”
- “Solution Output”

Avoid:
- “Compute Recipe Output”
- “Solver result”
- “Solution recipe”

## 5) Examples

✅ “Nutrient Solution (Solution Output): `elements_mg_per_l`”

❌ “Recipe results: elements mg/l”

