# HORTICALC GUI (Recipe Wheel Redesign)

The frontend now uses a dark app-shell layout with workflow-first navigation:

- Header with HORTICALC brand, API connectivity pill, recipe load/save controls, compact API config.
- Sidebar Recipe Wheel workflow steps:
  - Wasser
  - Dünger
  - Zielwerte
  - Berechnen
  - Ergebnis
  - Details
- Main content keeps the original calculator, solver, water, and fertilizer-editor logic while presenting card-first primary UI.
- Expert/advanced tables are still present and accessible (fallback/expert mode).
- Sticky live metrics bar at the bottom shows high-level status.

## Implementation notes

- Vanilla JS only; no framework/build tooling.
- Existing backend contracts and calculation/solver flows unchanged.
- Existing IDs/state and primary event wiring preserved.
