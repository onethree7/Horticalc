# Speciation (pH, Aktivitäten, Ausfällungen)

## Überblick
Der Speciation‑Schritt ist optional und liefert „Real‑Chemistry“‑Ergebnisse wie pH,
Aktivitätskoeffizienten und Sättigungsindizes (Ausfällungs‑Warnungen). Er wird **nur**
ausgeführt, wenn er explizit aktiviert ist.

Aktuell unterstützt der Core als Backend **pyequion2**. Das Paket wird **nicht**
automatisch installiert, um das Grundsetup leichtgewichtig zu halten.

## Aktivierung im Rezept

Minimal:
```yaml
speciation: true
```

Erweitert:
```yaml
speciation:
  enabled: true
  backend: pyequion2
  activity_model: PITZER  # IDEAL | DEBYE | EXTENDED_DEBYE | PITZER
  temperature_c: 25.0
  include_gas_phases: false
```

## Output
Im Ergebnis‑JSON erscheint ein `speciation`‑Block, z. B.:
```json
{
  "speciation": {
    "status": "ok",
    "ph": 6.8,
    "ionic_strength_mol_per_kg": 0.02,
    "activity_coefficients": { "Ca++": 0.56, "...": 1.0 },
    "saturation_indexes": { "Calcite": -0.4 },
    "precipitation_warnings": [
      { "phase": "Gypsum", "saturation_index": 0.2, "saturation_ratio": 1.58 }
    ]
  }
}
```

## Unterstützte Elemente
Die Speciation arbeitet elementbasiert. pyequion2 unterstützt u. a.:
`C, N, P, S, Ca, Mg, K, Na, Cl, Fe, Mn, Cu, Zn`. Spurenelemente außerhalb dieses
Spektrums (z. B. B, Mo, Si) werden aktuell ignoriert und im `speciation.skipped_elements`
gelistet.

## Installation (optional)
```bash
python -m pip install pyequion2
```

> Hinweis: pyequion2 bringt optionale GUI‑Abhängigkeiten mit. Der Core nutzt nur die
> Berechnungs‑Module; fehlende GUI‑Libraries führen dann nicht zu einem Crash im Core,
> solange das Paket installiert ist.
