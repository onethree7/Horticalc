# Horticalc Docs

This folder is the active documentation set. Every page below is either
current-state documentation, an accepted decision log, or a clearly labelled
historical report.

## Start Here

- [Architecture](architecture.md): how backend, core, UI, launcher, data, and packaging fit together.
- [User guide](user_guide.md): UI, launcher, and CLI workflows.
- [Development guide](development.md): setup, tests, and common commands.
- [Documentation maintenance](documentation_maintenance.md): anti-drift rules for future agents.

## Subsystems

- [API reference](api_reference.md): FastAPI routes and payload shapes.
- [Data model](data_model.md): persisted files, units, conversions, and output fields.
- [Nutrient solution profiles](nutrient_solution_profiles.md): cited formulations
  and conversion rules.
- [GUI](GUI.MD): current frontend shell and workflow behavior.
- [Solver](solver.MD): solver objective semantics, defaults, and configuration.
- [EC model](EC.md): electrical conductivity calculation.
- [Solver matrix benchmark](solver_matrix.md): removable solver research harness.

## Operations

- [Release builds](release_build.md): PyInstaller and GitHub Actions release process.
- [Security and release verification](../SECURITY.md): checksums,
  attestations, and false-positive notes.
- [Decisions log](decisions.md): accepted defaults and policy choices.
- [Terminology and style guide](terminology_style_guide.md): canonical naming.

## Audits And History

- [Documentation audit 2026-06-01](audit_2026_06_01.md): what was stale and what changed.
- [Solver matrix deep run report 2026-05-31](solver_matrix_deep_run_2026_05_31.md): historical benchmark evidence.

The pre-rework docs are backed up under `_docs_backup/2026-06-01-pre-docs-rework/`.
That folder is ignored by git.
