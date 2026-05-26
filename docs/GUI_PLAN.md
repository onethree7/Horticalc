# GUI Plan: HORTICALC Recipe Wheel

- Static Vanilla JS app shell only (`index.html`, `styles.css`, `app.js`).
- No backend/API/math/payload changes.
- Header: brand, API status, recipe controls, compact API URL + reload, fertilizer editor shortcut.
- Left navigation: Recipe Wheel (desktop) + horizontal stepper fallback (mobile).
- Right content: existing mode panels preserved and restyled.
- Calculator: card-based fertilizer amount controls + existing tables preserved as expert/fallback.
- Solver: first-class page with macro card inputs + existing target/fixed/results tables preserved.
- Water: overview cards + advanced collapsible table.
- Details: expert tables moved behind details panel; summary IDs preserved.
- Bottom sticky live bar: key metrics and latest calculation timestamp.

## Required preserved state/contracts

- Keep: `selectedFertilizers`, `fertilizerAmounts`, `waterValues`, `solverTargetValues`, `solverAllowedFertilizers`, `solverFixedGrams`, `lastCalculation`, `lastSolveResult`.
- Keep IDs and existing `setMode()` flow and existing calculate/solve button behavior.
- Keep old expert tables mounted and updated from existing render flow.
