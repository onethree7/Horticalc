# GUI

Status: `current-state`.

The frontend is a static Vanilla JS app in `frontend/`. It is served by FastAPI from the same origin as the API.

## Files

- `frontend/index.html`: DOM structure, workflow panels, stable IDs, icon sprite, and live sidebar.
- `frontend/app/main.js`: single ES-module entry point, startup, and controller composition.
- `frontend/app/constants.js`: immutable UI defaults, formatters, and presentation schemas.
- `frontend/app/api.js`: HTTP transport and serialized preference writes; it does not access the DOM or render.
- `frontend/app/units.js`: stateful unit service with canonical liters and dose conversion.
- `frontend/app/dom.js`: shared DOM helpers and table rendering.
- `frontend/app/calculator.js`: calculator controller, owned rows/results, scaling, and clipboard.
- `frontend/app/water.js`: water controller, owned water/profile state, and summaries.
- `frontend/app/solver.js`: solver controller, owned targets/selections/results, and clipboard.
- `frontend/app/editor.js`: editor controller, owned rows, sorting, and save/load.
- `frontend/app/profiles.js`: recipe and nutrient-target profile controls.
- `frontend/app/settings.js`: batch, unit, theme, and language controls.
- `frontend/app/shell.js`: workflow navigation and view lifecycle controller.
- `frontend/app/notifications.js`: status, error, and copy status helpers.
- `frontend/app/formatting.js`, `frontend/app/scaling.js`, `frontend/app/storage.js`: pure shared helpers.
- `frontend/request_gate.js`: latest-request ownership state.
- `frontend/i18n/`: frontend-only translation catalogs and runtime.
- `frontend/styles.css`: app frame layout, tables, responsive rules, and themes.

`frontend/index.html` loads only `frontend/app/main.js` as a native ES module. Feature modules export controller factories, own their mutable state and event bindings, and do not import other feature controllers. `main.js` injects services and coordinates the small number of cross-feature operations. This keeps the dependency graph acyclic without a production build step or application globals.

## App Areas And Workflow Navigation

The workflow menu has four user-facing areas:

- **Fertilizer editor**: inspect, search, and edit fertilizer products and composition.
- **Water values**: load, edit, save, and mix water profiles with reverse-osmosis water.
- **Calculator**: build recipes manually, calculate, and inspect results.
- **Solver**: enter targets, select allowed fertilizers, and solve for doses.

The workflow menu is the single owner of visible area navigation. The large editor and solver picker tables are mounted only while their workflow is active and removed from the DOM when another workflow is selected. Their JavaScript state remains intact.

## Preferences, Language, Themes, Units

The `Configuration` card in `frontend/index.html` contains the global batch volume input, volume unit selector, solid dose unit selector, liquid dose unit selector, theme selector, and language selector. Theme options are defined in `api/app.py` (`THEME_OPTIONS`). Locale options are `de`, `en`, `nl`, `es`, `zh` (`LOCALE_OPTIONS` in `api/app.py`).

`frontend/app/api.js` fetches unit definitions from `/schema/units`. `frontend/app/units.js` keeps working values in canonical liters and g-for-solids/mL-for-liquids. `frontend/app/settings.js` applies the selected theme to `document.body.dataset.theme`. The selected language is stored in `localStorage` and `user/preferences.json` so it overrides browser detection on later loads. Data contracts such as API route names, JSON keys, CSV fields, element symbols, solver config keys, and units remain literal and are not translated.

Preferences supply startup defaults. An explicitly loaded recipe overrides its liters and any non-empty `solver_config` for the current working state without rewriting the user's defaults. A water profile loaded with the water-profile controls becomes the next startup profile; a water profile loaded indirectly from a recipe does not.

## Browser State And `localStorage`

The UI stores small workflow state in `localStorage`:

- last calculated solution snapshot,
- solver allowed-fertilizer selections by context,
- solver auto-apply preference,
- selected frontend language.

`user/preferences.json` stores theme, default batch liters, volume and dose display units, solver defaults, and last directly loaded water profile. Solver config is not restored from saved solution snapshots.

## API Calls From The Frontend

The UI calls:

- `/health`
- `/schema/fertilizer-comp-keys`
- `/schema/solver-config`
- `/schema/units`
- `/fertilizers`
- `/water-profiles`
- `/nutrient-solutions`
- `/recipes`
- `/molar-masses`
- `/calculate`
- `/solve`

The API base is the same origin as the served frontend.

## Stable Contracts For Tests

Tests rely on:

- workflow buttons with `data-shell-view`,
- panels with `data-panel-anchor` and `data-testid`,
- calculator, water, solver, and editor IDs used by `frontend/app/`,
- solver copy/apply controls,
- summary tabs and output tables,
- reduced solver config controls from `/schema/solver-config`,
- frontend i18n catalogs with matching keys for `de`, `en`, `nl`, `es`, and `zh`.

Before changing IDs or panel names, search tests and the `frontend/app/` modules.

`tests/test_frontend_module_architecture.py` protects the module dependency rules. `tests/test_frontend_browser_smoke.py` runs the main calculator, water, editor, and solver workflows in Chrome through `scripts/frontend_smoke.cjs` and treats browser errors or application dialogs as failures.
