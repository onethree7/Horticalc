# API Reference

The FastAPI app lives in `api/app.py`. It serves JSON API routes and the static
frontend from the same origin. Save endpoints also accept YAML request bodies
for compatibility, but JSON is the documented API contract.

JSON and YAML save bodies must decode to an object. Malformed bodies return
HTTP 400, model-shape errors return HTTP 422, and unknown mapping keys or
non-finite mapping values return HTTP 400. Non-finite model fields such as
liters, fertilizer grams, fixed grams, and osmosis percentage return HTTP 422.
Water values use the same allowed-key and finite-number validation in profile
saves, `/calculate`, and `/solve`.
Empty lists and strings are not treated as missing objects; malformed nested
water mappings return HTTP 400.

Resource-list routes skip an unreadable or malformed YAML file and log a
warning so one damaged user file does not hide every valid profile. Directly
loading that damaged file still fails.

## Health And Schema

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Returns `{"status": "ok"}`. |
| `GET` | `/schema/fertilizer-comp-keys` | Returns fertilizer composition keys from `core.COMP_COLS`. |
| `GET` | `/schema/solver-config` | Returns solver config definitions from `solver_config.py`. |
| `GET` | `/molar-masses` | Returns `data/molar_masses.yml`. |

## Preferences

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/preferences` | Return persisted UI preferences. |
| `PUT` | `/preferences` | Validate and merge one or more UI preferences. |

Accepted fields are `theme`, `locale`, positive `default_liters`,
`solver_config`, and `last_water_profile`. `locale` accepts `de`, `en`, `nl`,
`es`, or `zh`. Preference Solver keys and value types must match the
UI-visible definitions from `/schema/solver-config`; definitions marked
`ui: false` remain available to recipes and `/solve` but are not preference
defaults. Water-profile values must be filenames rather than paths. Partial
payloads are merged with existing preferences. Preferences are stored in
`user/preferences.json` so they survive the launcher's temporary browser
profiles.

Sending `{"solver_config": {}}` removes saved Solver overrides and restores
the schema defaults on the next load.

Solver configuration is validated consistently for preferences, saved
recipes, and `/solve`. Unknown keys, incorrect JSON types, unsupported
`nitrogen_objective_mode` values, non-finite numbers, and invalid
`n_form_priority_weights` mappings return HTTP 400.

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
    "comp": {"NO3": 0.1, "K2O": 0.2}
  }
]
```

Names are matched case-insensitively after whitespace normalization. The
shipped catalog remains `data/fertilizers.csv`; the endpoint writes only user
deltas under `user/`. `liquid` is required and Boolean; the API does not accept
localized form strings. Names must be non-empty and unique, weight factors must
be positive finite numbers, and nutrient values must be finite; violations
return HTTP 400 with English error details.

## Water Profiles

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/water-profiles` | List shipped profiles with user overrides layered by filename. |
| `GET` | `/water-profiles/{profile_name}` | Load one water profile and include normalized values. |
| `POST`/`PUT` | `/water-profiles` | Save a water profile. |

Allowed water keys are defined in `api/app.py` as `ALLOWED_WATER_KEYS`.
Current keys include nitrogen forms, oxide forms, element helpers, carbonate
helpers, trace elements, and `KH`.

Save payload:

```json
{
  "name": "My Water",
  "source": "",
  "mg_per_l": {"Ca": 80, "Mg": 20, "HCO3": 120},
  "osmosis_percent": 0
}
```

## Nutrient Solution Targets

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/nutrient-solutions` | List target profiles. |
| `GET` | `/nutrient-solutions/{solution_name}` | Load target profile. |
| `POST`/`PUT` | `/nutrient-solutions` | Save target profile. |

Allowed target keys are defined in `src/horticalc/solver.py` as
`ALLOWED_TARGET_KEYS` and reused by `api/app.py`.

GET responses expose only the runtime contract: `name`, `source`, and
`targets_mg_per_l`. Optional shipped-profile conversion notes are not returned
by the API. POST/PUT uses the same three-field contract.

## Recipes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/recipes/default` | Load the user override or shipped default recipe. |
| `GET` | `/recipes` | List layered shipped/user recipes except `default.yml` and `solve_*.yml`. |
| `GET` | `/recipes/{recipe_name}` | Load a recipe. |
| `POST`/`PUT` | `/recipes` | Save a recipe. |

Recipe payload:

```json
{
  "name": "Example Recipe",
  "liters": 10,
  "fertilizers": [{"name": "Calcinit", "grams": 4.5}],
  "fertilizers_allowed": ["Calcinit"],
  "urea_as_nh4": false,
  "water_profile": "default",
  "osmosis_percent": 0,
  "solver_config": {}
}
```

## Calculate

`POST /calculate` computes a nutrient solution from explicit fertilizer grams.

Request:

```json
{
  "liters": 10,
  "fertilizers": [{"name": "Calcinit", "grams": 4.5}],
  "urea_as_nh4": false,
  "water_mg_l": {"Ca": 80},
  "osmosis_percent": 0
}
```

Instead of `water_mg_l`, callers may pass `water_profile_name`.

Response follows `CalcResult.to_dict()` in `src/horticalc/core.py`; see
[Data model](data_model.md).
This includes the fertilizer-only element, oxide, ion-balance, and EC fields,
plus the Sluijsmann result.

The `ion_balance` response object keeps legacy raw CBE fields
`error_percent_signed` and `error_percent_abs` and also includes explicit
`raw_cbe_percent_signed`, `raw_cbe_percent_abs`,
`din_38402_62_percent_signed`, `din_38402_62_percent_abs`, and
`balance_method` fields.

## Solve

`POST /solve` solves target values into fertilizer grams.

Request:

```json
{
  "targets": {"N_total": 160, "P": 30, "K": 180},
  "liters": 10,
  "water_profile": {"mg_per_l": {}, "osmosis_percent": 0},
  "fertilizers_allowed": ["Calcinit"],
  "fixed_grams": {},
  "urea_as_nh4": false,
  "solver_config": {}
}
```

Response follows `SolveResult.to_dict()` in `src/horticalc/solver.py`.

## Static Frontend

`app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")`
serves `frontend/index.html` and static assets after API routes are registered.
