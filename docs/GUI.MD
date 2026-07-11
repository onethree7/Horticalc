# GUI

Status: current-state.

The frontend is a static Vanilla JS app in `frontend/`. It is served by
FastAPI from the same origin as the API.

## Files

- `frontend/index.html`: DOM structure, workflow panels, stable IDs.
- `frontend/app/`: modular JavaScript loaded in dependency order.
  - `frontend/app/app.js`: entry point and `init()` wiring.
  - `frontend/app/state.js`: top-level shared state and constants.
  - `frontend/app/api.js`: fetch/persistence helpers and payload builders.
  - `frontend/app/units.js`: unit conversion and dose formatting.
  - `frontend/app/dom.js`: shared DOM helpers and table rendering.
  - `frontend/app/calculator.js`: selection/calculator tables, scaling, and calculator clipboard.
  - `frontend/app/water.js`: water table, profiles, and water summary.
  - `frontend/app/solver.js`: solver targets, allowed picker, fixed doses, results, and solver clipboard.
  - `frontend/app/editor.js`: fertilizer editor rendering, sorting, and save/load.
  - `frontend/app/shell.js`: workflow navigation and heavy view lifecycle.
  - `frontend/app/i18n-controls.js`: theme/language controls and `refreshLocalizedUi`.
  - `frontend/app/notifications.js`: status, error, and copy status helpers.
- `frontend/request_gate.js`: executable latest-request ownership state.
- `frontend/i18n/`: frontend-only translation catalogs and runtime.
- `frontend/styles.css`: app frame layout, tables, responsive rules.

## App Areas

The active navigation has four user-facing areas:

- `DUENGER-EDITOR`: fertilizer CSV editing, liquid checkbox, density/factor
  column, search, and add/delete rows.
- `WASSERWERTE`: water profiles, osmosis percent, helper conversions, mg/L or mmol/L display.
- `RECHNER`: recipe profiles, row-specific fertilizer doses, calculation output, details.
- `SOLVER`: target values, compact searchable allowed-fertilizer picker,
  optional fixed doses, solver config, solve result, and calculator handoff.

The workflow menu is the single owner of visible area navigation; it directly
selects the matching calculator, water, solver, or fertilizer-editor panel.
The large fertilizer-editor and Solver picker tables are mounted only while
their workflow is active and are removed from the DOM when another workflow is
selected. Their JavaScript state remains intact across navigation.

The `Konfiguration` card in `frontend/index.html` contains the global batch
volume input with an L, US gal, Imp gal, or m³ selector, separate solid/liquid
dose-unit selectors, a `Design` selector, and a `Sprache` selector.
`frontend/app/api.js` fetches unit definitions from `/schema/units`,
`frontend/app/units.js` keeps the working values in canonical liters plus
g-for-solids/mL-for-liquids, and `frontend/app/i18n-controls.js` applies the
selected theme to `document.body.dataset.theme`. Theme, the user's
default batch liters, volume/dose display units, Solver defaults, and the last directly loaded water
profile are written through `/preferences` to `user/preferences.json`, because
launcher-managed browser profiles are temporary. `frontend/i18n/runtime.js` stores the
selected language under `horticalc.locale`, updates `document.documentElement.lang`,
and applies `data-i18n` attributes from the static catalogs. `frontend/styles.css`
defines the available visual themes: Horticalc Dark, Horticalc Light, High
Contrast, Soil, VT Green, and Blue Matrix. Language remains browser-local
presentation state and is not sent to recipes or solver payloads.

Preferences supply startup defaults. An explicitly loaded recipe overrides its
liters and any non-empty `solver_config` for the current working state without
rewriting the user's defaults. A water profile loaded with the water-profile
controls becomes the next startup profile; a water profile loaded indirectly
from a recipe does not. Missing remembered profiles fall back to `default.yml`.

Preferences and independent startup resources begin loading concurrently. If
any required catalog or schema fails, the System indicator shows `Data
incomplete` instead of
claiming that the complete UI is ready. Calculation, Solver, recipe-profile,
and water-profile requests use latest-request ownership: a slower response from
an older edit or selection is discarded instead of overwriting newer UI state.
The request gate is exercised directly with Node's built-in runtime in the
standard test suite; no npm package is required.

The workflow menu and primary workspace headings reuse one inline SVG icon
sprite from `frontend/index.html`. Its seven reduced scientific monoline
symbols use `currentColor` for primary strokes and `--app-teal` for restrained
accents, so the same paths adapt to every visual theme. Workflow icons retain small
step-number badges, while translated heading text remains separate from the
decorative SVG markup. The fertilizer-components symbol is a connected
five-atom molecule, and the ion-balance symbol uses a conventional beam scale
with hanging pans. The other primary workflow
symbols are literal fertilizer bags, a tap-water faucet, a calculator, and a
target reticle containing one leaf.

The calculator fertilizer-selection table labels the Boolean physical state as
`Typ` and renders it as localized solid/liquid text. The adjacent
`weight_factor` column is presented as `Dichte [g/mL] / Faktor`; liquid rows
show density with `g/mL`, unit-factor solid rows show `×`, and ordinary solid
rows show an em dash.

In the fertilizer editor, the sticky `Liquid` and `Dichte [g/mL] / Faktor` columns use fixed
compact widths. The sticky fertilizer-name column starts at `18rem` and has a
drag handle on its right edge; resizing is limited to 180-640 pixels and only
affects the editor table. The four-column sticky base block uses theme-specific
opaque row colors so horizontally scrolled nutrient values cannot show through.
The editor keeps the complete catalog in one continuous table while it is
active. Its debounced name search toggles existing row visibility instead of
rebuilding thousands of inputs for every typed character.

The frontend selects the first supported language from `navigator.languages`
on first use and falls back to English. An explicit language selection is
stored in both browser storage and `user/preferences.json`; the saved
preference overrides browser detection on later loads. German, English, Dutch,
Spanish, and Simplified Chinese catalogs live in `frontend/i18n/`. Visible
labels, placeholders, ARIA labels, status messages, empty states, and clipboard
section labels use translation keys. Data contracts such as API route names,
JSON keys, CSV fields like `Düngername` and `Liquid`, element symbols, solver
config keys, and units remain literal and are not translated.

The live sidebar in `frontend/index.html` is populated by `frontend/app/calculator.js`
(render) and `frontend/app/shell.js` (live-result timestamp). It displays the
latest calculation's NPK totals, compact P-normalized and NPK-only bubbles,
the ion-based `Ca:Mg` ratio, centered EC solution/water values, and compact
mg/L ion-ratio chips from `npk_metrics.npk_ratios_ion`.

Configuration keeps the calculation-relevant batch amount visible. Persistent
appearance, language, and display-unit preferences live in a native, collapsed
`details.rail-settings` disclosure. Its summary shows the active volume, solid,
and liquid unit symbols so users can read the current unit context without
opening the controls.

The solver allowed-fertilizer picker in `frontend/index.html` is rendered by
`frontend/app/solver.js` as a compact searchable checkbox table using the same
`grid grid--form` rendering as the surrounding Solver target and result tables.
The equal-width action controls can merge the calculator fertilizer selection,
select all fertilizers, hide inactive rows for a focused selected-only view, or
clear the selection. It stores allowed fertilizer selections by context in
`localStorage` and does not write fertilizer favorites or defaults to CSV.

The Solver view in `frontend/index.html` places the editable Zielwerte table
next to the Solver target/achieved/delta result table in the top comparison
grid. The allowed-fertilizer picker sits below it on the left, and
Fertilizer amounts sit on the right. Before a solve result exists, Solver Results
shows an instruction hint instead of the empty result table.

Solver fixed doses live in the collapsed `solverOverrides` details panel and
use each fertilizer's selected display unit.
`frontend/app/solver.js` opens the panel when an override value is active and keeps
zero-override use out of the main flow.

The solver can automatically apply a successful solve result to the calculator.
The `solverAutoApply` checkbox lives in the collapsed advanced Solver options,
defaults on, stores its preference in `localStorage`, and uses the same
`applyRecipe()` calculator path as loaded recipes so the live sidebar updates
after the recalculation. The primary Solver and calculator calculate buttons
live in their respective panel headers; the Solver clipboard and explicit
calculator-view actions remain below the result workbench.

The solver result table always shows the standard nutrient rows after a solve;
rows that were not active targets are muted so collateral nutrient changes are
visible without implying they were optimized objectives. The fertilizer result
table lets long product names wrap while keeping the `Menge` column compact.
Each value includes its explicit mass or liquid-volume unit. Dose formatting
uses up to eight decimals for small converted quantities so unit switching does
not display a positive dose as zero. The same conversion and formatting path is
used by Solver results, the Solver clipboard export, fixed-dose controls, and
calculator inputs.

The solver clipboard export in `frontend/app/solver.js` includes the batch volume in
the selected display unit, osmosis percent, fertilizer doses with a separate
row-specific unit column, NPK metrics, EC,
Solver target/achieved/delta values, and ion mg/L values. It uses compact space-aligned columns for
monospace copy/paste code blocks instead of tab-separated columns.

The calculator exports its current recipe and complete result report in the
same format; input changes disable copying until recalculation finishes.

The solver advanced config lives at the bottom of the Solver panel in
`frontend/index.html` and includes the urea representation control plus the
solver-configuration controls wired in `frontend/app/app.js` (with logic in
`frontend/app/solver.js`). The latter are backed by `/schema/solver-config`. The visible `N-total statt N-Formen` checkbox writes
`solver_config.nitrogen_objective_mode`: checked sends `n_total_only`,
unchecked sends `n_forms_only`.
The explicit `Reset solver configuration` button in the same advanced
panel restores every schema default and persists an empty `solver_config`,
removing previous preference overrides.

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
- Selected frontend language.

`user/preferences.json` stores the selected visual theme, default batch liters,
volume and dose display units, Solver defaults, and last directly loaded water profile.

Solver config is not restored from saved solution snapshots. Startup defaults
come from preferences, while a non-empty config in an explicitly loaded recipe
overrides the active controls. The UI fetches the backend schema from
`/schema/solver-config`. Use `Reset solver configuration` inside
`Erweitert` to discard non-default preference values.

## Stable Contracts

Tests rely on these categories of frontend contracts:

- Workflow buttons with `data-shell-view`.
- Panels with `data-panel-anchor` and `data-testid`.
- Calculator, water, solver, and editor IDs used by the `frontend/app/` modules.
- Solver copy/apply controls.
- Summary tabs and output tables.
- Reduced solver config controls from `/schema/solver-config`.
- Frontend i18n catalogs with matching keys for `de`, `en`, `nl`, `es`, and `zh`.

Before changing IDs or panel names, search tests and the `frontend/app/` modules.

## Verification

```bash
python scripts/test.py tests/test_frontend_serving.py tests/test_frontend_recipe_wheel_shell.py -q
python scripts/test.py tests/test_frontend_solver_config_ui.py tests/test_frontend_allowed_fertilizers_ui.py -q
```

For visual work, also run the API and inspect `http://127.0.0.1:8000/` in a
browser.
