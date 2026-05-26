# HORTICALC GUI (Recipe Wheel)

Die Oberfläche wurde in ein modernes dunkles App-Layout umgebaut, ohne Framework-Migration.

## Aufbau
- Header mit Branding, API-Status, Rezept laden/speichern und sekundärer API/Datensteuerung.
- Linke Sidebar mit Recipe Wheel Workflow-Navigation.
- Rechte Content-Karte mit bestehenden Modus-Panels.
- Sticky Live-Ergebnisleiste am unteren Rand.

## Workflow
- **Wasser**: Wasserprofil und Basiswerte.
- **Dünger**/**Berechnen**/**Ergebnis**/**Details**: Rechner-Flow mit Fokus-Ankern.
- **Zielwerte**: Solver als eigene primäre Seite.
- **Dünger-Editor**: weiterhin verfügbar.

## Kompatibilität
- IDs, API-Endpunkte, Payloads und State-Objekte bleiben kompatibel.
- Bestehende Tabellen bleiben als Expert/Fallback-Ansicht vorhanden.
