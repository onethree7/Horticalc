# Horticalc (molar‑correct)

Horticalc ist ein molar‑korrekter Düngerrechner mit Python‑Backend. Die Kernlogik läuft in einer schlanken CLI, eine Web‑GUI ist optional angebunden. Alle Stammdaten liegen versionierbar in lesbaren Textformaten (CSV/YAML), sodass Berechnungen nachvollziehbar und reproduzierbar bleiben.

**Schwerpunkte**
- Molar‑stimmige Umrechnungen (Oxide → Elemente)
- Getrennte N‑Formen (NH4, NO3, Urea)
- Ionenbilanz (Anionen/Kationen) inkl. wählbarer Phosphat‑Spezies
- EC‑Berechnung aus Ionenzusammensetzung
- Erweiterbar um weitere Module (z. B. zusätzliche EC‑Modelle)

---

## Quickstart (CLI)

Voraussetzung: Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .

# Testlauf (Golden Recipe)
horticalc recipes/golden.yml --pretty

# Ergebnis in Datei
horticalc recipes/golden.yml --pretty --out solutions/golden_output.json

# Solver: Zielwerte -> Rezept (S/SO4 werden ignoriert)
horticalc solve recipes/solve_golden.yml --pretty
```

---

## GUI + API (Web UI)

Die GUI ist ein **statisches Frontend** unter `frontend/` und spricht die **FastAPI** unter `api/`. Die Tabellenansicht ist auf kompakte, ausrichtbare Spalten optimiert (Zebra‑Streifen, feste Spaltenbreiten, gruppierte N‑Formen).

### Planung (Roadmap)
- GUI modularisieren: **Settings**, **Wasserwerte‑Menü**, **Dünger‑Tab**

### Voraussetzungen
- Python 3.10+

### Setup (Windows / PowerShell)

```powershell
git clone https://github.com/onethree7/Horticalc
cd Horticalc

py -m venv .venv
.\.venv\Scripts\python -m pip install -U pip setuptools wheel
.\.venv\Scripts\python -m pip install -r .\requirements.txt
.\.venv\Scripts\python -m pip install -e .\
```

### Setup (Linux / macOS)

```bash
git clone https://github.com/onethree7/Horticalc
cd Horticalc

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Backend starten (Terminal 1)

```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```

API‑Check:
```
http://127.0.0.1:8000/health
```

### Frontend starten (Terminal 2)

```bash
python -m http.server 5173 --directory frontend
```

Frontend‑URL:
```
http://127.0.0.1:5173/
```

---

## Datenmodell

### 1) `data/fertilizers.csv`
Enthält die Düngeranalysen in Massenanteilen.

Wichtig:
- Die Analysenwerte sind **Massenanteile** (z.B. `0,14` = 14%).
- `NH4`, `NO3`, `Ur-N` sind **N‑Anteile als Element N** und werden zu `N_NH4`, `N_NO3`, `N_UREA` aggregiert.
- `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O` sind Oxid‑Deklarationen (wie Düngeretikett).
- `SO4`, `CO3`, `SiO2`, `Cl` etc. sind als die jeweilige Form gespeichert.
- `Gewicht` ist ein Faktor für Flüssigdünger (z.B. Dichte/Be): **effektive Gramm = Gramm * Gewicht**.

### 2) `data/molar_masses.yml`
Molare Massen für alle verwendeten Formen (Elemente, Oxide, Ionen).

### 3) `data/water_profiles/*.yml`
Wasserprofile in mg/L.

Hinweise:
- `HCO3` wird als mg/L (Bicarbonat) geführt.
- Optional kann `osmosis_percent` (0–100) gesetzt werden; der Core verdünnt die Wasserwerte entsprechend.

### 4) `data/nutrient_solutions/*.yml`
Referenz‑Zielwerte (Elemente in mg/L), kein Dünger‑Rezept:
- `targets_mg_per_l` (Zielwerte als mg/L **Elemente**)

### 5) `recipes/*.yml`
Ein Rezept definiert:
- `liters`
- `water_profile`
- `fertilizers: [{name, grams}, ...]`
- optional: `phosphate_species` (`H2PO4` oder `HPO4`) für die Ladungsbilanz
- optional: `urea_as_nh4` (Default `false`) – wenn `true`, zählt Urea‑N als NH4+ (Hydrolyse)

Zusätzlich zum Golden-Recipe gibt es einen zweiten Regressionstest:
- `recipes/green_go_12_12_36.yml`

### 6) `recipes/solve_*.yml` (Solver)
Ein Solver‑Rezept definiert:
- `liters`
- `water_profile`
- `targets_mg_per_l` (Zielwerte als mg/L **Elemente**)
- `fertilizers_allowed` (Liste der nutzbaren Dünger)
- optional: `fixed_grams` (Dünger → feste Gramm)
- optional: `phosphate_species` und `urea_as_nh4`

Hinweis: **S/SO4 werden in der Optimierung ignoriert**, aber im Ergebnis weiterhin ausgegeben.

---

## Was genau wird gerechnet?

### Nährstoff‑Totals (mg/L als Element)

Der Core liefert u.a.:
- `N_total`, `N_NH4`, `N_NO3`, `N_UREA`
- `P`, `K`, `Ca`, `Mg`, `Na`, `S`, `Cl`, `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`, `Si`, `C`

Umrechnungen sind **stöchiometrisch** über Molmassen:
- `P2O5 → P` mit Faktor `2*M(P)/M(P2O5)`
- `K2O → K` mit Faktor `2*M(K)/M(K2O)`
- `CaO → Ca`, `MgO → Mg`, `Na2O → Na`, `SO4 → S`, `SiO2 → Si`, `CO3 → C`

Bei Wasserwerten wird `NH4`/`NO3` als **Molekül** interpretiert und zu `N_NH4`/`N_NO3` umgerechnet (z.B. NO3→N ist /4,427).
Bei Düngern ist `NH4`, `NO3`, `Ur-N` als **N‑Anteil** hinterlegt und wird entsprechend zu `N_NH4`, `N_NO3`, `N_UREA` gerechnet.

### Ionenbilanz (meq/L)

Der Core rechnet eine „klassische“ Ladungsbilanz aus den Hauptionen:

Kationen: `NH4+`, `K+`, `Ca2+`, `Mg2+`, `Na+`

Anionen: `NO3-`, `H2PO4-` (oder `HPO4^2-`), `SO4^2-`, `Cl-`, optional `HCO3-` und `CO3^2-`

Ergebnis:
- Summe Kationen (meq/L)
- Summe Anionen (meq/L)
- Fehler in % (signed + absolut)

Hinweis: Phosphat‑Ladung ist pH‑abhängig; deshalb ist `phosphate_species` konfigurierbar.

### Electrical Conductivity (EC)

Der Core berechnet EC **ionenbasiert** aus der vorhandenen Ionenzusammensetzung.
Ausgabe ist in der Ergebnis‑JSON unter `ec` enthalten (EC bei 18 °C und 25 °C).

Details, Formeln, Einheiten, Parameter und Quellen stehen in [`docs/EC.md`](docs/EC.md).

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
│   ├── default.yml
│   ├── golden.yml
│   └── green_go_12_12_36.yml
├── solutions/
│   ├── golden_output.json
│   └── green_go_12_12_36_output.json
├── api/
│   └── app.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── src/horticalc/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   └── data_io.py
└── docs/
    ├── AGENTS.md
    ├── EC.md
    ├── feature_osmosis_mix.md
    ├── GUI.MD
    └── golden_example_output.txt
```

---
