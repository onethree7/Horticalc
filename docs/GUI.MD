# GUI

Status: current-state.

The frontend is a static Vanilla JS app in `frontend/`. It is served by
FastAPI from the same origin as the API.

## Files

- `frontend/index.html`: DOM structure, workflow panels, stable IDs.
- `frontend/app.js`: state, API calls, rendering, workflow navigation.
- `frontend/request_gate.js`: executable latest-request ownership state.
- `frontend/i18n/`: frontend-only translation catalogs and runtime.
- `frontend/styles.css`: app frame layout, tables, responsive rules.

## App Areas

The active navigation has four user-facing areas:

- `DUENGER-EDITOR`: fertilizer CSV editing, liquid checkbox, mass-factor column
  labelled as italic `m [g]`, search, and add/delete rows.
- `WASSERWERTE`: water profiles, osmosis percent, helper conversions, mg/L or mmol/L display.
- `RECHNER`: recipe profiles, fertilizer grams, calculation output, details.
- `SOLVER`: target values, compact searchable allowed-fertilizer picker,
  optional override grams, solver config, solve result, and calculator handoff.

The workflow menu is the single owner of visible area navigation; it directly
selects the matching calculator, water, solver, or fertilizer-editor panel.
The large fertilizer-editor and Solver picker tables are mounted only while
their workflow is active and are removed from the DOM when another workflow is
selected. Their JavaScript state remains intact across navigation.

The `Konfiguration` card in `frontend/index.html` contains the global batch
liters input, a `Design` selector, and a `Sprache` selector. `frontend/app.js`
applies the selected theme to `document.body.dataset.theme`. Theme, the user's
default batch liters, Solver defaults, and the last directly loaded water
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
`weight_factor` column is presented as `Masse`.

In the fertilizer editor, the sticky `Liquid` and `m [g]` columns use fixed
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

The live sidebar in `frontend/index.html` and `frontend/app.js` displays the
latest calculation's NPK totals, compact P-normalized and NPK-only bubbles,
the ion-based `Ca:Mg` ratio, centered EC solution/water values, and compact
mg/L ion-ratio chips from `npk_metrics.npk_ratios_ion`.

The solver allowed-fertilizer picker in `frontend/index.html` is rendered by
`frontend/app.js` as a compact searchable checkbox table using the same
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

Solver override grams live in the collapsed `solverOverrides` details panel.
`frontend/app.js` opens the panel when an override value is active and keeps
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
table lets long product names wrap while keeping the `Gramm/ml` dose column
compact and right-aligned. Solid doses are grams and liquid doses are
milliliters. Doses below `0.01` use up to four decimal places in Solver results,
the Solver clipboard export, and calculator inputs so a positive trace dose is
not displayed as zero. Values below the display precision are labelled
`<0.0001` in read-only Solver output while calculator inputs retain the numeric
value.

The solver clipboard export in `frontend/app.js` includes the batch liters,
osmosis percent, fertilizer doses in grams or milliliters, NPK metrics, EC,
Solver target/achieved/delta values, and ion mg/L values. It uses compact space-aligned columns for
monospace copy/paste code blocks instead of tab-separated columns.

The solver advanced config lives at the bottom of the Solver panel in
`frontend/index.html`, includes the urea and phosphate solver options, is backed
by `/schema/solver-config`, and is wired in `frontend/app.js`. The visible
`N-total statt N-Formen` checkbox writes
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
Solver defaults, and last directly loaded water profile.

Solver config is not restored from saved solution snapshots. Startup defaults
come from preferences, while a non-empty config in an explicitly loaded recipe
overrides the active controls. The UI fetches the backend schema from
`/schema/solver-config`. Use `Reset solver configuration` inside
`Erweitert` to discard non-default preference values.

## Stable Contracts

Tests rely on these categories of frontend contracts:

- Workflow buttons with `data-shell-view`.
- Panels with `data-panel-anchor` and `data-testid`.
- Calculator, water, solver, and editor IDs used by `app.js`.
- Solver copy/apply controls.
- Summary tabs and output tables.
- Reduced solver config controls from `/schema/solver-config`.
- Frontend i18n catalogs with matching keys for `de`, `en`, `nl`, `es`, and `zh`.

Before changing IDs or panel names, search tests and `frontend/app.js`.

## Verification

```bash
python scripts/test.py tests/test_frontend_serving.py tests/test_frontend_recipe_wheel_shell.py -q
python scripts/test.py tests/test_frontend_solver_config_ui.py tests/test_frontend_allowed_fertilizers_ui.py -q
```

For visual work, also run the API and inspect `http://127.0.0.1:8000/` in a
browser.
