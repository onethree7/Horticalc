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

Print the canonical version:

```bash
python -m horticalc --version
```

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

The entrypoint creates the Python environment as needed, installs pinned Python
and Node development tooling when missing, then runs Ruff formatting/linting,
ESLint, Stylelint, Node unit tests, Playwright behavior tests, and pytest.

Focused examples:

```bash
python scripts/test.py tests/test_ec.py -q
python scripts/test.py tests/test_solver_golden.py tests/test_solver_weighting.py -q
python scripts/test.py tests/test_frontend_serving.py tests/test_frontend_module_architecture.py -q
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
python scripts/solver_matrix_exhaustive.py --workers 24 --queue-depth 10000 --out-dir logs/solver_matrix/exhaustive_001
python scripts/solver_matrix_exhaustive.py --analyze-only --workers 24 --out-dir logs/solver_matrix/exhaustive_001
python scripts/solver_model_matrix.py --out-dir logs/solver_matrix/goal_model_001
python scripts/solver_preference.py pairs --count 120
python scripts/solver_preference.py label
python scripts/solver_preference.py train --feature-structure grouped
python scripts/solver_preference.py pairs --model logs/solver_matrix/exhaustive_001/preference_model.json --append --count 40
python scripts/solver_preference.py label
python scripts/solver_preference.py train --feature-structure grouped
python scripts/solver_preference.py rank --top 200
python scripts/solver_preference_screen.py --workers 24 --queue-depth 10000 --out-dir logs/solver_matrix/preference_screen_001
python scripts/solver_preference_barrage.py --ranking logs/solver_matrix/preference_screen_001/screening_ranking.json --top 50000 --workers 24 --queue-depth 10000 --out-dir logs/solver_matrix/preference_barrage_wide_001
python scripts/solver_preference_barrage.py --ranking logs/solver_matrix/preference_screen_001/screening_ranking.json --top 50000 --out-dir logs/solver_matrix/preference_barrage_wide_001 --analyze-only --analysis-model logs/solver_matrix/exhaustive_001/preference_model_grouped.json --analysis-out logs/solver_matrix/preference_barrage_wide_001/barrage_ranking_grouped.json
python scripts/solver_preference_barrage.py --top 200 --workers 24 --queue-depth 10000
```

`quick` runs the canonical baseline, `matrix` runs the controlled setting
catalog, and `deep` adds named/leave-one-out nutrient-portfolio barrage rows.
Generated CSV, JSONL, manifest, summary, analysis JSON, and Markdown files stay
under the selected ignored output directory.

The goal-model command compares the two legacy controls with deterministic
mg/L and mmol/L minimax LP policies across all selection and diagnostic
portfolios plus the seven matched recipe roundtrips. It writes a compact gzip
JSONL evidence stream and a JSON quality-gate/ranking summary. Exit code `0`
means every numerical, Pareto, roundtrip, and worst-case improvement gate
passed; exit code `2` means the evidence must not be committed as an accepted
research result.

The exhaustive command runs all conditionally effective setting interactions
and writes a resumable, deduplicated SQLite database plus JSON summary and
Pareto analysis. Repeating the same command resumes the database. Use
`--max-configs N` for a smoke test and `--skip-analysis` when generation and
Pareto analysis should run separately.

The preference commands turn Pareto conflicts into persistent A/B labels,
fit a monotone model, and rank configurations without allowing good elements
to compensate for the single worst learned element penalty. After an initial
model exists, `pairs --model ... --append` selects uncertain conflicts for
active learning. The screen command evaluates every exhaustive configuration
on three discriminating stress portfolios and creates a union shortlist from
several non-equivalent ranking and holdout views. `--include-ranking` forms a
lossless union with an earlier shortlist. Passing that shortlist to the barrage
tests every selected setting on all 35 configured portfolios (33 selection and
two diagnostic); `--extend-shortlist` reuses compatible stored solves when the
shortlist only grows. Diagnostic Humin portfolios are reported but excluded
from ranking, holdouts, deduplication, and bootstrap sampling. `--analysis-model`
rescoring never reruns the solver. The smaller direct barrage command evaluates
the primary top 200 plus the two historical references (at most 70,700 solves).
Both report behavior-deduplicated profile/portfolio holdouts and bootstrap rank
stability. All generated files remain under ignored `logs/solver_matrix/`
paths by default.

## Docs Anti-Drift

```bash
rg -n "TODO|UNDECIDED|Task [0-9]|Implementation Roadmap" docs README.md --glob "!**/commands.md"
```
