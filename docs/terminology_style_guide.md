# Terminology And Style Guide

Status: current-state.

Use these terms consistently in docs, UI labels, and API descriptions.

## Canonical Terms

| Term | Meaning |
| --- | --- |
| Recipe | A calculator input with fertilizer grams. |
| Solver Recipe | An input for solving targets into fertilizer grams. |
| Nutrient Solution | The computed solution represented by calculation output. |
| Solution Output | The JSON object returned by the calculator core. |
| Target Profile | A saved nutrient-solution target profile. |
| Water Profile | A saved water baseline profile. |
| AppRoot | Repo root in dev, executable folder in release. |

German UI labels currently use:

| UI label | Meaning |
| --- | --- |
| `DUENGER-EDITOR` | Fertilizer editor. |
| `WASSERWERTE` | Water profile and water values. |
| `RECHNER` | Calculator recipe workflow. |
| `SOLVER` | Target solver workflow. |

## Units

- Use `mg/L` for element, oxide, and input concentration text.
- Use `mmol/L` for ion molarity display.
- Use `meq/L` for ion charge balance display.
- Use `mS/cm` and `uS/cm` for EC.
- Use `grams` for fertilizer dosing.

## Output Keys

When describing JSON, use exact keys from code. Do not paraphrase keys.

Calculator output keys are listed in [Data model](data_model.md).
Solver output keys are listed in [Data model](data_model.md).

## Writing Rules

- Current docs describe current code behavior and cite owning files.
- Historical reports keep their original conclusions but must be labelled as
  historical.
- Avoid duplicating long command lists across docs; link to the operation guide.
- Prefer ASCII in new docs unless a file already requires specific symbols or
  user-facing labels.
