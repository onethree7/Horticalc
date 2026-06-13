# AGENTS

Contributor and automation entrypoint for Horticalc.

## Golden Rule

Use **Plan -> Edit -> Verify** for every change.

- Keep changes scoped to the requested behavior.
- Prefer existing utilities and patterns over new dependencies.
- Check for nested `AGENTS.md` before editing inside a subdirectory.
- Do not change runtime behavior while doing documentation work unless the task
  explicitly asks for code changes.
- Treat `src/horticalc/`, `api/app.py`, `frontend/`, `scripts/`, and tests as
  the source of truth. Docs must describe code, not wishful plans.

## Docs Structure

- [README.md](README.md): user entrypoint and fastest run commands.
- [AGENTS.md](AGENTS.md): automation and contributor contract.
- [docs/index.md](docs/index.md): docs map.
- [docs/architecture.md](docs/architecture.md): current subsystem map.
- [docs/user_guide.md](docs/user_guide.md): how to use UI and CLI.
- [docs/api_reference.md](docs/api_reference.md): FastAPI surface.
- [docs/data_model.md](docs/data_model.md): files, units, output fields.
- [docs/solver.MD](docs/solver.MD): solver behavior.
- [docs/GUI.MD](docs/GUI.MD): frontend behavior.
- [docs/release_build.md](docs/release_build.md): packaging and release.
- [docs/decisions.md](docs/decisions.md): accepted decisions and current defaults.
- [docs/documentation_maintenance.md](docs/documentation_maintenance.md): anti-drift rules.

## Documentation Law

1. Current-state docs must say what the code does now and cite the owning file.
2. Plans and research reports must be labelled as such.
3. When code changes an API route, output key, file path, solver default,
   launcher behavior, persistence rule, or UI workflow, update the matching doc
   in the same change.
4. Do not leave obsolete roadmap docs in the active docs set. Move historical
   material into an ignored backup or a clearly labelled historical report.
5. Avoid duplicate instructions. Link to the source-of-truth document instead.

The pre-rework documentation backup is intentionally ignored at
`_docs_backup/`.

## Standard Verification

Run the standard suite when relevant. Use the repository test entrypoint; do
not probe with bare `python -m pytest`. The entrypoint creates `.venv` when
needed and installs the declared development dependencies only when pytest is
missing:

```bash
python scripts/test.py
```

Pass pytest arguments after the script name for focused runs, for example
`python scripts/test.py tests/test_ec.py -q`.

For docs-only changes, also check links and stale references:

```bash
rg -n "TODO|UNDECIDED|Task [0-9]|Implementation Roadmap" docs README.md --glob "!**/development.md" --glob "!**/documentation_maintenance.md"
rg -n "GUI_PLAN|feature_osmosis|golden_example" docs README.md --glob "!**/audit_2026_06_01.md" --glob "!**/development.md" --glob "!**/documentation_maintenance.md"
```

Investigate any hit before merging, then skim this file for the same issues.
