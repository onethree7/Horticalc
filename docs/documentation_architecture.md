# Documentation Architecture

Status: `operation-guide`.

This document is the charter for the Horticalc docs set. Every active doc must declare a status label from the taxonomy below.

## Status Labels

- `current-state`: Describes how the code behaves now and cites the owning file.
- `operation-guide`: Commands, runbooks, and workflows.
- `decision-log`: Accepted design, policy, and default decisions.
- `historical-report`: Past research or benchmark reports; not maintained as current procedure.

## Audience Tracks

- **Start here**: [quickstart.md](quickstart.md), [user_guide.md](user_guide.md), [development.md](development.md), [documentation_architecture.md](documentation_architecture.md).
- **For users**: [user_guide.md](user_guide.md), [cli_reference.md](cli_reference.md), [commands.md](commands.md), [unit_handling.md](unit_handling.md).
- **For researchers**: [data_model.md](data_model.md), [solver.md](solver.md), [ec.md](ec.md), [nutrient_solution_profiles.md](nutrient_solution_profiles.md), [unit_handling.md](unit_handling.md).
- **For contributors**: [development.md](development.md), [architecture.md](architecture.md), [api_reference.md](api_reference.md), [gui.md](gui.md), [terminology_style_guide.md](terminology_style_guide.md), [decisions.md](decisions.md).
- **Operations**: [release_build.md](release_build.md), [solver_matrix.md](solver_matrix.md).

## Single-Source Rules

To avoid duplication, the docs have one owning document for each concern:

- **Commands** -> [commands.md](commands.md)
- **Release verification** -> [release_build.md](release_build.md)
- **Output schemas** -> [data_model.md](data_model.md)
- **Solver semantics** -> [solver.md](solver.md)
- **UI behavior** -> [gui.md](gui.md)
- **Dev setup** -> [development.md](development.md)
- **Decisions** -> [decisions.md](decisions.md)

Other docs may explain behavior and point to the owner, but they must not reproduce the owner's command blocks.

## Update Triggers

When any of these change, update the matching doc in the same change:

- API routes, request, or response shapes -> [api_reference.md](api_reference.md), [data_model.md](data_model.md)
- `CalcResult` or `SolveResult` output keys -> [data_model.md](data_model.md)
- Solver config definitions or defaults -> [solver.md](solver.md), [data_model.md](data_model.md)
- AppRoot layout or portable data policy -> [architecture.md](architecture.md), [release_build.md](release_build.md), [data_model.md](data_model.md)
- Frontend workflow IDs or layout -> [gui.md](gui.md), [api_reference.md](api_reference.md)
- Build scripts or the release workflow -> [release_build.md](release_build.md)

## Contributor Contract

The root [AGENTS.md](../AGENTS.md) is the automation and contributor entrypoint. It lists the docs tree and points to this file for the full docs charter.
