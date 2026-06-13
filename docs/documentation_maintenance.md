# Documentation Maintenance

This page is the anti-drift contract for future documentation work.

## Status Labels

Every active doc must be one of these:

- `current-state`: describes current behavior and cites source files.
- `decision-log`: records accepted defaults or policy choices.
- `operation-guide`: commands and procedures that are valid now.
- `historical-report`: evidence kept for context, not a current procedure.

Do not mix planned work into current-state docs. Put future work in an issue,
decision entry, or clearly labelled historical/research report.

## Required Updates

Update docs in the same change when any of these change:

- API routes, payloads, validation keys, or response fields.
- `CalcResult.to_dict()` or `SolveResult.to_dict()`.
- Solver config defaults or objective semantics.
- AppRoot, user data, logs, lockfile, or package layout.
- Frontend workflow names, persistent browser storage, or critical DOM IDs.
- Build scripts, release workflow, artifact names, or smoke-test behavior.

## Single Source Rules

- `src/horticalc/core.py` owns calculation output.
- `src/horticalc/solver.py` owns solver behavior.
- `src/horticalc/solver_config.py` owns solver config schema and defaults.
- `src/horticalc/paths.py` owns portable path policy.
- `api/app.py` owns API routes and validation keys.
- `frontend/` owns visible UI workflow behavior.
- `scripts/packaging/` and `.github/workflows/release.yml` own release mechanics.
- `docs/decisions.md` owns accepted defaults and policy decisions.

Docs may summarize these sources, but should not invent independent defaults.

## Obsolete Docs

When a doc becomes obsolete:

1. Back it up under `_docs_backup/<date>-<reason>/`.
2. Make sure `_docs_backup/` is ignored by git.
3. Delete the obsolete tracked doc or rewrite it as a clearly labelled
   historical report.
4. Remove links from `docs/index.md`.

## Verification

Docs-only minimum:

```bash
rg -n "TODO|UNDECIDED|Task [0-9]|Implementation Roadmap" docs README.md --glob "!**/development.md" --glob "!**/documentation_maintenance.md"
rg -n "GUI_PLAN|feature_osmosis|golden_example" docs README.md --glob "!**/audit_2026_06_01.md" --glob "!**/development.md" --glob "!**/documentation_maintenance.md"
```

Full verification:

```bash
python scripts/test.py
```

Before merging, read `docs/index.md` and confirm every linked file exists.
