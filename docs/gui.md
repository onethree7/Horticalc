# GUI

Status: `current-state`.

The frontend is a static Vanilla JS app in `frontend/`. It is served by FastAPI
from the same origin as the API and displayed in a native pywebview window.
pywebview is only the window host: the frontend does not use a Python-JavaScript
bridge. WebView2 is selected on Windows and GTK/WebKitGTK on Linux.

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
- `frontend/app/solver_config.js`: solver schema normalization and bounded control values.
- `frontend/app/solver_payload.js`: solve/clipboard payload formatting and result-key ordering.
- `frontend/app/solver_rendering.js`: stateless solver result-table rendering.
- `frontend/app/solver_printable.js`: shared pure formatting for live and historical Solver output.
- `frontend/app/history.js`: Solver-history summaries, lazy detail preview, dialog, copy, and restore controller.
- `frontend/app/editor.js`: editor controller, owned rows, sorting, and save/load.
- `frontend/app/profiles.js`: recipe and nutrient-target profile controls.
- `frontend/app/settings.js`: batch, unit, theme, and language controls.
- `frontend/app/shell.js`: workflow navigation and view lifecycle controller.
- `frontend/app/notifications.js`: status, error, and copy status helpers.
- `frontend/app/formatting.js`, `frontend/app/scaling.js`, `frontend/app/storage.js`: pure shared helpers.
- `frontend/request_gate.js`: latest-request ownership state.
- `frontend/i18n/`: frontend-only translation catalogs and runtime.
- `frontend/styles/`: ordered base, theme-token, shell, feature-component, and responsive stylesheets.

`frontend/index.html` loads only `frontend/app/main.js` as a native ES module. Feature modules export controller factories, own their mutable state and event bindings, and do not import other feature controllers. `main.js` injects services and coordinates the small number of cross-feature operations. This keeps the dependency graph acyclic without a production build step or application globals.

## App Areas And Workflow Navigation

The workflow menu has four user-facing areas:

- **Fertilizer editor**: inspect, search, and edit fertilizer products and composition.
- **Water analysis**: load, edit, save, and mix water profiles with reverse-osmosis water.
- **Calculator**: build recipes manually, calculate, and inspect results.
- **Solver**: enter targets, select allowed fertilizers, and solve for doses.

The collapsible **Solver history** Sidebar card is not a fifth workflow. It
shows pinned rows first and then compact newest-first rows in its own scroll area. A
separate star button pins a run without opening its detail; pinned runs are
excluded from retention and survive the normal clear action. Hover or keyboard focus
opens a short, non-scrollable and non-interactive preview without an additional
native tooltip; click opens the full scrollable dialog on desktop and touch
layouts. Detail records load lazily and are cached in the current page.
Copy and preview use the same formatter as current Solver clipboard output.
Restoring preflights fertilizer names, then replaces liters, embedded water,
RO-water proportion, targets, allowed fertilizers, fixed doses, urea mode, and Solver
configuration. It clears the current result and does not run the Solver.

Recipe and Solver-target selectors share a small favorite button. Favorites
are stored independently for both profile kinds, prefixed with a star in the
native select, and sorted ahead of otherwise unchanged list order. Favoriting
does not modify the underlying recipe or target YAML.

The Solver model selector is visible above the workbench rather than hidden in
the advanced section. `NNLS + tuning (standard)` is the production default
and is persisted as `nnls_tuning`.
`Mass balance (mg/L², experimental)` and `Prioritized targets (staged,
experimental)` are opt-in models. The latter exposes separate **Too little**
and **Too much** priority selectors for every target. Tuning controls are
disabled for both experimental models. A product with
`SolverMaxDosePerL=0` is excluded from variable dosing but remains available
for an explicit fixed amount. The result header and copied output identify the
model that actually ran, including any experimental label. The selection is
stored in `user/preferences.json` through the normal serialized preference
write.

Directional priority values are `1 Must`, `2 Important`, `3 Normal`,
`4 Flexible`, and `0 Report only`. Priority `1` is solved first; later tiers
cannot worsen a completed earlier tier. These selectors define ordering, not
numeric weights or concentration limits. Every omitted user-selectable
direction defaults to `3`; no element-specific priority is built into the UI.
`Na` and `Cl` remain disabled report-only rows. Results show the effective
`↓under` and `↑over` levels beside each target, and copied output includes the
same audit label. Setting both directions to `0` produces a visibly muted
report-only row; setting every active direction to `0` produces a validation
error.

The obsolete **Ignore/Egal** control is not rendered. Existing
`solver_config.ignored_elements` values are migrated in memory to priority `0`
in both directions and the next GUI persistence writes the canonical
`target_priorities` mapping.

The workflow menu is the single owner of visible area navigation. The large editor and solver picker tables are mounted only while their workflow is active and removed from the DOM when another workflow is selected. Their JavaScript state remains intact.

Target profiles normally store only nutrient targets. In Solver mode,
**Save/load Solver setup** additionally stores the batch volume, selected water
profile and RO-water proportion, allowed fertilizers, fixed amounts, urea mode, and
Solver configuration. When the option is enabled while loading such a profile,
Horticalc preflights its referenced water and fertilizer names, then replaces
the complete saved setup. When it is disabled, only the nutrient targets are
loaded and the current Solver setup remains unchanged. A missing
dependency leaves the current state unchanged and produces an explicit error.
Profiles without setup change only the targets; profiles containing
only `solver_config` apply it only when the option is enabled. Active fixed amounts produce a
visible warning and confirmation when the setup option is off. Saving as a
fertilizer recipe remains an output operation and does not retain Solver
constraints. Profile replacement is confirmed only after the API identifies
the effective canonical filename; this also prevents two different visible
names from silently colliding after filename sanitization. Source:
`frontend/app/profiles.js`, `frontend/app/main.js`, `frontend/app/api.js`, and
`frontend/app/solver.js`.

The profile Delete button is enabled only for user-saved recipes and target
profiles. Deletion requires confirmation. Shipped profiles remain protected;
deleting a same-named user override exposes the shipped profile again.

## Preferences, Language, Themes, Units

The `Configuration` card in `frontend/index.html` contains the global batch volume input, volume unit selector, solid dose unit selector, liquid dose unit selector, theme selector, language selector, Solver-history limit, and confirmed clear action. The history limit is `0..10000`, defaults to `1000`, counts only unpinned runs, and `0` disables normal logging while retaining pins. The clear action likewise removes only unpinned runs. Theme and locale options are defined once in `frontend/preferences.json`, exposed by `/schema/preferences`, and rendered into the selectors by `frontend/app/settings.js`; the API validates the same asset. Themes are styled through semantic tokens in `frontend/styles/themes.css`. In addition to the original themes, the selector offers Solarized Light, Dracula, Gruvbox Dark, Catppuccin Mocha, Monokai Classic, Windows 95, and Amber CRT. The retro skins also alter shared typography, corner, depth, and screen-effect tokens; they do not own component selectors. Amber CRT keeps a deliberately faint scanline layer. Disabled controls, hints, and inactive Solver rows use theme-aware contrast tokens.

`frontend/app/api.js` fetches unit definitions from `/schema/units`. `frontend/app/units.js` keeps working values in canonical liters and g-for-solids/mL-for-liquids. `frontend/app/settings.js` applies the selected theme to `document.body.dataset.theme`. The selected language is stored in `localStorage` and `user/preferences.json` so it overrides browser detection on later loads. Data contracts such as API route names, JSON keys, CSV fields, element symbols, solver config keys, and units remain literal and are not translated.

Preferences supply startup defaults. An explicitly loaded recipe overrides its liters and any non-empty `solver_config` for the current working state without rewriting the user's defaults. A target profile restores optional Solver fields only when they are present and **Save/load Solver setup** is enabled; otherwise it changes only the targets. A water profile loaded with the water-profile controls becomes the next startup profile; a water profile loaded indirectly from a recipe or target profile does not.

## WebView State And `localStorage`

The UI stores small workflow state in `localStorage`:

- last calculated solution snapshot,
- solver allowed-fertilizer selections by context,
- solver auto-apply preference,
- selected frontend language.

`user/preferences.json` stores theme, default batch liters, volume and dose display units, solver defaults, Solver-history retention, recipe and target-profile favorites, and last directly loaded water profile. Full Solver history and its pin metadata live in portable `user/solver_history.jsonl`, not `localStorage`. Solver config is not restored from saved solution snapshots.

The WebView storage root is `user/webview/`. External links, downloads, file
URLs, and remote debugging are disabled by the desktop host. API responses use
a same-origin Content Security Policy and reject unexpected Host headers.

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
- `/solver-history`

The API base is the same origin as the served frontend.

## Stable Contracts For Tests

Tests rely on:

- workflow buttons with `data-shell-view`,
- panels with `data-panel-anchor` and `data-testid`,
- calculator, water, solver, and editor IDs used by `frontend/app/`,
- solver copy/apply controls,
- summary tabs and output tables,
- reduced solver config controls from `/schema/solver-config`,
- per-element Solver directional priorities and their visible result labels,
- frontend i18n catalogs with matching keys for `de`, `en`, `nl`, `es`, and `zh`.

Before changing IDs or panel names, search tests and the `frontend/app/` modules.

`tests/test_frontend_module_architecture.py` protects the module dependency
rules. Node tests cover formatting, scaling, storage, request gating, solver
config normalization, and payload formatting. The Playwright smoke test runs
calculator, water/profile, editor, solver, theme, unit, keyboard, responsive,
and stale-response behavior in Chrome.
