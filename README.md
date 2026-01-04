# Horticalc (molar‑correct) – Projekt

Ziel: deinen Excel‑Düngerrechner **1:1 inhaltlich** nachbauen, aber mit **professioneller, simpler Struktur**:

- **kein Excel‑Backend**
- alle Stammdaten in **lesbaren Textdateien** (CSV/YAML)
- Core‑Logik als **kleines Python‑Backend** (CLI zuerst, GUI später)

Diese ZIP‑Version ist bewusst „minimal, aber produktiv“: du kannst direkt eine Rezeptdatei rechnen lassen.

---

## Quickstart

Voraussetzung: Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Testlauf (Golden Recipe)
horticalc recipes/golden.yml --pretty

# Ergebnis in Datei
horticalc recipes/golden.yml --pretty --out solutions/golden_output.json
```

---

## Datenmodell (statt Excel)

### 1) `data/fertilizers.csv`
Export aus deinem Sheet **„DüngerTab“**.

Wichtig:
- Die Analysenwerte sind **Massenanteile** (z.B. `0,14` = 14%).
- `NH4`, `NO3`, `Ur-N` sind **N‑Anteile als Element N**, getrennt nach Stickstoffform.
- `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O` sind Oxid‑Deklarationen (wie Düngeretikett).
- `SO4`, `CO3`, `SiO2`, `Cl` etc. sind als die jeweilige Form gespeichert.
- `Gewicht` ist ein Faktor für Flüssigdünger (z.B. Dichte/Be): **effektive Gramm = Gramm * Gewicht**.

### 2) `data/molar_masses.yml`
Export aus deinem Sheet **„MolareMasse“** + kleine Ergänzungen, damit die Umrechnungen funktionieren.

### 3) `data/water_profiles/*.yml`
Wasserprofile als mg/L.

In dieser ZIP:
- `default.yml` stammt aus deinem Sheet **„Wasserwerte“** (bereits mit deinem Verdünnungsfaktor angewendet).
- `HCO3` wird als mg/L (Bicarbonat) mitgeführt.

### 4) `recipes/*.yml`
Ein Rezept definiert:
- `liters`
- `water_profile`
- `fertilizers: [{name, grams}, ...]`
- optional: `phosphate_species` (`H2PO4` oder `HPO4`) für die Ladungsbilanz
- optional: `urea_as_nh4` (Default `false`) – wenn `true`, zählt Urea‑N als NH4+ (Hydrolyse)

Zusätzlich zum Golden-Recipe gibt es einen zweiten Regressionstest:
- `recipes/green_go_12_12_36.yml`

---

## Was genau wird gerechnet?

### Nährstoff‑Totals (mg/L als Element)

Der Core liefert u.a.:
- `N_total` + Aufschlüsselung nach Formen (`NH4`, `NO3`, `Urea`)
- `P`, `K`, `Ca`, `Mg`, `Na`, `S`, `Cl`, `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`, `Si`, `C`

Umrechnungen sind **stöchiometrisch** über Molmassen:
- `P2O5 → P` mit Faktor `2*M(P)/M(P2O5)`
- `K2O → K` mit Faktor `2*M(K)/M(K2O)`
- `CaO → Ca`, `MgO → Mg`, `Na2O → Na`, `SO4 → S`, `SiO2 → Si`, `CO3 → C`

Bei Wasserwerten wird `NH4`/`NO3` als **Molekül** interpretiert und zu `N` umgerechnet (z.B. NO3→N ist /4,427).
Bei Düngern ist `NH4`, `NO3`, `Ur-N` als **N‑Anteil** hinterlegt und wird entsprechend auf mg/L N gerechnet.

### Ionenbilanz (meq/L)

Der Core rechnet eine „klassische“ Ladungsbilanz aus den Hauptionen:

Kationen: `NH4+`, `K+`, `Ca2+`, `Mg2+`, `Na+`

Anionen: `NO3-`, `H2PO4-` (oder `HPO4^2-`), `SO4^2-`, `Cl-`, optional `HCO3-` und `CO3^2-`

Ergebnis:
- Summe Kationen (meq/L)
- Summe Anionen (meq/L)
- Fehler in % (signed + absolut)

Hinweis: Phosphat‑Ladung ist pH‑abhängig; deshalb ist `phosphate_species` konfigurierbar.

---

## Ordnerstruktur

```
.
├── data/
│   ├── fertilizers.csv
│   ├── molar_masses.yml
│   └── water_profiles/
│       └── default.yml
├── recipes/
│   └── golden.yml
│   └── green_go_12_12_36.yml
├── solutions/
│   └── golden_output.json
│   └── green_go_12_12_36_output.json
├── src/horticalc/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   └── data_io.py
└── docs/
    └── AGENTS.md
```

---

## Nächste Schritte (Roadmap)

1. **CSV/YAML Schema finalisieren** (welche Spalten sind „Wahrheit“ – Oxide vs. Ionen vs. Elemente).
2. **Ein paar Standard‑Rezepte** als Regressionstests (`solutions/*.json`).
3. **GUI**: erst lokal (z.B. Tauri/React oder Qt), später Web.
