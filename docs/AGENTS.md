# AGENTS.md

Dieses Dokument ist für „Agenten“ (Codex, ChatGPT, Menschen) gedacht, die am Code arbeiten.

## Kernanforderung
Excel soll **nicht** das Backend sein. Die Logik muss aus **CSV/YAML** gespeist werden.

## Was in dieser ZIP bereits umgesetzt ist

### 1) Backend-Export (bereits im Repo enthalten)
Aus dem Excel wurden die folgenden Artefakte in Textform übernommen:

- `data/fertilizers.csv` – entspricht „DüngerTab“
- `data/molar_masses.yml` – entspricht „MolareMasse“ (+ kleine Ergänzungen: C, Cl, CO3, SiO2)
- `data/water_profiles/default.yml` – entspricht „Wasserwerte“ (bereits mit deinem Verdünnungsfaktor angewandt)
- `recipes/golden.yml` – Golden Recipe Test
- `solutions/golden_output.json` – Ergebnis der Golden Recipe Berechnung (als Basis für manuelle Checks)

### 2) Core-Rechenlogik
`src/duengerrechner/core.py` implementiert:

- Stöchiometrische Umrechnung Oxide → Elemente über Molmassen
- N-Formen: NH4-N, NO3-N, Urea-N separat
- Wasser: NH4/NO3 als Moleküle → N
- Ionenbilanz (meq/L) für Hauptionen

### 3) CLI
`duengerrechner recipes/golden.yml --pretty` druckt ein kompaktes JSON auf stdout.

## Konventionen & Entscheidungen

### Stickstoff
- In `fertilizers.csv` sind `NH4`, `NO3`, `Ur-N` **N-Anteile als Element N**.
- Für die Ionenbilanz werden daraus (bei Bedarf) NH4 bzw. NO3 als Moleküle berechnet.
- `urea_as_nh4` ist eine Option (Hydrolyse), default **false**.

### Phosphat-Ladung
- In der Ionenbilanz ist `phosphate_species` wählbar:
  - `H2PO4` (−1) Default
  - `HPO4` (−2)

## Nächste Schritte
1. **Vergleich gegen Excel**: aktuell manuell über `solutions/golden_output.json` + Excel-Screenshot.
2. **Mehr Rezepte** als Regressionstests.
3. **GUI** aufsetzen (separates Paket, Core bleibt headless).
