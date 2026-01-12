# GUI – Aktueller Stand der Web‑UI

Dieses Dokument beschreibt die **aktuelle** GUI, wie sie im Ordner `frontend/` umgesetzt ist.
Der Fokus liegt auf den vorhandenen Bereichen, Datenflüssen und UI‑Elementen.

## 1) Kopfbereich: API‑Verbindung

**Zweck:** Verbindung zur FastAPI konfigurieren und Daten neu laden.

**Inhalte:**
- Eingabefeld **API Base URL** (`http://localhost:8000` als Default).
- Button **„Dünger laden“** (lädt Dünger und Wasserprofile neu).

## 2) Wasserwerte (Profile + Eingabe)

**Zweck:** Wasserprofil laden/speichern und manuelle Werte pflegen.

**Inhalte & Funktionen:**
- Einklappbarer Bereich („Wasserwerte anzeigen“).
- **Profile auswählen**, **Laden**, **Reset Default**.
- **Profilname speichern** (Profil als YAML über API speichern).
- **Osmoseanteil (%)** zur Verdünnung.
- **Einheiten‑Toggle** (mg/L ↔ mol/L Darstellung/Eingabe).
- Tabelle **Parameter/Wert/Einheit** für alle Wasser‑Parameter (NH4, NO3, PO4, K, Ca,
  Mg, Na, SO4, Spurenelemente, Cl, HCO3/CO3, CaCO3, KH, SiO2).

## 3) Vorauswahl der Düngerkomponenten

**Zweck:** Auswahl der Dünger aus der Datenbank.

**Inhalte:**
- Tabelle mit Spalten **#**, **Dünger (Dropdown)**, **Form**, **Gewicht**.
- Buttons **+ / -** zum Hinzufügen/Entfernen von Zeilen.
- Dropdowns greifen auf die geladene Dünger‑Datenbank zu.

## 4) Düngercalculator

**Zweck:** Eingabe der Gramm‑Mengen pro ausgewähltem Dünger und Start der Berechnung.

**Inhalte:**
- Tabelle mit **Düngername** (aus Auswahl) und **Menge (g)**.
- Button **„Berechnen“** ruft `/calculate` auf.

**Ergebnis‑Karten:**
- **NPK Gesamt (%)**
- **NPK P‑Norm**
- **NPK Verhältnis (%)**
- **EC‑Werte** für Wasser sowie Wasser + Dünger (EC18/EC25)

**Zusammenfassung:**
- Tabelle **„Oxidformen & Ionen (ppm, mg/l)“** mit Spaltenpaaren
  (Oxid‑Deklaration + Element), inkl. Spurenelemente sowie Na2O/Na, Cl, HCO3.

## 5) Ionenbilanz

**Zweck:** Sichtbarkeit der Ladungsbilanz.

**Inhalte:**
- Tabelle **Ionen (meq/L)** mit Einzelwerten.
- Tabelle **Bilanz** mit Summen/Fehlern.

## Datenfluss (kurz)

1. Dünger & Wasserprofile werden von der API geladen.
2. Nutzer wählt Dünger, trägt Mengen ein und pflegt Wasserwerte.
3. GUI sendet `fertilizers`, `liters`, `water_profile_name` oder `water_mg_l`
   an `/calculate`.
4. Ergebnis‑JSON befüllt NPK‑Karten, EC‑Werte, Zusammenfassung und Ionenbilanz.
