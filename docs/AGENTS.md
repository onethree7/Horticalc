# AGENTS.md (Codex) — Portable Desktop Releases (Windows + Linux) via Local Web App

This document defines the implementation contract for Codex/agents working in this repo.
Follow it strictly. If anything is unclear: STOP and report findings; do not guess.

## 0) What we are building (Option A, fully defined here)

Goal: A user can run Horticalc as a portable app from an extracted folder (no installation).
- Windows: double-click `Horticalc.exe` → a browser opens automatically → the UI works.
- Linux: run `./horticalc` (optionally double-click via `.desktop`) → browser opens → UI works.
- The user must not need to understand backend/frontend/server.

**Runtime model (Option A):**
1) A single “launcher” executable starts a local HTTP server bound to `127.0.0.1`.
2) The server serves:
   - the static frontend (HTML/CSS/JS) at `/` (and SPA fallback as needed)
   - the API under `/api/...` (or existing routes, but avoid conflicts)
3) The launcher waits until the server is ready (`/health` returns OK).
4) The launcher opens the system default browser to `http://127.0.0.1:<port>/`.
5) All persistent data and logs are written into the extracted app folder (portable-only).
6) On re-launch: no duplicate server. If already running, just open the browser.

**Non-goals:**
- No embedded WebView / Electron.
- No system/user directories for storage.
- No second frontend server process (no separate `python -m http.server` for release).

## 1) Hard constraints (must never be violated)

### 1.1 Portable-only writes (NO OS user dirs)
All writes MUST be relative to the extracted release folder (“AppRoot”).
- DO NOT use: `%APPDATA%`, `%LOCALAPPDATA%`, `~/.config`, `~/.local/share`, XDG dirs, registry, etc.
- If AppRoot is not writable: FAIL FAST with a clear message:
  - “Extract to a writable folder (e.g. Desktop/Downloads). Do not run from Program Files.”

### 1.2 Single-origin web app (no CORS by design)
- Backend serves frontend itself.
- Frontend must call the API using relative URLs (same origin), not hard-coded ports/hosts.
- No second process for frontend serving in release.

### 1.3 Bind localhost only
- Server MUST bind to `127.0.0.1` (not `0.0.0.0`), to avoid LAN exposure and reduce Windows firewall prompts.

### 1.4 Minimal-scope changes
- One task per PR.
- No broad refactors, no reformatting-only PRs, no “cleanup while here”.
- Touch only files required for the task; list them explicitly.

### 1.5 Progress tracking is mandatory
Every implemented change must update:
- `AGENTS.md` (this file): mark completed items as **[DONE.]** while preserving text.
- `docs/release_build.md`: reflect the latest implemented reality (commands, paths, verification).
- `docs/decisions.md`: if a decision is made or changed, record it explicitly.

No PR is “done” until progress tracking is updated.

## 2) Repository structure assumptions (verify, then adapt)
Assumed canonical paths (verify in Task 0; if different, report exact real paths):
- Frontend: `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`
- Backend/API: `app.py` or `api/app.py` (FastAPI application entry)
- Data IO: `data_io.py` (or similar module for reading/writing fertilizers)
- Data defaults: `data/fertilizers.csv` (or wherever `DEFAULT_FERTILIZERS` points)

If paths differ, Codex must:
- print the discovered authoritative paths
- update later tasks to use the real ones
- update this section of `AGENTS.md` to match the repo truth
- STOP if unsure which file is authoritative

## 3) Release folder layout (portable target)
The produced artifact is an extracted folder with everything inside:

AppRoot/
- Horticalc.exe (Windows) or horticalc (Linux)
- _internal/ (pyinstaller runtime)
- frontend/ (static UI shipped)
- data/ (defaults shipped, read-only in concept)
- recipes/ (defaults shipped)
- user/ (persistent user data created/used at runtime)
- logs/ (runtime logs)

Write policy:
- persistent files go to `AppRoot/user/...`
- logs go to `AppRoot/logs/...`
- shipped defaults are read from `AppRoot/data/...` and copied to `AppRoot/user/...` on first run

## 4) Runtime policies (must be implemented explicitly)

### 4.1 AppRoot definition (must not depend on CWD)
- In a packaged executable: AppRoot = directory containing the executable.
- In dev mode: AppRoot = repo root (or a deterministic equivalent).
- Never assume “current working directory == repo root”.

### 4.2 First-run copy semantics (portable)
On first run:
- Ensure `AppRoot/user/` exists.
- If `AppRoot/user/fertilizers.csv` missing, copy from shipped default `AppRoot/data/fertilizers.csv`.
- Same idea for other editable defaults (if any).

### 4.3 Port selection (robust)
Default policy:
- Try a fixed range (e.g. 8000–8100) on `127.0.0.1` and pick the first free port.
- Record chosen port in a lockfile in AppRoot (see below).

### 4.4 Single-instance / lockfile policy (recommended)
Create `AppRoot/user/horticalc.lock.json` (or similar) containing:
- pid, port, start timestamp
On startup:
- If lock exists and `/health` responds: do NOT start a second server; just open the browser.
- If lock exists but server not reachable: treat as stale; remove lock and start normally.

### 4.5 Readiness check (must not race)
Launcher must:
- start server
- poll `/health` until success or timeout
- only then open browser
- on timeout: print/log actionable error (including log file path)

### 4.6 Logging (portable)
- Always write logs to `AppRoot/logs/`.
- If cannot write logs: fail fast (same as unwritable AppRoot).

## 5) Build strategy (Windows + Linux)

### 5.1 Packaging approach
Default:
- PyInstaller **onedir** (not onefile) for predictable asset layout and portability.
- Include shipped asset directories (`frontend/`, `data/`, `recipes/`) inside the dist folder.

### 5.2 OS-specific builds
- Build Windows artifact on Windows runner.
- Build Linux artifact on Linux runner.
- Do not attempt cross-OS builds.

### 5.3 Linux compatibility baseline (decision)
Codex must not silently choose.
- Provide a recommendation (default: `ubuntu-22.04` runner) and document it in `docs/decisions.md`.
- If the maintainer chooses otherwise, reflect that explicitly.

## 6) Work breakdown (Codex tasking model)

Codex must implement in small, reviewable PRs. Use this order.
Each task must update the progress trackers (AGENTS.md + docs) before completion.

### Task 0 — Docs only (NO code) [DONE.]
Create/overwrite:
- `docs/release_build.md`: open guide for implementing Option A in this repo (concept + steps + verification).
- `docs/decisions.md`: decisions checklist with defaults (port policy, lockfile, linux baseline).
- Optional: `docs/progress.md` (if needed) as a simple checklist of tasks and PR links.

Output must include:
- “files to touch” list for each later task (based on actual repo inspection).
- “verification commands” for each later task.

Progress tracking update:
- Mark Task 0 as **[DONE.]** in AGENTS.md once docs exist and are coherent.

STOP if:
- FastAPI app entrypoint cannot be identified.

### Task 1 — Single-origin serving (Backend serves frontend) [DONE.]
Scope:
- FastAPI serves static frontend at `/` and assets under a stable path.
- Add SPA fallback (serve `index.html` for unknown non-API paths) if the frontend uses client-side routing.
- API routes remain stable; if conflicts, move API under `/api`.

Required doc updates:
- Update `docs/release_build.md` with the new “one server” dev run commands.
- Update README dev instructions accordingly.

Progress tracking update:
- In AGENTS.md, mark Task 1 section as **[DONE.]** and keep the text.

Acceptance:
- Running backend locally and opening `http://127.0.0.1:<port>/` loads the UI assets.
- UI calls API successfully with relative URLs (no CORS).
- No requirement for separate frontend server in release.

STOP if:
- Unclear where FastAPI app is defined; report findings instead of guessing.

### Task 2 — Launcher (start server → wait → open browser) [DONE.]
Scope:
- Add a GUI launcher entrypoint (new console_script or module entry).
- Implements: bind 127.0.0.1, port selection, lockfile policy, /health wait, browser open, portable logs.
- Implement “already running” behavior: if server running, open browser only.

Required doc updates:
- Update `docs/release_build.md`: “How to run launcher in dev”, “lockfile behavior”, “log location”.
- Update `docs/decisions.md`: confirm chosen port range and lockfile name/location.

Progress tracking update:
- Mark Task 2 as **[DONE.]** in AGENTS.md after acceptance tests pass.

Acceptance:
- One command starts everything in dev and opens browser after readiness.
- Second start does not spawn duplicate server (lockfile policy).
- Fail-fast if AppRoot not writable (because logs/user/ must be writable).

STOP if:
- Any path depends on CWD; must anchor to AppRoot.

### Task 3 — Portable-only data policy
Scope:
- Ensure all writes go to `AppRoot/user/`.
- Implement first-run copy from shipped defaults to user editable copies.
- Enforce fail-fast on unwritable AppRoot.
- Ensure the API endpoints read/write user copies (not shipped defaults).

Required doc updates:
- `docs/release_build.md`: explicitly describe “defaults vs user copies”, first-run behavior, and failure modes.

Progress tracking update:
- Mark Task 3 as **[DONE.]** in AGENTS.md after persistence test passes.

Acceptance:
- Edits (e.g. fertilizers) persist across restart and stay inside extracted folder.
- Running from a writable extracted folder works; running from unwritable folder fails with clear message.

STOP if:
- Any code writes outside AppRoot.
- Any code introduces OS user dirs.

### Task 4 — PyInstaller onedir packaging
Scope:
- Add packaging spec/scripts and short packaging docs.
- Ensure dist includes shipped asset directories `frontend/`, `data/`, `recipes/`.
- Ensure Windows build is double-click friendly.

Required doc updates:
- `docs/release_build.md`: exact build commands for Win/Linux, exact artifact layout.

Progress tracking update:
- Mark Task 4 as **[DONE.]** in AGENTS.md when packaged artifacts pass smoke tests.

Acceptance:
- Dist folder can be zipped/tarred and run from any writable path.
- Running packaged binary opens browser and UI loads.

STOP if:
- Onefile is chosen without explicit maintainer approval (default is onedir).
- Assets are not present in dist (or require external server).

### Task 5 — GitHub Actions CI build & release artifacts
Scope:
- Add workflow to build Windows+Linux artifacts (matrix).
- Trigger on tags `v*` to upload release assets.
- Also allow manual workflow dispatch.
- Include minimal smoke tests in CI (import test + CLI version/health).

Required doc updates:
- `docs/release_build.md`: “How to cut a release” steps.
- `docs/decisions.md`: record runner OS versions.

Progress tracking update:
- Mark Task 5 as **[DONE.]** in AGENTS.md after a successful tag build.

Acceptance:
- Workflow produces two downloadable artifacts that start and open browser.
- Artifact names include version tag.

STOP if:
- Workflow uses unpinned assumptions that break reproducibility without documenting it.

## 7) Task execution rules (how Codex should work)

### 7.1 Always start with inspection
Before implementing a task:
- Identify authoritative entrypoints and modules.
- Identify any hardcoded URLs/ports in frontend.
- Identify all places that read/write fertilizers, recipes, or config.

If anything is ambiguous: STOP and report.

### 7.2 Always list file changes and why
For every task, output (in PR description or final response):
- Files changed (exact paths)
- What changed in each file (1–2 lines)
- Verification commands and expected output
- Known limitations

### 7.3 Update progress trackers at the end of every task
Each completed task MUST:
- Update `AGENTS.md`: mark the task as **[DONE.]** (do not delete text).
- Update `docs/release_build.md`: reflect reality (commands, paths, behavior).
- Update `docs/decisions.md`: record any decision taken.

## 8) STOP conditions (must stop and report)
Stop and report (do not implement) if:
- You cannot locate the authoritative FastAPI app object.
- You find multiple competing entrypoints and cannot confirm which one is used.
- Frontend/API routing assumptions are unclear (hardcoded origins, build step missing).
- Data read/write paths cannot be made portable without a design decision.

When stopping, output:
- the exact files/lines involved
- the minimal set of decisions needed
- a recommended default decision

## 9) Verification checklist (portable)
Before marking any task complete, verify:
- AppRoot is independent of CWD.
- All writes are inside AppRoot (user/ logs/).
- Server binds only to 127.0.0.1.
- Browser opens only after /health OK.
- UI loads assets and API works from same origin.
- Restart does not lose edits (portable persistence works).

End of AGENTS.md
