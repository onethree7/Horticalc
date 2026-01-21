# Horticalc (molar‑korrekt) — ! WORK IN PROGRESS !

Horticalc ist ein Düngerrechner mit Python‑Backend. Die Berechnung basiert auf molaren Massen und stöchiometrisch korrekten Umrechnungen (z. B. Oxide → Elemente). Eingaben (Rezepte, Wasserprofile, Zielprofile) liegen als YAML, Stammdaten zu Düngern als CSV vor, sodass Ergebnisse reproduzierbar bleiben.

Wichtig: Das Projekt ist in aktiver Entwicklung. Schnittstellen, Dateiformate und Annahmen können sich ändern.

## Überblick: Komponenten (was macht was?)

Rechner (Berechnung)
- Zweck: Rechnet aus einem Rezept (Wasserprofil + Düngermengen) die resultierenden Konzentrationen.
- Ergebnis u. a.: mg/L‑Totals (Elemente und Oxide), Ionen (mmol/L, meq/L), Ladungsbilanz, EC‑Schätzung, sowie Wasser‑ und Dünger‑Anteil separat.
- Implementierung/Files:
  - Kernberechnung: `src/horticalc/core.py`
  - EC‑Berechnung: `src/horticalc/ec.py`
  - Kennzahlen/NPK‑Metriken: `src/horticalc/metrics.py`
  - Optional: Sluijsmann‑Kennzahlen (experimentell): `src/horticalc/sluijsmann.py`

Solver (Zielwerte → Rezept)
- Zweck: Ermittelt Gramm‑Mengen für eine erlaubte Dünger‑Liste, um gegebene Zielwerte (mg/L als Elemente) möglichst gut zu treffen.
- Eigenschaften:
  - Nichtnegative Lösung (keine negativen Gramm).
  - Relative Gewichtung (kleine Targets werden nicht automatisch „wegoptimiert“), milde Overshoot‑Strafe und zusätzliche Heuristiken (z. B. „singleton supplier“‑Pass) zur Reduktion typischer Übertreibungen einzelner Dünger.
  - In der Optimierung werden bestimmte Keys bewusst ignoriert (derzeit: S/SO4 sowie Na/Cl). Diese Werte werden trotzdem im finalen Ergebnis ausgerechnet und ausgegeben.
- Implementierung/Files:
  - Solver/Optimierer: `src/horticalc/solver.py`
  - Finales Ergebnis wird immer über dieselbe Kernberechnung gerechnet: `src/horticalc/core.py`

Dünger‑Editor (Stammdaten bearbeiten)
- Zweck: Bearbeiten/Normalisieren der Dünger‑Stammdaten in `data/fertilizers.csv` über die Web‑GUI.
- Typische Funktionen:
  - Große editierbare Tabelle (Sticky Header/Spalten) für schnelles Scannen und Editieren.
  - Speichern zurück in CSV über die API; Meta‑Spalten bleiben erhalten (werden nicht als Nährstoff interpretiert).
- Implementierung/Files:
  - Frontend: `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`
  - Backend‑API zum Laden/Speichern: `api/app.py` (nutzt `src/horticalc/data_io.py`)

---

## Quickstart (CLI)

Voraussetzung: Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .

# Rechner: Golden Recipe (Beispiel)
horticalc recipes/golden.yml --pretty

# Ergebnis in Datei
horticalc recipes/golden.yml --pretty --out solutions/golden_output.json

# Solver: Zielwerte -> Rezept (Hinweis: S/SO4 sowie Na/Cl werden in der Optimierung ignoriert)
horticalc solve recipes/solve_golden.yml --pretty
```

---

## GUI + API (Web UI)

Die GUI ist ein statisches Frontend unter `frontend/` und spricht eine FastAPI unter `api/` an.

- Backend starten:
```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```
- Frontend starten:
```bash
python -m http.server 5173 --directory frontend
```

URLs:
- API Health: `http://127.0.0.1:8000/health`
- Frontend: `http://127.0.0.1:5173/`

API (Auszug, relevant für GUI):
- `GET /health` – Healthcheck
- `POST /calculate` – Rechner‑API (RecipeRequest → CalculationResponse)
- `POST /solve` – Solver‑API (SolveRequest → SolveResponse)
- `GET /fertilizers` / `PUT /fertilizers` – Dünger‑Stammdaten laden/speichern
- `GET/POST/PUT /water-profiles` – Wasserprofile laden/speichern
- `GET/POST/PUT /nutrient-solutions` – Zielprofile (Nährlösungen) laden/speichern
- `GET/POST/PUT /recipes` – Rezepte laden/speichern

Hinweis: Details zur GUI (Layout/Bedienung) stehen zusätzlich in `docs/GUI.MD`.

---

## Datenmodell (Dateien und Bedeutung)

1) `data/fertilizers.csv` (Dünger‑Stammdaten)
- Enthält die Düngeranalysen als Massenanteile.
- Analysenwerte sind Anteile (z. B. `0,14` = 14%).
- N‑Formen:
  - In der CSV sind `NH4`, `NO3`, `Ur-N` als N‑Anteil (Element N) hinterlegt.
  - In der Ausgabe werden diese als `N_NH4`, `N_NO3`, `N_UREA` geführt.
- Oxid‑Deklarationen wie auf Etiketten: `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O`.
- Weitere deklarierte Formen: z. B. `SO4`, `CO3`, `SiO2`, `Cl`.
- `weight_factor` („Gewicht“): Skalierungsfaktor für Flüssigdünger (z. B. Dichte‑/Massenfaktor). Effektive Gramm = Gramm * weight_factor.
- Meta‑Spalten (z. B. `Nr.` mit Punkt) sind keine Nährstoffe; sie werden beim Laden ignoriert, bleiben aber beim Speichern erhalten.
- Historische Varianten wie `HCO3-V` werden nicht mehr geführt; es bleibt `HCO3`.

2) `data/molar_masses.yml` (Molmassen)
- Molare Massen für alle verwendeten Elemente/Verbindungen/Ionen, die für Umrechnungen und Ionenbilanz/EC benötigt werden.

3) `data/water_profiles/*.yml` (Wasserprofile)
- Wasserwerte in mg/L.
- `HCO3` wird als mg/L Bicarbonat geführt.
- Optional: `osmosis_percent` (0–100). Wasserwerte werden dann entsprechend gemischt/verdünnt (Osmose‑Anteil).

4) `data/nutrient_solutions/*.yml` (Zielprofile / Referenzlösungen)
- Zielwerte als `targets_mg_per_l` (mg/L als Elemente). Das ist kein Rezept, sondern ein Referenzprofil.

5) `recipes/*.yml` (Rezepte für den Rechner)
Ein Rezept definiert u. a.:
- `liters`
- `water_profile` (Name → Datei unter `data/water_profiles/`)
- `fertilizers: [{name, grams}, ...]`
- optional: `phosphate_species` (`H2PO4` oder `HPO4`) für die Ladungsbilanz
- optional: `urea_as_nh4` (Default `false`) – wenn `true`, wird Urea‑N als NH4+ behandelt (Hydrolyse‑Annahme)
- optional: `sluijsmann` – Konfiguration für zusätzliche Kennzahlen (siehe unten; experimentell)

Beispiele/Regressionen:
- `recipes/golden.yml`
- `recipes/green_go_12_12_36.yml`

6) `recipes/solve_*.yml` (Solver‑Rezepte)
Ein Solver‑Rezept definiert u. a.:
- `liters`
- `water_profile`
- `targets_mg_per_l` (mg/L als Elemente)
- `fertilizers_allowed` (Liste der nutzbaren Dünger‑Namen)
- optional: `fixed_grams` (Düngername → feste Gramm, die der Solver nicht verändern darf)
- optional: `phosphate_species`, `urea_as_nh4`
- optional: Solver‑Tuning (Gewichtungen/Heuristiken; siehe `src/horticalc/solver.py`)

Hinweis: In der Optimierung werden derzeit `S`, `SO4`, `Na`, `Cl` ignoriert. Diese Elemente/Ionen werden im finalen Ergebnis dennoch berechnet und ausgegeben.

---

## Was wird gerechnet? (Inhalte der Ausgabe)

### 1) Konzentrationen (mg/L)

Der Rechner liefert u. a. Totals als mg/L:
- Elemente: `N_total`, `N_NH4`, `N_NO3`, `N_UREA`, `P`, `K`, `Ca`, `Mg`, `Na`, `S`, `Cl`, `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`, `Si`, `C`
- Oxid‑Darstellung (wie Etiketten): `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O` usw. (zusätzlich zu den Element‑Totals)

Umrechnungen erfolgen stöchiometrisch über Molmassen, z. B.:
- `P2O5 → P` mit Faktor `2*M(P) / M(P2O5)`
- `K2O → K` mit Faktor `2*M(K) / M(K2O)`
- `CaO → Ca`, `MgO → Mg`, `Na2O → Na`, `SO4 → S`, `SiO2 → Si`, `CO3 → C`

Wasserprofil‑Spezialfall:
- `NH4`/`NO3` im Wasserprofil werden als Moleküle interpretiert und in `N_NH4`/`N_NO3` umgerechnet.
- In `fertilizers.csv` sind `NH4`/`NO3`/`Ur-N` bereits als „N‑Anteil“ (Element N) hinterlegt.

### 2) Ionen (mmol/L, meq/L) und Ladungsbilanz

Aus den Totals werden die Hauptionen für eine klassische Ladungsbilanz gebildet.

Kationen (typisch):
- `NH4+`, `K+`, `Ca2+`, `Mg2+`, `Na+`

Anionen (typisch):
- `NO3-`, `H2PO4-` oder `HPO4^2-` (je nach `phosphate_species`), `SO4^2-`, `Cl-`
- optional: `HCO3-` und `CO3^2-`

Ergebnis:
- Summe Kationen (meq/L)
- Summe Anionen (meq/L)
- Fehler in % (signed und absolut)

Wichtig: Phosphat‑Spezies ist pH‑abhängig; daher ist `phosphate_species` ein expliziter Schalter. Es wird hier nicht automatisch aus pH geschätzt.

### 3) EC (Electrical Conductivity) — Näherung

EC wird aus der Ionenzusammensetzung berechnet und ist eine Näherung.

- Ansatz:
  - Für unterstützte Ionen wird ein McCleskey‑Modell verwendet (temperaturabhängige Parameter + Korrektur über Ionenstärke).
  - Für einzelne Ionen existiert eine Fallback‑Leitfähigkeit (z. B. bei fehlenden McCleskey‑Parametern) mit einfacher Temperatur‑Skalierung.
  - Ionen ohne Parameter werden ignoriert und als „nicht abgedeckt“ gekennzeichnet.
- Ausgabe:
  - EC bei 18 °C und 25 °C
  - optional ein Beitrags‑Breakdown pro Ion
  - optional Transportzahlen
  - optional ATC‑Hochrechnung auf 25 °C über einen festen Alpha‑Faktor

Interpretation:
- Die EC‑Werte sind nicht „gemessen“, sondern aus Tabellen/Parametern berechnet.
- Abdeckung und Warnungen werden im EC‑Output mitgeführt (welche Ionen einbezogen/ignoriert wurden).
- Details, Formeln und Parameter sind in `docs/EC.md` dokumentiert.

### 4) Sluijsmann‑Kennzahlen (experimentell / hypothetisch)

Optional kann die Berechnung zusätzliche Kennzahlen nach „Sluijsmann“ erzeugen.
- Status: experimentell/hypothetisch; das Modell stammt aus der Agrarwirtschaft und ist nicht als Standard‑Werkzeug für hydroponische Nährlösungen etabliert.
- Aktivierung: über den Schlüssel `sluijsmann` im Rezept (siehe `recipes/*.yml`).
- Implementierung: `src/horticalc/sluijsmann.py` (Tests: `tests/test_sluijsmann.py`).

---

## Ordnerstruktur (relevant für Entwicklung)

```
.
├── api/
│   └── app.py
├── data/
│   ├── fertilizers.csv
│   ├── molar_masses.yml
│   ├── nutrient_solutions/
│   └── water_profiles/
├── docs/
│   ├── EC.md
│   ├── GUI.MD
│   └── ...
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── recipes/
│   ├── golden.yml
│   ├── green_go_12_12_36.yml
│   └── solve_golden.yml
├── solutions/
├── src/horticalc/
│   ├── __main__.py
│   ├── core.py
│   ├── data_io.py
│   ├── ec.py
│   ├── metrics.py
│   ├── sluijsmann.py
│   └── solver.py
├── tests/
│   ├── test_ec.py
│   ├── test_sluijsmann.py
│   └── test_solver_golden.py
├── pyproject.toml
├── requirements.txt
└── start_dev.bat
```

---

## Tests

```bash
python -m pytest -q
```
