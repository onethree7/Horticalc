# Nutrient Solution Profiles

Status: `current-state`.

The shipped catalogue in `data/nutrient_solutions/` contains target profiles. Each profile stores solver targets, a concise source, and at most one short conversion note. Original source tables are not duplicated. Most profiles cite published sources; the explicitly accepted Bugbee and Saloner/Bernstein profiles retain `User provided dataset` as their provenance.

## Shipped Profile List

The set includes historical water cultures, Hoagland and Arnon 1950 Solutions 1 and 2, Murashige and Skoog 1962, Long Ashton nitrate type, Steiner Universal, Yoshida rice, Cooper NFT, Sonneveld-Voogt 2009 tables, and recent species-specific targets from Sapkota, Houston, Yeo, Gong, and de la Rosa-Rodriguez.

A full list is available by listing `data/nutrient_solutions/*.yml`.

## Conversion Rule

`targets_mg_per_l` stores elemental targets. `S` means elemental sulfur, not sulfate mass:

```text
S mg/L = SO4 mg/L * molar_mass(S) / molar_mass(SO4)
S mg/L = SO3 mg/L * molar_mass(S) / molar_mass(SO3)
```

For molar source data, one mole of `SO4` or `SO3` contains one mole of `S`. Unknown values are omitted. Zero is used only where the cited composition explicitly excludes a form.

## Runtime Overrides

Horticalc lists shipped profiles from `data/nutrient_solutions/` and layers same-filename files from `user/nutrient_solutions/` on top. New and edited profiles are stored only in `user/`. On startup, byte-identical copies and known untouched legacy defaults are removed so the current shipped profile is used; user-edited copies are preserved. Source: `src/horticalc/paths.py` and `api/app.py`.

## Sources

- Hoagland, D. R. and Arnon, D. I. (1950), *The Water-Culture Method for Growing Plants without Soil*, California Agricultural Experiment Station Circular 347.
- Murashige, T. and Skoog, F. (1962), DOI 10.1111/j.1399-3054.1962.tb08052.x.
- van Delden, S. H., Nazarideljou, M. J., and Marcelis, L. F. M. (2020), *Plant Methods* 16:72, DOI 10.1186/s13007-020-00606-4.
- Hewitt, E. J. (1966), *Sand and Water Culture Methods Used in the Study of Plant Nutrition*, second edition.
- Rueda-Lopez, I. et al. (2024), DOI 10.2478/fhort-2024-0017.
- Yoshida, S. et al. (1976), *Laboratory Manual for Physiological Studies of Rice*, third edition, ISBN 978-9711040352.
- Cooper, A. J. (1979), *The ABC of NFT*, ISBN 978-0901361226.
- Sonneveld, C. and Voogt, W. (2009), *Plant Nutrition of Greenhouse Crops*, DOI 10.1007/978-90-481-2532-6.
- Sapkota, S., Sapkota, S., and Liu, Z. (2019), DOI 10.3390/horticulturae5040072.
- Houston, L. L. et al. (2023), DOI 10.3390/horticulturae9040486.
- Yeo, K. H. et al. (2023), DOI 10.3390/horticulturae9040412.
- Gong, B. et al. (2024), DOI 10.3390/agronomy14061160.
- de la Rosa-Rodriguez, R. et al. (2025), DOI 10.47163/agrociencia.v59i8.3444.

Each YAML keeps one concise source line, optional conversion text, and the elemental target values. Detailed research decisions are recorded in the historical report.
