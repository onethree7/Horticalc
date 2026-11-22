# Architecture

Horticalc is a local desktop application with a browser-based interface and a
Python calculation core. The runtime has five boundaries:

1. static UI in `frontend/`;
2. same-origin FastAPI application in `api/app.py`;
3. calculation and data services in `src/horticalc/`;
4. Solver implementations in `src/horticalc/solver.py` and
   `src/horticalc/priority_solver.py`;
5. desktop launcher and packaging in `src/horticalc/launcher.py` and
   `scripts/packaging/`.

## Desktop startup

The launcher reserves a loopback listening socket before claiming the
single-instance lock and gives that socket directly to uvicorn. It waits for
`/health`, then opens a pywebview window at the local origin. Windows selects
WebView2; Linux selects GTK/WebKitGTK. The application does not open or control
an external browser during startup.

A second launch authenticates to the hidden activation endpoint using the
random token in the owner lock, restores the existing native window, and exits.
Closing that window stops uvicorn and removes the lock.

## Request flow

Calculator requests pass validated fertilizer doses and water data from the UI
through `POST /calculate` to `compute_solution()` in
`src/horticalc/core.py`. The core performs composition conversion, water
mixing, ion and balance calculations, EC, NPK metrics, and Sluijsmann without a
dependency on HTTP or the DOM.

Solver requests pass targets, allowed and fixed fertilizers, water, and model
configuration through `POST /solve`. The Solver builds the fertilizer
contribution problem, applies the selected optimization model, then calls the
same calculation core to report the achieved solution. Successful API solves
are recorded as canonical JSONL snapshots; history-write failures are non-fatal
to the solve.

## API boundary

The supported automation boundary contains health, calculation, Solver, and
their schemas as defined in [HTTP API](api.md). Other routes exist to support
the bundled UI's persistence and launcher lifecycle and are internal to the
desktop application. The launcher bootstraps an HttpOnly, same-site session
cookie from its random activation token. Internal data routes require that
cookie and reject requests carrying a foreign `Origin`; the supported
automation routes remain available to loopback clients without a desktop
session.

The request-body limit buffers and replays accepted body chunks. Once replay
is complete, further receive calls use the transport so response handling
observes the actual client connection lifetime.

The frontend uses native ES modules with no production bundler or
Python–JavaScript bridge. Feature controllers own their UI state; shared
transport, formatting, units, and storage helpers remain independent of the
feature DOM.

Clipboard exports share column alignment and fertilizer-table rendering in
`frontend/app/formatting.js`, quantity formatting in the unit service and the
clipboard transport in `frontend/app/notifications.js`. Sidebar ratio rows are
shared with Calculator's export. Stock preparation exports plain text through
this same path.

Stock preparation is a Calculator subview owned by `frontend/app/stocks.js`.
Calculator and Solver retain the accepted request alongside its result; changes
to calculation inputs invalidate dependent preparation output. The composition
root connects the controllers without cross-feature imports.

`src/horticalc/stock_solutions.py` scales the selected recipe using the existing
fertilizer definitions. It compares declared composition between different
products, preserving each manufacturer's formulation as one ingredient. The
same pair risks drive deterministic, best-effort tank suggestions and advisory
findings. Calcium/phosphorus, calcium/sulfate, carbonate and silicon risks guide
separation; magnesium/phosphorus prefers separation when a tank is available,
but remains advisory because it depends on pH and concentration. Trace-metal
contents alone do not trigger findings or separation suggestions. Liquid
products and products without composition need manual assignment. Existing
assignments are never overwritten by suggestions, and products that do not fit
remain open.

The planner has no filesystem or HTTP operations and does not alter Solver
objectives. The API validates input and returns the preparation plan. Stocks
retain reviewed material fingerprints until explicit reassessment. Export
readiness is calculated by the planner from assignments, capacity and pending
product changes; chemical guidance remains advisory. Batch-volume changes
refresh an open preparation view after Calculator accepts its scaled request,
using the existing request gate to discard superseded preparation responses.
Configured stock volumes and concentration factors stay unchanged. Stocks
use mineral-free RO/distilled preparation water. The existing core computes
the diluted result using an additive-volume estimate for displaced batch
water. It does not predict concentrate pH, solubility,
temperature-dependent stability or shelf life. Recipe attachments persist
settings and source-water context; derived output is recomputed.

The reading action opens both external articles in the system browser through
the desktop renderer's existing new-window handler. Text selection overlapping
the stock panel is copied as plain text so HTML form options are not exported.

## AppRoot and persistence

`app_root()` in `src/horticalc/paths.py` resolves to the repository root during
development and the executable directory in a packaged application.

```text
AppRoot/
  data/       shipped data
  recipes/    shipped recipes
  frontend/   static UI
  user/       preferences, overrides, profiles, and Solver history
  logs/       rotating launcher and server logs
```

Shipped resources are read-only defaults. User YAML files override same-named
shipped resources; fertilizer edits are stored as catalogue deltas. WebView
state lives in `user/webview/`, separate from Solver history and structured
profiles.

Preference updates serialize their read/merge/write operation within the API
process and replace the file atomically. A write failure preserves the previous
file. Changing history retention persists preferences before trimming history;
a trim failure is reported without rolling back the saved preference. The
frontend queues writes and reports failed operations without blocking later
updates.

The API owns validation and persistence. The core owns chemistry and
optimization inputs but not filesystem or HTTP presentation. The UI owns
display units, locale, navigation, and transient interaction state.

## Packaging boundary

PyInstaller produces an onedir application containing Python, Horticalc,
frontend assets, data, recipes, the portable README, and the license. Windows
adds an Inno Setup installer. Linux deliberately relies on the target system's
coherent GTK/WebKitGTK stack instead of bundling a partial renderer stack.

Build and release gates are documented in [Releases](../RELEASE.md); the
authoritative implementation is `scripts/packaging/` and
`.github/workflows/release.yml`.
