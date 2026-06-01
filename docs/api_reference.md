# API Reference

The FastAPI app lives in `api/app.py`. It serves JSON/YAML API routes and the
static frontend from the same origin.

## Health And Schema

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Returns `{"status": "ok"}`. |
| `GET` | `/schema/fertilizer-comp-keys` | Returns fertilizer composition keys from `core.COMP_COLS`. |
| `GET` | `/schema/solver-config` | Returns solver config definitions from `solver_config.py`. |
| `GET` | `/molar-masses` | Returns `data/molar_masses.yml`. |

## Fertilizers

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/fertilizers` | List loaded fertilizers. |
| `PUT` | `/fertilizers` | Replace the effective fertilizer list by saving user overrides and disabled shipped names. |

`PUT /fertilizers` accepts a list:

```json
[
  {
    "name": "Example",
    "form": "fest",
    "weight_factor": 1.0,
    "comp": {"NO3": 0.1, "K2O": 0.2}
  }
]
```

Names are matched case-insensitively after whitespace normalization. The
shipped catalog remains `data/fertilizers.csv`; the endpoint writes only user
deltas under `user/`.

## Water Profiles

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/water-profiles` | List user water profiles. |
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

Allowed target keys are defined in `api/app.py` as `ALLOWED_TARGET_KEYS`.

## Recipes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/recipes/default` | Load the user default recipe. |
| `GET` | `/recipes` | List user recipes except `default.yml` and `solve_*.yml`. |
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
  "phosphate_species": "H2PO4",
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
  "phosphate_species": "H2PO4",
  "water_mg_l": {"Ca": 80},
  "osmosis_percent": 0
}
```

Instead of `water_mg_l`, callers may pass `water_profile_name`.

Response follows `CalcResult.to_dict()` in `src/horticalc/core.py`; see
[Data model](data_model.md).

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
  "phosphate_species": "H2PO4",
  "solver_config": {}
}
```

Response follows `SolveResult.to_dict()` in `src/horticalc/solver.py`.

## Static Frontend

`app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")`
serves `frontend/index.html` and static assets after API routes are registered.
