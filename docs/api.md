# HTTP API

Horticalc exposes a loopback HTTP API for calculation automation. The desktop
launcher chooses an available local port. For a fixed development endpoint,
complete the [source setup](../CONTRIBUTING.md#set-up-from-source) and use the
commands below.

The supported endpoints cover calculation, Solver, health, and their
machine-readable schemas.

## Run locally

After completing the source setup, start a fixed development endpoint.

Linux:

```bash
./.venv/bin/python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

## Supported endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Return `{"status":"ok"}`. |
| `GET` | `/schema/fertilizer-comp-keys` | Return accepted fertilizer composition keys. |
| `GET` | `/schema/solver-config` | Return Solver configuration definitions and defaults. |
| `GET` | `/schema/units` | Return supported volume and dose units. |
| `POST` | `/calculate` | Calculate a solution from explicit fertilizer doses. |
| `POST` | `/solve` | Solve nutrient targets into fertilizer doses. |

FastAPI publishes the exact request and response schemas at `/docs` and
`/openapi.json`. Those generated schemas, the Pydantic models in `api/app.py`,
and the domain keys in `src/horticalc/chemistry.py` own field-level truth.

## Calculate

`POST /calculate` accepts a positive batch volume, fertilizer names and
non-negative canonical doses, optional water composition, RO-water proportion,
and the urea-display mode.

Example for Bash:

```bash
curl -s http://127.0.0.1:8000/calculate \
  -H 'Content-Type: application/json' \
  --data '{
    "liters": 10,
    "fertilizers": [{"name": "Yara Tera CALCINIT", "grams": 10}],
    "water_mg_l": {},
    "osmosis_percent": 100,
    "urea_as_nh4": false
  }'
```

Equivalent PowerShell:

```powershell
$body = @{
  liters = 10
  fertilizers = @(@{name = "Yara Tera CALCINIT"; grams = 10})
  water_mg_l = @{}
  osmosis_percent = 100
  urea_as_nh4 = $false
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/calculate `
  -ContentType "application/json" -Body $body
```

Instead of `water_mg_l`, `water_profile_name` may select a stored profile. The
response reports elemental and oxide concentrations, ions, ion balances,
water/fertilizer contributions, EC, NPK metrics, Sluijsmann, volume, and
RO-water proportion.

## Solve

`POST /solve` accepts elemental targets, a positive batch volume, allowed
fertilizer names, optional fixed doses, optional water, and Solver settings.

Example for Bash:

```bash
curl -s http://127.0.0.1:8000/solve \
  -H 'Content-Type: application/json' \
  --data '{
    "targets": {"N_total": 155, "Ca": 190},
    "liters": 10,
    "water_profile": {"mg_per_l": {}, "osmosis_percent": 100},
    "fertilizers_allowed": ["Yara Tera CALCINIT"],
    "fixed_grams": {},
    "urea_as_nh4": false,
    "solver_config": {"solver_model": "nnls_tuning"}
  }'
```

Equivalent PowerShell:

```powershell
$body = @{
  targets = @{N_total = 155; Ca = 190}
  liters = 10
  water_profile = @{mg_per_l = @{}; osmosis_percent = 100}
  fertilizers_allowed = @("Yara Tera CALCINIT")
  fixed_grams = @{}
  urea_as_nh4 = $false
  solver_config = @{solver_model = "nnls_tuning"}
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/solve `
  -ContentType "application/json" -Body $body
```

The response identifies the model used, proposed doses, objective elements,
targets, achieved concentrations, errors, and model-specific priority audit
data. A successful API solve is also recorded in local Solver history when the
configured retention limit permits it; a history-write failure does not replace
a valid Solver response.

Canonical API `grams` means grams for solid fertilizers and milliliters for
liquid fertilizers. Concentrations use `mg/L`. See [Data formats](data-formats.md)
and [Solver](solver.md).

## Validation and errors

Malformed request bodies return HTTP `400`; model-shape and bounded-field errors
return `422`; domain validation such as unknown nutrient keys or fertilizer
names returns `400`. A named water profile that does not exist returns `404`.
All numeric inputs must be finite, and concentrations and doses must be
non-negative. Request bodies are limited to 1 MiB.

## Internal routes

Preferences, Solver history, launcher activation, fertilizer persistence,
water-profile persistence, nutrient-target profiles, recipes, molar-mass data,
and the static frontend are implementation APIs for the desktop UI. They may be
visible in OpenAPI, but they are not part of the supported external contract
defined by this page. The persistence and desktop-data routes require the
authenticated session established by the launcher and reject foreign origins.
