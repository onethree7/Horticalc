# AGENTS

Contributor and automation entrypoint for Horticalc.

## Golden Rule

Use **Plan -> Edit -> Verify** for every change.

- Keep changes scoped to the requested behavior.
- Prefer existing utilities and patterns over new dependencies.
- Do not preserve obsolete internal identifiers through runtime aliases,
  fallbacks, or backward-detection shims. Replace them completely and migrate
  affected local persisted files in place when necessary.
- Check for nested `AGENTS.md` before editing inside a subdirectory.
- Do not change runtime behavior while doing documentation work unless the task
  explicitly asks for code changes.
- Treat `src/horticalc/`, `api/app.py`, `frontend/`, `scripts/`, and tests as
  the source of truth. Docs must describe code, not wishful plans.

## Docs Structure

- [README.md](README.md): user entrypoint and fastest run commands.
- [AGENTS.md](AGENTS.md): automation and contributor contract.
- [docs/documentation_architecture.md](docs/documentation_architecture.md): docs charter, status taxonomy, and single-source rules.
- [docs/index.md](docs/index.md): docs map.
- [docs/quickstart.md](docs/quickstart.md): install and first run.
- [docs/user_guide.md](docs/user_guide.md): UI and workflow.
- [docs/cli_reference.md](docs/cli_reference.md): CLI command reference.
- [docs/commands.md](docs/commands.md): single source of truth for commands.
- [docs/development.md](docs/development.md): setup, tests, packaging, and docs updates.
- [docs/architecture.md](docs/architecture.md): current subsystem map.
- [docs/api_reference.md](docs/api_reference.md): FastAPI surface.
- [docs/data_model.md](docs/data_model.md): files, units, output fields.
- [docs/unit_handling.md](docs/unit_handling.md): canonical and display units.
- [docs/solver.md](docs/solver.md): solver behavior.
- [docs/ec.md](docs/ec.md): electrical conductivity model.
- [docs/gui.md](docs/gui.md): frontend behavior.
- [docs/nutrient_solution_profiles.md](docs/nutrient_solution_profiles.md): cited formulations.
- [docs/release_build.md](docs/release_build.md): packaging, release, and verification.
- [docs/decisions.md](docs/decisions.md): accepted decisions and current defaults.
- [docs/terminology_style_guide.md](docs/terminology_style_guide.md): canonical terms and units.
- [docs/solver_matrix.md](docs/solver_matrix.md): removable solver research harness.

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

For docs-only changes, also check links and stale references using the docs anti-drift command in `docs/commands.md`.
