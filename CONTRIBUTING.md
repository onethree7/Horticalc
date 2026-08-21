# Contributing

Horticalc uses Python for the calculation core, local API, and desktop host.
The frontend is static JavaScript and CSS with Node-based development checks.

## Set up from source

Source installs support Python 3.10 through 3.13. The complete test suite also
requires Node.js and npm.

Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m horticalc.launcher
```

Install GTK/WebKitGTK first using the distribution command in
[README.md](README.md#system-requirements-and-startup-help).

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m horticalc.launcher
```

No environment activation is required when using the explicit `.venv`
interpreter shown above. Set `HORTICALC_NO_GUI=1` to run the launcher without a
desktop window. Direct API commands are in [HTTP API](docs/api.md#run-locally).

## Make a change

Use **Plan → Edit → Verify**. Keep the change focused, prefer existing patterns,
and check for a nested `AGENTS.md` before editing a subdirectory.

Runtime sources of truth are:

- `src/horticalc/` for calculation, units, solver, paths, and launcher behavior;
- `api/app.py` for HTTP models and routes;
- `frontend/` for workflows, labels, and presentation;
- `scripts/` and `.github/workflows/` for tests, packaging, and releases;
- `tests/` for enforced behavior.

Do not add compatibility aliases for obsolete internal identifiers. Replace
them and migrate affected local persisted files when a code change requires it.

## Run tests

Run the repository entrypoint, not bare Pytest:

```bash
python scripts/test.py
```

The wrapper intentionally starts with an available system Python, then runs all
project tools inside `.venv`. It installs missing declared Python dependencies
and runs `npm ci` when frontend packages are absent. Use `py scripts/test.py`
on Windows if `python` is not registered as a command.

The full suite requires an installed Chrome or Chromium for the Playwright
workflow smoke test. Set `HORTICALC_BROWSER_PATH` when the browser is outside a
standard location. The repository does not declare a separate Node version;
use a maintained Node.js release with npm.

The entrypoint runs Ruff format and lint checks, ESLint, Stylelint, frontend
unit tests, the browser smoke test, and the complete Pytest suite. For a focused
Pytest run:

```bash
python scripts/test.py --pytest-only tests/test_ec.py -q
```

Frontend workflow changes must pass the relevant Node tests and the Playwright
browser smoke test included in the standard suite.

## Update documentation

Write current behavior, not plans or implementation history. Keep a fact in the
smallest document that owns the task:

- install and first run: `README.md`;
- source development and tests: `CONTRIBUTING.md`;
- packaging and release verification: `RELEASE.md`;
- user workflows: `docs/usage.md`;
- CLI and supported HTTP contracts: `docs/cli.md` and `docs/api.md`;
- data, solver, EC, and runtime design: their matching page under `docs/`.

Run the focused documentation checks after changing Markdown:

```bash
python scripts/test.py --pytest-only tests/test_documentation.py tests/test_project_metadata.py -q
```
