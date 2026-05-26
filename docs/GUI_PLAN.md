# GUI Plan: HORTICALC Recipe Wheel

## Scope
- Static Vanilla JS frontend only.
- Preserve existing IDs, state objects, API behavior, solver/calc flows.
- Keep legacy tables as advanced/expert fallback.

## App shell
- Sticky top header with brand, API status, recipe controls, compact API URL/reload.
- Two-column desktop shell: left Recipe Wheel sidebar, right active content card.
- Sticky live result footer bar.

## Navigation
- Wheel/stepper buttons: Wasser, Dünger, Zielwerte, Berechnen, Ergebnis, Details.
- Buttons wrap existing `setMode()` and then scroll/focus anchors.

## Calculator page
- Card-based selected fertilizer amounts (+/-/input/remove, non-negative clamp).
- Primary calculate action still triggers existing `#calculateBtn` flow.
- Legacy `#fertilizerSelectTableWrap` and `#calculatorTableWrap` remain as expert sections.
- Result cards + nutrient strip added.
- Expert details panel wraps summary/ion tables.

## Solver page
- First-class page with settings row + macro target cards.
- Full target table kept as advanced fallback.
- Allowed fertilizers, fixed grams, solve/copy/apply/save actions remain.

## Water page
- Water overview cards + profile/osmosis/unit controls.
- Full `#waterValuesTable` moved behind collapsible advanced section.
