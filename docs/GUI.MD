# GUI – Arbeitsbeschreibung (auf Basis der referenzierten Screenshot-Ansicht)

Dieses Dokument fasst die aktuelle, theoretische GUI semantisch zusammen. Die Beschreibung orientiert sich **primär am Screenshot** und ergänzt die Anforderungen aus dem Text nur dort, wo sie das Bild sinnvoll ergänzen (z. B. Datenbankgröße, Dropdown-Behavior, spätere EC-Funktion).

## 1) Kopfbereich: Vorauswahl der Düngerkomponenten

**Zweck:** Auswahl der bis zu 10 verwendeten Dünger aus der Datenbank.

**Layout & Inhalte (Screenshot-basiert):**
- Tabellenkopf „Vorauswahl der Düngerkomponenten“.
- Pro Zeile ein auswählbarer Düngername (Dropdown).
- Begleitspalten: `Nr.`, `Dünger Name`, `Form`, `Gewicht`.
- Nährstoffspalten in Prozentangaben/Anteilen pro Dünger:
  - `N_total`, `P2O5`, `K2O`, `CaO`, `MgO`, `Na2O`, `SO4`
  - Spurenelemente/Ionen: `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`, `Cl`, `CO3`, `SiO2`, `HCO3-V`
- Beispielwerte zeigen, dass es sich um Dünger-Analysewerte handelt (z. B. NPK/oxidische Formen).

**Ergänzende Anforderung (aus Text):**
- Dropdown muss eine **lange Dünger-Datenbank (150+ Einträge)** unterstützen (scrollbar, optional Sidebar/Filter).
- Es sind **maximal 10 Dünger** auswählbar (entspricht der 10‑Zeilen-Struktur).

## 2) Zentraler Block: Düngercalculator / Nährstoffmengen

**Zweck:** Eingabe der Dünger-Mengen und Berechnung der Nährstoffmengen in verschiedenen Einheiten.

**Layout & Inhalte (Screenshot-basiert):**
- Kopfzeile mit **Düngername** und **Menge eingeben** (pro ausgewähltem Dünger).
- Pro Dünger wird eine Zeile mit Mengen (Zahlenfeld) geführt.
- Nährstoffspalten spiegeln die Auswahl aus dem oberen Block (N_total, P2O5, K2O, CaO, …, HCO3‑V).
- Linke Seitenleiste mit **EC‑Parametern**:
  - EC‑Feinjustierung (Dünger), EC‑Dünger (bei 18°/25°), EC‑Gesamt (bei 18°/25°).
  - Kalk-Parameter: „Proportionale Kalkrechnung der Oxide“, „Kalkrechnung“, „Kalkbalance“, „Stickstoffmodifikator“.

**Berechnungsausgaben (Screenshot + Ergänzung):**
Es gibt mehrere **Summenzeilen** im Bereich der Nährstoffmengen:
- **Nährstoffmenge Dünger**: in `g` und in `mg`
- **Nährstoffmenge Dünger + Wasser**: in `g` und in `mg`
- **Nährstoffmenge Dünger + Wasser (aka ppm)**: in `mg/l`

**Zentrales Element:**
- Der **Hauptwert** ist **„Nährstoffmenge Dünger + Wasser aka ppm (mg/l)“**.
- Alle anderen Mengen sind unterstützend, müssen aber mitberechnet werden.

**Hinweis für spätere Iteration:**
- **EC‑Berechnung ist noch nicht final** (der Block ist sichtbar, aber die endgültige EC‑Logik kommt später).

## 3) Unterer Block: Einzelne Ionen & Nährstoffverhältnisse

**Zweck:** Ionenspezifische Auswertung (mg/l) und Verhältnisberechnungen.

**Layout & Inhalte (Screenshot-basiert):**
- Tabellenblock **„Einzelne Ionen“** mit Spalten:
  - `N_total`, `P`, `K`, `Ca`, `Mg`, `Na`, `S`
  - Spurenelemente: `Fe`, `Mn`, `Cu`, `Zn`, `B`, `Mo`, `Cl`, `C`, `Si`
  - `HCO3‑V (mg/l)`
- Zeilenstruktur analog zum zentralen Block:
  - `Nährstoffm. Dünger+Wasser in g`
  - `Nährstoffm. Dünger+Wasser in mg`
  - **`Nährstoffm. Dünger+Wasser aka ppm in mg/l`** (hier soll man wieder zum Hauptwert kommen)

**Nährstoffverhältnisse (rechter Block im Screenshot):**
- Tabellenkopf „Nährstoffverhältnisse“ mit Spalten `Von Zu`, `IST`, `Min`, `Max`.
- Beispiele (aus Screenshot): `CaO zu K2O`, `MgO zu CaO`, `Na2O zu MgO`, `SO4 zu P2O5`, `P2O5 zu K2O`, `Fe zu MgO`, `CO3 zu SiO2`.

**Zusätzliche Berechnungen (Screenshot):**
- **Ionenbilanzfehler** mit Anionen/Kationen (meq/L) und Summenbereich.
- **NPK‑Verhältnisse der Oxidformen** (z. B. „Gesamt NPK all %“, „Phosphor NPK%“, „N zu P zu K %“).

## 4) Interaktions- und Datenlogik (kompakt)

- Nutzer wählt **bis zu 10 Dünger** im Kopfbereich aus.
- Pro ausgewähltem Dünger wird im Calculator eine **Menge** eingegeben.
- Das System berechnet:
  - Nährstoffmengen aus Dünger,
  - Nährstoffmengen aus Dünger + Wasser,
  - **ppm (mg/l)** als zentralen Zielwert.
- Im unteren Block werden die **einzelnen Ionen** in g/mg/mg/l aufgeschlüsselt und müssen **konsistent** zum zentralen ppm‑Wert sein.
- **EC‑Berechnung** ist als UI‑Element vorgesehen, wird aber erst später vollständig umgesetzt.

---

**Hinweis zur Weiterarbeit:** Dieses Dokument dient als Leitfaden für die GUI‑Umsetzung. Der Screenshot gilt als Referenz für die semantische Struktur; zusätzliche Anforderungen (z. B. 150+ Dünger mit Dropdown-Scroll) ergänzen die Darstellung.

---

# Architektur‑Skizze (einmal UI, Web + Desktop)

Ziel: **Eine einzige UI** für Web + Windows + Linux (Desktop‑Wrapper).

## Module & Verantwortungen

### Core (bestehend, headless)
- Pfad: `src/horticalc/`
- Liest CSV/YAML (`data/`) und liefert Berechnungsergebnisse als JSON.

### API‑Schicht (neu)
- Stellt Core‑Berechnungen als REST‑API bereit.
- Beispiel (siehe `api/app.py`):
  - `GET /fertilizers` → Liste der Dünger (Dropdown, 150+ Einträge)
  - `GET /water-profiles` → verfügbare Wasserprofile
  - `POST /calculate` → Berechnung (ppm, g, mg, Ionen, Verhältnisse)

### Frontend (ein einziges UI)
- Web‑UI (React/Vue/Svelte + DataGrid).
- Komponenten:
  1. **FertilizerSelectorGrid** (10 Zeilen, Dropdown, Filter/Scroll)
  2. **CalculatorGrid** (Mengen + Summen g/mg/ppm)
  3. **IonBreakdownGrid** (Ionen g/mg/mg/l)
  4. **RatiosPanel** (IST/Min/Max)
  5. **Sidebar** (EC‑Felder später aktivieren)

### Desktop‑Wrapper
- **Tauri** oder **Electron** lädt dasselbe Frontend und spricht lokal mit der API.

## Datenfluss (vereinfacht)

```
Frontend (Auswahl + Mengen)
      ↓
POST /calculate (API)
      ↓
Core (CSV/YAML → Berechnung)
      ↓
Frontend rendert Tabellen & ppm
```
