# API Reference

Status: `current-state`.

The FastAPI app lives in `api/app.py`. It serves JSON API routes and the static frontend from the same origin. Save endpoints also accept YAML request bodies for compatibility, but JSON is the documented contract.

Malformed bodies return HTTP 400, model-shape or bounded-field errors return
HTTP 422, and unknown, negative, or non-finite domain mapping values return
HTTP 400. Model fields enforce positive liters, non-negative fertilizer grams,
and osmosis percentage within `0..100`.
Resource list routes skip unreadable or malformed YAML and log a warning so one
damaged file does not hide valid profiles. Resource names resolve only inside
the configured shipped and user directories; absolute paths and traversal are
rejected by `src/horticalc/paths.py`.

## Health And Schema

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | `{"status": "ok"}` |
| `GET` | `/schema/fertilizer-comp-keys` | Fertilizer composition keys from `COMP_COLS` in `src/horticalc/core.py`. |
| `GET` | `/schema/solver-config` | Solver config definitions from `src/horticalc/solver_config.py`. |
| `GET` | `/schema/units` | Volume and dose conversion metadata from `src/horticalc/units.py`. |
| `GET` | `/molar-masses` | `data/molar_masses.yml`. |

## Preferences

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/preferences` | Return persisted UI preferences. |
| `PUT` | `/preferences` | Validate and merge one or more UI preferences. |

Accepted fields are `theme`, `locale`, positive `default_liters`, `volume_unit`, `solid_dose_unit`, `liquid_dose_unit`, `solver_config`, and `last_water_profile`. `locale` accepts `de`, `en`, `nl`, `es`, or `zh`. `volume_unit` accepts `liter`, `us_gallon`, `imperial_gallon`, or `cubic_meter`. `solid_dose_unit` accepts `gram`, `kilogram`, `ounce`, or `pound`. `liquid_dose_unit` accepts `milliliter`, `liter`, `us_fluid_ounce`, or `imperial_fluid_ounce`. These are GUI-only; API and recipe `grams` stay canonical. `solver_config` in preferences is restricted to UI-visible keys; advanced keys marked `ui: false` are only accepted in recipes and `/solve`.

Preferences are stored in `user/preferences.json` so they survive the launcher's temporary browser profiles. Partial payloads merge with existing preferences. Sending `{"solver_config": {}}` removes saved solver overrides.

## Fertilizers

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/fertilizers` | List loaded fertilizers. |
| `PUT` | `/fertilizers` | Replace the effective fertilizer list by saving user overrides and disabled shipped names. |

The in-memory effective catalog is replaced only after persistence succeeds.

`PUT /fertilizers` accepts a list:

```json
[
  {
    "name": "Example",
    "liquid": false,
    "weight_factor": 1.0,
    "comp": {"NO3": 0.1, "K2O": 0.2},
    "solver_role": "variable",
    "solver_max_dose_per_l": 0.25
  }
]
```

Names are matched case-insensitively after whitespace normalization. The
shipped catalog remains `data/fertilizers.csv`; the endpoint writes only user
deltas under `user/`. `liquid` is required and Boolean; the API does not accept
localized form strings. Names must be non-empty and unique, weight factors must
be positive finite numbers, and nutrient values must be finite; violations
return HTTP 400 with English error details.
`solver_role` is optional and accepts `variable` (default) or `fixed_only`.
Fixed-only products contribute only through an explicit `fixed_grams` dose.
`solver_max_dose_per_l` is optional, finite, and non-negative. `null` means no
Solver limit.

## Water Profiles

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/water-profiles` | List shipped profiles with user overrides layered by filename. |
| `GET` | `/water-profiles/{profile_name}` | Load one water profile with normalized values. |
| `POST`/`PUT` | `/water-profiles` | Save a water profile. |

Allowed water keys are defined in `src/horticalc/chemistry.py` and reused as `ALLOWED_WATER_KEYS` in `api/app.py`.

## Nutrient Solution Targets

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/nutrient-solutions` | List target profiles. |
| `GET` | `/nutrient-solutions/{solution_name}` | Load a target profile. |
| `POST`/`PUT` | `/nutrient-solutions` | Save a target profile. |

Allowed target keys are defined in `src/horticalc/solver.py` as `ALLOWED_TARGET_KEYS` and reused by `api/app.py`.

## Recipes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/recipes/default` | Load the user override or shipped default recipe. |
| `GET` | `/recipes` | List layered shipped/user recipes except `default.yml` and `solve_*.yml`. |
| `GET` | `/recipes/{recipe_name}` | Load a recipe. |
| `POST`/`PUT` | `/recipes` | Save a recipe. |

Recipe payloads use `name`, `liters`, `fertilizers`, `fertilizers_allowed`, `urea_as_nh4`, `water_profile`, `osmosis_percent`, and `solver_config`. The calculator uses `fertilizers`; the solver uses `fertilizers_allowed`, `fixed_grams`, and `solver_config`.

## Calculate

`POST /calculate` computes a nutrient solution from explicit doses. The `grams` field is canonical grams for solids and canonical mL for liquids.

Instead of `water_mg_l`, callers may pass `water_profile_name`. The response follows `CalcResult.to_dict()` in `src/horticalc/core.py` and is documented in [data_model.md](data_model.md).

## Solve

`POST /solve` solves target values into canonical fertilizer doses using the
same solid-grams/liquid-mL `grams` field contract.

Request:

```json
{
  "targets": {"N_total": 160, "P": 30, "K": 180},
  "liters": 10,
  "water_profile": {"mg_per_l": {}, "osmosis_percent": 0},
  "fertilizers_allowed": ["Calcinit"],
  "fixed_grams": {},
  "urea_as_nh4": false,
  "solver_config": {"solver_model": "mass_nnls"}
}
```

`fertilizers_allowed` must list each fertilizer name at most once. Solver
config overrides use the bounded definitions returned by
`GET /schema/solver-config`; see [solver.md](solver.md#solver-config-defaults-and-validation).

Response follows `SolveResult.to_dict()` in `src/horticalc/solver.py` and is
documented in [data_model.md](data_model.md). Its `solver_model` field confirms
which runtime model produced the doses.

## Static Frontend

`app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")` in `api/app.py` serves `frontend/index.html` and assets after API routes are registered.
