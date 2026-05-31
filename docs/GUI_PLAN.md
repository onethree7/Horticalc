# GUI Plan - Horticalc App Frame

## Ziel

Der Duengerrechner wird als gerahmte Horticalc-App umgesetzt. Das Backend bleibt Quelle der Wahrheit; die UI organisiert die bestehenden Funktionen neu und bewahrt alle API- und State-Vertraege.

## Funktionsmatrix

| Bereich | Bestehende Funktion | Neuer Ort |
| --- | --- | --- |
| Duenger-Editor | CSV laden/speichern, Suche, Add/Delete | Bereich `DÜNGER-EDITOR` |
| Wasserprofile | Laden, Speichern, Reset, Osmose, mg/L/mmol, Helperwerte | Bereich `WASSERWERTE` |
| Duengerrezept | Rezeptprofile, Komponenten-Dropdowns, Form, Gewicht, Zeilen +/-, Gramm, Skalierung, `/calculate`, Auto-Recalculate | Bereich `RECHNER` |
| Zielprofil-Rechner | Zielwerte, Allowed, Fix-Gramm, Solve, Copy, Apply | Bereich `SOLVER`, farblich hervorgehoben |
| Ergebnisse und Details | NPK, EC, Wasser/Oxidformen/Ionen, Ionen-meq, Bilanz, Expertentabellen, N-Expand | Kein eigener Rail-Button; innerhalb `RECHNER` und Live-Kacheln |

## Linke Arbeitsleiste

- Brand-Kachel: Horticalc, Zweck der App und Logo.
- System-Kachel: direkt unter dem Logo, mit API-Status, API Base URL und Daten laden.
- Ablauf-Kachel: eigene Duenger im DÜNGER-EDITOR laden oder anlegen, WASSERWERTE konfigurieren, Rezepte im RECHNER manuell berechnen oder NPK-Ziele im SOLVER loesen lassen.
- Bereichs-Kachel: genau vier Navigationsziele, keine separaten Buttons fuer Manuell, Ergebnis oder Details.
- Status-Kachel: aktueller aktiver Bereich.
- Live-Kacheln: NPK gross hervorgehoben, EC25, EC18, Wasser-EC25, Wasser-EC18 und eine breite Bilanzsummen-Kachel als schnelle Orientierung, ohne den rechten Arbeitsbereich zu ueberlagern.

## Umsetzung

- `frontend/index.html`: App-Shell ohne separate Headerbar oder Kreisgrafik, versteckte Mode-Radios, stabile `data-testid`/`data-panel-anchor`-Vertraege sowie Brand-, Ablauf-, Bereichs-, System- und Live-Kacheln in der linken Arbeitsleiste.
- `frontend/app.js`: top-level Navigationshelfer `bindShellNavigation`, `setActiveShellView`, `showShellView`, `scrollToPanelAnchor` und `updateLiveResultBar`. Bestehende Renderfunktionen und API-Aufrufe bleiben die Arbeitslogik.
- `frontend/styles.css`: dunkles, dichtes Frame-Layout mit linker Arbeitsleiste, intern scrollendem Arbeitsbereich, stabilen Tabellencontainern und Live-Kacheln.
- Resize-Stabilitaet: sehr schmale Fenster bleiben im sichtbaren Browserraum; breite Tabellen behalten eigene horizontale Scrollcontainer statt die gesamte Seite seitlich aufzuziehen.
- `docs/GUI.MD`: aktuelle Bedien- und Kompatibilitaetsbeschreibung.
- Tests: HTML-/JS-Vertraege, keine doppelten IDs, alte sichtbare Modus-Leiste entfernt.

## Screenshot-Pflicht

Vor einem PR muessen Browser-Screenshots fuer diese Zustaende vorliegen:

- Duengerrezept inklusive Ergebnis-/Detailtabellen
- WASSERWERTE
- SOLVER
- DÜNGER-EDITOR

## Akzeptanzkriterien

- `python -m pytest -q` besteht.
- `git ... diff --check` besteht.
- Browser-Console zeigt keine Errors.
- Die linke Bereichsnavigation zeigt nur DÜNGER-EDITOR, WASSERWERTE, RECHNER und SOLVER.
- Es gibt keine separaten Rail-Buttons fuer Manuell, Ergebnis oder Details.
- Alle vier Navigationsziele zeigen nicht-leere Panels.
- Berechnen, Solver, Copy und Apply-to-Calculator funktionieren ohne Backend-Aenderungen.
