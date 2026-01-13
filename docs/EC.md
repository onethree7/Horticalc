# Electrical Conductivity (EC)

## Motivation
EC (elektrische Leitfähigkeit) wird **ionenbasiert** berechnet. Das vermeidet unzuverlässige
ppm/TDS‑Faktoren und macht die Berechnung nachvollziehbar, sobald die Ionenspezies
und ihre Konzentrationen bekannt sind. Das Modell nutzt die in `ions_mmol_per_l` bereits
vorliegende Ionenzusammensetzung.

Primärquelle ist McCleskey et al. (2012), die ein praxistaugliches Leitfähigkeitsmodell
für natürliche Wässer mit Temperatur- und Ionenstärke‑Abhängigkeit angeben.

## Modelle und Formeln (Einheiten)

### (7) Leitfähigkeit aus Spezies
\[
\kappa = \sum_i k_i \cdot m_i
\]
- \(\kappa\): Leitfähigkeit der Lösung [mS/cm]
- \(k_i\): ionische molale Leitfähigkeit [mS·kg/(cm·mol)]
- \(m_i\): Molalität [mol/kg]

**Einheitencheck:**
\(k_i\) [mS·kg/(cm·mol)] × \(m_i\) [mol/kg] = [mS/cm].

### (8) Ionische molale Leitfähigkeit (McCleskey)
\[
 k(T,I) = k_0(T) - \frac{A(T)\sqrt{I}}{1 + B\sqrt{I}}
\]
- \(T\) in °C
- \(I\): Ionenstärke [mol/kg]

\(k_0(T)\) und \(A(T)\) werden als Polynome angegeben:
\[
 k_0(T) = a_2 T^2 + a_1 T + a_0
\]
\[
 A(T) = b_2 T^2 + b_1 T + b_0
\]

### (9) Ionenstärke
\[
 I = \tfrac{1}{2} \sum_i m_i z_i^2
\]
mit Ladung \(z_i\) (z. B. +2 für Ca²⁺).

### (6) Transportzahlen
\[
 t_i = \frac{k_i m_i}{\sum_j k_j m_j}
\]

### (2) ATC/EC25 (optional)
\[
 \kappa_{25} = \frac{\kappa_T}{1 + \alpha (T - 25)}
\]
Standardwert \(\alpha = 0.019\) (typisch 0.019–0.020). Diese Normierung ist **optional**
und unabhängig von der physikalischen Temperaturabhängigkeit im McCleskey‑Modell.

## Parameter (McCleskey Table 1)
Die Parameter werden aus **Table 1** in McCleskey et al. (2012) transkribiert und im Code
unter `src/horticalc/ec.py` als `MCCLESKEY_PARAMS` gepflegt.

**Abgedeckte Ionen (mindestens):**
K⁺, Na⁺, NH₄⁺, Ca²⁺, Mg²⁺, Cl⁻, SO₄²⁻, NO₃⁻, HCO₃⁻, CO₃²⁻

## Fallback: Ionen ohne McCleskey‑Parameter
Für Ionen, die in Table 1 nicht enthalten sind (z. B. **H₂PO₄⁻**), verwenden wir
Vanysek (CRC Handbook, 93rd ed.) mit **limiting ionic molar conductivity** \(\lambda^\circ\)
bei 25 °C:

- H₂PO₄⁻: \(\lambda^\circ_{25} = 36\) (S·cm²/mol)

Temperaturkorrektur (Näherung):
\[
\lambda(T) = \lambda(25)\,[1 + \beta (T - 25)]
\]
mit \(\beta = 0.022\) (Standard; ca. 2–3 %/°C). Optional kann \(\beta = 0\) gesetzt werden,
wenn keine Temperatur-Skalierung gewünscht ist.

Beitrag zur Leitfähigkeit (Verdünnungsannahme):
\[
\kappa_i \approx \lambda(T) \cdot c_i
\]
mit \(c_i\) in mol/L und \(\lambda\) in S·cm²/mol, wodurch **numerisch mS/cm**
resultiert (1 L = 1000 cm³; mS = 10⁻³ S). Das ist eine gemischte, aber in verdünnten
Lösungen konsistente Näherung.

## Annahmen & Grenzen
- **Molalität** wird aus mol/L mit fester Dichte \(\rho = 1.0\) kg/L angenähert.
- Fehlende Spezies (z. B. H⁺/OH⁻, Komplexe) werden nicht berücksichtigt.
- Phosphat‑Spezies (H₂PO₄⁻ vs. HPO₄²⁻) hängt vom pH; wir verwenden die bereits
  im Core gewählte Speziation.
- Fallback‑Ionen haben keine Ionenstärke‑Korrektur; nur verdünnt belastbar.

## Workflow
1. Rezept → Ionen (mmol/L) in `ions_mmol_per_l`.
2. Umrechnung zu Molalität (mol/kg).
3. Ionenstärke \(I\) berechnen.
4. Für jedes T: \(k_i(T,I)\) und Beiträge \(k_i m_i\) summieren.
5. EC18/EC25, Beiträge, Transportzahlen ausgeben.
6. Optional ATC‑Normierung auf 25 °C.

## Output
Die Berechnung wird als neuer Knoten `ec` im Ergebnis‑JSON ausgegeben:

```
"ec": {
  "ec_mS_per_cm": {"18.0": ..., "25.0": ...},
  "ec_uS_per_cm": {"18.0": ..., "25.0": ...},
  "contrib_mS_per_cm": {"18.0": {"K+": ...}, "25.0": {...}},
  "transport_numbers": {"18.0": {...}, "25.0": {...}},
  "ionic_strength_mol_per_kg": ...,
  "warnings": [...]
}
```

Für die reinen Wasserwerte wird zusätzlich `ec_water` (gleiche Struktur) ausgegeben.

## Optional: EC-Validierung mit pyEQL
Für einen Abgleich mit einer externen Bibliothek kann die optionale
EC‑Validierung über pyEQL aktiviert werden. Das beeinflusst **nicht** das primäre
McCleskey‑Ergebnis, sondern liefert lediglich Vergleichswerte.

Beispiel (Recipe/API):
```
ec_validation:
  enabled: true
  engine: pyeql
  engine_variant: native
  temperature_c: 25
  ph: 7.0
```

Output:
```
"ec_validation": {
  "enabled": true,
  "status": "ok",
  "engine": "pyeql",
  "engine_variant": "native",
  "temperature_c": 25.0,
  "pyeql_ec_mS_per_cm": ...,
  "primary_ec_mS_per_cm": ...,
  "delta_mS_per_cm": ...,
  "warnings": [...]
}
```

## Quellen
- McCleskey RB, Nordstrom DK, Ryan JN, Ball JW. **A new method of calculating electrical
  conductivity with applications to natural waters.** Geochimica et Cosmochimica Acta 77
  (2012) 369–382. DOI: 10.1016/j.gca.2011.10.031. (Eq. 2, 6–9; Table 1)
- Vanysek P. **Ionic Conductivity and Diffusion at Infinite Dilution.** In: CRC Handbook
  of Chemistry and Physics, 93rd Edition. (\(\lambda^\circ\) Tabellenwerte, u.a. H₂PO₄⁻)
