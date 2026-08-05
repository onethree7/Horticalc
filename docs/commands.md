# Commands

Status: `operation-guide`.

Single source of truth for all commands. The other docs link here instead of duplicating command blocks.

## Install And Run From Source

Linux (bash):

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m horticalc.launcher
```

Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m horticalc.launcher
```

On Ubuntu, Debian, or Linux Mint install the GTK/WebKitGTK runtime before
starting Horticalc:

```bash
sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1
```

On Fedora:

```bash
sudo dnf install -y webkit2gtk4.1
```

Set `HORTICALC_NO_GUI=1` to start the server without creating a desktop window.

## Run The API Server Directly

```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

## CLI Recipes

The CLI entry point is `python -m horticalc` from `src/horticalc/__main__.py`.

Print the canonical version:

```bash
python -m horticalc --version
```

Calculate a recipe:

```bash
python -m horticalc recipes/reference_calcinit_1g_per_l.yml --pretty
python -m horticalc recipes/reference_calcinit_epso_top_1g_per_l_each.yml --pretty
python -m horticalc recipes/reference_agrolution_313_1g_per_l.yml --out user/exports/reference_output.json --pretty
```

Solve a target recipe:

```bash
python -m horticalc solve user/recipes/<solver-recipe>.yml --pretty
python -m horticalc solve user/recipes/<solver-recipe>.yml --nitrogen-objective-mode n_forms_only --pretty
python -m horticalc solve user/recipes/<solver-recipe>.yml --solver-config relative_weighting=true
python -m horticalc solve user/recipes/<solver-recipe>.yml --solver-config solver_model=hierarchical --solver-config 'target_priorities={"N_total":{"under":1,"over":1},"Ca":{"under":2,"over":3}}'
```

Global options for both modes:

- `--load-recipe <file>`: load a recipe file explicitly.
- `--load-water <file>`: load a water profile.
- `--out <file>`: write the JSON result to a file.
- `--pretty`: pretty-print the JSON output.
- `--solver-config KEY=VALUE ...`: override any solver config key (solve mode only).

## Run Tests

Standard product suite:

```bash
python scripts/test.py
```

The entrypoint creates the Python environment as needed, installs pinned Python
and Node development tooling when missing, then runs Ruff formatting/linting,
ESLint, Stylelint, Node unit tests, Playwright behavior tests, and the complete
Pytest suite.

Focused examples:

```bash
python scripts/test.py --pytest-only tests/test_ec.py -q
python scripts/test.py --pytest-only tests/test_calculation_chemistry.py tests/test_solver_weighting.py -q
python scripts/test.py --pytest-only tests/test_frontend_serving.py tests/test_frontend_module_architecture.py -q
```

`--pytest-only` prepares Python test dependencies but skips Ruff, npm, frontend
lint, and Node unit tests. Remaining arguments are passed to Pytest.

Run only the browser workflow smoke test:

```bash
python scripts/test.py --pytest-only tests/test_frontend_browser_smoke.py -q
```

## Release Build (PyInstaller)

Install PyInstaller with the release constraints:

```bash
PIP_CONSTRAINT=constraints-release.txt python -m pip install . pyinstaller
```

Then run the platform build script:

```bash
chmod +x scripts/packaging/build_linux.sh
./scripts/packaging/build_linux.sh
```

Windows:

```powershell
.\scripts\packaging\build_windows.ps1
```

## Release Verification

Compare a checksum file against the downloaded archive.

Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 .\horticalc-vX.Y.Z-windows.zip
Get-Content .\horticalc-vX.Y.Z-windows.zip.sha256
```

Linux:

```bash
sha256sum -c horticalc-vX.Y.Z-linux.tar.gz.sha256
```

With the GitHub CLI:

```bash
gh attestation verify horticalc-vX.Y.Z-windows.zip --repo onethree7/Horticalc
gh attestation verify horticalc-vX.Y.Z-linux.tar.gz --repo onethree7/Horticalc
```

## Docs Anti-Drift

```bash
rg -n "TODO|UNDECIDED|Task [0-9]|Implementation Roadmap" docs README.md --glob "!**/commands.md"
```
