# Speciation (pH, Aktivitätskoeffizienten, Ausfällung)

## Ziel
Horticalc kann optional eine chemische Gleichgewichts‑Speziation durchführen.
Dabei werden pH, Aktivitätskoeffizienten und mögliche Ausfällungen (Sättigung)
auf Basis der aktuellen Ionen‑/Elementzusammensetzung berechnet.

## Optionaler Stack
Die Speziation ist **optional** und standardmäßig deaktiviert. Aktuell wird
`pyequion2` unterstützt. Wenn das Paket fehlt, wird eine Fehlermeldung im
Speciation‑Block ausgegeben, ohne den Rest der Berechnung zu verändern.

## Aktivierung (Recipe/API)
```
speciation:
  enabled: true
  engine: pyequion2
  activity_model: PITZER
  temperature_c: 25
  precipitation_si_threshold: 0.0
```

Alternativ kann `speciation_enabled: true` gesetzt werden, um das `enabled`
Flag direkt zu überschreiben.

## Output (JSON)
```
"speciation": {
  "enabled": true,
  "status": "ok",
  "engine": "pyequion2",
  "activity_model": "PITZER",
  "temperature_c": 25.0,
  "ph": 5.8,
  "ionic_strength_molal": 0.012,
  "activity_coefficients": {"Ca++": 0.63, ...},
  "saturation_indexes": {"Calcite": -0.5, ...},
  "precipitation_risks": [
    {"phase": "Gypsum", "saturation_index": 0.2, "saturation_ratio": 1.58}
  ],
  "warnings": []
}
```

## Hinweise & Grenzen
- Nur Elemente, die von `pyequion2` unterstützt werden, werden verwendet
  (z. B. Ca, Mg, K, Na, Cl, S, N, P, C).
- Wasseraktivität und Dichte werden in der aktuellen Implementierung
  standardmäßig angenähert.
- Fehlende Bibliotheken oder fehlende Molmassen werden als Warnungen
  zurückgegeben, ohne den Core‑Output zu beeinflussen.
