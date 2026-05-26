# GUI Plan: HORTICALC Recipe Wheel

- Static Vanilla frontend bleibt erhalten (index.html + styles.css + app.js).
- App-Shell: Header (Brand, API-Status, Rezeptsteuerung), 2-Spalten Hauptbereich, sticky Live-Bar.
- Linke Navigation als Recipe Wheel (Desktop) mit 6 Buttons: Wasser, Dünger, Zielwerte, Berechnen, Ergebnis, Details.
- Mobile: Wheel als horizontale Stepper-Buttons.
- Rechte Inhaltskarte zeigt bestehende Modi (`calculator`, `solver`, `fertilizers`, `water`) über bestehendes `setMode()`.
- Bestehende Tabellen bleiben erhalten als Experten-/Advanced-Bereiche (collapsible), primärer Pfad über Karten.
- Rechen- und Solver-Math unverändert; State-Objekte unverändert.
- Dünger-Editor bleibt über Header erreichbar.
- Live-Bar zeigt NPK/EC/CaMg/Balance + letzte Berechnung.
