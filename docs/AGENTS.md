# AGENTS.md

Dieses Dokument richtet sich an Agenten/Contributor und beschreibt den aktuellen Stand,
Konventionen sowie die nächste Entwicklungslinie.

## Kernanforderungen
- **Excel ist kein Backend.** Die Logik wird aus **CSV/YAML** gespeist.
- Alle Berechnungen laufen im **Python‑Backend** (CLI/Backend zuerst, GUI danach).

## Aktueller Stand (kurz)
- Datenquellen in Textform: `data/fertilizers.csv`, `data/molar_masses.yml`,
  `data/water_profiles/*.yml`
- Core‑Logik: Umrechnung Oxide → Elemente, getrennte N‑Formen, Ionenbilanz, EC‑Berechnung
- API/GUI: FastAPI liefert Dünger, Wasserprofile, Berechnungen; GUI bietet Wasserprofile,
  NPK‑Metriken, EC‑Metriken und Ionenbilanz
- CLI: `horticalc recipes/<file>.yml --pretty`

## Geplante Features / Notizen
- **GUI modular aufbauen**:
  - Settings
  - Wasserwerte‑Menü
  - Dünger‑Tab

## Zuletzt bearbeitetes Feature
- `docs/feature_osmosis_mix.md`
