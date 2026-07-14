# Commands

Status: `operation-guide`.

Single source of truth for all commands. The other docs link here instead of duplicating command blocks.

## Install And Run From Source

Linux/macOS (bash):

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

Set `HORTICALC_NO_BROWSER=1` to start the server without opening a browser.

## Run The API Server Directly

```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

## CLI Recipes

The CLI entry point is `python -m horticalc` from `src/horticalc/__main__.py`.

Calculate a recipe:

```bash
python -m horticalc recipes/golden.yml --pretty
python -m horticalc recipes/golden.yml --load-water 65936 --pretty
python -m horticalc recipes/golden.yml --out solutions/golden_output.json --pretty
```

Solve a target recipe:

```bash
python -m horticalc solve recipes/solve_golden.yml --pretty
python -m horticalc solve recipes/solve_golden.yml --nitrogen-objective-mode n_forms_only --pretty
python -m horticalc solve recipes/solve_golden.yml --solver-config relative_weighting=true
```

Global options for both modes:

- `--load-recipe <file>`: load a recipe file explicitly.
- `--load-water <file>`: load a water profile.
- `--out <file>`: write the JSON result to a file.
- `--pretty`: pretty-print the JSON output.
- `--solver-config KEY=VALUE ...`: override any solver config key (solve mode only).

## Run Tests

Standard suite:

```bash
python scripts/test.py
```

The entrypoint creates the Python environment as needed and installs the locked Playwright development dependency with `npm ci` when it is missing. Chrome or Chromium is required for the frontend browser smoke test; use `HORTICALC_BROWSER_PATH` for a non-standard browser location.

Focused examples:

```bash
python scripts/test.py tests/test_ec.py -q
python scripts/test.py tests/test_solver_golden.py tests/test_solver_weighting.py -q
python scripts/test.py tests/test_frontend_serving.py tests/test_frontend_recipe_wheel_shell.py -q
```

Run only the browser workflow smoke test:

```bash
python scripts/test.py tests/test_frontend_browser_smoke.py -q
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

## Solver Matrix Harness

```bash
python scripts/solver_matrix.py --preset quick --out-dir logs/solver_matrix/smoke
python scripts/solver_matrix.py --preset matrix --out-dir logs/solver_matrix/settings_001
python scripts/solver_matrix.py --preset matrix --primary-portfolio restricted_313_bittersalz_mkp --out-dir logs/solver_matrix/settings_restricted_313
python scripts/solver_matrix.py --preset deep --max-runs 0 --out-dir logs/solver_matrix/deep_001
python scripts/solver_matrix_analyze.py logs/solver_matrix/deep_001 --top 40
```

`quick` runs the canonical baseline, `matrix` runs the controlled setting
catalog, and `deep` adds named/leave-one-out nutrient-portfolio barrage rows.
Generated CSV, JSONL, manifest, summary, analysis JSON, and Markdown files stay
under the selected ignored output directory.

## Docs Anti-Drift

```bash
rg -n "TODO|UNDECIDED|Task [0-9]|Implementation Roadmap" docs README.md --glob "!**/commands.md"
```
