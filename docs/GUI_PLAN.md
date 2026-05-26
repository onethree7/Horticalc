# GUI Plan – HORTICALC Recipe Wheel

## Ziel
Modernes dunkles App-Shell-Layout mit Rezept-Wheel, Live-Bar und first-class Solver/Wasser/Details, ohne Backend- oder Mathematikänderungen.

## Umsetzungsgrenzen
- Static Vanilla JS beibehalten.
- Nur `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`, `docs/GUI_PLAN.md`, `docs/GUI.MD` angepasst.
- Bestehende IDs, Zustandsobjekte und API-Flows bleiben erhalten.

## Struktur
1. Header mit Brand, API-Config, Rezeptaktionen.
2. App-Shell mit Sidebar (Recipe Wheel) + Content.
3. Wheel-Schritte: Wasser, Dünger, Zielwerte, Berechnen, Ergebnis, Details.
4. Sticky Live-Bar unten.
5. Bestehende Experten-Tabellen bleiben als Fallback/Details erreichbar.

## JS-Helfer
- `bindRecipeWheel`
- `setActiveWheelStep`
- `navigateWheelStep`
- `scrollToPanelAnchor`
- `openExpertDetails`
- `updateLiveResultBar`

## Verifikation
- Wheel-Navigation schaltet Modus/Scroll wie spezifiziert.
- Berechnen/Solve-Flows unverändert funktional.
- Expertenansicht und vorhandene Tabellen bleiben verfügbar.
- Keine Backend-Dateien geändert.
