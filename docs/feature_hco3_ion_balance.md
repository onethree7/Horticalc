# Feature: HCO3-Wirkung je Stickstofftyp

## Ziel
Die HCO3- (Bicarbonat-)Wirkung soll als eigene Sparte in der Berechnung abgebildet werden.
Im Excel gab es dafür Formeln, die je Stickstofftyp eine numerische Wirkung (+/-) abbilden.

## Anforderungen
- Pro N-Form (NH4, NO3, Urea) eine HCO3-Wirkung erfassen und berechnen.
- Für bestimmte Dünger/N-Formen sind die Werte **bekannt** und werden direkt hinterlegt,
  nicht aus einer Formel abgeleitet.
- Ergebnis sollte im Output als eigene Kennzahl / Sparte sichtbar sein.

## Hinweise
- Diese Logik darf **nicht** wieder aus Excel kommen, sondern aus CSV/YAML bzw.
  einer klaren Konfiguration im Repo.
