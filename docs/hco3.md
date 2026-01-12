## **Goal:** A computable scheme for an “HCO₃⁻ vector” from nutrients

Below is a compact, implementation‑oriented framework you can feed into a CODEX/solver. It is based on carbonate chemistry plus the nutrient–pH relations described for hydroponic solutions  (Leibar-Porcel et al., 2020; Langenfeld et al., 2022; Tellbüscher et al., 2024; Rijck & Schrevens, 1997).

### Unit mapping for solver inputs (recipe + water profile)

**Recipe inputs → mmol/L ions (pH/DIC solver).** The recipe/fertilizer layer is expressed as **mg/L oxide or element forms** (see `data/fertilizers.csv`). In `src/horticalc/core.py`, oxide forms are first converted to elemental mg/L in `_oxide_to_element` (e.g., `P2O5 → P`, `K2O → K`, `CaO → Ca`), then element or ionic species are converted to mmol/L by dividing by the molar mass. For N forms, `_n_element_to_molecule` and `_n_molecule_to_element` govern the NH4/NO3 mg/L ⇄ N‑element conversions before the mmol/L step. This means the pH/DIC solver should expect **mmol/L ions** (K⁺, Ca²⁺, Mg²⁺, NH₄⁺, NO₃⁻, SO₄²⁻, H₂PO₄⁻/HPO₄²⁻, HCO₃⁻/CO₃²⁻) derived from those oxide/element mg/L entries in the recipe.

**Water profile inputs → DIC/alkalinity.** `normalize_water_profile` in `src/horticalc/core.py` accepts water profiles in **mg/L** and normalizes them into the same oxide/ion keys used above. For alkalinity, it explicitly maps:

- `HCO3` (mg/L) → kept as **mg/L HCO₃⁻** (direct DIC input).
- `CaCO3` (mg/L) → **mg/L HCO₃⁻** via `hco3_from_caco3`, using CaCO₃ equivalent weight (`CaCO3 / 2`) before converting to HCO₃⁻.
- `KH` (°dKH) → **mg/L CaCO₃** via `17.848 * dKH`, then to **mg/L HCO₃⁻** via `hco3_from_caco3`.

Once normalized, convert water‑profile `HCO3` mg/L to **mmol/L HCO₃⁻** (divide by molar mass) and treat this as the **water DIC/alkalinity input** to the pH/DIC solver.

### Assumptions (current)

- **Temperature reference:** 25 °C for equilibrium constants.
- **Kw value:** use `Kw = 1e-14` at 25 °C (or `Kw = [H⁺][OH⁻]` with temperature‑specific constants if you implement it).
- **Simplifications:** fixed phosphate pKa (e.g., pKa2 ≈ 7.2) and no ionic‑strength corrections.
- **Note:** these constants should be centralized in the backend when implemented.

### 1. Define what your “HCO₃⁻ vector” represents

Use a state vector per solution (or time step):

- `H_vec = [C_DIC, C_CO2aq, C_HCO3, C_CO3, pH]`

Where:

- `C_DIC` = total dissolved inorganic C from water and fertilizers  
  `= C_CO2aq + C_HCO3 + C_CO3`  
- Speciation (`C_CO2aq`, `C_HCO3`, `C_CO3`) is controlled by pH and equilibrium constants.

Your CODEX should, given a nutrient recipe, compute:
1) the **DIC input from fertilizers**,  
2) the **pH implied by nutrient composition**,  
3) **carbonate speciation** from pH, then export `H_vec`.

---

## 2. Step 1 – Parse nutrient recipe into acid/base equivalents

Follow Rijck & Schrevens: pH in nutrient solutions is governed mainly by **H₂PO₄⁻ / HPO₄²⁻**, **NH₄⁺**, and **HCO₃⁻ / CO₃²⁻**  (Rijck & Schrevens, 1997).

For each salt in the recipe (per liter):

- Convert to mmol of each ion.
- Classify ions:

  - **Strong cations:** K⁺, Ca²⁺, Mg²⁺, Na⁺  
  - **Strong anions:** NO₃⁻, Cl⁻, SO₄²⁻  
  - **Weak‑acid / weak‑base species:**  
    - N: NH₄⁺ (weak acid), NO₃⁻ (neutral for acid–base)  
    - P: H₂PO₄⁻ / HPO₄²⁻ (buffer pair)  
    - C: HCO₃⁻ / CO₃²⁻ / CO₂(aq) (buffer pair)  (Leibar-Porcel et al., 2020; Zhang et al., 2024; Rijck & Schrevens, 1997)

Compute:

```text
Alk_tot ≈ [strong cations charge] – [strong anions charge]
          + (α_P_base * C_P_total) + (α_C_base * C_DIC_initial) – [NH4+ equivalents]
```

Where:
- `α_P_base` ≈ fraction of phosphate present as HPO₄²⁻ at your target pH  
- `α_C_base` ≈ fraction of DIC present as (HCO₃⁻ + 2·CO₃²⁻) per mole C (depends on pH)  
- For a first pass, you can treat `NH4+` as +1 equivalent of acid (it will lower pH relative to nitrate solutions)  (Langenfeld et al., 2022; Rijck & Schrevens, 1997).

This gives you an **alkalinity / charge excess**, which constrains possible pH solutions.

---

## 3. Step 2 – Include fertilizer‑derived DIC

Typical hydroponic salts:

- **KHCO₃, NaHCO₃:**  
  DIC contribution: `C_DIC_fert += [HCO3−]_added`  (Zhang et al., 2024)
- **carbonate‑containing or lime‑treated salts (rare in hydroponics)**:  
  DIC from CO₃²⁻: `C_DIC_fert += [CO3²−]_added`

So:

```text
C_DIC_initial = C_DIC_water + C_DIC_fert
```

If you know water alkalinity in mg/L CaCO₃, convert to mmol/L DIC equivalent.

---

## 4. Step 3 – Compute pH from nutrient composition

Rijck & Schrevens give analytical formulas for nutrient‑solution pH from [H₂PO₄⁻], [NH₄⁺], and [HCO₃⁻]  (Rijck & Schrevens, 1997). If you do not implement their exact formulas, use this numerical scheme:

1. Fix `C_DIC_initial`, `C_P_total`, `C_NH4`, `C_strong_cations`, `C_strong_anions`.
2. For a trial pH:

   - Compute carbonate distribution using equilibrium constants (25 °C)  (Rijck & Schrevens, 1997):

     ```text
     K1 ≈ 10^(-6.35)    (CO₂ + H₂O ⇌ H⁺ + HCO₃⁻)
     K2 ≈ 10^(-10.33)   (HCO₃⁻ ⇌ H⁺ + CO₃²⁻)

     α0 = 1 / (1 + K1/[H⁺] + K1*K2/[H⁺]²)         (fraction as CO₂(aq))
     α1 = (K1/[H⁺]) * α0                          (fraction as HCO₃⁻)
     α2 = (K1*K2/[H⁺]²) * α0                      (fraction as CO₃²⁻)

     C_CO2 = α0 * C_DIC_initial
     C_HCO3 = α1 * C_DIC_initial
     C_CO3  = α2 * C_DIC_initial
     ```

   - For phosphate (simplified):

     ```text
     pKa2 (H2PO4− ⇌ H+ + HPO4²−) ≈ 7.2

     β1 = 1 / (1 + 10^(pH − 7.2))            (fraction as H2PO4−)
     β2 = 1 − β1                              (fraction as HPO4²−)

     C_H2PO4 = β1 * C_P_total
     C_HPO4  = β2 * C_P_total
     ```

3. Write electroneutrality:

```text
[H⁺]
+ (C_NH4)
+ (C_K + 2C_Ca + 2C_Mg + C_Na)
= (C_NO3 + C_Cl + 2C_SO4
   + C_H2PO4 + 2C_HPO4
   + C_HCO3 + 2C_CO3)
+ [OH⁻]
```

Where `[OH⁻] = Kw / [H⁺]`.

4. Solve for pH such that LHS – RHS = 0 (e.g., Newton–Raphson or bisection). This gives you a **self‑consistent pH** determined by the nutrient composition and DIC  (Langenfeld et al., 2022; Tellbüscher et al., 2024; Rijck & Schrevens, 1997).

This step captures:  
- Strong impact of NH₄⁺ vs NO₃⁻ ratio on pH  (Langenfeld et al., 2022; Rijck & Schrevens, 1997)
- Buffering by HCO₃⁻ and phosphate  (Leibar-Porcel et al., 2020; Zhang et al., 2024; Rijck & Schrevens, 1997).

---

## 5. Step 4 – Extract the “HCO₃⁻ vector”

Once pH converges:

```text
H_vec = [
  C_DIC_initial,
  C_CO2,      # α0*C_DIC_initial
  C_HCO3,     # α1*C_DIC_initial
  C_CO3,      # α2*C_DIC_initial
  pH
]
```

You can also store **HCO₃⁻ alkalinity**:

```text
Alk_C = C_HCO3 + 2*C_CO3
```

This is the part that interacts strongly with Fe, P, Zn solubility and uptake  (Leibar-Porcel et al., 2020; Zhao & Wu, 2017; Ilyas et al., 2025).

---

## 6. Hooking to plant uptake / time evolution (optional layer)

For dynamic simulations like NFT or recirculating systems, combine the above chemistry with a **mass balance / uptake module**  (Langenfeld et al., 2022; Vought et al., 2024; Tellbüscher et al., 2024):

At each time step `Δt`:

```text
C_DIC(t+Δt) = C_DIC(t)
              + (DIC_in_from_topup − DIC_out_through_drain)/V
              − U_DIC_by_plants/V
              ± gas_exchange_term
```

- Use empirical uptake / loss terms similar to the N, P, K mass balance frameworks in hydroponics  (Langenfeld et al., 2022; Vought et al., 2024).  
- After updating `C_DIC`, re‑run Steps 3–4 to get new pH and speciation.

---

## 7. How nutrient forms map into this logic (examples)

Your CODEX can have **rules/templates** per fertilizer:

- KNO₃ → `+K⁺`, `+NO₃⁻` (neutral for acid–base)  
- Ca(NO₃)₂ (Calcinit) → `+Ca²⁺`, `+2 NO₃⁻`  
- MgSO₄ (Bittersalz) → `+Mg²⁺`, `+SO₄²⁻`  
- KH₂PO₄ → `+K⁺`, `+H₂PO₄⁻` (adds to phosphate buffer)  
- NH₄H₂PO₄ → `+NH₄⁺` (acid), `+H₂PO₄⁻`  
- KHCO₃ → `+K⁺`, `+HCO₃⁻` (direct DIC + alkalinity)  (Leibar-Porcel et al., 2020; Zhang et al., 2024)

CODEx then:

1. Parses grams/L → mmol/L of each ion.  
2. Fills the variables used in Steps 2–4.  
3. Returns `H_vec`.

---

## 8. Why this is consistent with the literature

- Bicarbonate used explicitly as buffer in lettuce nutrient solutions stabilizes pH between 7.2–7.7, with uptake effects only at high levels, showing that **HCO₃⁻ concentration plus nutrient composition jointly set pH and speciation**  (Leibar-Porcel et al., 2020; Zhang et al., 2024).  
- Nutrient‑solution pH is a **deterministic function of composition** (H₂PO₄⁻, NH₄⁺, HCO₃⁻ and strong ions), and analytical formulas for this relationship are available  (Rijck & Schrevens, 1997).  
- Mass‑balance approaches for nutrients in recirculating hydroponics show how such chemistry modules can be coupled to uptake and dosing control  (Langenfeld et al., 2022; Vought et al., 2024; Wei et al., 2025; Tellbüscher et al., 2024).

This gives you a clear, modular “calculation model” for an HCO₃⁻/+CO₃²⁻ vector driven by the underlying NPK + micronutrient forms.
 
_These papers were sourced and synthesized using Consensus, an AI-powered search engine for research. Try it at https://consensus.app_
 
## References
 
Leibar-Porcel, E., McAinsh, M., & Dodd, I. (2020). Elevated Root-Zone Dissolved Inorganic Carbon Alters Plant Nutrition of Lettuce and Pepper Grown Hydroponically and Aeroponically. *Agronomy*. https://doi.org/10.3390/agronomy10030403
 
Langenfeld, N., Pinto, D., Faust, J., Heins, R., & Bugbee, B. (2022). Principles of Nutrient and Water Management for Indoor Agriculture. *Sustainability*. https://doi.org/10.3390/su141610204
 
Vought, K., Bayabil, H., Pompeo, J., Crawford, D., Zhang, Y., Correll, M., & Martin-Ryals, A. (2024). Dynamics of micro and macronutrients in a hydroponic nutrient film technique system under lettuce cultivation. *Heliyon*, 10. https://doi.org/10.1016/j.heliyon.2024.e32316
 
Zhao, K., & Wu, Y. (2017). Effects of Zn Deficiency and Bicarbonate on the Growth and Photosynthetic Characteristics of Four Plant Species. *PLoS ONE*, 12. https://doi.org/10.1371/journal.pone.0169812
 
Wei, C., Li, Z., Zhu, D., Xu, T., Liang, Z., Liu, Y., & Zhao, N. (2025). Regulation of the physicochemical properties of nutrient solution in hydroponic system based on the CatBoost model. *Comput. Electron. Agric.*, 229, 109729. https://doi.org/10.1016/j.compag.2024.109729
 
Tellbüscher, A., Van Hullebusch, E., Gebauer, R., & Mráz, J. (2024). Assessing the fate and behaviour of plant nutrients in aquaponic systems by chemical equilibrium modelling: A meta-analytical approach.. *Water research*, 264, 122226. https://doi.org/10.1016/j.watres.2024.122226
 
Zhang, M., Wang, W., Zhong, L., Ji, F., & He, D. (2024). Bicarbonate used as a buffer for controling nutrient solution pH value during the growth of hydroponic lettuce. *International Journal of Agricultural and Biological Engineering*. https://doi.org/10.25165/j.ijabe.20241703.8692
 
Ilyas, M., Imran, M., Naeem, A., Reichwein, A., & Mühling, K. (2025). Iron Solubility and Uptake in Fava Bean and Maize as a Function of Iron Chelates under Alkaline Hydroponic Conditions. *Journal of Agricultural and Food Chemistry*, 73, 28100 - 28116. https://doi.org/10.1021/acs.jafc.5c08914
 
Rijck, G., & Schrevens, E. (1997). pH Influenced by the elemental composition of nutrient solutions. *Journal of Plant Nutrition*, 20, 911-923. https://doi.org/10.1080/01904169709365305
 
