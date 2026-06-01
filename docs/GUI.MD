# GUI

Status: current-state.

The frontend is a static Vanilla JS app in `frontend/`. It is served by
FastAPI from the same origin as the API.

## Files

- `frontend/index.html`: DOM structure, workflow panels, stable IDs.
- `frontend/app.js`: state, API calls, rendering, workflow navigation.
- `frontend/styles.css`: app frame layout, tables, responsive rules.

## App Areas

The active navigation has four user-facing areas:

- `DUENGER-EDITOR`: fertilizer CSV editing, search, add/delete rows.
- `WASSERWERTE`: water profiles, osmosis percent, helper conversions, mg/L or mmol/L display.
- `RECHNER`: recipe profiles, fertilizer grams, calculation output, details.
- `SOLVER`: target values, searchable allowed-fertilizer picker, optional fixed
  grams, solver config, solve result, and calculator handoff.

The older visible mode bar is not the user workflow. Some hidden radio inputs
remain only to keep existing JavaScript paths stable.

The live sidebar in `frontend/index.html` and `frontend/app.js` displays the
latest calculation's NPK totals, compact P-normalized and NPK-only bubbles,
the ion-based `Ca:Mg` ratio, centered EC solution/water values, and compact
mg/L ion-ratio chips from `npk_metrics.npk_ratios_ion`.

The solver allowed-fertilizer picker in `frontend/index.html` is rendered by
`frontend/app.js` as a searchable checkbox list. It stores allowed fertilizer
selections by context in `localStorage` and does not write fertilizer favorites
or defaults to CSV.

The solver can automatically apply a successful solve result to the calculator.
The `solverAutoApply` checkbox defaults on, stores its preference in
`localStorage`, and uses the same `applyRecipe()` calculator path as loaded
recipes so the live sidebar updates after the recalculation.

The solver advanced config lives inside the Solver panel in
`frontend/index.html`, is backed by `/schema/solver-config`, and is wired in
`frontend/app.js`. The visible
`N-total statt N-Formen` checkbox writes
`solver_config.nitrogen_objective_mode`: checked sends `n_total_only`,
unchecked sends `n_forms_only`.

## API Use

The UI calls:

- `/health`
- `/schema/fertilizer-comp-keys`
- `/schema/solver-config`
- `/fertilizers`
- `/water-profiles`
- `/nutrient-solutions`
- `/recipes`
- `/molar-masses`
- `/calculate`
- `/solve`

The API base is the same origin as the served frontend.

## Browser State

The UI stores small workflow state in `localStorage`:

- Last calculated solution snapshot.
- Solver allowed fertilizer selections by context.
- Solver auto-apply preference.

Solver config is intentionally not restored from saved solution snapshots and
is not automatically applied from loaded recipes. The UI fetches the backend
schema from `/schema/solver-config`.

## Stable Contracts

Tests rely on these categories of frontend contracts:

- Workflow buttons with `data-shell-view`.
- Panels with `data-panel-anchor` and `data-testid`.
- Calculator, water, solver, and editor IDs used by `app.js`.
- Solver copy/apply controls.
- Summary tabs and output tables.
- Reduced solver config controls from `/schema/solver-config`.

Before changing IDs or panel names, search tests and `frontend/app.js`.

## Verification

```bash
python -m pytest tests/test_frontend_serving.py tests/test_frontend_recipe_wheel_shell.py -q
python -m pytest tests/test_frontend_solver_config_ui.py tests/test_frontend_allowed_fertilizers_ui.py -q
```

For visual work, also run the API and inspect `http://127.0.0.1:8000/` in a
browser.
