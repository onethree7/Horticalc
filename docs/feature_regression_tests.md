# Feature: Regressionstest-Rezept (Green-Go 12-12-36)

## Kontext
Wir ergänzen ein zweites Rezept als Regressionstest, damit die Kernlogik nicht nur am Golden-Recipe validiert wird.

## Umsetzung
- Neues Rezept: `recipes/green_go_12_12_36.yml`
- Referenz-Output: `solutions/green_go_12_12_36_output.json`

## Ausführen
```bash
PYTHONPATH=src python -m horticalc recipes/green_go_12_12_36.yml --pretty
PYTHONPATH=src python -m horticalc recipes/green_go_12_12_36.yml --pretty --out solutions/green_go_12_12_36_output.json
```

## Akzeptanzkriterium
Die Ausgabe muss deterministisch bleiben (JSON-Keys und Werte), damit Regressionen sichtbar sind.
