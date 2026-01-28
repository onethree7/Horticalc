# Portable Release Build Plan (Option A)

## Runtime model (Option A)

Exactly as specified in `docs/AGENTS.md`, the runtime model is:

1. A single launcher executable starts a local HTTP server bound to `127.0.0.1`.
2. The backend serves the static frontend from the same origin at `/` and serves static assets under a stable path (root).
3. The launcher waits until `/health` returns OK.
4. The launcher opens a Chromium-based app window (no URL bar) to `http://127.0.0.1:<port>/` when available, or falls back to the system default browser.
5. Closing the app window stops the server (within 1–2 seconds, hard timeout 5 seconds). If the app is already running, open the browser and do not start a second server.
6. All persistent data and logs live inside the extracted app folder (portable-only).
7. Per-launch browser profile directories are cleaned up with `shutil.rmtree(..., ignore_errors=True)`.

## Current status (validated)

* ✅ Portable onedir binaries run on Windows and Linux from extracted folders.
* ✅ CI/CD workflow builds Windows + Linux artifacts and publishes release assets.
* ✅ Linux runtime verified on Debian/Ubuntu when a Chromium-based browser is installed (e.g., `chromium`, `google-chrome`, or `microsoft-edge`).
  * If Chromium is not available, the launcher falls back to the system default browser. If this fallback is an issue on certain distributions, note the requirement in the README and ship with the current behavior unchanged.

## Maintenance notes

* 2026-01-28: Removed unused `load_water_profile` helper from `src/horticalc/data_io.py` (no runtime behavior change).

## Portable-only policy (AppRoot-only writes)

* **Portable-only writes:** All runtime writes must stay inside the extracted release folder (“AppRoot”).
* **No OS user dirs:** Do not write to `%APPDATA%`, `%LOCALAPPDATA%`, `~/.config`, `~/.local/share`, XDG paths, registry, etc.
* **Fail-fast:** If AppRoot is not writable, exit immediately with a clear, user-facing message, e.g.:
  * “Extract to a writable folder (e.g. Desktop/Downloads). Do not run from Program Files.”

## Repository hygiene (no hidden Unicode control characters)

To avoid hidden/bidirectional Unicode control characters (category `Cf`) in source and docs, we enforce a repo-wide scan for text files (`.py`, `.md`, `.html`, `.js`, `.css`, `.toml`, `.yml/.yaml`).

**Verification commands (exact) + success:**
* `python scripts/check_unicode_controls.py`
  * Success: exit code 0 with “No Unicode control characters found.”
* `python -m pytest -q`
  * Success: the unicode-control guard test passes.

## Target release folder layout (AppRoot/*)

```
AppRoot/
├── Horticalc.exe (Windows) or horticalc (Linux)
├── _internal/              (PyInstaller runtime)
├── frontend/               (static UI shipped)
├── data/                   (shipped defaults; treated as read-only)
├── recipes/                (shipped defaults)
├── user/                   (persistent user data)
└── logs/                   (runtime logs)
```

### First-run copy semantics (defaults → user/)

* On first run, ensure `AppRoot/user/` exists.
* If `AppRoot/user/fertilizers.csv` is missing, copy from `AppRoot/data/fertilizers.csv`.
* Copy shipped, editable defaults into user space on first run:
  * `AppRoot/data/water_profiles/*.yml` → `AppRoot/user/water_profiles/`
  * `AppRoot/data/nutrient_solutions/*.yml` → `AppRoot/user/nutrient_solutions/`
  * `AppRoot/recipes/*.yml` → `AppRoot/user/recipes/`
* API reads and writes only from `AppRoot/user/` after the copy, so shipped defaults remain read-only.

---

# Implementation Roadmap (Tasks 1–5)

Each task below mirrors the scope and boundaries from `docs/AGENTS.md`. **Do not broaden scope.**

## Task 1 — Single-origin serving (Backend serves frontend)

**Scope boundary (exact):**
* FastAPI serves static frontend at `/` and assets under a stable path.
* Add SPA fallback (serve `index.html` for unknown non-API paths) if the frontend uses client-side routing.
* API routes remain stable; if conflicts, move API under `/api`.

**Files to touch (based on repo inspection):**
* `api/app.py` (FastAPI app where routes are defined).
* `frontend/index.html` (API base URL input defaults).
* `frontend/app.js` (API base URL usage).
* `README.md` (dev run instructions).
* `docs/release_build.md` (update with new single-origin dev run commands).

**Acceptance criteria:**
* Running the backend and opening `http://127.0.0.1:<port>/` loads the UI assets (CSS/JS from the same origin).
* UI calls API successfully with relative URLs (same origin; no CORS).
* No separate frontend server is required in release mode.

**Stop conditions:**
* If the FastAPI app definition is unclear, stop and report.
* If API/frontend routing conflicts cannot be resolved without design decisions, stop and report.

**Verification commands (exact) + success:**
* `python -m uvicorn api.app:app --host 127.0.0.1 --port 8000`
  * Success: visiting `http://127.0.0.1:8000/` loads the UI and API calls succeed with relative URLs.
  * Legacy/dev split (optional): run `python -m http.server 5173 --directory frontend` and set the UI API Base URL to `http://127.0.0.1:8000`.

---

## Task 2 — Launcher (start server → wait → open browser)

**Scope boundary (exact):**
* Add a GUI launcher entrypoint (new console_script or module entry).
* Implements: bind `127.0.0.1`, port selection, lockfile policy, `/health` wait, app-window browser open, portable logs.
* Implement “already running” behavior: if server running, open browser only.

**Files to touch (based on repo inspection):**
* `pyproject.toml` (add launcher entrypoint).
* `src/horticalc/` (add launcher module; e.g. `src/horticalc/launcher.py`).
* `api/app.py` (if an app factory or programmatic server hook is required).
* `docs/release_build.md` (document dev run + lockfile behavior).
* `docs/decisions.md` (record port range + lockfile path/name decisions).

**Acceptance criteria:**
* One command starts everything in dev and opens the browser after `/health` is OK.
* A second launch does not spawn a duplicate server (lockfile policy).
* Fail-fast if AppRoot is not writable (for logs/user data).
* Closing the app window stops the server within 1–2 seconds (hard timeout 5 seconds).

**Dev launcher (one command):**
* `python -m horticalc.launcher`

**Browser app-window behavior:**
* The launcher prefers Chromium-based browsers (Edge/Chrome/Chromium) in app mode with a unique profile dir at `AppRoot/user/browser_profiles/`.
* If no supported browser is found, it falls back to the system default browser and stops the server after a 5-second grace period unless `HORTICALC_KEEP_SERVER=1` is set.
* Linux note: Debian/Ubuntu users may need to install Chromium (`sudo apt install chromium`) for the preferred app-window behavior.

**Stop conditions:**
* Any path depends on CWD; must anchor to AppRoot.

**Verification commands (exact) + success:**
* `python -m horticalc.launcher`
  * Success: server starts on `127.0.0.1`, `/health` becomes OK, then the browser opens to the UI.
* `python -m horticalc.launcher` (run again)
  * Success: no second server process; browser opens to existing server.
  * Notes: logs are written to `AppRoot/logs/launcher.log`, and the lockfile lives at `AppRoot/user/horticalc.lock.json`.

---

## Task 3 — Portable-only data policy

**Scope boundary (exact):**
* Ensure all writes go to `AppRoot/user/`.
* Implement first-run copy from shipped defaults to user editable copies.
* Enforce fail-fast on unwritable AppRoot.
* Ensure the API endpoints read/write user copies (not shipped defaults).

**Files to touch (based on repo inspection):**
* `src/horticalc/data_io.py` (read/write paths for fertilizers and data files).
* `api/app.py` (ensure API uses user copies).
* `src/horticalc/` (likely add a small AppRoot/path helper module).
* `docs/release_build.md` (document defaults vs user copies and failure modes).

**Acceptance criteria:**
* Edits (e.g. fertilizers) persist across restart and stay inside `AppRoot/user/`.
* Running from a writable extracted folder works; running from an unwritable folder fails with a clear message.

**Stop conditions:**
* Any code writes outside AppRoot.
* Any code introduces OS user dirs.

**Verification commands (exact) + success:**
* `PYTHONPATH=src python -m uvicorn api.app:app --host 127.0.0.1 --port 8000`
  * Success: first run creates `AppRoot/user/` and copies defaults when missing; edits persist in `AppRoot/user/`.
* `python -m pytest -q`
  * Success: all tests pass (including portable copy/paths coverage).

---

## Task 4 — PyInstaller onedir packaging

**Scope boundary (exact):**
* Add packaging spec/scripts and short packaging docs.
* Ensure dist includes shipped asset directories (`frontend/`, `data/`, `recipes/`).
* Ensure Windows build is double-click friendly.

**Files to touch (based on repo inspection):**
* `scripts/` (add build script and/or PyInstaller spec).
* `docs/release_build.md` (exact build commands and artifact layout).
* `requirements.txt` (if PyInstaller is added as a build dependency).

**Build prerequisites (Windows + Linux):**
* Python **3.10+** (recommend 3.11.x) with `pip`.
* Install build dependencies from repo root:
  * `python -m pip install -r requirements.txt`
  * `python -m pip install pyinstaller`
* Windows note: the PyInstaller spec includes `tzdata` as a hidden import to avoid `zoneinfo` crashes and CI warnings on Windows.

**Build commands (exact):**
* Windows (PowerShell):
  * `.\scripts\packaging\build_windows.ps1`
* Linux (bash):
  * `./scripts/packaging/build_linux.sh`

**Expected dist layout (exact):**
```
dist/
└── Horticalc/               (Windows) or horticalc/ (Linux)
    ├── Horticalc.exe        (Windows) or horticalc (Linux)
    ├── _internal/
    ├── frontend/
    ├── data/
    ├── recipes/
    ├── user/                (created at runtime)
    └── logs/                (created at runtime)
```

**Acceptance criteria:**
* Dist folder can be zipped/tarred and run from any writable path.
* Running packaged binary opens browser and UI loads.

**Stop conditions:**
* Onefile is chosen without explicit maintainer approval.
* Assets are missing from dist or require an external server.

**Verification commands (exact) + success:**
* Windows: `.\scripts\packaging\build_windows.ps1`
  * Success: `dist/Horticalc/` contains the AppRoot layout with `frontend/`, `data/`, and `recipes/` alongside `Horticalc.exe`.
  * Success: Running `dist\\Horticalc\\Horticalc.exe` from a writable folder opens the browser and the UI works.
* Linux: `./scripts/packaging/build_linux.sh`
  * Success: `dist/horticalc/` contains the AppRoot layout with `frontend/`, `data/`, and `recipes/` alongside `horticalc`.
  * Success: Running `./dist/horticalc/horticalc` from a writable folder opens the browser and the UI works.

---

## Task 5 — GitHub Actions CI build & release artifacts

**Scope boundary (exact):**
* Add workflow to build Windows+Linux artifacts (matrix).
* Trigger on tags `v*` to upload release assets.
* Also allow manual workflow dispatch.
* Include smoke tests in CI against the packaged binary.

**Files to touch (based on repo inspection):**
* `.github/workflows/` (add release workflow).
* `docs/release_build.md` (how to cut a release).
* `docs/decisions.md` (record runner OS versions).
* `scripts/` (optional: add CI smoke-test helper script).

**Acceptance criteria:**
* Workflow produces two downloadable artifacts that start and open the browser.
* Artifact names include the version tag.

**Stop conditions:**
* Workflow uses unpinned assumptions that break reproducibility without documenting it.

**Verification commands (exact) + success:**
* `python -m PyInstaller --noconfirm --onedir <spec-or-entry>`
  * Success: local artifacts build without errors (mirrors CI build).

### How to cut a release

1) Create a release tag locally:
   * `git tag vX.Y.Z`
2) Push the tag:
   * `git push origin vX.Y.Z`
3) GitHub Actions will:
   * Build Windows + Linux onedir artifacts.
   * Run smoke tests on the packaged binary with `HORTICALC_NO_BROWSER=1` to avoid opening a browser in CI.
   * Upload artifacts to the workflow run.
   * Attach the artifacts to a GitHub Release for the tag (requires workflow `contents: write` permission).

### CI smoke test behavior (packaged binary)

The release workflow runs a smoke test against the packaged binary (not Python) to prove:
* The binary starts with `HORTICALC_NO_BROWSER=1`.
* The launcher writes the lockfile at `AppRoot/user/horticalc.lock.json`.
* `/health` responds with HTTP 200 from the port in the lockfile.
* `AppRoot/frontend/index.html`, `AppRoot/data/`, `AppRoot/recipes/`, and `AppRoot/logs/` exist.
