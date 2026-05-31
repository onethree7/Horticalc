# GUI - Horticalc App Frame

Dieses Dokument beschreibt die aktuelle Web-UI in `frontend/`. Die GUI ist eine statische Vanilla-JS-App und nutzt die bestehende FastAPI unveraendert.

## App-Shell

- Die linke Arbeitsleiste beginnt mit Horticalc-Logo und App-Titel, direkt darunter folgt das Systempanel mit API-Status, API Base URL und Daten laden.
- Die vertikale Bereichsnavigation zeigt nur die vier echten App-Bereiche: DÜNGER-EDITOR, WASSERWERTE, RECHNER und SOLVER. Separate Buttons fuer Manuell, Ergebnis und Details sind entfernt.
- Hauptarbeitsflaeche mit bestehenden Rechner-, Solver-, Wasser- und Editor-Panels in einem eigenen scrollbaren rechten Frame.
- Linke Arbeitsleiste mit aktivem Bereich und Live-Ergebnis-Kacheln fuer NPK, EC18/EC25, Wasser-EC25, Wasser-EC18 und Ionenbilanz mit Summen.
- Sehr schmale Viewports bleiben im sichtbaren Browserraum; die App erzwingt keine starre Mindestbreite.
- Breite Ergebnis- und Ionen-Tabellen scrollen innerhalb ihres Moduls horizontal, statt die gesamte Seite seitlich aufzuziehen.
- Das alte sichtbare Modus-Menue ist entfernt; interne Radio-Inputs bleiben versteckt, damit bestehende JS-Pfade stabil bleiben.

## Workflow-Bereiche

- **DÜNGER-EDITOR**: eigene Duenger laden, anlegen, suchen und Zeilen bearbeiten.
- **WASSERWERTE**: Wasserprofile laden/speichern/resetten, Osmoseanteil setzen, mg/L oder mmol/L anzeigen und Helperwerte wie CO3, CaCO3, KH und S pflegen.
- **RECHNER**: Rezeptprofile laden/speichern/resetten, Komponenten aus der Duengerliste waehlen, Zeilen hinzufuegen/entfernen, Gramm-Mengen bearbeiten und den bestehenden `/calculate`-Flow ausloesen. Ergebnis- und Detailtabellen bleiben innerhalb dieses Bereichs.
- **SOLVER**: Zielwerte, Liter, Urea-as-NH4, Phosphat-Spezies, erlaubte Duenger und fixe Gramm verwalten. Dieser Weg ist in der Navigation farblich eigenstaendig hervorgehoben.

## Kompatibilitaet

- Backend-Vertraege bleiben unveraendert: `/calculate`, `/solve`, `/fertilizers`, `/recipes`, `/water-profiles`, `/nutrient-solutions`, `/molar-masses`.
- Kritische IDs bleiben im DOM, unter anderem `calculatorMode`, `solverMode`, `fertilizerEditorMode`, `waterSection`, `profileSection`, `fertilizerSelectTableWrap`, `calculatorTableWrap`, `waterValuesTable`, `summaryViewToggle`, `waterSummaryTable`, `oxideSummaryTable`, `ionSummaryTable`, `ionMeqList`, `ionBalanceList`, `solverTargetsTable`, `solverAllowedFertilizers`, `solverFixedTable`, `solveBtn`, `copySolverResults`, `applySolverToCalculator` und `saveSolverAsRecipe`.
- Neue stabile UI-Vertraege sind `data-shell-view`, `data-panel-anchor` und `data-testid`.

## Verifikation

- Standardtests: `python -m pytest -q`.
- Whitespace-Check: `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check`.
- Browser-Check: App unter `http://127.0.0.1:8000/` oeffnen, Console Errors pruefen und Screenshots fuer RECHNER, WASSERWERTE, SOLVER und DÜNGER-EDITOR aufnehmen.
