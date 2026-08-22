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
an external browser.

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

The frontend uses native ES modules with no production bundler or
Python–JavaScript bridge. Feature controllers own their UI state; shared
transport, formatting, units, and storage helpers remain independent of the
feature DOM.

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
