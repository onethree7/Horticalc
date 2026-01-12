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
- **HCO3‑Wirkung je Stickstofftyp**: Im Excel gab es Formeln für die numerische Wirkung
  pro N‑Form (NH4/NO3/Urea). Teilweise sind die Werte **direkt bekannt** und sollen
  ohne Formel übernommen werden. Das soll als **eigene Sparte** im Output erscheinen.
- **GUI modular aufbauen**:
  - Settings
  - Wasserwerte‑Menü
  - Dünger‑Tab

## Zuletzt bearbeitetes Feature
- `docs/feature_hco3_ion_balance.md`
