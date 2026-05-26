# HORTICALC GUI

The frontend now uses a dark modern **Recipe Wheel** app shell while keeping the original static architecture and backend contracts.

## Workflow UI
- Header: brand, API status, recipe actions, compact API base/reload.
- Left wheel (desktop) / stepper (mobile): Wasser, Dünger, Zielwerte, Berechnen, Ergebnis, Details.
- Right content card renders the active mode.
- Bottom live bar surfaces NPK/EC/Ca:Mg/balance at a glance.

## Compatibility guarantees
- Existing element IDs and JS state model remain in place.
- Existing calculate/solve endpoints and payloads are unchanged.
- Existing expert tables are preserved and available in advanced sections.
- Fertilizer editor remains reachable from header and mode controls.
