# AGENTS

Contributor and automation entrypoint for the Horticalc repo. This file describes workflow, testing, and where to find deeper documentation.

## Quick links

- Release/build recipes: [docs/release_build.md](docs/release_build.md)
- Decision history: [docs/decisions.md](docs/decisions.md)
- Docs hub: [docs/index.md](docs/index.md)

## Workflow

- **Plan → Edit → Verify** for any change.
- Keep changes minimal and scoped; avoid unrelated refactors.
- Prefer existing utilities and patterns over new dependencies.
- Check for nested `AGENTS.md` in subdirectories before editing files there.

## how to ask Codex

When filing a task or request:
- State the goal and the success criteria.
- List the exact files to touch (or constraints if unknown).
- Specify required verification commands and what “success” looks like.
- Call out constraints (e.g., no new deps, avoid file moves, keep links stable).

## Tests

Run the standard test suite when relevant:

```bash
python -m pytest -q
```

## Build & release

See [docs/release_build.md](docs/release_build.md) for detailed build, packaging, and release steps.

## Docs policy

- **README.md** = user-facing entrypoint (what it is + how to run).
- **AGENTS.md** = contributor/automation entrypoint.
- **docs/index.md** = docs hub.
- **docs/decisions.md** = decision log.
- Avoid duplicating instructions across documents; prefer links to the single source of truth.
