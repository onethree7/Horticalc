# AGENTS

Contributor and automation entrypoint for Horticalc.

## Working rule

Use **Plan → Edit → Verify** for every change.

- Keep work scoped to the requested behavior.
- Prefer existing utilities and patterns over new dependencies.
- Check for a nested `AGENTS.md` before editing a subdirectory.
- Do not preserve obsolete internal identifiers through aliases, fallback
  detection, or runtime shims. Replace them and migrate affected persisted data
  when required.
- Do not change runtime behavior during documentation work unless the task also
  requests a code change.

## Sources of truth

Treat `src/horticalc/`, `api/app.py`, `frontend/`, `scripts/`, `.github/`, and
`tests/` as authoritative. Documentation must describe implemented behavior.

Documentation ownership is intentionally small:

- `README.md`: product entrypoint, downloads, and first run.
- `CONTRIBUTING.md`: source setup, tests, and documentation changes.
- `RELEASE.md`: packaging, release gates, and artifact verification.
- `SECURITY.md`: security support and reporting.
- `docs/usage.md`, `docs/cli.md`, and `docs/api.md`: supported user interfaces.
- `docs/data-formats.md`, `docs/solver.md`, `docs/ec.md`, and
  `docs/architecture.md`: technical contracts and design.

## Documentation rules

1. Write current behavior and cite its owning source where that helps
   maintenance.
2. Keep commands with the task that uses them; link instead of copying.
3. Keep implementation history in Git, not in current-state guides.
4. When code changes an API route, output key, data path, solver default,
   launcher behavior, persistence rule, UI workflow, or release artifact,
   update its owning document in the same change.
5. Delete obsolete documentation instead of retaining active redirects or
   compatibility pages.

## Verification

The standard command is intentionally repeated here as the automation bootstrap;
all focused and documentation commands belong in `CONTRIBUTING.md`. Run the
repository test entrypoint, not bare Pytest:

```bash
python scripts/test.py
```

For focused checks, see [Run tests](CONTRIBUTING.md#run-tests). For documentation
checks, see [Update documentation](CONTRIBUTING.md#update-documentation) before
the full suite.
