# Feature: Osmose-Mix im Core

## Ziel
Der Core soll den Osmosewasser-Anteil aus dem Wasserprofil (oder optional aus dem Rezept)
auslesen und die Wasserwerte entsprechend verdünnen. Der verwendete Osmoseanteil muss im
Output sichtbar sein.

## Anforderungen
- Wasserprofile können `osmosis_percent` definieren (0–100).
- Rezept kann den Wert optional überschreiben.
- Core mischt die Wasserwerte mit RO-Wasser (0 mg/L) und nutzt die gemischten Werte für
  alle Wasser-baseline Berechnungen.
- Output enthält den verwendeten `osmosis_percent`.
