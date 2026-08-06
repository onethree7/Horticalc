# Terminology And Style Guide

Status: `decision-log`.

Use these terms consistently in docs, UI labels, and API descriptions.

## Canonical Terms

| Term | Meaning |
| --- | --- |
| Recipe | A calculator input with fertilizer doses. |
| Solver recipe | An input for solving targets into fertilizer doses. |
| Nutrient solution | The computed solution represented by calculation output. |
| Solution output | The JSON object returned by the calculator core. |
| Target profile | A saved nutrient-solution target profile. |
| Water profile | A saved water baseline profile. |
| AppRoot | Repo root in dev, executable folder in release. |

## UI Labels

| German | English | Dutch | Spanish | Simplified Chinese |
| --- | --- | --- | --- | --- |
| Dünger-Editor | Fertilizer editor | Meststoffen-editor | Editor de fertilizantes | 肥料编辑器 |
| Wasserwerte | Water analysis | Wateranalyse | Análisis del agua | 水质分析 |
| Rechner | Calculator | Calculator | Calculadora | 计算器 |
| Solver | Solver | Solver | Solver | Solver |
| Zielprofil | Target profile | Doelprofiel | Perfil objetivo | 目标配置 |

For water-analysis UI copy, use the domain terms **water analysis** for the
section, **water composition** for the measured ion values, and **RO-water
proportion** for the reverse-osmosis mixing percentage. Keep
`water_profile` and `osmosis_percent` unchanged in API, YAML, and file names.

Do not translate data contract names when they refer to actual files, payloads, or keys. Examples: `Düngername`, `fertilizers_allowed`, `N_total`, `NO3`, `mg/L`, `solver_config`.

## Units

- Use `mg/L` for element, oxide, and input concentration text.
- Use `mmol/L` for ion molarity display.
- Use `meq/L` for ion charge balance display.
- Use `mS/cm` and `uS/cm` for EC.
- Use `grams` for fertilizer dosing (grams for solids, mL for liquids). Display units are described in [unit_handling.md](unit_handling.md).

## Output Keys

When describing JSON, use exact keys from code. Do not paraphrase keys.

- Calculator output keys are listed in [data_model.md](data_model.md).
- Solver output keys are listed in [data_model.md](data_model.md).

## Writing Rules

- Current docs describe current code behavior and cite owning files.
- Historical reports keep their original conclusions but must be labelled as historical.
- Avoid duplicating long command lists; link to [commands.md](commands.md).
- Prefer ASCII in new docs unless a file already requires specific symbols or user-facing labels.
