# Nutrient Solution Profiles

The shipped catalogue in `data/nutrient_solutions/` contains 31 target profiles.
Each profile stores solver targets, a concise source, and at most one short
conversion note. Original source tables are not duplicated in profile YAML.

The evidence-backed set includes:

- Historical water cultures: Sachs 1860, Knop 1865, Pfeffer 1900, and Crone 1902.
- Hoagland and Arnon 1950 Solutions 1 and 2.
- Murashige and Skoog 1962 tissue-culture medium.
- Somerville-Ogren, Tocquin, Hermans, Conn, and the evaluated half-strength
  Hoagland Solution 2 for Arabidopsis.
- Long Ashton nitrate type, Steiner Universal, Yoshida rice, and Cooper NFT.
- The exact 2009 Sonneveld-Voogt table rows for tomato closed-system supply,
  tomato free-drainage supply, and cucumber closed-system supply.
- Houston's 2023 species-specific replenishment targets for arugula and basil.
- Yeo's 2023 two-stage NIHHS-Coir supply targets for winter paprika.
- Sapkota's 2019 N3 lettuce treatment, the highest-yielding treatment in the
  reported floating-hydroponic experiment.
- De la Rosa-Rodriguez's 2025 lettuce treatments T2-T5. T1 is the Steiner
  control and is not duplicated.
- Gong's 2024 validated lettuce T1, derived from the actually tested table 7
  formulation rather than the inconsistent nominal total-N value in table 6.

## Consensus Report Review, 2026-06-15

The supplied Consensus report was treated as a literature index. Profile data
were accepted only after checking the primary publication.

| Report reference | Decision | Evidence result |
| --- | --- | --- |
| De la Rosa-Rodriguez et al. 2025, lettuce | Imported T2-T5 | Table 1 reports complete macro-ion charge concentrations; methods report common micronutrients. T1 is the existing Steiner control. |
| Gong et al. 2024, lettuce | Imported validated T1 | Tables 7-8 document the tested formulation and performance. Table 6's 22.0 mmol/L N conflicts with the 20.3 mmol/L implied by table 7, so the profile follows table 7 and records the discrepancy. |
| Sapkota et al. 2019, lettuce | Imported N3 | Table 1 directly reports ppm targets; N3 gave the highest fresh weight for both cultivars. Unreported or excluded nutrients remain omitted. |
| Neocleous et al. 2021, tomato | Not imported | The accessible source material did not provide a complete standalone starting or supply ion composition suitable for a new profile. |
| Yeo et al. 2023, paprika | Imported two final stages | Table 5 directly reports the recommended NIHHS-Coir winter supply composition for fruit-set groups 1-2 and 3-6. |
| van Delden et al. 2020, Arabidopsis | Already represented | Conn, Tocquin, Hermans, Somerville-Ogren, and half-strength Hoagland are already present. The study supports Conn, Tocquin, and half-strength Hoagland for deep-water culture and reports full-strength MS as unsuitable at its measured high EC. |
| Houston et al. 2023, arugula and basil | Imported two replenishment profiles | Table 2 directly reports species-specific mg/L targets and common micronutrients. These are replenishment solutions, not initial root-zone fills. |
| Hossain et al. 2025, watermelon | Not imported | The publication reports compound quantities with stock-like concentrations but no unambiguous final dilution factor. Converting them to final mg/L would require an unsupported assumption. |
| Hong et al. 2024 | Not imported | This is a review and useful index, not a primary composition table for a new static profile. |

The report also led to Savvas et al. (2024), DOI
`10.17660/ActaHortic.2024.1389.22`, on watermelon supply and root-zone
compositions. Its abstract confirms relevant computed targets, but the numeric
table was not available in the reviewed primary-source material, so no values
were inferred from the abstract.

### Gong T1: Original Values and HortiCalc Reconstruction

Gong table 7 reports T1 as 2.70 mmol/L monoammonium phosphate,
6.40 mmol/L potassium nitrate, 5.60 mmol/L calcium nitrate, and 7.10 mmol/L
magnesium sulfate. Stoichiometric conversion gives the profile basis:

```text
N-NO3 17.6 mmol/L; N-NH4 2.7 mmol/L; P 2.7 mmol/L;
K 6.4 mmol/L; Ca 5.6 mmol/L; Mg 7.1 mmol/L; S 7.1 mmol/L
```

This equals elemental N-P-K of `284.336-83.629-250.229 mg/L`, or the fertilizer
label convention N-P2O5-K2O of `284.336-191.625-301.425 mg/L`.

The exact four-salt reconstruction is not possible with the current HortiCalc
catalogue because its available Haifa calcium nitrate also supplies ammonium.
Running HortiCalc's solver with only existing catalogue entries and adding the
existing MKP product as a compensating phosphorus source produced this 1000 L
research reconstruction:

```text
Haifa MAP 12-61-0                         206.321754 g
HAIFA MKP                                  125.800069 g
Kaliumnitrat Multi-K RECI                 556.965422 g
Haifa Cal GG                              1187.401791 g
K+S EPSO Top                              1758.312957 g
```

HortiCalc calculated elemental N-P-K as
`283.996-83.475-250.506 mg/L`, equivalent to N-P2O5-K2O
`283.996-191.272-301.759 mg/L`. Macro-target errors were between -1.69% and
+0.41%. This reconstruction is an audit note only; it is not stored as recipe
data in the solver profile.

The 1999 Sonneveld-Voogt-Spaans universal algorithm is not a static nutrient
solution. It adjusts a selected crop standard for EC, water composition, pH,
and root-zone analysis before calculating fertilizers. It is therefore not
represented as a target YAML. The wider crop families mentioned in the 2009
book are likewise not collapsed into one invented "universal crop" profile.

`Bugbee_Utah_Hydroponic_Cannabis_2022.yml` remains a legacy user-provided
dataset because the research note supplied for this change did not contain a
source table sufficient to reconstruct it. The Bernstein profile was explicitly
excluded from changes.

## Conversion Rule

`targets_mg_per_l` stores elemental targets. In particular, `S` means elemental
sulfur, not sulfate mass:

```text
S mg/L = SO4 mg/L * molar_mass(S) / molar_mass(SO4)
S mg/L = SO3 mg/L * molar_mass(S) / molar_mass(SO3)
```

For molar source data, one mole of `SO4` or `SO3` contains one mole of `S`.
The conversion always moves from the reported sulfur-bearing form toward
elemental `S` for target profiles. Fertilizer composition may still use `SO4`;
that is a different input schema described in [Data model](data_model.md).

Unknown values are omitted. Zero is used only where the cited composition
explicitly excludes a form, such as ammonium in Hoagland Solution 1. Historical
sources that say only "trace" do not produce a numeric target.

## Historical Formulation Basis

Solver target profiles never store fertilizer recipes, compound quantities, or
substance masses. For Sachs, Knop, Pfeffer, Crone, MS, and Yoshida, the cited
formulation was converted outside the runtime profile to elemental mg/L. The
YAML retains only those targets, the citation, and a short conversion note.

Circular 347 prints the Sachs, Knop, Pfeffer, and Crone formulas without
hydrate notation. That limitation was considered during conversion but is not
stored as runtime-profile metadata.

The legacy filename `Knop_1861_Standard.yml` is retained for saved-profile and
script compatibility, while the displayed name and provenance identify the
1865 formulation reproduced in Circular 347.

## Runtime Copies

HortiCalc normally reads `user/nutrient_solutions/`. On startup,
`ensure_portable_layout()` copies new shipped profiles and refreshes an old
profile only when its SHA-256 hash exactly matches a known untouched legacy
file. User-edited copies are not overwritten. Source:
`src/horticalc/paths.py`.

## Main Sources

- Hoagland, D. R. and Arnon, D. I. (1950), *The Water-Culture Method for
  Growing Plants without Soil*, California Agricultural Experiment Station
  Circular 347.
- Murashige, T. and Skoog, F. (1962), DOI
  `10.1111/j.1399-3054.1962.tb08052.x`.
- van Delden, S. H., Nazarideljou, M. J., and Marcelis, L. F. M. (2020),
  *Plant Methods* 16:72, DOI `10.1186/s13007-020-00606-4`.
- Hewitt, E. J. (1966), *Sand and Water Culture Methods Used in the Study of
  Plant Nutrition*, second edition.
- Rueda-Lopez, I. et al. (2024), Table 1, Steiner solution at 100%, DOI
  `10.2478/fhort-2024-0017`; the table attributes the solution to Steiner
  (1984) and reports its macro- and micronutrients directly in mg/L.
- Yoshida, S. et al. (1976), *Laboratory Manual for Physiological Studies of
  Rice*, third edition, ISBN `978-9711040352`.
- Cooper, A. J. (1979), *The ABC of NFT*, ISBN `978-0901361226`.
- Sonneveld, C. and Voogt, W. (2009), *Plant Nutrition of Greenhouse Crops*,
  DOI `10.1007/978-90-481-2532-6`.
- Sapkota, S., Sapkota, S., and Liu, Z. (2019), DOI
  `10.3390/horticulturae5040072`.
- Houston, L. L. et al. (2023), DOI `10.3390/horticulturae9040486`.
- Yeo, K. H. et al. (2023), DOI `10.3390/horticulturae9040412`.
- Gong, B. et al. (2024), DOI `10.3390/agronomy14061160`.
- de la Rosa-Rodriguez, R. et al. (2025), DOI
  `10.47163/agrociencia.v59i8.3444`.

Each YAML keeps one concise source line, optional conversion text, and the
elemental target values. Detailed research decisions and source review remain
in this document instead of the profile files.
