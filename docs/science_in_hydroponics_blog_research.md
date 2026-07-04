# Science in Hydroponics Blog: Code-Oriented Research Index

Status: historical-report (research snapshot, not current runtime behavior).

Snapshot date: 2026-06-30.

## Purpose

This report gathers the scientific themes in Dr. Daniel Fernandez's [Science in Hydroponics](https://scienceinhydroponics.com/) blog into a source-linked form that can be relayed into HydroBuddy or Horticalc work. It is an index and synthesis, not a copy of the articles and not an implementation specification.

The blog is a valuable expert-authored secondary source and literature trail. A blog claim alone is not enough to establish a new solver default, safety threshold, crop target, or chemistry model. Before code or shipped data changes, follow the post's references to the primary paper, verify the reported units and experimental context, and add a focused test.

## Coverage And Method

- The public WordPress REST API reported 307 posts on 2026-06-30. All 307 are summarized and linked below.
- The inventory spans 2009-02-01 through 2026-01-07. It includes scientific articles, tutorials, project notes, product/software announcements, and a few service-oriented posts because omitting them would make the archive incomplete.
- The detailed synthesis prioritizes subjects that can affect a nutrient calculator: units, mass balance, fertilizer composition, water, stock solutions, pH, EC, ionic activity, chelation, nutrient ratios, measurement uncertainty, and target profiles.
- Per-post summaries were generated locally from article body text, then audited for coverage, unsupported numbers, cross-article contamination, and code-relevant chemistry errors. They remain research aids rather than substitutes for the primary article.
- Summaries below are paraphrases. Consult the linked post for Daniel's full explanation, figures, references, caveats, and corrections.

WordPress taxonomy counts are non-exclusive. The largest categories at snapshot time were Article (131), Uncategorized (72), Nutrient Solutions (67), HydroBuddy (20), pH (14), Automation (14), Additives (12), EC (6), Media (6), and Lamps (6).

## Executive Synthesis

1. A nutrient calculator is fundamentally a mass-balance tool. Targets must retain whether a value is elemental, ionic, or an oxide-equivalent label value. Salt masses follow from solution volume, compound composition, hydration state, assay/composition, and every nutrient contributed by every selected material.
2. Product composition and reagent purity are different concepts. A product can contain a small percentage of a nutrient while still being a high-purity instance of the stated compound. A calculator should not silently use one field for both meanings.
3. Input water belongs inside the formulation. Calcium, magnesium, iron, sodium, chloride, carbonate/bicarbonate, and acid used for alkalinity neutralization can all change the final nutrient and ion balance. Water reports are snapshots and may vary seasonally.
4. Concentrated stocks are a separate chemical problem from final solutions. Solubility, precipitation compatibility, source-water alkalinity, final-volume preparation, temperature, injector calibration, and storage stability all matter even when the final elemental arithmetic is correct.
5. EC measures bulk charge transport, not nutrient identity, total nutrient mass, osmotic pressure, or plant availability. EC comparisons are most defensible for tracking one solution of approximately stable composition. A theoretical EC value is an estimate whose ion coverage and assumptions must remain visible.
6. Concentration is not activity. Ionic strength changes activity coefficients, especially for multivalent ions, while plants additionally respond to transport kinetics, ion competition, rhizosphere chemistry, and ion-specific toxicity. An activity model would complement—not replace—concentration outputs.
7. The familiar soil-derived pH availability chart is not a hydroponic law. Nitrate remains soluble through the practical range; precipitation depends on actual ion concentrations; and chelate identity changes micronutrient behavior. Universal availability bars should not become calculator warnings.
8. Chelation is equilibrium chemistry. Stability depends on ligand protonation, metal-ligand affinity, competing metals, and precipitation sinks. Recording only total Fe, Mn, Zn, or Cu cannot prove that the nutrient will remain soluble.
9. Nitrogen form matters. Nitrate, ammonium, and urea are not interchangeable merely because they contribute elemental N. Their uptake, toxicity risk, microbial conversion, and effect on root-zone pH differ.
10. Crop targets are starting points tied to environment and management. Water, medium, VPD, irrigation frequency, drainage, growth stage, and absolute concentration can change the result. Ratios without absolute concentrations and context are insufficient.
11. Preparation error can dominate mathematical precision. Scale resolution, volumetric uncertainty, density, dosing volume, and reservoir-volume error should be exposed when the requested dose is near the instrument's resolution.

## Science-To-Code Evidence Map

| Topic | Blog-derived conclusion | Horticalc state at this snapshot | Evidence-gated next step | Key posts |
| --- | --- | --- | --- | --- |
| Units and forms | In dilute aqueous work, mg/L is commonly called ppm, but the named species still matters. Molar and mass units require molar-mass conversion. | `src/horticalc/core.py` and `src/horticalc/chemistry.py` separate several elements, oxides, and ions; `docs/data_model.md` defines target units. | Preserve the reported species in import provenance and reject ambiguous bare “ppm” inputs. | [Describing concentration](https://scienceinhydroponics.com/2009/02/describing-concentration-in-hydroponics.html), [concentrations to weights](https://scienceinhydroponics.com/2009/02/preparing-hydroponics-nutrient-solutions-from-concentrations-to-weights.html) |
| Coupled salt contributions | A fertilizer salt normally contributes multiple ions; fitting one target changes others, so formulation is a constrained multi-element problem. | `src/horticalc/solver.py` optimizes allowed targets and `src/horticalc/core.py` reports all modeled contributions. | Keep non-objective achieved elements visible and add tests whenever a new compound form is introduced. | [Concentrations to weights](https://scienceinhydroponics.com/2009/02/preparing-hydroponics-nutrient-solutions-from-concentrations-to-weights.html), [five formulation mistakes](https://scienceinhydroponics.com/2021/02/five-common-mistakes-people-make-when-formulating-hydroponic-nutrients.html) |
| Label oxides | Fertilizer-label P2O5 and K2O are reporting conventions, not the dissolved species. | `src/horticalc/core.py` performs oxide/element conversion; `docs/data_model.md` distinguishes fertilizer composition keys from elemental targets. | Continue storing source form and converted target separately; never label oxide-equivalent mass as ionic phosphate or potassium oxide in solution. | [Why labels express P and K as oxides](https://scienceinhydroponics.com/2020/05/why-do-npk-labels-express-p-and-k-as-oxides.html), [NPK meaning](https://scienceinhydroponics.com/2010/08/the-npk-mistery-what-do-these-numbers-mean-and-how-are-they-calculated.html) |
| Composition versus purity | Nutrient percentage within a compound/product is not reagent assay purity. Unknown impurities may also be insoluble or nutritionally relevant. | Fertilizer composition fractions and liquid density/weight factor are described in `docs/data_model.md`; no independent reagent-purity field is documented. | If purity support is added, model it explicitly and define whether it scales the whole declared composition or a characterized compound assay. Do not overload density. | [Reagent purity](https://scienceinhydroponics.com/2010/09/understanding-reagent-purity-and-its-importance-in-hydroponics.html), [powder quality](https://scienceinhydroponics.com/2020/06/three-ways-to-judge-the-quality-of-powdered-hydroponic-nutrient-products.html) |
| Measurement uncertainty | Small weighed masses and poorly known final volumes can create errors far larger than solver tolerances. | Runtime inputs are validated for finite values, but `src/horticalc/core.py` does not propagate instrument uncertainty. | Consider an optional preparation audit using scale resolution, volume tolerance, density tolerance, and minimum practical dose. | [Instrument precision](https://scienceinhydroponics.com/2010/10/instrument-precision-its-importance-in-hydroponic-solution-preparation.html), [importance of accuracy](https://scienceinhydroponics.com/2021/04/the-importance-of-accuracy-in-hydroponic-nutrient-preparation.html) |
| Source water | Water nutrients and non-nutrients alter targets, alkalinity demand, toxicity risk, and reproducibility. | `src/horticalc/core.py` adds normalized water forms and models an RO mixing percentage; `src/horticalc/data_io.py` owns water profiles. | Keep laboratory date/source metadata. Consider scenario comparison rather than pretending one profile is season-invariant. | [Tap water and formulation](https://scienceinhydroponics.com/2020/11/how-tap-water-affects-your-hydroponic-nutrient-formulation.html), [water suitability](https://scienceinhydroponics.com/2020/05/is-my-water-source-good-for-hydroponics.html), [RO water](https://scienceinhydroponics.com/2017/03/do-you-really-need-ro-water.html) |
| pH-adjustment nutrients | Nitric, phosphoric, sulfuric, and basic adjustment chemicals can add modeled nutrients and neutralize alkalinity. | Water ions are modeled, but `docs/data_model.md` does not describe acid/base dose or alkalinity-neutralization calculation. | Add only after defining alkalinity inputs, acid concentration/assay, neutralization chemistry, and contribution tests; do not infer acid demand from pH alone. | [pH down options](https://scienceinhydroponics.com/2020/05/a-guide-to-different-ph-down-options-in-hydroponics.html), [pH up options](https://scienceinhydroponics.com/2022/08/a-guide-to-different-ph-up-options-in-hydroponics.html), [phosphorus added during pH adjustment](https://scienceinhydroponics.com/2020/10/how-much-phosphorous-are-you-adding-to-your-solution-to-adjust-ph.html) |
| Stock solutions | A correct final recipe can still fail as a concentrate because of solubility, precipitation, temperature, source water, or incorrect final-volume technique. | Calculator recipes express final doses; no stock compatibility or solubility engine is documented. | Treat stock planning as a distinct feature with temperature-qualified solubility data, incompatible-pair checks, final-volume instructions, and explicit evidence sources. | [Mixing liquid nutrients](https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html), [A+B preparation](https://scienceinhydroponics.com/2020/10/preparing-your-own-low-cost-ab-generic-hydroponic-nutrients-at-a-small-scale-from-raw-salts.html), [dilutions](https://scienceinhydroponics.com/2020/10/how-to-correctly-prepare-dilutions-from-concentrated-solutions-in-hydroponics.html) |
| EC calculation | Conductivity depends on ion identity, concentration, temperature, ionic strength, pairing/speciation, and model coverage. Early HydroBuddy LMC and empirical models had explicit domains and known errors. | `src/horticalc/ec.py` uses McCleskey equations plus a documented fallback and reports ignored ions/warnings; see `docs/EC.md`. | Benchmark against prepared solutions spanning the actual fertilizer catalogue. Preserve per-ion coverage and never present the estimate as a meter replacement. | [HydroBuddy conductivity estimates](https://scienceinhydroponics.com/2020/04/nutrient-solution-conductivity-estimates-in-hydrobuddy.html), [empirical model](https://scienceinhydroponics.com/2020/07/a-new-conductivity-model-in-hydrobuddy.html), [LMCv2](https://scienceinhydroponics.com/2021/03/improving-on-hydrobuddys-theoretical-conductivity-model-the-lmcv2.html) |
| EC interpretation | Equal EC does not imply equal nutrients, equal total dissolved mass, equal osmotic pressure, or equal toxicity. | `docs/EC.md` identifies the output as an ion-based estimate but does not make EC a nutrient target. | Add user-facing interpretation text where EC comparisons are shown, especially across different recipes. | [EC versus ionic activity](https://scienceinhydroponics.com/2026/01/electrolyte-conductivity-vs-ionic-activity-why-ec-alone-can-mislead-your-nutrient-decisions.html), [TDS is not total dissolved solids](https://scienceinhydroponics.com/2020/05/why-tds-is-not-equal-to-total-dissolved-solids-in-hydroponics.html), [comparing conductivities](https://scienceinhydroponics.com/2017/08/comparing-the-conductivity-of-two-different-solutions.html) |
| Activity and speciation | Ionic activity diverges from concentration as ionic strength rises; multivalent ions are affected more strongly. Activity is still only one part of plant response. | `src/horticalc/ec.py` calculates ionic strength for conductivity, while `docs/EC.md` states that complexes and pH-dependent phosphate speciation are not modeled. | A future activity output needs a declared thermodynamic model, validity range, species set, charge balance, and tests against a trusted speciation package. | [EC versus ionic activity](https://scienceinhydroponics.com/2026/01/electrolyte-conductivity-vs-ionic-activity-why-ec-alone-can-mislead-your-nutrient-decisions.html) |
| pH and availability | Soil-derived availability charts mix pH with lime, microbiology, and soil reactions; hydroponic availability depends on actual composition, precipitation, chelates, and root physiology. | Horticalc does not claim to predict pH-dependent availability. | Avoid universal colored-bar warnings. If precipitation/speciation is added, compute from composition and state the equilibrium assumptions. | [Rethinking pH charts](https://scienceinhydroponics.com/2025/10/ph-vs-nutrient-availability-rethinking-the-classic-charts.html), [origin of availability charts](https://scienceinhydroponics.com/2021/02/nutrient-availability-and-ph-are-those-charts-really-accurate.html) |
| Chelation | Total micronutrient concentration does not establish soluble or plant-available concentration. Ligand protonation, stability constants, competing metals, and solid formation matter. | Fe, Mn, Cu, and Zn totals are represented, but chelate identity/speciation is not part of the documented calculation model. | Add chelate identity only with conditional stability/equilibrium data and competitive-metal tests. A plain “chelated” Boolean is unlikely to be sufficient. | [Metal-chelate stability](https://scienceinhydroponics.com/2021/03/the-stability-of-metal-chelates.html), [higher chelate stability](https://scienceinhydroponics.com/2021/04/a-great-trick-to-higher-chelate-stability-in-hydroponics.html), [calcium EDTA](https://scienceinhydroponics.com/2020/05/calcium-edta-and-its-problems-in-hydroponics.html) |
| Nitrogen forms and pH drift | Nitrate, ammonium, and urea differ in uptake and root-zone effects; ammonium uptake tends to acidify while nitrate-dominant uptake often raises pH. | `src/horticalc/core.py` reports nitrate/ammonium forms and has an explicit urea-as-ammonium option; `src/horticalc/solver_config.py` controls N objective semantics. | Keep forms first-class. Any crop-specific ratio recommendation needs primary evidence and environmental context rather than a universal default. | [Nitrate, ammonium and pH](https://scienceinhydroponics.com/2017/03/nitrate-ammonium-and-ph-in-hydroponics.html), [formulation mistakes](https://scienceinhydroponics.com/2021/02/five-common-mistakes-people-make-when-formulating-hydroponic-nutrients.html), [urea](https://scienceinhydroponics.com/2010/05/urea-in-hydroponics-positive-or-negative.html) |
| Ratios and crop context | K:Ca and other ratios interact with absolute concentration, species, VPD, transport, quality defects, and yield objectives. | `src/horticalc/metrics.py` reports ratios; nutrient target YAML files carry a concise source in `data/nutrient_solutions/`. | Present ratios as diagnostics, not universal optima. Extend profile provenance before adding environment- or stage-specific presets. | [K:Ca ratio](https://scienceinhydroponics.com/2021/06/the-potassium-to-calcium-ratio-in-hydroponics.html), [calcium behavior](https://scienceinhydroponics.com/2019/07/calciums-behavior-in-nutrient-solutions.html), [different situations need different formulations](https://scienceinhydroponics.com/2020/11/why-are-different-hydroponic-formulations-required-for-different-situations.html) |
| Scientific profiles | Standard formulations are useful baselines, not proof of universal optimality. Historical solutions may omit elements that entered as impurities or from media. | Shipped target profiles and their primary-source review are documented in `docs/nutrient_solution_profiles.md`. | Use the blog as a discovery index, then verify every numeric profile against the original table and retain omissions as unknown rather than zero. | [Standard formulations](https://scienceinhydroponics.com/2021/03/standard-hydroponic-formulations-from-the-scientific-literature.html), [Hoagland solution](https://scienceinhydroponics.com/2009/02/the-hoaglands-solution-for-hydroponic-cultivation.html) |

## Recommended Relay Order

These are documentation or research candidates, not authorized runtime changes.

1. Add a short EC interpretation note to the UI/docs: EC is composition-dependent and is not TDS or nutrient strength across different recipes.
2. Audit whether fertilizer records need an explicit assay/purity field distinct from composition and liquid density.
3. Design an optional preparation-uncertainty report before changing solver tolerances: minimum weighable mass, scale resolution, final-volume tolerance, and liquid-dose tolerance.
4. Define an acid/base amendment model that starts from measured alkalinity and includes the nutrients added by the selected reagent.
5. Draft a stock-solution design document covering final-volume preparation, concentration factor, temperature-dependent solubility, and A/B incompatibilities.
6. Keep chelation, precipitation, and activity as research tracks until a full species model and primary validation dataset are selected.
7. Enrich future crop/stage target profiles with context metadata—system, medium, source water, environmental conditions, supply versus root-zone sample, and growth stage—without inventing missing values.

## Evidence And Safety Gates

- Prefer a peer-reviewed primary source, standard method, manufacturer certificate of analysis, or Daniel's own HydroBuddy source/data over a paraphrased blog statement when implementing a number.
- Record the publication date. Newer posts may correct the framing or limitations of older posts.
- Preserve units exactly as reported before conversion. Explicitly distinguish elemental P from P2O5, elemental K from K2O, elemental S from sulfate/SO3, and elemental N from nitrate/ammonium/urea mass.
- Never convert an unreported nutrient to zero. Unknown and zero are scientifically different.
- Do not turn crop observations into universal safety limits. Water-quality, ion-toxicity, pH, EC, and nutrient-ratio thresholds depend on species and conditions.
- For oxidizers, concentrated acids/bases, pesticides, and foliar treatments, implementation or procedural guidance requires a separate safety review and authoritative handling sources.

## Curated Theme Trail

### Formulation And Preparation

- [Preparing a hydroponic nutrient solution](https://scienceinhydroponics.com/2009/02/preparing-a-hydroponic-nutrient-solution.html)
- [Preparing nutrients: complete beginner guide](https://scienceinhydroponics.com/2010/07/preparing-your-own-hydroponic-nutrients-a-complete-guide-for-beginners.html)
- [Preparing A and B solutions](https://scienceinhydroponics.com/2010/06/preparing-a-and-b-solutions-using-my-hydroponics-nutrient-calculator.html)
- [Preparing A, B and C concentrates](https://scienceinhydroponics.com/2010/06/preparing-a-b-and-c-three-part-concentrated-nutrient-solutions-a-tutorial-for-my-hydroponic-nutrient-calculator.html)
- [Copying commercial nutrients: five considerations](https://scienceinhydroponics.com/2020/09/five-things-to-consider-when-trying-to-copy-commercial-hydroponic-nutrients.html)
- [Commercial label versus actual composition](https://scienceinhydroponics.com/2021/02/differences-between-labels-and-actual-composition-values-in-commercial-hydroponic-fertilizers.html)

### EC, Ions, And Measurement

- [FAQ: EC in hydroponics](https://scienceinhydroponics.com/2009/02/faq-electrical-conductivity-ec-in-hydroponics.html)
- [Building an EC prediction model](https://scienceinhydroponics.com/2020/07/building-a-model-to-predict-ec-in-hydroponic-nutrient-solutions.html)
- [EC-to-ppm chart and calculator](https://scienceinhydroponics.com/2021/04/the-ultimate-ec-to-ppm-chart-and-calculator.html)
- [Ion-selective electrodes in practice](https://scienceinhydroponics.com/2020/11/practical-use-of-ion-selective-electrodes-in-hydroponics.html)
- [Preparing EC calibration solutions](https://scienceinhydroponics.com/2017/03/how-to-prepare-your-own-solutions-for-ec-meter-calibration.html)

### Water, pH, And Root-Zone Chemistry

- [Understanding pH, part 1](https://scienceinhydroponics.com/2010/06/understanding-ph-in-hydroponics-part-no-1.html)
- [Understanding pH, part 2](https://scienceinhydroponics.com/2010/06/understanding-ph-in-hydroponics-part-no-2.html)
- [Better understanding pH dynamics](https://scienceinhydroponics.com/2019/07/better-understanding-ph-dynamics-in-hydroponic-culture.html)
- [Media exchange solution test](https://scienceinhydroponics.com/2020/04/the-media-exchange-solution-test-a-better-measurement-of-media-effects-in-hydroponics.html)
- [Managing run-to-waste nutrition](https://scienceinhydroponics.com/2017/04/managing-a-run-to-waste-rtw-hydroponic-crop-from-a-nutritional-perspective.html)
- [Life limits of recirculating solutions](https://scienceinhydroponics.com/2020/10/factors-limiting-the-life-of-a-recirculating-hydroponic-nutrient-solution.html)

### Elements, Chelates, And Additives

- [Iron sources](https://scienceinhydroponics.com/2010/08/iron-sources-in-hydroponics-which-one-is-the-best.html)
- [Low-cost chelated micronutrient solution](https://scienceinhydroponics.com/2020/05/how-to-prepare-a-low-cost-chelated-micronutrient-solution.html)
- [Phosphorus: high or low?](https://scienceinhydroponics.com/2019/08/high-p-or-low-p-the-mystery-of-phosphorus-in-hydroponic-culture.html)
- [Sodium](https://scienceinhydroponics.com/2017/03/some-things-you-should-know-about-sodium-in-hydroponics.html)
- [Chloride](https://scienceinhydroponics.com/2017/03/what-is-the-effect-of-chloride-in-hydroponics.html)
- [Silicon questions](https://scienceinhydroponics.com/2023/02/common-questions-about-silicon-in-nutrient-solutions.html)

### Diagnostics And Context

- [Macro- and micronutrient sufficiency ranges](https://scienceinhydroponics.com/2017/03/hydroponic-micro-and-macro-nutrient-sufficiency-ranges.html)
- [Leaf tissue analysis basics](https://scienceinhydroponics.com/2017/04/a-few-basics-of-leaf-tissue-analysis-in-hydroponic-crops.html)
- [Five things learned from tissue analysis](https://scienceinhydroponics.com/2020/09/five-things-you-can-learn-from-leaf-tissue-analysis.html)
- [Why optimize for a particular setup](https://scienceinhydroponics.com/2019/08/why-you-should-optimize-your-nutrient-solution-for-your-particular-setup.html)

## Complete Summarized Post Digest

Every public post in the snapshot has a paraphrased content summary below. The title links to the canonical article for figures, references, procedures, and full context.

### 2026

#### [2026-01-07 — Peptide Biostimulants in Plants: What They Are and What They Actually Do](https://scienceinhydroponics.com/2026/01/peptide-biostimulants-in-plants-what-they-are-and-what-they-actually-do.html)

Peptide biostimulants improve plant growth under specific conditions but their mechanisms remain unclear. Research shows they can enhance hormone-like activity and nitrogen metabolism, though their effectiveness varies depending on source material, application method, and growing environment. The evidence base has significant limitations, including suboptimal baseline conditions in experiments and a lack of understanding about why certain formulations outperform others.

#### [2026-01-05 — Aquaporins and Water Flow Regulation: A Microphysiological View of Plant Water Uptake](https://scienceinhydroponics.com/2026/01/aquaporins-and-water-flow-regulation-a-microphysiological-view-of-plant-water-uptake.html)

Aquaporins play a crucial role in regulating root water uptake under various conditions. Research indicates that they can contribute up to 50% of total transport, with their activity being influenced by environmental factors such as pH and oxygen levels. For hydroponic growers, understanding aquaporin function helps optimize water management strategies, especially regarding dissolved gases like CO2 and H2O2 which are linked to photosynthesis and stress signaling.

#### [2026-01-02 — Electrolyte Conductivity vs. Ionic Activity: Why EC Alone Can Mislead Your Nutrient Decisions](https://scienceinhydroponics.com/2026/01/electrolyte-conductivity-vs-ionic-activity-why-ec-alone-can-mislead-your-nutrient-decisions.html)

EC aggregates charge transport from all dissolved ions, so equal readings can hide different nutrient ratios, toxic sodium or chloride, and different crop responses. Ionic strength also lowers chemical activity, especially for divalent ions, but activity is only one influence alongside membrane transport, competition, and rhizosphere chemistry; composition-specific analysis is needed when a solution changes.

### 2025

#### [2025-12-31 — Foliar Sprays in Hydroponics: What Actually Enters the Plant?](https://scienceinhydroponics.com/2025/12/foliar-sprays-in-hydroponics-what-actually-enters-the-plant.html)

The plant cuticle acts as a formidable barrier to nutrient entry through its lipid-rich structure, limiting penetration primarily via aqueous pores. Only small ions can pass through these tiny channels (0.45-1.18 nm radius), making foliar feeding effective for specific problems under constrained conditions. Timing and formulation are crucial; optimal results occur during afternoon or early morning when stomata are open, with urea providing superior penetration compared to ionic forms of micronutrients.

#### [2025-12-29 — Bio-stimulants: Which Pure Compounds Have Reproducible Effects](https://scienceinhydroponics.com/2025/12/bio-stimulants-in-soilless-culture-which-compounds-have-reproducible-effects.html)

This post discusses various pure chemical compounds that have demonstrated consistent positive effects on crop performance, including amino acids like glycine betaine and L-proline, silicon compounds such as potassium silicate, plant hormones like gibberellic acid, and vitamins like thiamine. The key advantage of using these pure compounds is reproducibility; knowing exactly what you are applying allows for effective system optimization and troubleshooting. However, crop conditions can vary significantly, so results may differ depending on the specific circumstances.

#### [2025-12-27 — Thiamine as a biostimulant in hydroponic and soilless systems](https://scienceinhydroponics.com/2025/12/thiamin-as-a-biostimulant-in-hydroponic-and-soilless-systems.html)

Thiamine, a vitamin B1, enhances plant growth under stress conditions like drought and salinity. Research shows foliar applications of 500 ppm thiamine can increase pod numbers by up to 63% and root length by up to 62%, compared to untreated controls. Thiamine acts as a signaling molecule that activates calcium signal transduction pathways, improving antioxidant defense systems in plants.

#### [2025-12-22 — Exogenous Sugar Applications: A deeper look](https://scienceinhydroponics.com/2025/12/exogenous-sugar-applications-a-deeper-look.html)

The review of exogenous sugar applications on mature plants highlights both beneficial effects, such as enhanced growth and stress tolerance in Andrographis paniculata and tomato under suboptimal conditions, alongside detrimental impacts like growth retardation and increased oxidative stress. Key challenges include the inefficient transport of sugars from roots to shoots, concentration-dependent physiological responses, and potential for photosynthetic downregulation. Research gaps indicate a lack of studies on yield effects in commercial systems, making sugar applications impractical without further evidence supporting their efficacy.

#### [2025-12-08 — Ascorbic Acid as a Biostimulant: Alleviating Stress to Improve Yield and Quality in Hydroponic Systems](https://scienceinhydroponics.com/2025/12/ascorbic-acid-as-a-biostimulant-enhancing-yield-and-quality-in-hydroponic-systems.html)

Ascorbic acid (vitamin C) enhances yield and quality in hydroponic systems by modulating antioxidant defense mechanisms, stress tolerance, and nutrient use efficiency. Research shows that foliar applications of 100-400 ppm can significantly improve lettuce growth under saline conditions, while root zone applications at 200 ppm enhance Rhizobium activity in leguminous crops. The compound strengthens plant antioxidant systems, leading to improved stress tolerance and better cellular integrity during growth and storage.

#### [2025-12-05 — Organic Sulfur Foliar Sprays: Beyond Sulfate Salts for Hydroponic Crops](https://scienceinhydroponics.com/2025/12/organic-sulfur-foliar-sprays-beyond-sulfate-salts-for-hydroponic-crops.html)

Daniel Fernandez discusses the benefits of using organic sulfur compounds like thiourea, cysteine, glutathione, methionine, and S-methylmethionine over traditional sulfate salts. These compounds function as both sulfur sources and bioregulators, improving stress tolerance, enhancing photosynthesis, and promoting better nutrient partitioning. He provides practical formulations for foliar sprays in g/gal units, emphasizing the effectiveness of thiourea during tillering and flowering stages.

#### [2025-12-03 — Creating an Effective “Greener” Foliar Spray from Raw Salts to Combat Yellowing in Productive Crops](https://scienceinhydroponics.com/2025/12/creating-an-effective-greener-foliar-spray-from-raw-salts-to-combat-yellowing-in-productive-crops.html)

The post discusses how to prepare a “greener” foliar spray from common fertilizer salts to combat chlorosis caused by nitrogen, iron, and magnesium deficiencies. It explains that foliar applications are effective for micronutrients like iron but less so for macronutrients like nitrogen due to their limited translocation within the plant. The post also outlines the science behind foliar uptake, including how positively charged nutrients can enter through the cuticle of leaves, and provides practical guidelines on application timing and concentration.

#### [2025-12-01 — Using Glycine Betaine as a Biostimulant](https://scienceinhydroponics.com/2025/12/glycine-betaine-in-hydroponic-and-soilless-crops-what-works-and-what-doesnt.html)

Glycine betaine acts as a compatible solute in plants, protecting against stress by maintaining cellular water balance and reducing oxidative damage. This post addresses common questions about its use, including application methods (foliar or root) and concentrations for different crops like rice, lettuce, and tomato under various stresses. Effective dosing is crucial; higher concentrations are needed for nitrate reduction applications in NFT systems, while lower doses can improve yield and quality in foliar treatments.

#### [2025-11-24 — Methods to Enhance Terpene Production](https://scienceinhydroponics.com/2025/11/methods-to-enhance-terpene-production-in-commercially-important-plants.html)

Daniel Fernandez discusses methods to boost terpene production in commercially relevant crops like mint and orange. He highlights the importance of understanding terpene biosynthesis through two pathways: MVA for sesquiterpenes and triterpenes, and MEP for monoterpenes and diterpenes. Controlled drought stress management is shown to enhance terpene content by upregulating protective secondary metabolites, while temperature optimization can increase terpene emissions and biosynthetic gene expression.

#### [2025-11-21 — Exogenous Terpenes in Agriculture: Can External Application Improve Crop Performance?](https://scienceinhydroponics.com/2025/11/exogenous-terpenes-in-agriculture-can-external-application-improve-crop-performance.html)

This post explores whether applying external terpenes can improve crop performance under stress conditions. It highlights foliar sprays of monoterpenes for tomato plants under water deficit stress, showing significant improvements in oxidative stress management with optimal concentrations reducing damage by 50%. Root zone applications of sesquiterpenes like E-β-caryophyllene enhance biological pest control through attracting entomopathogenic nematodes. However, practical adoption requires further development and optimization for specific crop systems.

#### [2025-11-19 — An Expanded View on Root Zone Temperature in Soilless and Hydroponic Systems](https://scienceinhydroponics.com/2025/11/an-expanded-view-on-root-zone-temperature-in-soilless-and-hydroponic-systems.html)

The optimal root zone temperature varies significantly between DWC (18-22°C) and soilless media systems (20-28°C). DWC requires more restrictive control due to oxygen limitations, while soilless media offer greater flexibility. Maintaining optimal temperatures can improve plant growth rates and crop quality, but careful attention is needed for successful implementation.

#### [2025-10-31 — NIR Devices for Leaf Tissue Mineral Analysis](https://scienceinhydroponics.com/2025/10/nir-devices-for-leaf-tissue-mineral-analysis.html)

NIR spectroscopy for leaf tissue analysis reduces sample preparation cost and time by 50-150 USD per sample and weeks compared to traditional methods. It achieves high accuracy (R²: 0.80-0.95) for macronutrients like nitrogen, phosphorus, and potassium in various crops, with RPD values above 2.0 indicating good predictions. Calibration requires precise reference data and standardized samples; generic calibrations from manufacturers are insufficient. Proper calibration development is essential for reliable nutrient management decisions.

#### [2025-10-29 — Oxygenation of Nutrient Reservoirs in Substrate-Based Soilless Crops](https://scienceinhydroponics.com/2025/10/oxygenation-of-nutrient-reservoirs-in-substrate-based-soilless-crops.html)

In substrate-based hydroponics systems like rockwool and coconut coir, roots primarily obtain oxygen from air-filled pores within the medium rather than dissolved oxygen in the nutrient solution. The key parameter governing this is air-filled porosity, which should ideally be between 10-20% for optimal plant growth. Proper irrigation management that allows substrates to dry down between irrigations is crucial for maintaining adequate air-filled porosity and preventing hypoxia, rather than relying on aeration in the nutrient reservoir.

#### [2025-10-27 — Top 5 Open Source Hardware Tools to Boost Your Hydroponic Yields](https://scienceinhydroponics.com/2025/10/top-5-open-source-hardware-tools-to-boost-your-hydroponic-yields.html)

This post discusses five open-source hardware tools to improve hydroponics yields, including an automated pH and EC control system using Raspberry Pi 3 with fuzzy logic for precise adjustment of nutrient solution. The system reduces labor by 90% and increases leaf width by 7%, costing under $200. Another tool is the Open Source PAR Sensor built with ESP32 microcontroller and AS7341 spectral sensor, which costs around $50-70 and provides accurate data for optimizing lighting strategy.

#### [2025-10-24 — Growing Soilless Crops Without Nitrates: Practical Options When Nitrate Salts Are Unavailable](https://scienceinhydroponics.com/2025/10/growing-soilless-crops-without-nitrates-practical-options-when-nitrate-salts-are-unavailable.html)

This post discusses growing soilless crops without nitrates by using alternative nitrogen sources like ammonium salts and urea. It highlights that plants can tolerate up to 15-20% of total nitrogen as ammonium, but requires careful management due to rapid uptake and acidification. The key is establishing microbial communities in the substrate to convert ammonium to nitrate, which mimics soil processes.

#### [2025-10-22 — Using Portable Low-Cost Chlorophyll Sensors to Assess Plant Health and Improve Crop Quality in Hydroponics](https://scienceinhydroponics.com/2025/10/using-portable-low-cost-chlorophyll-sensors-to-assess-plant-health-and-improve-crop-quality-in-hydroponics.html)

Daniel Fernandez discusses the use of portable chlorophyll sensors for assessing plant health in hydroponics. These devices provide non-destructive estimates of chlorophyll content, which is a reliable proxy for nitrogen status. They offer immediate feedback and can be used to make timely adjustments to nutrient solutions, enhancing crop quality and efficiency.

#### [2025-10-20 — The Problems with Brix Analysis of Sap in  Crops](https://scienceinhydroponics.com/2025/10/the-problems-with-brix-analysis-of-sap-in-crops.html)

Brix analysis measures soluble solids in plant sap using a refractometer but suffers from significant diurnal variation (up to 30%) due to photosynthesis and sugar mobilization. Spatial heterogeneity within plants also leads to inconsistent readings, making it unreliable for assessing overall nutritional health of vegetative crops in hydroponic systems. Instead, regular tissue analysis should be used for informed nutrient adjustments, providing more reliable data that can improve crop performance.

#### [2025-10-17 — Comparing Nutrient Solutions for Hydroponic Strawberry Production](https://scienceinhydroponics.com/2025/10/comparing-nutrient-solutions-for-hydroponic-strawberry-production.html)

The study by researchers at the Technological Institute of Torreón found that optimal nutrient ratios for hydroponic strawberries include 168 ppm nitrogen with 430 ppm potassium, resulting in a yield of 97 grams per plant and highest soluble solids content (10.8° Brix). The critical role of potassium was highlighted as it enhances fruit quality by promoting sugar transport through the phloem. For Chinese greenhouses, optimal formulations include nitrogen at 156 to 172 ppm, phosphorus at 54 to 63 ppm, and potassium at 484 to 543 ppm. Excessive nutrients can negatively impact yield and quality.

#### [2025-10-15 — Comparing Nutrient Solutions for Hydroponic Tomatoes](https://scienceinhydroponics.com/2025/10/comparing-nutrient-solutions-for-hydroponic-tomatoes-what-the-research-says.html)

This post compares two common nutrient formulations for hydroponic tomatoes: the Arizona and Florida approaches. The Arizona formulation maintains consistent macronutrient levels throughout growth stages, while the Florida approach uses lower nitrogen during early growth to prevent excessive vegetative growth, increasing both nitrogen and potassium during fruit production. Key takeaways include maintaining nitrogen between 60-70 ppm for prevention of excessive vegetative growth, increasing potassium significantly during fruiting to enhance quality parameters, keeping calcium levels at 150-200 ppm throughout the season, and monitoring potassium levels to prevent antagonism with calcium.

#### [2025-10-13 — pH vs Nutrient Availability: Rethinking the Classic Charts](https://scienceinhydroponics.com/2025/10/ph-vs-nutrient-availability-rethinking-the-classic-charts.html)

The traditional pH vs nutrient availability charts for hydroponics are misleading due to their soil-based origins. They incorrectly show nitrate and micronutrients as less available at higher pH levels. A new heatmap based on modern solubility, speciation, and chelation chemistry better represents nutrient behavior across a wider pH range (4.0-8.5). This helps growers make more informed decisions about pH management and nutrient selection.

#### [2025-10-10 — Can you manage downy mildew in hydroponic basil with organic foliar sprays?](https://scienceinhydroponics.com/2025/10/managing-basil-downy-mildew-in-hydroponics-with-organic-foliar-sprays.html)

Basil downy mildew is a severe issue in hydroponic basil production caused by Peronospora belbahrii. It requires high humidity or wet leaves to infect, thriving in controlled environments where leaf moisture control is difficult. Effective organic treatments have not been found; instead, environmental management strategies like light manipulation and spacing improvements are recommended for better disease suppression.

#### [2025-10-08 — Triacontanol Foliar Sprays in Soilless Culture: Formulation and Application](https://scienceinhydroponics.com/2025/10/triacontanol-foliar-sprays-in-soilless-culture-formulation-and-application.html)

Triacontanol, a long-chain fatty alcohol found in plant cuticle waxes, enhances yield and quality effects in hydroponic systems like lettuce, tomatoes, cucumbers, and strawberries. At 10^-7 M (approximately 0.043 mg/L) for lettuce, it increased leaf fresh weight by 13-20% within 6 days. For tomatoes, weekly foliar applications of 70 µM (approximately 21 mg/L) significantly boosted flower and fruit numbers, leading to a 28% higher total yield at harvest. Cucumbers under salt stress benefited from triacontanol application, improving photosynthesis, stomatal conductance, and water use efficiency. The stock solution is prepared by combining ethanol with Tween-20 for stable concentration, which can be diluted into spray solutions based on crop needs.

#### [2025-10-06 — Calcium silicate (wollastonite) in soilless crops](https://scienceinhydroponics.com/2025/10/calcium-silicate-wollastonite-in-soilless-crops.html)

Calcium silicate (wollastonite) can enhance silicon availability for tomatoes and cucumbers grown without soil by raising pH. Studies show that at optimal rates, it improves postharvest durability of fruits but higher doses may reduce gas exchange and chlorophyll levels in tomatoes. For cucumbers, a 3 g L⁻¹ rate increased yield by about 25% under moderate moisture restriction with no penalty to fruit size or soluble solids. Use calcium silicate conservatively and verify its effects on pH and silicon content before scaling up.

#### [2025-10-03 — Calcium Thiosulfate as a Nitrate-Free Calcium Source in Soilless Culture](https://scienceinhydroponics.com/2025/10/calcium-thiosulfate-as-a-nitrate-free-calcium-source-in-soilless-culture.html)

Daniel Fernandez discusses the use of calcium thiosulfate as a nitrogen-free calcium source for hydroponic and soilless culture. This alternative to calcium nitrate is highly soluble and can be used in late-stage fertigation, replacing traditional sources like calcium nitrate or chloride. Studies show that both Arabidopsis and rice can absorb thiosulfate, though there are concentration thresholds and potential metabolic costs depending on the species. Despite limited research, using CaTSR as a zero-nitrogen source is practical for maintaining calcium levels without introducing nitrogen, with studies indicating no negative effects but also noting minimal impact under certain conditions.

#### [2025-10-01 — A low cost DIY oil IPM for your crops](https://scienceinhydroponics.com/2025/10/a-low-cost-diy-oil-ipm-for-your-crops.html)

Daniel Fernandez describes how to prepare and use a low-cost emulsified vegetable oil spray for controlling pests like mites, powdery mildew, and whiteflies. The blend of soybean and corn oils is stabilized with Tween 20 and Tween 80, ensuring uniformity in the final solution which can be diluted up to 32 mL/L for foliar application. This method offers broad efficacy against various pests and crops, maintaining effectiveness through proper dilution and storage.

#### [2025-09-29 — Coco Coir vs Rockwool in Soilless Crops](https://scienceinhydroponics.com/2025/09/coco-coir-vs-rockwool-and-coco-perlite-blends-in-soilless-crops.html)

Coco coir has emerged as a viable alternative to rockwool in greenhouse hydroponics. It outperforms rockwool in crops like tomatoes and cucumbers, improving yield and nutrient uptake. For leafy greens such as lettuce, coco peat often produces more biomass than perlite or mineral wool. The 70:30 coir/perlite blend is recommended for crops with high oxygen demands, including strawberries, which show equal or better performance compared to rockwool when root-zone aeration is managed.

#### [2025-09-26 — Recent advances in hydroponic cucumber cultivation: media, irrigation, nutrition and biostimulants](https://scienceinhydroponics.com/2025/09/recent-advances-in-hydroponic-cucumber-cultivation-media-irrigation-nutrition-and-biostimulants.html)

Daniel Fernandez discusses recent advances in hydroponic cucumber cultivation. Key findings include the superior performance of coconut coir over rockwool, as demonstrated by a 2022 study showing higher yields and mineral content in coir compared to rockwool. Additionally, waste-based substrates like cocopeat, palm peat, vermicompost, sawdust, and pumice have been tested for their ability to replace peat, with some blends producing comparable results. The summary also covers the importance of oxygenation in irrigation water and the use of complete nutrient recipes, as well as the need to manage element interactions like silicon and iron.

#### [2025-09-24 — Foliar Calcium in Hydroponics](https://scienceinhydroponics.com/2025/09/foliar-calcium-in-hydroponics.html)

Essential for plant health, calcium is poorly mobile in plants leading to deficiencies even when solution levels are adequate. This article reviews research on foliar calcium applications, highlighting that calcium chloride (CaCl₂) remains the most effective and reliable source, followed by calcium nitrate (Ca(NO₃)₂), sorbitol-chelated Ca, calcium acetate, lactate, and gluconate for specific crops and stress conditions. Practical rates are provided along with expected outcomes.

#### [2025-09-22 — Do oil-producing crops need extra manganese or just enough?](https://scienceinhydroponics.com/2025/09/do-oil-producing-crops-need-extra-manganese-or-just-enough.html)

The literature indicates that oil-producing crops do not require higher manganese levels compared to non-oil producers. Studies on soybeans and canola show that correcting manganese deficiency is sufficient for yield and quality, without the need for additional supplementation. For essential oil crops like water mint and feverfew, manganese can modulate secondary metabolism but does not prove a need for supra-sufficiency. In hydroponic systems, maintaining adequate manganese levels is crucial to avoid deficiencies or toxicity issues.

#### [2025-09-19 — Moringa extract as a biostimulant in hydroponics](https://scienceinhydroponics.com/2025/09/moringa-extract-as-a-biostimulant-in-hydroponics.html)

Moringa leaf extract (MLE) was tested for its effects on hydroponic and soilless crops, showing improvements in yield and quality such as increased marketable lettuce yields by 30% and improved tomato fruit yield. The study found that the timing of applications is crucial, with a schedule of weekly foliar sprays at concentrations around 3-5% being most effective.

#### [2025-09-17 — Exogenous Root Applications of Wetting Agents in Soilless Media](https://scienceinhydroponics.com/2025/09/exogenous-root-applications-of-wetting-agents-in-soilless-media.html)

This post reviews exogenous root applications of wetting agents in soilless media like rockwool and coir. It discusses how nonionic surfactants can improve water uptake and nutrient distribution by reducing surface tension on hydrophobic surfaces, leading to better hydration efficiency and reduced nutrient loss. The practical implication is that using the right concentration of these agents can enhance yield quality without compromising plant health or soil structure.

#### [2025-09-15 — Root-applied auxins in hydroponics: where they help, where they don’t](https://scienceinhydroponics.com/2025/09/root-applied-auxins-in-hydroponics-where-they-help-where-they-dont.html)

The post discusses the use of root-applied auxins in hydroponics for crops such as sweet pepper, melon, and strawberry. It highlights that auxin applications at very low ppm (single-digit range) can improve yield or quality, but more is not better. For example, IBA applied weekly from early fruit development to sweet peppers increased marketable yield while improving root mass and water/nutrient uptake in perlite culture. However, for melons, the same approach did not result in improved yield or nutrient relations. The post also notes that toxic thresholds exist, with maize roots being stunted at 0.02 ppm IBA.

#### [2025-09-12 — Recent findings in hydroponic and soilless strawberries: a data-first look at the last decade](https://scienceinhydroponics.com/2025/09/what-actually-moves-the-needle-in-hydroponic-and-soilless-strawberries-a-data-first-look-at-the-last-decade.html)

The recent findings highlight that mineral nutrition plays a crucial role in improving strawberry yields and quality. A study found that maintaining a higher potassium to nitrogen ratio during vegetative growth followed by a lower ratio during fruiting significantly increased yield, firmness, and shelf-life compared to static recipes (1). Additionally, the optimal nitrate concentration for soilless strawberries is around 210 ppm N as nitrate, with quality improving as potassium approaches 430 ppm K (2). Biostimulants and exogenous hormone applications also show promise in enhancing yield and fruit quality under stress conditions, though excessive potassium can negatively impact yields in deep-water culture systems (3), (7). Cultural practices such as runner removal and proper spacing are still essential for optimal performance.

#### [2025-09-10 — Recent advances in the cultivation of CEA tomatoes: evidence from 2015–2025](https://scienceinhydroponics.com/2025/09/what-actually-moves-the-needle-on-hydroponic-tomato-yields-in-cea-evidence-from-2015-2025.html)

The post discusses recent advances in hydroponic tomato cultivation. Key points include maintaining stable nutrient concentration programs to match yield and improve size distribution, using closed-loop systems for better water and fertilizer efficiency compared to open setups, and employing biostimulants like seaweed extracts and chitosan under stress conditions. Exogenous hormones such as GA3 can also help with fruit set issues during heat or low pollen viability.

#### [2025-09-08 — How to easily lower the costs of your Athena nutrient regime](https://scienceinhydroponics.com/2025/09/lower-the-costs-of-your-athena-regime.html)

Daniel Fernandez suggests replacing expensive branded pH management products like Athena Balance and Pro Balance with cheaper raw materials such as potassium carbonate and AgSil 16H. By understanding their formulations, he demonstrates how to replicate these solutions at a fraction of the cost, highlighting savings up to ten times over the branded product.

#### [2025-09-05 — Chitosan in hydroponic and soilless crops: what actually works](https://scienceinhydroponics.com/2025/09/chitosan-in-hydroponic-and-soilless-crops-what-actually-works.html)

Chitosan can be effective in hydroponic and soilless systems under specific conditions: doses of 100 to 400 ppm are recommended for cucumber rootzone applications, while foliar sprays at 50 to 150 ppm are suitable for leafy greens and fruiting vegetables. The effectiveness depends on the degree of deacetylation (DD) and molecular weight (MW), with lower MW chitosan generally penetrating tissues better. This review highlights controlled trials showing improved growth, disease suppression, and stress mitigation in crops like lettuce, cucumber, and tomato.

#### [2025-09-03 — Iodine in Hydroponic Crops: An Emerging Biostimulant](https://scienceinhydroponics.com/2025/09/iodine-in-hydroponic-crops-an-emerging-biostimulant.html)

Iodine supplementation can act as a biostimulant in hydroponic crops by influencing redox balance and stress signaling. The key is dose and form; potassium iodide (KI) is more phytotoxic than potassium iodate (KIO3). Studies on lettuce, strawberry, and basil show that low doses of iodine improve growth and quality without adverse effects. Practical implication includes favoring iodate for new crops or cultivars due to its faster absorption and lower toxicity threshold.

#### [2025-09-01 — Cobalt in hydroponics as a biostimulant](https://scienceinhydroponics.com/2025/09/cobalt-in-hydroponics-as-a-biostimulant.html)

The literature does not support reliable growth or yield benefits from adding cobalt in hydroponics and soilless systems. Cobalt ions inhibit ethylene biosynthesis at low levels but become toxic when concentrations exceed 10 ppm. Practical studies show that tomato, lettuce, and cucumber grown with sub-ppm cobalt do not benefit, while higher doses lead to toxicity. Ethylene inhibition is observed in lab conditions but does not translate into production benefits under field conditions.

### 2023

#### [2023-02-02 — Common questions about silicon in nutrient solutions](https://scienceinhydroponics.com/2023/02/common-questions-about-silicon-in-nutrient-solutions.html)

Daniel Fernandez discusses silicon sources for hydroponics, highlighting potassium silicates as the most common and cost-effective. He explains that these products form monosilicic acid when diluted in nutrient solutions, which is highly available to plants. He also advises proper preparation of potassium silicate stock solutions and recommends using non-aqueous silicon reagents if mixing stocks or adjusting pH is problematic.

#### [2023-01-13 — Connecting a low cost TDR moisture content/EC/temp sensor to a NodeMCUv3](https://scienceinhydroponics.com/2023/01/connecting-a-low-cost-tdr-moisture-content-ec-temp-sensor-to-a-nodemcuv3.html)

This post describes connecting a low-cost TDR moisture content sensor to a NodeMCUv3 microcontroller, enabling precise soil moisture monitoring at less than $5 per unit. The author provides detailed instructions on wiring and software setup, including calibration steps for accurate EC (electrical conductivity) measurements.

#### [2023-01-05 — How to prepare your own hypochlorous acid cleaner using bleach](https://scienceinhydroponics.com/2023/01/how-to-prepare-your-own-hypochlorous-acid-cleaner-using-bleach.html)

Daniel Fernandez describes how to prepare a hypochlorous acid solution for cleaning hydroponic reservoirs using readily available and low-cost materials. The process involves adding sodium chloride, sodium tripolyphosphate, monopotassium phosphate, magnesium sulfate, and freshly bought Clorox (7.4%) to distilled water. The final concentration of hypochlorous acid is expected to be around 0.02% (200 ppm), suitable for use from 2 to 10 mL per gallon of nutrient solution depending on the severity of issues needing resolution.

### 2022

#### [2022-08-26 — A cost analysis of fertilizers for hydroponic/soilless growing in 2022](https://scienceinhydroponics.com/2022/08/a-cost-analysis-of-fertilizers-for-hydroponic-soilless-growing-in-2022.html)

The cost analysis of fertilizers for hydroponic growing shows that boutique fertilizers can be significantly more expensive, with a medium scale facility spending up to $4000 per day. High energy and inflation costs have increased fertilizer prices, especially for soluble phosphates. The author recommends using blended solutions or custom formulations to reduce costs, noting traditional large-scale growers have been achieving cost-effective fertilizer prices for decades.

#### [2022-08-25 — How to reuse your coco coir in soilless growing](https://scienceinhydroponics.com/2022/08/how-to-reuse-your-coco-coir-in-soilless-growing.html)

Daniel Fernandez discusses how to reuse coco coir media in hydroponics, highlighting its potential cost savings through recycling. He explains that after multiple cycles, the media retains valuable nutrients like calcium and magnesium, which can be beneficial for subsequent crops if properly managed. However, he warns of changes in media composition post-crop, requiring adjustments to nutrient formulations to maintain consistent plant growth.

#### [2022-08-24 — Are Iron chelates of humic/fulvic acids better or worse than synthetics?](https://scienceinhydroponics.com/2022/08/are-iron-chelates-of-humic-fulvic-acids-better-or-worse-than-synthetics.html)

The article discusses iron (Fe) deficiencies in hydroponics and soil systems, highlighting that while synthetic chelates like EDDHA are effective, they can be problematic at high pH. Natural humic/fulvic acids offer a potential alternative with synergistic benefits for Fe nutrition, especially beneficial for monocot species where synthetic chelates may not suffice. The effectiveness of these solutions depends on their ability to maintain Fe in soluble forms and plant uptake mechanisms.

#### [2022-08-23 — A guide to different pH up options in hydroponics](https://scienceinhydroponics.com/2022/08/a-guide-to-different-ph-up-options-in-hydroponics.html)

Daniel Fernandez discusses different pH up options for hydroponics, including potassium hydroxide pellets as the most powerful but unstable option. He recommends potassium silicate due to its stability at high pH values and ability to provide both potassium and silicon nutrients. For situations where rapid pH increase is needed, protein-based solutions can be effective.

#### [2022-07-08 — How to make a stabilized ortho-silicic acid solution with only 3 inputs](https://scienceinhydroponics.com/2022/07/how-to-make-a-stabilized-ortho-silicic-acid-with-3-inputs.html)

Daniel Fernandez simplified a procedure for creating stabilized ortho-silicic acid using sorbitol as a stabilizing agent, reducing complexity and reliance on expensive or controversial additives. The process uses potassium silicate with high K/Si ratio, sulfuric acid, and sorbitol; it yields a stable solution with around 1% SiO2 concentration at 8mL per use.

#### [2022-06-21 — A one-part hydroponic nutrient formulation for very hard water](https://scienceinhydroponics.com/2022/06/a-one-part-hydroponic-nutrient-formulation-for-very-hard-water.html)

Daniel Fernandez formulates a one-part hydroponic nutrient solution suitable for Valencia's very hard water. He uses Calcium Nitrate, Magnesium Nitrate, Potassium Nitrate, Phosphoric acid (85%), and Force Mix Eco to neutralize high alkalinity and hardness without adding sulfates or phosphates. The final solution has a pH of 5.6-5.8 and low electrical conductivity, supporting various plants including basil, rosemary, chives, mint, malabar spinach, and spear mint.

#### [2022-05-13 — New tissue analysis feature in HydroBuddy v1.99](https://scienceinhydroponics.com/2022/05/new-tissue-analysis-feature-in-hydrobuddy-v1-99.html)

HydroBuddy v1.99 introduces a Tissue Analysis feature that allows users to input target tissue concentrations and WUE values, enabling them to determine required nutrient concentrations in hydroponic solutions based on the assumption that all elements taken up by plants are deposited as minerals upon transpiration. The volume of water used for growth is called Water Use Efficiency (WUE), which ranges from 3.0 to 6.0; a higher WUE indicates more efficient plant growth and lower transpiration, while a lower WUE suggests less efficient growth and increased transpiration.

### 2021

#### [2021-06-08 — The Potassium to Calcium ratio in hydroponics](https://scienceinhydroponics.com/2021/06/the-potassium-to-calcium-ratio-in-hydroponics.html)

The post examines research on the potassium to calcium ratio's impact on plant growth, quality, and yield across various species. It highlights that while both elements compete for absorption, their different transport mechanisms limit this competition. The optimal K:Ca ratio varies by crop type but is generally between 1:1 and 2:1 in high EC solutions, with specific exceptions noted.

#### [2021-04-29 — How to use organic fertilizers in Kratky hydroponics](https://scienceinhydroponics.com/2021/04/how-to-use-organic-fertilizers-in-kratky-hydroponics.html)

Daniel Fernandez discusses how to use organic fertilizers in Kratky hydroponics, highlighting that while some OMRI-listed products can be used, those containing plant or animal proteins and bacteria are problematic due to oxygen depletion. He recommends running the solution through a UV filtering system to remove fungi and bacteria, ensuring an organically derived fertilizer can still work effectively without compromising root health.

#### [2021-04-28 — The importance of accuracy in hydroponic nutrient preparation](https://scienceinhydroponics.com/2021/04/the-importance-of-accuracy-in-hydroponic-nutrient-preparation.html)

Daniel Fernandez discusses the importance of accuracy in hydroponic nutrient preparation, highlighting that even small measurement errors can significantly affect final solution concentrations. He explains two types of error: systematic (due to instrument calibration) and random (related to measuring process). The article emphasizes the critical role of accurate scales for weights and calibrated containers for volumes, noting that these errors can lead to significant deviations in nutrient values. Fernandez concludes by advocating for accuracy as a key factor for reproducibility and learning in hydroponics.

#### [2021-04-27 — My Kratky tomato project, tracking a Kratky setup from start to finish](https://scienceinhydroponics.com/2021/04/my-kratky-tomato-project-tracking-a-kratky-setup-from-start-to-finish.html)

Daniel Fernandez is tracking a Kratky tomato setup from start to finish, monitoring variables like pH, EC, temperature, and nutrient concentrations. His goal is to understand how these factors change over time and develop better management techniques for large flowering plants in passive hydroponic systems.

#### [2021-04-26 — Kinetin, a powerful hormone for flowering plants](https://scienceinhydroponics.com/2021/04/kinetin-a-powerful-hormone-for-flowering-plants.html)

Kinetin was tested on tomatoes, cucumbers, and peas grown in solutions containing different concentrations. At low concentrations (0.0215mg/L to 2.15 mg/L), kinetin suppressed plant height and altered flowering cycles. High concentrations led to undesirable elongation effects or no effects at all. Effective concentration is critical; too much can compromise yields, while too little might have no effect. Foliar applications of 2.5-10mg/L showed varied responses in different plants.

#### [2021-04-23 — Arduino hydroponics, how to build a sensor station with an online dashboard](https://scienceinhydroponics.com/2021/04/arduino-hydroponics-how-to-build-a-sensor-station-with-an-online-dashboard.html)

Daniel Fernandez describes how to build an Arduino-based sensor station that measures media moisture levels. This station connects via WiFi to flespi's MQTT server, where it transmits data to a custom dashboard. The project requires no soldering or proto-boards and is suitable for beginners in Arduino hydroponics and IoT interfacing. It uses a low-cost capacitive moisture sensor connected to an LCD shield on an Arduino Wifi Rev2, with the code needing only basic setup like WiFi credentials and flespi token input.

#### [2021-04-21 — How to choose the best hydroponic bucket system for you](https://scienceinhydroponics.com/2021/04/how-to-choose-the-best-hydroponic-bucket-system-for-you.html)

The Kratky bucket system is a simple, passive method that requires minimal maintenance. It uses capillary action to draw water through media for plant roots to access nutrients directly from the solution. However, it's not suitable for large plants due to its inability to manage high water and nutrient consumption. For larger scales or leafy greens on a small scale, an air pump system is recommended as it provides better oxygenation and temperature control without requiring precise volume management.

#### [2021-04-20 — Arduino hydroponics, how to go from simple to complex](https://scienceinhydroponics.com/2021/04/arduino-hydroponics-how-to-go-from-simple-to-complex.html)

Daniel Fernandez recommends starting with an Arduino Wifi Rev2 for simple projects and moving to more complex ones using shields like the LCD12864. He suggests buying sensors that are easy to plug-in, such as the SHT1x sensor or uFire's isolated boards, which can be used in a temperature/humidity monitoring station. For control, he recommends using relays for simple tasks and moving on to more advanced algorithms like PID and reinforcement learning for complex systems.

#### [2021-04-19 — A great trick to higher chelate stability in hydroponics](https://scienceinhydroponics.com/2021/04/a-great-trick-to-higher-chelate-stability-in-hydroponics.html)

Daniel Fernandez discusses how adding an excess of EDTA can increase the stability of iron chelates, reducing free heavy metal ions and preventing precipitation. He recommends adding 1.2mg/L of disodium EDTA for every 1ppm of Fe to achieve this.

#### [2021-04-16 — Hydroponics vs soil, all you wanted to know](https://scienceinhydroponics.com/2021/04/hydroponics-vs-soil-all-you-wanted-to-know.html)

This post compares yields, quality, cost, and environmental impact of hydroponic versus soil crops using peer-reviewed literature. It shows that while hydroponics can produce better or equal results compared to soil, it is not guaranteed. The author also highlights the importance of adequate system control and higher-quality soil for optimal performance in hydroponics. The post concludes by suggesting a balanced approach considering quality, yield, environmental impact, and cost.

#### [2021-04-15 — The best hydroponic medium you have never heard of](https://scienceinhydroponics.com/2021/04/the-best-hydroponic-medium-you-have-never-heard-of.html)

Daniel Fernandez introduces rice hulls, a lesser-known hydroponic medium that decomposes slowly without altering pH. He pairs it with washed river sand to create an ideal combination for crops needing controlled moisture retention and tunable physical properties. This mix avoids issues of peat moss, coco coir, and perlite, offering low environmental impact and ease of reuse.

#### [2021-04-14 — How to make an organic hydroponic nutrient solution](https://scienceinhydroponics.com/2021/04/how-to-make-an-organic-hydroponic-nutrient-solution.html)

Daniel Fernandez describes how to create an organic hydroponic nutrient solution using OMRI-approved raw materials like bark compost, Solubor, and copper sulfate. The process involves mixing these ingredients in water over 15 days with aeration to ensure bioavailability of nutrients such as nitrogen, phosphorus, potassium, magnesium, calcium, sulfur, iron, zinc, boron, copper, molybdenum, and manganese. This solution is designed for organic growing operations and avoids synthetic chemicals.

#### [2021-04-12 — How to get more phosphorus in organic hydroponics](https://scienceinhydroponics.com/2021/04/how-to-get-more-phosphorus-in-organic-hydroponics.html)

Daniel Fernandez discusses how to address phosphorus availability issues in organic hydroponics, highlighting the challenges posed by insolubility of many phosphorus compounds. Solutions include using high-P soluble organic sources like Seabird guano and corn steep liquor, as well as incorporating mineral amendments such as rock phosphates and bone meal into media. He also suggests using citric or malic acid to help solubilize P in rock phosphate amendments.

#### [2021-04-10 — Why NFT is the best hydroponic system beginners should avoid](https://scienceinhydroponics.com/2021/04/why-nft-is-the-best-hydroponic-system-beginners-should-avoid.html)

Nutrient Film Technique (NFT) provides ideal conditions for plants but requires strict control over multiple variables. Its fragility makes it prone to failure due to issues like power outages, root blockage, and disease spread. Small-scale growers often overlook these problems, leading to lower yields or crop failures. For reliable production, small-scale hydroponic growers should consider systems like open media-based setups that offer better success rates with less initial investment.

#### [2021-04-08 — Organic nitrogen in hydroponics, the proven way](https://scienceinhydroponics.com/2021/04/organic-nitrogen-in-hydroponics-the-proven-way.html)

Daniel Fernandez discusses the complexities of using organic nitrogen in hydroponics. He explains that while plants can uptake some organic nitrogen, it's unlikely to replace the main absorption pathway for nitrogen (inorganic nitrate). Studies show that organic nitrogen sources perform poorly compared to synthetic inorganic nitrate solutions. To address this issue, he proposes preparing compost teas with organic nitrogen sources and using nitrifying bacteria to convert them into mineral nitrate, which plants can readily metabolize.

#### [2021-04-07 — Aquaponics vs hydroponics, which is best and why?](https://scienceinhydroponics.com/2021/04/aquaponics-vs-hydroponics-which-is-best-and-why.html)

Daniel Fernandez discusses the comparison between aquaponics and hydroponics in his blog post. He highlights that while aquaponics simplifies management by integrating fish farming with plant cultivation, it requires complex biofilter systems to convert nitrogen from fish waste into a form plants can use. Despite these challenges, studies show that yields and quality of products from aquaponic setups are often equivalent or superior to hydroponic environments due to beneficial biological effects in the nutrient solution.

#### [2021-04-06 — A powerful organic fungicide for powdery mildew](https://scienceinhydroponics.com/2021/04/a-powerful-organic-fungicide-for-powdery-mildew.html)

Daniel Fernandez introduces an organic fungicide for powdery mildew (PM), effective against multiple plant species, using jojoba oil and sunflower oil emulsified with yucca extract. This formulation is designed to inhibit spore germination effectively, reducing crop losses from PM.

#### [2021-04-05 — Making a nitrate rich compost tea for organic hydroponics](https://scienceinhydroponics.com/2021/04/making-a-nitrate-rich-compost-tea-for-organic-hydroponics.html)

Daniel Fernandez describes how he created nitrate-rich compost teas from organic sources like corn steep liquor and fish emulsion, using saprophytic bacteria. The process takes around 12 days to produce a solution with high levels of nitrates (450-600 ppm) that are readily available for plants without sodium contamination, suitable for growing tomatoes in hydroponics.

#### [2021-04-03 — The ultimate EC to ppm chart and calculator](https://scienceinhydroponics.com/2021/04/the-ultimate-ec-to-ppm-chart-and-calculator.html)

This page provides tools for converting between electrical conductivity (EC) readings and parts per million (ppm), which are different scales of measurement. It explains how to determine the scale of your meter, convert TDS readings from one scale to another, and offers recommendations for a go-to EC meter like the Apera EC60. The main practical implication is facilitating accurate comparisons between different hydroponic equipment or sources.

#### [2021-04-02 — Never fail with ebb and flow hydroponic systems](https://scienceinhydroponics.com/2021/04/never-fail-with-ebb-and-flow-hydroponic-systems.html)

Daniel Fernandez discusses common issues and best practices for flood and drain (ebb and flow) hydroponic systems, emphasizing the importance of ensuring complete drainage, fast cycle speed, appropriate media selection, using water content sensors for precise irrigation timing, and adjusting reservoir pH to match root zone conditions. He recommends avoiding overly absorbent media like peat moss and opting for faster-draining options such as rockwool or perlite.

#### [2021-04-01 — The value of Fulvic Acid in hydroponics](https://scienceinhydroponics.com/2021/04/the-value-of-fulvic-acid-in-hydroponics.html)

Fulvic acid is discussed as a smaller family of organic acids with unique properties compared to humic acids. Studies show fulvic acids are more soluble at both acidic and alkaline pH, making them easier for plants to access. Research indicates that foliar applications of 1-3g/L can enhance yield and quality in crops like tomatoes, while root applications of 25-150ppm improve nutrient transport. Fulvic acid's low risk of clogging equipment makes it a safer alternative to humic acids in hydroponics. Its potential synergistic effects with other additives suggest it could boost the efficacy of existing treatments.

#### [2021-03-31 — New to organic hydroponics? Consider these six things](https://scienceinhydroponics.com/2021/03/new-to-organic-hydroponics-consider-these-six-things.html)

Daniel Fernandez discusses six important things for creating an organic hydroponic crop, including using media friendly to microbes like peat moss or coco, providing a complete nutrient solution with sources such as fish emulsions and kelp extracts, amending the media with nitrogen and phosphorus from vegetable protein, bone meal, and rock phosphate, ensuring adequate aeration in the media, avoiding heavy metals that can be harmful, and inoculating the media with beneficial bacteria and fungi. He emphasizes the need for careful management to achieve successful organic hydroponics.

#### [2021-03-30 — Is hydroponics organic? Is it better or worse?](https://scienceinhydroponics.com/2021/03/is-hydroponics-organic-is-it-better-or-worse.html)

The post discusses whether hydroponically produced crops can be considered organic, focusing on the USDA organic standard requirements for nutrients and environmental sustainability. It highlights that hydroponic crops use significantly less water and fertilizer than traditional soil-based methods, making them more sustainable but also raises concerns about their compliance with organic standards due to lack of soil and potential synthetic inputs.

#### [2021-03-27 — HydroBuddy v1.9, MacOS binary, new EC model, many bug fixes and more!](https://scienceinhydroponics.com/2021/03/hydrobuddy-v1-9-macos-binary-new-ec-model-many-bug-fixes-and-more.html)

Daniel Fernandez updates HydroBuddy v1.9, introducing precompiled MacOS binaries and several improvements including an updated LMCv2 conductivity model, simplified substance input options, and corrected EC prediction errors. These changes aim to enhance user experience and accuracy in hydroponics software applications.

#### [2021-03-26 — Improving on HydroBuddy’s theoretical conductivity model, the LMCv2](https://scienceinhydroponics.com/2021/03/improving-on-hydrobuddys-theoretical-conductivity-model-the-lmcv2.html)

LMCv2 is a theoretical conductivity model, not the separate empirical regression model. It starts from limiting molar conductivity and applies ion-specific corrections based on ionic charge and total ionic strength, replacing HydroBuddy's older practice of applying one blunt reduction factor to every formulation.

#### [2021-03-25 — Creating a pH/EC wireless sensing station for MyCodo using an Arduino MKR Wifi 1010](https://scienceinhydroponics.com/2021/03/creating-a-ph-ec-wireless-sensing-station-for-mycodo-using-an-arduino-mkr-wifi-1010.html)

Daniel Fernandez developed a wireless sensing station for MyCodo using an Arduino MKR Wifi 1010 to measure pH and EC levels in hydroponics systems. The station uses uFire pH and EC boards, which are less expensive but offer adequate electrical isolation for multiple probes. It connects to a MQTT server for data transmission and can be calibrated remotely via the CALIB1 topic. This setup allows for flexible deployment of multiple sensing stations without needing extensive development.

#### [2021-03-24 — A simple cheatsheet for macro nutrient additions in hydroponics](https://scienceinhydroponics.com/2021/03/a-simple-cheatsheet-for-macro-nutrient-additions-in-hydroponics.html)

Daniel Fernandez provides a simple cheat sheet for calculating the amounts of various salts needed to increase macronutrients in hydroponic solutions by 10 ppm. The cheat sheet includes common salts like calcium nitrate and magnesium chloride, detailing their elemental contributions such as nitrogen, calcium, and chloride content per liter.

#### [2021-03-23 — How to make your own stabilized mono-silicic acid for use in hydroponics](https://scienceinhydroponics.com/2021/03/how-to-make-your-own-stabilized-mono-silicic-acid-for-use-in-hydroponics.html)

Daniel Fernandez describes a simplified method to produce stabilized mono-silicic acid for hydroponics using readily available materials. The process involves adding potassium silicate, carnitine hydrochloride, phosphoric acid, and propylene glycol in precise quantities over time, resulting in a stable solution that can be used at 1g/gal to provide around 18-20ppm of Si as elemental Si, which is more stable than directly adding potassium silicate.

#### [2021-03-22 — HydroBuddy coming to Android, free and open source!](https://scienceinhydroponics.com/2021/03/hydrobuddy-coming-to-android-free-and-open-source.html)

The HydroBuddy open source hydroponic nutrient calculator is being ported to Android. It will be available for free and without ads within a couple of weeks in the Google Playstore, with most features present but some initial functionality missing. The app's development process continues as it moves towards v2.0, which aims to include more flexible database structures for community use.

#### [2021-03-19 — Calibrating a capacitive moisture/water content sensor for hydroponics](https://scienceinhydroponics.com/2021/03/calibrating-a-capacitive-moisture-water-content-sensor-for-hydroponics.html)

Daniel Fernandez calibrates a capacitive moisture/water content sensor for hydroponics using an Arduino, LCD shield, and low-cost sensor. He shares a calibration procedure that involves natural drying and weighing media to create a curve representing signal vs. water saturation, which aids in precise irrigation timing.

#### [2021-03-18 — Properly positioning temperature and humidity sensors in a hydroponic growing environment](https://scienceinhydroponics.com/2021/03/properly-positioning-temperature-and-humidity-sensors-in-a-hydroponic-growing-environment.html)

Daniel Fernandez discusses optimal sensor placement for temperature and humidity in hydroponic environments, emphasizing the importance of accurate readings based on their location. He outlines setups for single and multiple sensors, including hot wire anemometers for air movement verification, and explains how to minimize climate control gradients using multiple sources of control.

#### [2021-03-15 — Making the most out of your hydroponic setup’s logged sensor and control data](https://scienceinhydroponics.com/2021/03/making-the-most-out-of-your-hydroponic-setups-logged-sensor-and-control-data.html)

Daniel Fernandez discusses the benefits of utilizing logged sensor and control data in hydroponic setups. He suggests using moving averages to smooth out noisy sensor readings, which allows for more effective control algorithms and custom visualizations that can help diagnose issues like humidity spikes or temperature fluctuations. Additionally, he outlines how combining this data with plant age information can lead to advanced climate control systems that avoid environmental extremes, potentially improving crop yields.

#### [2021-03-12 — Commercial sensor and data logging solutions for hydroponics](https://scienceinhydroponics.com/2021/03/commercial-sensor-and-data-logging-solutions-for-hydroponics.html)

Growtronix offers a complete monitoring and automation solution for hydroponic crops with support for both analogue and third-party sensors. However, it requires cabled connections and lacks support for i2c sensors, making data analysis challenging. Agrowtek provides their own touchscreen computers but is closed ecosystem limited to basic control mechanisms. Growtronix has stellar customer support, while Agrowtek's setup can be quickly set up with 200 sensors/relays per day. Growtronix allows third-party sensor integration and advanced climate control options, making it the most complete solution for hydroponics.

#### [2021-03-11 — MyCodo: an open-source solution for control, data logging and visualization](https://scienceinhydroponics.com/2021/03/mycodo-an-open-source-solution-for-control-data-logging-and-visualization.html)

MyCodo is an open-source solution that offers expandable features for data logging, visualization, and control of environmental conditions. It uses MQTT to enable independent sensor/control stations, making it suitable for large-scale hydroponic setups without relying solely on a Raspberry Pi.

#### [2021-03-10 — Pros and cons of building your own sensor and data logging system in hydroponics](https://scienceinhydroponics.com/2021/03/pros-and-cons-of-building-your-own-sensor-and-data-logging-system-in-hydroponics.html)

The post discusses the pros and cons of building your own data logging system in hydroponics. Key points include having full control over all aspects, leveraging low-cost hardware, and gaining deeper understanding of sensors and systems. However, it also highlights challenges like no one to support when things go wrong, limited by personal knowledge, and lower build quality compared to commercial solutions.

#### [2021-03-09 — Standard hydroponic formulations from the scientific literature](https://scienceinhydroponics.com/2021/03/standard-hydroponic-formulations-from-the-scientific-literature.html)

Twelve historical and modern standard solutions are compared after conversion from mmol/L to elemental mg/L. Later formulations explicitly include micronutrients and chelation that older solutions may have received through impurities or media; their convergent macro ratios make them defensible starting points, not universal optima, for crop-specific refinement.

#### [2021-03-02 — The stability of metal chelates](https://scienceinhydroponics.com/2021/03/the-stability-of-metal-chelates.html)

A chelate exists in equilibrium with free metal and ligand, and its stability constant describes how strongly that equilibrium favors the complex. Actual performance also depends on pH-dependent ligand protonation, competing metals, temperature, and precipitation sinks, so total micronutrient concentration alone does not establish soluble or plant-available concentration.

#### [2021-03-01 — Six things to look for in a Hydroponic sensor data logging system](https://scienceinhydroponics.com/2021/03/six-things-to-look-for-in-a-hydroponic-sensor-data-logging-system.html)

Daniel Fernandez emphasizes sensor compatibility, expandability, not cloud reliance, robust connectivity, direct data access via API, and ability to repair as key priorities when evaluating hydroponics data logging systems. He stresses that a system should allow for easy expansion, have local data storage, be able to connect sensors using cables or robust wireless implementations, and provide an open API for flexible data analysis.

#### [2021-02-25 — Differences between labels and actual composition values in commercial hydroponic fertilizers](https://scienceinhydroponics.com/2021/02/differences-between-labels-and-actual-composition-values-in-commercial-hydroponic-fertilizers.html)

Daniel Fernandez highlights that commercial hydroponic fertilizers often underreport their actual composition values compared to what is stated on labels. For instance, a fertilizer labeled as 2% N might actually contain 3%. This misrepresentation can lead to significant deviations in nutrient ratios and performance if not corrected through lab analysis. He shares data from Oregon government tests showing an average deviation of up to 20%, with some products deviating by over 100%, indicating deliberate underreporting to prevent reverse engineering.

#### [2021-02-24 — Nutrient availability and pH: Are those charts really accurate?](https://scienceinhydroponics.com/2021/02/nutrient-availability-and-ph-are-those-charts-really-accurate.html)

The familiar pH-availability bars descend from 1935 and 1942 soil-liming diagrams built from agronomic experience, not hydroponic solution experiments. They confound pH with lime, microbial nitrogen conversion, and carbonate chemistry; hydroponic interpretation must instead consider supplied nitrate, actual calcium/phosphate concentrations, media, and chelate identity.

#### [2021-02-24 — Understanding Calcium deficiency issues in plants](https://scienceinhydroponics.com/2021/02/understanding-calcium-deficiency-issues-in-plants.html)

This post discusses calcium deficiency issues in plants, particularly focusing on tomato blossom end rot and lettuce inner tip burn. It explains that these problems occur when calcium transport fails to keep up with other elements, especially under favorable growing conditions. Strategies for fixing the issue include balancing calcium transport, adjusting relative humidity, pruning excessive leaves, reducing nitrogen, increasing relative humidity at night, and using growth regulators or foliar sprays.

#### [2021-02-22 — Disinfection of nutrient solutions in recirculating hydroponic systems](https://scienceinhydroponics.com/2021/02/disinfection-of-nutrient-solutions-in-recirculating-hydroponic-systems.html)

Daniel Fernandez discusses different disinfection methods for recirculating hydroponic nutrient solutions, including chemical and non-chemical approaches. Chemical methods like ozone require additional filtration steps due to their toxicity, while UV sterilization is effective but requires careful dosing and can affect beneficial microbe populations in the rhizosphere.

#### [2021-02-19 — Optimal air speed in a hydroponic crop](https://scienceinhydroponics.com/2021/02/optimal-air-speed-in-a-hydroponic-crop.html)

The optimal airspeed around a plant canopy is crucial for maximizing photosynthesis and preventing fungal issues. Plants exposed to higher wind speeds experience increased metabolism, but this effect plateaus at 0.3 m/s due to transpiration and wind-chill effects. An accurate measurement of these low-speed winds requires a hot wire anemometer, which can measure up to +/-0.1 m/s. The study on tomato plants with varying leaf area index (LAI) values indicates that crops with lower LAI are more efficient under higher airflow conditions, but there is also a limit to increases in photosynthetic rates based on airflow speed.

#### [2021-02-18 — Advanced phosphorous fertilizers: Are polyphosphates worth it?](https://scienceinhydroponics.com/2021/02/advanced-phosphorous-fertilizers-are-polyphosphates-worth-it.html)

Advanced phosphorous fertilizers: Polyphosphates are not superior in general conditions. However, they can be beneficial for crops grown in high pH and calcium-rich soils where P sequestration due to precipitation is a significant issue, potentially increasing yields compared to traditional orthophosphate fertilizers.

#### [2021-02-17 — Keeping plants short: Natural gibberellin inhibitors](https://scienceinhydroponics.com/2021/02/keeping-plants-short-natural-gibberellin-inhibitors.html)

This post discusses natural gibberellin inhibitors found in plant extracts such as carob fruits. Research showed that these extracts contain abscisic acid (ABA), which inhibits gibberellins, but its complex chemistry and instability make it impractical for widespread use. Instead, the focus shifted to synthetic gibberellin inhibitors like Chloromequat and Paclobutrazol, which are more effective and easier to produce in large quantities.

#### [2021-02-16 — Five common mistakes people make when formulating hydroponic nutrients](https://scienceinhydroponics.com/2021/02/five-common-mistakes-people-make-when-formulating-hydroponic-nutrients.html)

Five recurring formulation errors are omitting source-water contributions, omitting nutrients added during pH correction, chelating iron while leaving manganese able to compete for the ligand, treating ammonium/nitrate/urea nitrogen as interchangeable, and ignoring media contributions. A calculated elemental target is therefore incomplete without water, amendment chemistry, nitrogen form, chelation, and substrate context.

#### [2021-02-12 — Using VH400 sensors to build an automated irrigation setup](https://scienceinhydroponics.com/2021/02/using-vh400-sensors-to-build-an-automated-irrigation-setup.html)

Daniel Fernandez discusses the use of Vegetronix's VH400 moisture sensor for automated irrigation. The sensor is waterproof, accurate, and unaffected by salt, suitable for hydroponic setups with rockwool or other media. It can be interfaced with Arduino boards and triggers a pump based on pre-set moisture thresholds. He also mentions the battery-powered relay board that connects to multiple sensors and allows remote monitoring of irrigation systems.

#### [2021-02-11 — Practical aspects of carbon dioxide enrichment in hydroponics](https://scienceinhydroponics.com/2021/02/practical-aspects-of-carbon-dioxide-enrichment-in-hydroponics.html)

Carbon dioxide (CO₂) enrichment improves plant growth in hydroponics by increasing atmospheric CO₂ concentration, which plants use as the primary source of carbon during photosynthesis. Practical considerations include using pure CO₂ canisters for control and minimizing harmful emissions from fossil fuel burners. Optimal CO₂ levels depend on factors like temperature, light intensity, and nutrient availability; a common recommendation is to enrich atmospheres up to 1000 ppm with increased nitrogen feeding to counteract higher demand for nutrients.

#### [2021-02-10 — The cricket IoT board: A great way to create simple low-power remote sensing stations for hydroponics](https://scienceinhydroponics.com/2021/02/the-cricket-iot-board-a-great-way-to-create-simple-low-power-remote-sensing-stations-for-hydroponics.html)

Daniel Fernandez introduces the Cricket IoT board as an ideal solution for creating low-power remote sensing stations in hydroponic environments. It connects easily via Wi-Fi and supports MQTT communication, making it user-friendly and capable of handling up to two sensors without requiring extensive modifications or advanced protocols like i2c.

#### [2021-02-10 — Can you grow large flowering plants like tomatoes using the Kratky method? (passive hydroponics)](https://scienceinhydroponics.com/2021/02/can-you-grow-large-flowering-plants-like-tomatoes-using-the-kratky-method-passive-hydroponics.html)

Daniel Fernandez discusses the challenges in growing large flowering plants like tomatoes using the Kratky method, highlighting that traditional set-and-forget methods are ineffective for such plants due to rapid water consumption and nutrient imbalances. He presents a modified system involving suspended tomato plants over larger solution beds, which can yield better results but requires careful management of pH and EC levels to prevent mosquito breeding and plant toxicity issues.

#### [2021-02-09 — Timing irrigations with moisture sensors in hydroponics](https://scienceinhydroponics.com/2021/02/timing-irrigations-with-moisture-sensors-in-hydroponics.html)

Daniel Fernandez discusses using moisture sensors for irrigation timing in hydroponics. He explains calibration procedures, set points, and maintenance issues, emphasizing the importance of considering plant species sensitivity, VPD, and media volume ratios. Proper sensor placement is crucial to ensure all plants receive adequate water.

#### [2021-02-08 — Tensiometers (irrometers) the best way to time irrigations in hydroponics](https://scienceinhydroponics.com/2021/02/tensiometers-irrometers-the-best-way-to-measure-soil-moisture-in-hydroponics.html)

Daniel Fernandez discusses tensiometers as reliable sensors for measuring water potential in hydroponics and soil. He explains how these devices work by sensing the pressure difference between inside and outside a ceramic cup filled with distilled water, mimicking plant's root system behavior. Digital versions are available from Netafim and irrometer.com, offering data logging capabilities. However, tensiometers can be affected by salt buildup and have slow response times.

#### [2021-02-04 — The Chirp Sensor: A plug-and-play solution to moisture monitoring in hydroponics](https://scienceinhydroponics.com/2021/02/the-chirp-sensor-a-plug-and-play-solution-to-moisture-monitoring-in-hydroponics.html)

The Chirp Sensor simplifies moisture monitoring in hydroponics by using capacitive sensing technology unaffected by salts. By setting a threshold and indicating watering via chirping, it ensures precise irrigation without complex setup or calibration, suitable for both single plants and large greenhouses.

#### [2021-02-01 — How to identify resistive moisture sensors and why to never use them in hydroponics](https://scienceinhydroponics.com/2021/02/how-to-identify-resistive-moisture-sensors-and-why-to-never-use-them-in-hydroponics.html)

Daniel Fernandez explains the limitations of resistive moisture sensors in hydroponics, which often lead to inaccurate measurements due to changes in solution conductivity and electrode corrosion. He recommends avoiding these sensors because they cannot accurately measure water content over time, especially when salts accumulate, leading to unreliable readings.

### 2020

#### [2020-12-07 — Five tips to succeed when doing Kratky hydroponics](https://scienceinhydroponics.com/2020/12/five-tips-to-succeed-when-doing-kratky-hydroponics.html)

The post discusses five tips for successful Kratky hydroponics: maintaining the right volume per plant and container dimensions, ensuring proper starting water level, starting with lower nutrient dosage and pH levels, and disinfecting the solution to prevent pathogens. These practices help avoid common issues like root oxygen deprivation or nutrient concentration problems.

#### [2020-11-29 — Practical use of ion selective electrodes in hydroponics](https://scienceinhydroponics.com/2020/11/practical-use-of-ion-selective-electrodes-in-hydroponics.html)

Daniel Fernandez discusses how ion selective electrodes have become more accessible and affordable for hydroponics. He highlights that these electrodes can accurately measure potassium, calcium, and nitrate concentrations in nutrient solutions without needing complex calibration, making routine monitoring feasible. The electrodes are simple to use and provide instantaneous results, enabling quick adjustments to solution preparation.

#### [2020-11-28 — Inner leaf tipburn in hydroponic lettuce](https://scienceinhydroponics.com/2020/11/inner-leaf-tipburn-in-hydroponic-lettuce.html)

Inner leaf tipburn in hydroponic lettuce is caused by insufficient calcium at the edges of leaves, leading to rapid growth center death. Solutions include reducing K:Ca ratio and lowering EC, as well as applying foliar sprays with calcium chloride. Environmental modifications like reduced light intensity and increased air circulation can also help prevent this issue.

#### [2020-11-22 — The effect of Seaweed/Kelp extracts in plants](https://scienceinhydroponics.com/2020/11/the-effect-of-seaweed-kelp-extracts-in-plants.html)

Seaweed/kelp extracts are widely used by growers for enhancing plant quality and yields due to their high nutrient content and bioactive molecules like cytokinins and auxins. Research from 1991 and a 2014 review supports the effectiveness of these extracts, showing increases in growth, yield, and resistance to pests across various species. Application methods vary but consistency is key for optimal results, with some studies suggesting plant hormones can replace seaweed extracts effectively.

#### [2020-11-08 — Characterizing hydroponic stock nutrient solutions](https://scienceinhydroponics.com/2020/11/characterizing-hydroponic-stock-nutrient-solutions.html)

This post summarizes Daniel Fernandez's method for characterizing hydroponic nutrient solutions with simple and accurate techniques. A new video demonstrates these methods in practical use, showcasing his previously prepared B solution.

#### [2020-11-01 — Why are different hydroponic formulations required for different situations?](https://scienceinhydroponics.com/2020/11/why-are-different-hydroponic-formulations-required-for-different-situations.html)

Different hydroponic formulations are required due to varying conditions such as media type, water composition, temperature, humidity, irrigation frequency, and run-off volume. This variability means no single formulation is universally optimal; instead, an optimized solution must be tailored to specific growing conditions for best results.

#### [2020-11-01 — How tap water affects your hydroponic nutrient formulation](https://scienceinhydroponics.com/2020/11/how-tap-water-affects-your-hydroponic-nutrient-formulation.html)

Tap water changes a formulation through four groups: useful dissolved nutrients, carbonate alkalinity and its acid demand, non-nutrient ions such as sodium or chloride, and dissolved organics. Calcium, magnesium, iron, and the nutrient contribution of neutralizing acid belong in the mass balance, while seasonal variation makes dated laboratory analyses preferable to one permanent assumption.

#### [2020-10-25 — How much Phosphorous are you adding to your solution to adjust pH?](https://scienceinhydroponics.com/2020/10/how-much-phosphorous-are-you-adding-to-your-solution-to-adjust-ph.html)

Daniel Fernandez discusses the use of phosphoric acid in pH adjustment, highlighting its effectiveness but also warning about potential negative effects on plant growth due to excess phosphorous. He provides a formula for calculating phosphorus contribution and emphasizes the importance of monitoring and adjusting formulations when using high concentrations of phosphoric acid.

#### [2020-10-25 — How to deal with nutrient solution waste in hydroponics](https://scienceinhydroponics.com/2020/10/how-to-deal-with-nutrient-solution-waste-in-hydroponics.html)

Daniel Fernandez discusses methods to treat nutrient solution waste in hydroponics, focusing on denitrification using bacteria, artificial wetlands, and algae. Denitrification removes more than 90% of nitrogen but not phosphorous; artificial wetlands remove both N and P with a large footprint issue at low cost; algae can achieve over 90% removal efficiency for both nutrients in transparent tubes, offering additional value as harvestable biomass.

#### [2020-10-11 — Factors limiting the life of a recirculating hydroponic nutrient solution](https://scienceinhydroponics.com/2020/10/factors-limiting-the-life-of-a-recirculating-hydroponic-nutrient-solution.html)

Daniel Fernandez discusses factors limiting the life of a recirculating hydroponic nutrient solution such as selective nutrient uptake leading to phosphorous and micronutrient accumulation, contamination by pathogens, and accumulation of non-nutrient substances like sodium and chloride. Solutions can be extended up to 8-16 weeks with proper management but beyond this point risks increase due to ion accumulation that is hard to control.

#### [2020-10-10 — Preparing your own low cost A+B generic hydroponic nutrients at a small scale from raw salts](https://scienceinhydroponics.com/2020/10/preparing-your-own-low-cost-ab-generic-hydroponic-nutrients-at-a-small-scale-from-raw-salts.html)

Daniel Fernandez describes preparing a generic A+B hydroponic nutrient formulation using raw salts at a low cost (around $25/gallon) for small-scale use, with EC expected to be 2.2 mS/cm. He outlines the materials needed and steps for preparation, including avoiding micros due to convenience issues.

#### [2020-10-03 — How to correctly prepare dilutions from concentrated solutions in hydroponics](https://scienceinhydroponics.com/2020/10/how-to-correctly-prepare-dilutions-from-concentrated-solutions-in-hydroponics.html)

Daniel Fernandez discusses the importance of accurately preparing nutrient dilutions in hydroponics, highlighting that precise measurement is crucial to avoid errors, especially when dealing with non-standardized volume measurements which can lead to ±20% discrepancies. He recommends using calibrated volumetric materials and measuring conductivity at a small scale before scaling up to desired volumes.

#### [2020-10-03 — The cost of reproducing the label of a commercial hydroponic fertilizer with raw salts at a small scale](https://scienceinhydroponics.com/2020/10/the-cost-of-reproducing-the-label-of-a-commercial-hydroponic-fertilizer-with-raw-salts-at-a-small-scale.html)

Daniel Fernandez calculates the cost of recreating commercial hydroponic nutrients using raw salts. He finds that while it can save money, especially at larger scales, copying exact label compositions is not always cost-effective due to misleading label information and higher costs for small packages. Instead, he recommends designing formulations tailored to specific needs and budgets.

#### [2020-09-27 — Starting a youtube channel to teach chemistry related hydroponic skills](https://scienceinhydroponics.com/2020/09/starting-a-youtube-channel-to-teach-chemistry-related-hydroponic-skills.html)

Daniel Fernandez starts a YouTube channel called Chemisting to share chemistry-related practical skills in hydroponics. In his first video, he demonstrates how to accurately measure and transfer volumes for preparing concentrated solutions at small scales, emphasizing proper technique for effective hydroponic practices.

#### [2020-09-22 — Hardware for building a wifi-connected DIY monitoring/control system for a hydroponic crop](https://scienceinhydroponics.com/2020/09/hardware-for-building-a-wifi-connected-diy-monitoring-control-system-for-a-hydroponic-crop.html)

Daniel Fernandez discusses hardware for a DIY monitoring/control system in hydroponic crops, including Raspberry Pi 4, Arduino UNO WiFi REV2 with Tentacle shield, pH and EC probes. He emphasizes the importance of flexibility and quality sensors over cost savings, highlighting how these components enable efficient control and data collection.

#### [2020-09-19 — Nutrient problems and foliar sprays](https://scienceinhydroponics.com/2020/09/nutrient-problems-and-foliar-sprays.html)

Daniel Fernandez discusses nutrient problems in hydroponic crops, attributing them to issues like pH and EC fluctuations, humidity, temperature, and root damage. He emphasizes the importance of foliar sprays for quick recovery when chemical adjustments are insufficient due to transport problems not necessarily indicating low nutrient concentrations in solution. The article highlights how foliar applications can bypass these issues by directly delivering nutrients to leaves, aiding plant health until environmental or solution issues are resolved.

#### [2020-09-12 — Five things to consider when trying to copy commercial hydroponic nutrients](https://scienceinhydroponics.com/2020/09/five-things-to-consider-when-trying-to-copy-commercial-hydroponic-nutrients.html)

Growers often copy commercial hydroponic nutrients due to their high costs, but this process is complicated by label inaccuracies, hidden ingredients, and undisclosed substances. To accurately replicate a nutrient formulation, one must analyze the actual fertilizer composition, evaluate raw inputs, and consider potential additives that can significantly affect plant growth.

#### [2020-09-07 — Five things you can learn from leaf tissue analysis](https://scienceinhydroponics.com/2020/09/five-things-you-can-learn-from-leaf-tissue-analysis.html)

Leaf tissue analysis provides insights into VPD effects on Ca levels, heavy metal contamination detection, nutrient transport efficiency, and silicon supplementation success. Regular analysis aids in identifying deviations from expected growth patterns and ensures adequate nutrient uptake, enhancing crop yields.

#### [2020-09-07 — What is the ideal amount of media per plant in hydroponics?](https://scienceinhydroponics.com/2020/09/what-is-the-ideal-amount-of-media-per-plant-in-hydroponics.html)

The ideal amount of media per plant in hydroponics is crucial for determining irrigation setup and plant growth. Media volume affects root system oxygen, water retention, and nutrient uptake; larger volumes are recommended for novice growers or when close monitoring is not feasible. The study on tomatoes found that using 15L containers yielded higher yields compared to smaller container sizes, suggesting more media leads to better conditions and potentially higher crop success.

#### [2020-09-04 — Why most of the time a “deficiency” in hydroponics is not solved by just “adding more of it”](https://scienceinhydroponics.com/2020/09/why-most-of-the-time-a-deficiency-in-hydroponics-is-not-solved-by-just-adding-more-of-it.html)

Daniel Fernandez explains that a deficiency often isn't fixed by just adding more of the missing nutrient. He discusses how plants may struggle to absorb certain elements due to competition from other nutrients, ratios with other elements, or environmental factors like temperature and humidity, rather than an actual lack of the element in question.

#### [2020-09-04 — Getting all the data to evaluate a problem in a hydroponic crop](https://scienceinhydroponics.com/2020/09/getting-all-the-data-to-evaluate-a-problem-in-a-hydroponic-crop.html)

Daniel Fernandez discusses gathering data for diagnosing hydroponic crop issues, including detailed pictures of plants, environmental measurements, nutrient solution analysis, leaf tissue analysis, and microscopy. He emphasizes the importance of having comprehensive data to accurately diagnose problems and avoid ineffective solutions.

#### [2020-08-23 — Building a DIY control infrastructure for a hydroponic crop: Part one](https://scienceinhydroponics.com/2020/08/building-a-diy-control-infrastructure-for-a-hydroponic-crop-part-one.html)

Daniel Fernandez describes his DIY control infrastructure for hydroponic crops, focusing on flexibility and power. He uses a central computer with a database for managing devices, sensors, and alarms, supplemented by Arduino measuring and control stations. The system relies on MQTT protocol for communication, allowing easy addition of new devices and setting up custom measurements like temperature and humidity. This setup offers unparalleled control but requires significant investment in electronics and programming time.

#### [2020-08-18 — Five common misconceptions around nutrient management in hydroponics](https://scienceinhydroponics.com/2020/08/five-common-misconceptions-around-nutrient-management-in-hydroponics.html)

Daniel Fernandez discusses common misconceptions in nutrient management, such as thinking EC increases mean plants are not feeding (EC measures concentration, not absolute nutrients) and that yellowing always indicates a deficiency. He explains the importance of considering environmental factors like pH and VPD, and notes nutrient dynamics can be complex, with some elements becoming less available at higher concentrations.

#### [2020-08-16 — Five tips to successfully manage your nutrient solution in a recirculating hydroponic setup](https://scienceinhydroponics.com/2020/08/six-tips-to-successfully-manage-your-nutrient-solution-in-a-recirculating-hydroponic-setup.html)

To successfully manage nutrient solutions in recirculating hydroponics, ensure the reservoir volume is at least 10 times the irrigation volume to prevent rapid pH and EC changes. Additionally, add water rather than nutrients when EC increases with each irrigation cycle, adjusting for plant absorption and maintaining proper pH levels.

#### [2020-08-09 — About the default fertilizer database in HydroBuddy](https://scienceinhydroponics.com/2020/08/about-the-default-fertilizer-database-in-hydrobuddy.html)

Daniel Fernandez explains the default fertilizer database in HydroBuddy, a tool for creating hydroponic nutrient solutions. He details how different salts contribute to nutrition and pH, emphasizing flexibility and cost considerations, while noting limitations such as missing common substances.

#### [2020-07-29 — A new conductivity model in HydroBuddy](https://scienceinhydroponics.com/2020/07/a-new-conductivity-model-in-hydrobuddy.html)

Daniel Fernandez implemented a new conductivity model in HydroBuddy using empirical data from five salts. The model, based on linear regression, accurately predicts EC values within this experimental space but may not generalize to formulations with different ion combinations or strong acids/bases.

#### [2020-07-26 — Building a model to predict EC in hydroponic nutrient solutions](https://scienceinhydroponics.com/2020/07/building-a-model-to-predict-ec-in-hydroponic-nutrient-solutions.html)

Daniel Fernandez developed a model to predict electrical conductivity (EC) in hydroponic nutrient solutions, using 50 different EC measurements across various concentrations. The model uses simple modeling techniques and accounts for varying contributions of salts based on their composition, ensuring accurate predictions without needing experimental data. This tool will enhance HydroBuddy by providing reliable EC values for practical use.

#### [2020-07-11 — Keeping plants short: Using day/night temperature differences (DIF)](https://scienceinhydroponics.com/2020/07/keeping-plants-short-using-day-night-temperature-differences-dif.html)

Daniel Fernandez discusses using day/night temperature differences (DIF) to control plant height, citing research from Michigan State University showing that a 14F drop during early morning hours can reduce plant height without affecting productivity. He notes mixed results across different species and emphasizes the importance of testing specific plants under various DIF conditions for optimal results.

#### [2020-07-11 — Monitoring the quality of fertilizer stock solutions](https://scienceinhydroponics.com/2020/07/monitoring-the-quality-of-fertilizer-stock-solutions.html)

Daniel Fernandez discusses monitoring fertilizer stock solutions for quality control. He recommends measuring density using a pycnometer and pH with a calibrated pH meter, noting these parameters are sensitive to composition changes. Deviations from expected values indicate potential issues that may require further chemical analysis.

#### [2020-07-04 — Why red and blue LED grow lights never took off](https://scienceinhydroponics.com/2020/07/why-red-and-blue-led-grow-lights-never-took-off.html)

Daniel Fernandez explains why red and blue LED grow lights have not been widely adopted despite their potential. While they can effectively grow plants under controlled conditions, issues with plant health and visibility in large-scale applications led to a shift towards full spectrum LEDs. The main drawbacks include reduced plant growth efficiency compared to traditional lighting sources like HPS or MH lamps, as well as the inability to diagnose problems due to the lights' black appearance on these wavelengths.

#### [2020-07-04 — In-depth books to learn about hydroponics at an advanced level](https://scienceinhydroponics.com/2020/07/in-depth-books-to-learn-about-hydroponics-at-an-advanced-level.html)

Daniel Fernandez summarizes three advanced hydroponics books: 'Mineral Nutrition of Higher Plants' covers plant mineral absorption and interactions; 'Soilless Culture: Theory and Practice' delves into practical aspects like media properties, irrigation systems, and root systems; and 'Hydroponic Food Production: A Definitive Guidebook for the Advanced Home Gardener and the Commercial Hydroponic Grower' provides insights on manipulating plant environments to enhance secondary metabolite production. Each book offers foundational knowledge and references for further study.

#### [2020-06-28 — Six things you need to know before using plant hormones](https://scienceinhydroponics.com/2020/06/six-things-you-need-to-know-before-using-plant-hormones.html)

Plant hormones are used as chemical signals within plants; they trigger specific behaviors like growth, flowering, or terpene production. To effectively use them, one must know what behavior is desired and plan hormone applications strategically. Plant hormones interact with each other and have varying effects at different concentrations, so it's important to introduce them one by one and ensure the correct concentration for optimal results.

#### [2020-06-28 — Keeping plants short: Synthetic gibberellin inhibitors](https://scienceinhydroponics.com/2020/06/keeping-plants-short-synthetic-gibberellin-inhibitors.html)

Daniel Fernandez discusses synthetic gibberellin inhibitors as powerful tools to reduce plant height without affecting flowering. He explains that by disrupting gibberellin synthesis pathways, plants can be kept bushier and more compact while maintaining productivity. However, he notes the significant toxicity of existing inhibitors like paclobutrazol, leading to their restricted use in edible crops. Newer growth retardants such as Prohexadione-Ca and Trinexapac-ethyl have lower toxicities but require careful application for optimal results.

#### [2020-06-28 — Keeping plants short: Why is it important?](https://scienceinhydroponics.com/2020/06/keeping-plants-short-why-is-it-important.html)

Daniel Fernandez explains why keeping plants short is important in hydroponics and conventional agriculture, citing reasons such as mechanical stability, ease of harvesting, and better nutrient distribution. He also discusses the practical implications like increased productivity and reduced lodging risk for shorter crops.

#### [2020-06-19 — Using calcium sulfate in hydroponics](https://scienceinhydroponics.com/2020/06/using-calcium-sulfate-in-hydroponics.html)

Daniel Fernandez discusses using calcium sulfate in hydroponics, highlighting its high solubility at 20°C (68°F) of around 2.4 g/L allowing up to 550 ppm Ca without precipitation. He explains that unlike other sources like calcium chloride or nitrate, calcium sulfate does not contribute significantly to plant nutrition and has negligible effects on pH, making it suitable for independent calcium supplementation in hydroponic crops.

#### [2020-06-13 — Average yields per acre of hydroponic crops](https://scienceinhydroponics.com/2020/06/average-yields-per-acre-of-hydroponic-crops.html)

Daniel Fernandez discusses average yields per acre for hydroponic crops, highlighting discrepancies between theoretical and practical data. He cites Howard Resh's 1998 book as a source of expected yields but notes inconsistencies in the table's presence across editions, suggesting potential issues with the original data. The author emphasizes that actual yield expectations are complex and depend on various variables, recommending empirical testing for accurate guidance.

#### [2020-06-13 — Three ways to judge the quality of powdered hydroponic nutrient products](https://scienceinhydroponics.com/2020/06/three-ways-to-judge-the-quality-of-powdered-hydroponic-nutrient-products.html)

The post discusses three ways to judge the quality of powdered hydroponic nutrient products. It highlights that a good solid fertilizer should be finely mixed, homogeneous, stable over time, and have low standard deviation in analyzed samples, ensuring reproducibility and effective plant nutrition.

#### [2020-06-06 — How to control algae in a hydroponic crop](https://scienceinhydroponics.com/2020/06/how-to-control-algae-in-a-hydroponic-crop.html)

The article discusses the control of algae in hydroponic crops, highlighting their detrimental effects on nutrient solutions and plant growth. It outlines various methods to prevent or manage algae, including using opaque covers, fungicides, insecticides, algicides, and hydrogen peroxide. The effectiveness of IBA (3-(3-indolyl)butanoic acid), a non-phytotoxic indole derivative, in controlling algae populations is emphasized, with its ability to reduce algae growth even when nutrient solution directly contacts the media.

#### [2020-06-06 — Can you use regular soil fertilizers in hydroponics?](https://scienceinhydroponics.com/2020/06/can-you-use-regular-soil-fertilizers-in-hydroponics.html)

The post explains that while soil fertilizers can be used in hydroponics, they should not contain urea or ammonium as nitrogen sources due to their strong acidifying effect. Instead, hydroponic-specific fertilizers with nitrate forms of nitrogen are recommended for frequent feeding and healthy growth. The author recommends using a combination of micro nutrient fertilizer (0-10-10) and calcium nitrate to create an effective hydroponic solution.

#### [2020-06-05 — Accurately preparing large quantities of concentrated hydroponic nutrients](https://scienceinhydroponics.com/2020/06/accurately-preparing-larger-quantities-of-concentrated-hydroponic-nutrients.html)

Daniel Fernandez discusses the importance of having a reproducible process for preparing large quantities of concentrated hydroponic nutrients to ensure consistent results. He outlines how errors in volume measurement, especially at larger scales, can lead to inconsistent final nutrient solutions. To mitigate this, he describes a method involving precise weighing and using flow meters to accurately measure volumes, resulting in concentration values with error ranges as low as 0.1-1.0%, improving crop reproducibility.

#### [2020-05-31 — Plant Growth Promoting Rhizobacteria (PGPR) in hydroponics](https://scienceinhydroponics.com/2020/05/plant-growth-promoting-rhizobacteria-pgpr-in-hydroponics.html)

Daniel Fernandez discusses Plant Growth Promoting Rhizobacteria (PGPR) used in hydroponics, highlighting their ability to increase nutrient availability and stimulate plant growth. He notes that while PGPR have shown positive effects in soil, the application of these bacteria in hydroponic systems is not straightforward due to potential negative impacts from excessive use or improper inoculation methods. The author emphasizes the importance of choosing appropriate bacterial strains, concentrations, and inoculation techniques for optimal results.

#### [2020-05-25 — Why do NPK labels express P and K as oxides?](https://scienceinhydroponics.com/2020/05/why-do-npk-labels-express-p-and-k-as-oxides.html)

The post explains why phosphorus (P) and potassium (K) are expressed as oxides (K₂O and P₂O₅) on fertilizer labels instead of their elemental forms. This is due to historical analytical methods where K and P were quantified from calcined samples, leading to the concentration of these oxides being what was measured in labs. Despite not being present in pure oxide form within fertilizers, this practice continues as a legacy from early days of analysis, maintaining coherence with past NPK labels.

#### [2020-05-24 — HydroBuddy has now been updated to v1.70: New features and modifications](https://scienceinhydroponics.com/2020/05/hydrobuddy-has-now-been-updated-to-v1-70-new-features-and-modifications.html)

HydroBuddy v1.70 updates its substance selection screen by removing rarely used inputs and replacing them with commercially available raw fertilizers, including metal chelates and salts. It also adds links for purchasing these chemicals directly from Amazon affiliate partners, enhancing user convenience and support.

#### [2020-05-19 — Calcium EDTA and its problems in hydroponics](https://scienceinhydroponics.com/2020/05/calcium-edta-and-its-problems-in-hydroponics.html)

Daniel Fernandez discusses the use of Calcium EDTA in hydroponics, highlighting its high sodium content (12.15%) which can be detrimental to plants at higher concentrations. He also notes that EDTA's weak binding with calcium allows it to displace other ions like lead from media, and forms insoluble salts with calcium itself, complicating its use. Despite these issues, he mentions its advantages in foliar applications due to its resistance to precipitation.

#### [2020-05-17 — How to prepare a low cost chelated micronutrient solution](https://scienceinhydroponics.com/2020/05/how-to-prepare-a-low-cost-chelated-micronutrient-solution.html)

Daniel Fernandez outlines how to prepare a low-cost chelated micronutrient solution, using inexpensive salts like disodium EDTA and heavy metal sulfate salts. The article emphasizes the importance of these micronutrients in plant growth despite their small concentrations, detailing the preparation process including necessary equipment and cost considerations. It also highlights potential issues such as slow equilibrium formation and susceptibility to spoilage.

#### [2020-05-11 — How to prepare pH 4 and 7 buffers from scratch without using a pH meter](https://scienceinhydroponics.com/2020/05/how-to-prepare-ph-4-and-7-buffers-from-scratch-without-using-a-ph-meter.html)

Daniel Fernandez describes how to prepare pH 4 and 7 buffers from scratch using only a scale, distilled water, and food-grade salts for calibration purposes. He outlines precise steps for preparing these buffers in glass bottles, emphasizing the importance of accuracy with materials like potassium citrate, anhydrous citric acid, and phosphates.

#### [2020-05-10 — Why TDS is NOT equal to Total Dissolved Solids in hydroponics](https://scienceinhydroponics.com/2020/05/why-tds-is-not-equal-to-total-dissolved-solids-in-hydroponics.html)

A meter's TDS or ppm value is EC converted through a reference-salt scale, not a measurement of the nutrient solution's dissolved mass. Different ions conduct differently, and neutral solutes affect osmotic pressure without EC, so neither TDS nor equal EC can compare the strength of differently composed recipes; compare explicit nutrient composition instead.

#### [2020-05-09 — Understanding the carbonic acid/bicarbonate buffer in hydroponics](https://scienceinhydroponics.com/2020/05/understanding-the-carbonic-acid-bicarbonate-buffer-in-hydroponics.html)

Daniel Fernandez explains the carbonic acid/bicarbonate buffer in hydroponics, detailing its complexity and importance. He demonstrates how this buffer can stabilize pH even with minimal changes to atmospheric CO₂ levels, highlighting practical implications for nutrient solution preparation and system design.

#### [2020-05-05 — Hydroponics nutrients and microgreens](https://scienceinhydroponics.com/2020/05/hydroponics-nutrients-and-microgreens.html)

Daniel Fernandez discusses maximizing microgreen yield using hydroponic nutrients, highlighting studies showing significant weight gains but also noting potential decreases in nutritional value. He emphasizes that only a few papers exist on this topic and suggests further research is needed to balance increased yields with preserved quality.

#### [2020-05-03 — Is my water source good for hydroponics?](https://scienceinhydroponics.com/2020/05/is-my-water-source-good-for-hydroponics.html)

Determining if a water source is suitable for hydroponics involves assessing its mineral content. Key points include identifying sources with high sodium, chloride, or iron levels that require treatment and analyzing for heavy metals and other ions. Water sources must meet safety standards before being used in hydroponic systems.

#### [2020-05-02 — A guide to different pH down options in hydroponics](https://scienceinhydroponics.com/2020/05/a-guide-to-different-ph-down-options-in-hydroponics.html)

Daniel Fernandez discusses different pH down options in hydroponics, including strong acids (phosphoric and sulfuric) and weak acids. Strong acids offer the strongest ability to drop pH per unit of volume but can be difficult to use due to their concentrated forms. Weak acids are safer to handle but require larger additions for the same effect. The choice depends on whether users prefer stronger buffering capacity or lower cost, with drain-to-waste systems favoring strong acids and recirculating systems preferring options with added buffering capacity.

#### [2020-04-26 — Microgreen production at home: Getting the materials](https://scienceinhydroponics.com/2020/04/microgreen-production-at-home-getting-the-materials.html)

Daniel Fernandez decides to produce microgreens at home, aiming for large-scale consumption. He uses an LED lighting system with cool spectrum lights and Styrofoam trays to grow broccoli seeds in a hydroponic setup, which can yield up to 5 racks of microgreens simultaneously.

#### [2020-04-25 — Nutrient solution conductivity estimates in Hydrobuddy](https://scienceinhydroponics.com/2020/04/nutrient-solution-conductivity-estimates-in-hydrobuddy.html)

Daniel Fernandez explains how HydroBuddy calculates nutrient solution conductivity estimates, noting deviations from real measurements due to assumptions about ion activity. He discusses the limitations of using limiting molar conductivity values and suggests future improvements could account for non-linear relationships between ions.

#### [2020-04-19 — Sugars in hydroponic nutrient solutions](https://scienceinhydroponics.com/2020/04/sugars-in-hydroponic-nutrient-solutions.html)

Daniel Fernandez discusses the potential use of simple sugars in hydroponic nutrient solutions for plant growth. He highlights that plants can uptake and re-uptake exuded sugars through their roots but warns against adding sugars due to inefficient transport within the plant, leading to wasted sugar and possible negative effects on root microbiota. The author suggests focusing instead on microbe inoculations as a more effective strategy.

#### [2020-04-17 — Controlling pH in hydroponics using only electricity](https://scienceinhydroponics.com/2020/04/controlling-ph-in-hydroponics-using-only-electricity.html)

Daniel Fernandez describes an alternative method to control pH in hydroponics using electricity. He explains how water can be oxidized at the anode and reduced at the cathode, generating H+ ions for lowering pH or OH- ions for raising it, without needing strong acids or bases. This system uses ion exchange membranes to separate these reactions, allowing fine control over pH with minimal maintenance and risk of errors.

#### [2020-04-14 — Maximizing essential oil yields: A look into nutrient concentrations](https://scienceinhydroponics.com/2020/04/maximizing-essential-oil-yields-a-look-into-nutrient-concentrations.html)

Daniel Fernandez reviews studies on nutrient concentrations for maximizing essential oil yields in hydroponic setups. He summarizes findings showing optimal N concentration at 200 ppm, K at 200-300 ppm, and Ca at 160 ppm. A base formulation is proposed with these values to start optimizing from.

#### [2020-04-12 — How to make your growing more systematic](https://scienceinhydroponics.com/2020/04/how-to-make-your-growing-more-systematic.html)

Daniel Fernandez emphasizes the importance of systematic growing practices for better crop outcomes. He advocates for having a dedicated person record standard operating procedures and sensor data, ensuring consistency across all operations to detect issues early and make timely adjustments.

#### [2020-04-11 — The best cheap sensor setup for relative humidity in hydroponic automation projects](https://scienceinhydroponics.com/2020/04/the-best-cheap-sensor-setup-for-relative-humidity-in-hydroponic-automation-projects.html)

Daniel Fernandez recommends using a 2-sensor setup with an SHT1x and BME280 for accurate humidity measurement in hydroponics, noting that both sensors are reliable but prone to systematic errors. He suggests monitoring deviations between the two sensors and contacting him for custom sensing solutions.

#### [2020-04-11 — The media exchange solution test: A better measurement of media effects in hydroponics](https://scienceinhydroponics.com/2020/04/the-media-exchange-solution-test-a-better-measurement-of-media-effects-in-hydroponics.html)

The article introduces a direct comparison test between the nutrient solution and different types of growing media, focusing on their exchange capacity. This helps understand how media affects nutrient solutions and allows for adjustments to better match the needs of specific crops, reducing heartache in hydroponic setups.

#### [2020-04-10 — Using biochar in hydroponics to improve yields](https://scienceinhydroponics.com/2020/04/using-biochar-in-hydroponics.html)

Biochars derived from controlled burning of plant materials offer significant benefits when used as amendments to improve hydroponic media properties. Studies show that a 5% biochar amendment can substantially increase yields in cherry tomatoes and peppers, highlighting their potential to enhance root health and nutrient uptake. However, the quality control is crucial due to variations in biochar properties depending on the creation process and sourcing material, which could lead to detrimental effects if not properly managed.

### 2019

#### [2019-08-17 — Six things to consider when running experiments in hydroponics](https://scienceinhydroponics.com/2019/08/six-things-to-consider-when-running-experiments-in-hydroponics.html)

When running experiments in hydroponics, consider the number of plants and variations. A small sample size leads to higher variability and weaker conclusions, while too many variations can make statistical analysis difficult. Always include a control group and collect comprehensive data for accurate results. Blind experimentation is crucial to avoid bias.

#### [2019-08-09 — Why you should optimize your nutrient solution for your particular setup](https://scienceinhydroponics.com/2019/08/why-you-should-optimize-your-nutrient-solution-for-your-particular-setup.html)

Daniel Fernandez explains that optimizing a nutrient solution for each specific setup is crucial for maximizing yields. He highlights how root environment, media type, watering frequency, and outside conditions all influence nutrient absorption and transport efficiency, emphasizing that no one-size-fits-all solution exists in hydroponics.

#### [2019-08-06 — Five common reason why you’re losing yields](https://scienceinhydroponics.com/2019/08/five-common-reason-why-youre-losing-yields.html)

Daniel Fernandez identifies five common mistakes in hydroponics: improper vapor pressure deficit (VPD), poor root zone environments, lack of foliar spraying, insufficient silicate applications, and inadequate tailored nutrient optimization. These issues can significantly reduce yields; for instance, VPD mismanagement leads to suboptimal plant growth due to temperature or humidity extremes, while incorrect EC/pH measurements in non-recirculating setups result in high salinity and pH levels that are hard to correct.

#### [2019-08-04 — High P or low P? The mystery of phosphorus in hydroponic culture](https://scienceinhydroponics.com/2019/08/high-p-or-low-p-the-mystery-of-phosphorus-in-hydroponic-culture.html)

Daniel Fernandez discusses the confusion surrounding optimal phosphorus (P) levels in hydroponic culture, noting inconsistent recommendations ranging from 10 ppm to 200 ppm. He highlights conflicting evidence on P's effects and interactions with other nutrients, emphasizing that precise optimization depends on specific growing conditions.

#### [2019-08-02 — Using a biodegradable iron chelate (IDHA) in hydroponics](https://scienceinhydroponics.com/2019/08/using-a-biodegradable-iron-chelate-idha-in-hydroponics.html)

Daniel Fernandez discusses using a biodegradable iron chelate (IDHA) in hydroponics, highlighting its effectiveness compared to traditional chelating agents like EDTA. Despite being less stable in solution, IDHA provides better absorption and health benefits for plants without accumulating toxic residues. However, it may not be suitable for extended use in recirculating systems or media that easily captures it.

#### [2019-08-01 — Selenium in hydroponic culture](https://scienceinhydroponics.com/2019/08/selenium-in-hydroponic-culture.html)

Selenium is not commonly used in hydroponics due to its non-essential role for plant growth but is studied for human health benefits. Studies vary in Se source, concentration (typically 0.1-0.5ppm), and application form (cations or anions). Effects on tomato plants include delayed ripening with improved post-harvest fruit characteristics; studies show yield improvements when using Se. Selenium can also protect against temperature and salt stress, as demonstrated in pepper and wheat seedling studies. However, at high concentrations, selenium is toxic to plants, underscoring the importance of careful application.

#### [2019-07-27 — Five ways to save money in hydroponics](https://scienceinhydroponics.com/2019/07/five-ways-to-save-money-in-hydroponics.html)

Daniel Fernandez outlines five strategies for saving money on hydroponic operations: avoiding liquid fertilizers by switching to solids, preparing your own fertilizer blends, making foliar treatments at home, using a recirculating nutrient system, and incorporating silicon additives. These changes can significantly reduce costs in commercial hydroponics, potentially saving tens to hundreds of thousands of dollars annually.

#### [2019-07-25 — Using electro-degradation to enhance yields in recirculating hydroponics](https://scienceinhydroponics.com/2019/07/using-electro-degradation-to-enhance-yields-in-recirculating-hydroponics.html)

Daniel Fernandez's research demonstrates that electro-degradation, using alternating current (AC) through an electrode in nutrient solution, effectively degrades plant exudates without causing nutrient deficiencies. This method increases fruit yields by eliminating autotoxicity and maintaining consistent nutrient levels, offering a cost-effective alternative to filtration systems for recirculating hydroponics.

#### [2019-07-24 — Using machine learning control methods in hydroponics](https://scienceinhydroponics.com/2019/07/using-machine-learning-control-methods-in-hydroponics.html)

Daniel Fernandez discusses advanced control systems for hydroponics using machine learning. He highlights how these systems can anticipate environmental changes like humidity and temperature fluctuations, leading to more efficient and accurate control of conditions needed for optimal crop yields, up to 66% in one case study.

#### [2019-07-23 — Calcium’s behavior in hydroponics](https://scienceinhydroponics.com/2019/07/calciums-behavior-in-nutrient-solutions.html)

Daniel Fernandez discusses calcium behavior in hydroponics, highlighting its non-linear response to nutrient concentrations and the importance of environmental factors like vapor pressure deficit (VPD) for effective transport. He explains how increasing Ca levels can sometimes lead to lower Ca accumulation in leaf tissue due to favorable transport conditions at lower concentrations, emphasizing the need to adjust VPD rather than simply changing solution concentration.

#### [2019-07-21 — Better understanding pH dynamics in hydroponic culture](https://scienceinhydroponics.com/2019/07/better-understanding-ph-dynamics-in-hydroponic-culture.html)

Root-zone pH emerges from solution acid/base chemistry, charge-balanced plant uptake, and reactions with the medium. Nitrate-dominant uptake commonly drives pH upward, ammonium uptake drives it downward, phosphate or bicarbonate can buffer change, and peat or other media may impose their own drift; concentration changes cannot be interpreted without all three mechanisms.

#### [2019-07-20 — Five important things you should know about humidity in hydroponics](https://scienceinhydroponics.com/2019/07/five-important-things-you-should-know-about-humidity-in-hydroponics.html)

Understanding and controlling humidity is crucial in hydroponics. Relative humidity measures the percentage of water vapor present compared to air capacity, while absolute humidity indicates actual moisture content. Reliable instruments like semiconductor-based meters are unreliable; investing in multiple sensors with different chipsets can improve accuracy. Higher relative humidity generally benefits plants more than lower levels, but extreme conditions still harm them. Proper placement and monitoring of RH meters within plant canopies is essential for accurate readings.

### 2017

#### [2017-11-18 — DIY Warm white LED lamp PAR measurements, not so exciting after all!](https://scienceinhydroponics.com/2017/11/diy-warm-white-led-lamp-par-measurements-not-so-exciting-after-all.html)

Daniel Fernandez's measurements reveal that his DIY warm white LED lamps, despite their higher efficiency in lux, do not match the photo-synthetically active radiation (PAR) output of a 1000W High-Pressure Sodium (HPS) lamp. The PAR values are only around 1466 umol*s^-1*m^-2 at its highest point, far below even the poorest HPS models, indicating that these lamps cannot replace HPS effectively in terms of photosynthesis efficiency.

#### [2017-11-03 — Cheap DIY high power LED grow lights: Introducing the Zip-tie lamp](https://scienceinhydroponics.com/2017/11/cheap-diy-high-power-led-grow-lights-introducing-the-zip-tie-lamp.html)

Daniel Fernandez describes building an affordable high-power LED grow light using zip ties, aluminum heat sinks, and fans. The setup provides 40-50% of a 1000W HPS with around 60% less power consumption, making it safer and more cost-effective than traditional grow lights.

#### [2017-10-27 — Potassium concentration and yields in flowering plants](https://scienceinhydroponics.com/2017/10/potassium-concentration-and-yields-in-flowering-plants.html)

Daniel Fernandez discusses potassium's importance for flowering plants, noting that optimal concentrations vary based on media type and growing system. Studies show ideal potassium levels range from 200-300 ppm, with higher concentrations potentially harmful under certain conditions.

#### [2017-10-21 — Five reasons why a dedicated hydroponic testing room is a great idea](https://scienceinhydroponics.com/2017/10/five-reasons-why-a-dedicated-hydroponic-testing-room.html)

Daniel Fernandez argues for the importance of having a dedicated hydroponic testing room, emphasizing its ability to test product changes (e.g., new fertilizers), optimize current setups, try academic research modifications, and introduce new plant varieties. This ensures safety and gradual implementation of potential improvements without risking entire crop cycles.

#### [2017-10-03 — The use of phosphites in plant culture](https://scienceinhydroponics.com/2017/10/the-use-of-phosphite-in-plant-culture.html)

Daniel Fernandez discusses phosphite's role in plant culture, noting it is not an effective P fertilizer but can offer protective effects against pathogens. Research indicates that under sufficient Pi nutrition, phosphites provide biostimulating benefits without negative side effects.

#### [2017-09-26 — Five things you should know when mixing your own hydroponic liquid nutrients](https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html)

Daniel Fernandez discusses five key things hydroponic growers should know when mixing their own nutrients, including the importance of using a 1:100 concentration factor and avoiding overly concentrated solutions to prevent solubility issues. He also emphasizes the need for pure salts free from impurities and acidic deionized water to avoid problems with carbonates.

#### [2017-09-13 — Humic acids in hydroponics: What is their effect?](https://scienceinhydroponics.com/2017/09/humic-acids-in-hydroponics.html)

Humic acids, derived from the decomposition of plant and microorganism materials, enhance soil fertility by increasing iron availability. Studies on tomatoes show that different sources can stimulate root growth or both roots and shoots, with increased yields and mineral contents observed in some cases but not all. Humic acid applications are effective in foliar sprays and combinations with other biostimulants, though their impact on crop yield is variable depending on the specific humic acid source.

#### [2017-09-03 — How to prevent problems with powdery mildew in hydroponic crops](https://scienceinhydroponics.com/2017/09/how-to-prevent-problems-with-powdery-mildew-in-hydroponic-crops.html)

Daniel Fernandez discusses how to prevent powdery mildew in hydroponic crops by strengthening plants with silicon treatments, using beneficial microorganisms, or applying friendly chemical solutions like neem seed oil. He emphasizes the importance of maintaining optimal environmental conditions and temperature ranges to thwart fungal diseases.

#### [2017-08-26 — Five important things to consider when doing foliar spraying](https://scienceinhydroponics.com/2017/08/five-important-things-to-consider-when-doing-foliar-spraying.html)

Daniel Fernandez discusses five key considerations for successful foliar fertilization: not using root fertilizers on leaves, higher concentrations than roots, the importance of surfactants for even coverage, optimal timing to ensure stomata are open, and adding biostimulants for maximum yield. He emphasizes that foliar applications should be tailored specifically for leaf absorption rather than mimicking root treatments.

#### [2017-08-16 — Creating a robust pH/EC monitor for hydroponics using Atlas probes and an Arduino](https://scienceinhydroponics.com/2017/08/creating-a-robust-phec-monitor-for-hydroponics-using-atlas-probes-and-an-arduino.html)

Daniel Fernandez discusses building a robust pH/EC monitoring system for hydroponics using Atlas probes. He explains how the Atlas probes are more durable and have no cable connections to the Arduino, reducing noise and improving accuracy compared to Gravity probes. The project is significantly more expensive but offers longer service times due to its superior design.

#### [2017-08-06 — Comparing the conductivity of two different solutions](https://scienceinhydroponics.com/2017/08/comparing-the-conductivity-of-two-different-solutions.html)

Daniel Fernandez discusses a common misconception regarding conductivity as a measure of nutrient solution strength in hydroponics. He explains that while two solutions with the same conductivity can have different osmotic pressures due to varying ion compositions, leading to significant differences in actual concentration and plant response. He recommends using an osmometer for accurate comparison or matching element concentrations instead.

#### [2017-08-02 — Controlling aphids in a hydroponic crop. Part 1.](https://scienceinhydroponics.com/2017/08/controlling-aphids-in-a-hydroponic-crop-part-1.html)

Daniel Fernandez discusses various methods to control aphids, including neonicotinoids like imidacloprid which are effective but harmful to beneficial insects and the environment. He also recommends biocontrol options such as Lecanicillium fungi for controlling both aphids and powdery mildew, and less damaging alternatives like neem oil applications or using beneficial nematodes.

#### [2017-07-18 — Five ways to increase your seed germination rates](https://scienceinhydroponics.com/2017/07/five-ways-to-increase-your-seed-germination-rates.html)

To enhance seed germination, Daniel Fernandez suggests five strategies: maintaining optimal temperature (e.g., spinach requires 15-25°C), using PEG-6000 treatments tailored to the specific plant species, disinfecting seeds with chemicals like NaClO, introducing beneficial fungi such as Trichoderma harzianum, and applying gibberellic acid. These methods can significantly boost germination rates, which is crucial for successful seedling emergence.

#### [2017-07-13 — Making your own DIY plant rooting gel](https://scienceinhydroponics.com/2017/07/making-your-own-diy-plant-rooting-gel.html)

Daniel Fernandez describes how to create a DIY plant rooting gel using readily available ingredients at a fraction of the cost compared to commercial products. The process involves mixing distilled water with indole-3-butyric acid, potassium hydroxide, and Carbopol 940 in two containers, one heated to dissolve components, resulting in a final mixture that can be used for cloning plants without preservatives.

#### [2017-07-06 — Building your own DIY high power LED lamp: Part One](https://scienceinhydroponics.com/2017/07/building-your-own-diy-high-power-led-lamp-part-one.html)

Daniel Fernandez discusses how to build a high power LED lamp using 150W cobs with their own drivers, which can replace a 1000W HPS light for less than $100. He recommends using white diodes and proper safety precautions.

#### [2017-06-30 — What is the ideal nutrient solution temperature in hydroponics?](https://scienceinhydroponics.com/2017/06/what-is-the-ideal-nutrient-solution-temperature-in-hydroponics.html)

The ideal nutrient solution temperature varies by plant species; generally between 15-30°C (59-86°F). Higher temperatures increase metabolic rates but decrease oxygen solubility, leading to potential disease proliferation. Careful study of the specific plant species is necessary for optimal results, and sterile systems with enhanced filtration are recommended for higher temperature use.

#### [2017-06-22 — Are High Pressure Sodium (HPS) Lamps better than LEDs?](https://scienceinhydroponics.com/2017/06/are-high-pressure-sodium-hps-lamps-better-than-leds.html)

Daniel Fernandez compares High Pressure Sodium (HPS) and Light Emitting Diode (LED) lamps, highlighting HPS's fixed spectrum and higher photon flux. However, recent studies show mixed results with LED lamps outperforming in certain setups, especially when the spectral composition is optimized for plant growth efficiency. The study suggests that while LED lamps offer significant power savings, they require careful tuning to match the specific needs of different plants.

#### [2017-06-10 — Five dos and don’ts for automated pH control in hydroponics](https://scienceinhydroponics.com/2017/06/five-dos-and-donts-for-automated-ph-control-in-hydroponics.html)

Daniel Fernandez outlines five dos and don’ts for automated pH control in hydroponics, emphasizing the importance of frequent calibration (every week) to avoid inaccurate readings due to immersion in nutrient solutions. He also stresses the necessity of using electrodes designed for constant immersion and having addition limits in controllers to prevent over-correction that could harm crops.

#### [2017-06-07 — Using triacontanol to increase yields in hydroponics](https://scienceinhydroponics.com/2017/06/using-triacontanol-to-increase-yields-in-hydroponics.html)

Daniel Fernandez discusses triacontanol, a long fatty alcohol molecule used in hydroponics. It can significantly increase plant yields at very low concentrations (10-7 to 10-9 M or 0.01 to 1 ppm), far below the typical requirement for other additives. This makes it an economical and effective tool with minimal environmental impact, suitable for both foliar feeding and commercial use.

#### [2017-06-01 — Salicylic acid and its positive effect in hydroponics](https://scienceinhydroponics.com/2017/06/salicylic-acid-positive-effect-in-hydroponics.html)

Daniel Fernandez discusses the positive effects of salicylic acid in hydroponics, highlighting its ability to enhance dry mass and leaf area in crops like corn and soybean. He explains that it can also improve germination rates, oil content in basil, carbohydrate levels in maize, root development, and disease resistance, with applications ranging from foliar feeding at concentrations of 10^-5 to 10^-4 M.

#### [2017-05-22 — Using titanium to increase crop yields](https://scienceinhydroponics.com/2017/05/using-titanium-to-increase-crop-yields.html)

Daniel Fernandez discusses titanium's potential to increase crop yields, citing a literature review from 2017. He highlights its use in foliar applications and mentions that while some studies show up to 95.3% yield increases, others report less dramatic results often when combined with other additives like silicon (Si). The author emphasizes the importance of using soluble chelates rather than nanoparticles due to their negative effects on plant growth and DNA damage.

#### [2017-05-14 — Phosphorous toxicity and concentration in higher plants](https://scienceinhydroponics.com/2017/05/phosphorous-toxicity-concentration-higher-plants.html)

Daniel Fernandez discusses phosphorous toxicity and its rarity, attributing it to plants' mechanisms that down-regulate phosphorus uptake at high concentrations. He highlights how solubility issues with heavy metal dihydrogen phosphates can lead to deficiencies of other elements like zinc and copper, emphasizing the importance of chelation for preventing these problems.

#### [2017-05-03 — A simple Arduino based sensor monitoring platform for Hydroponics](https://scienceinhydroponics.com/2017/05/a-simple-arduino-based-sensor-monitoring-platform-for-hydroponics.html)

Daniel Fernandez describes building an Arduino-based sensor monitoring platform for hydroponics. The system monitors temperature, humidity, carbon dioxide concentration, pH, and electrical conductivity without requiring soldering or complex breadboard setups. Key components include the Arduino UNO R3, LCD screen shield, DHT22 temperature and humidity sensor, Gravity pH and EC sensors, and Gravity CO2 sensor. Calibration is necessary for accurate readings of pH and EC values. This setup allows users to track essential hydroponic variables effectively.

#### [2017-04-17 — What is the effect of amino acids in hydroponics?](https://scienceinhydroponics.com/2017/04/what-is-the-effect-of-amino-acids-in-hydroponics.html)

The post discusses the use of amino acids in hydroponics, highlighting their ability to reduce nitrate assimilation and help plants under stress conditions. It also mentions evidence showing benefits for Fe and Cu absorption, but cautions that there is no strong evidence for wide range beneficial effects under normal growing conditions.

#### [2017-04-11 — Calibrating your digital humidity sensors](https://scienceinhydroponics.com/2017/04/calibrating-your-digital-humidity-sensors.html)

Daniel Fernandez discusses calibrating digital humidity sensors for hydroponic cultivation, emphasizing their importance in accurately measuring relative humidity. He explains that these sensors need to be calibrated due to potential damage from dew point conditions and provides methods including using saturated salt solutions or pastes, with a recommended initial calibration at 75% relative humidity.

#### [2017-04-10 — Probes for constant immersion in hydroponic nutrient solutions](https://scienceinhydroponics.com/2017/04/probes-for-constant-immersion-in-hydroponic-nutrient-solutions.html)

The post discusses solutions for constant monitoring of hydroponic nutrient solutions without frequent probe calibration. It highlights that low-quality EC/pH pens are not suitable due to their inability to withstand constant immersion in nutrient solutions, leading to inaccurate readings and potential damage. The author recommends using submersible electrode assemblies or industrial probes with BNC connectors, which provide robustness and compatibility with various pH controllers. For conductivity measurements, electrode-less probes are suggested as they avoid polarization issues and offer more accurate readings across different solution types.

#### [2017-04-09 — Five things that will damage your pH probes](https://scienceinhydroponics.com/2017/04/five-things-that-will-damage-ph-probes.html)

Daniel Fernandez discusses five things that can damage pH probes, including letting them dry or keeping them in water, measuring very basic solutions, using chemicals that react with glass, and not cleaning the probe. Proper care such as storing adequately and cleaning ensures accurate readings for a long time.

#### [2017-04-08 — Vapor pressure deficit (VPD) in hydroponics](https://scienceinhydroponics.com/2017/04/vapor-pressure-deficit-vpd-in-hydroponics.html)

Daniel Fernandez discusses vapor pressure deficit (VPD) in hydroponics, explaining that it measures how much water vapor is needed for air saturation and its importance for plant hydration. He highlights VPD's relationship with temperature and humidity, noting that a low VPD can lead to stress due to inability of plants to transport water effectively, while high VPD causes excessive transpiration leading to wilting if root mass or water availability are insufficient.

#### [2017-04-07 — Maximizing yields per area in hydroponics](https://scienceinhydroponics.com/2017/04/maximizing-yields-per-area-in-hydroponics.html)

Daniel Fernandez discusses maximizing hydroponic crop yields by either increasing the number of plants per area or improving yield per plant. He outlines strategies such as ensuring optimal nutrient solution contact and composition, using efficient irrigation systems, and managing light distribution and ventilation to achieve these goals. However, he notes that this often requires more energy expenditure and specialized equipment, which can be vulnerable to power outages and grower errors.

#### [2017-04-06 — A few basics of leaf tissue analysis in hydroponic crops](https://scienceinhydroponics.com/2017/04/a-few-basics-of-leaf-tissue-analysis-in-hydroponic-crops.html)

Daniel Fernandez discusses the importance of leaf tissue analysis for monitoring nutrient composition in hydroponic crops. He explains that while traditional models suggest increasing nutrients within solution to correct deficiencies, he finds more often than not environmental factors like temperature and pH are the root cause of nutrient absorption issues, complicating interpretation of results.

#### [2017-04-05 — Managing a Run To Waste (RTW) hydroponic crop from a nutritional perspective](https://scienceinhydroponics.com/2017/04/managing-a-run-to-waste-rtw-hydroponic-crop-from-a-nutritional-perspective.html)

The post discusses managing RTW hydroponic crops by ensuring adequate substrate water retention, monitoring run-off to control salt accumulation and maintain proper nutrient levels, and adjusting pH as needed. Key is effective run-off management to prevent high conductivity and ensure plants receive sufficient nutrition.

#### [2017-04-04 — Using coco coir in hydroponics](https://scienceinhydroponics.com/2017/04/using-coco-coir-in-hydroponics.html)

Daniel Fernandez discusses using coco coir in hydroponics. He highlights its excellent root propagation and aeration properties but also points out issues like variability in chemical makeup, pH, and EC values. Proper treatment with calcium nitrate and EDTA solutions can help neutralize nutrients for better plant growth.

#### [2017-04-03 — Measuring ion concentrations in hydroponics using electronic tongues](https://scienceinhydroponics.com/2017/04/measuring-ions-in-hydroponics-using-electronic-tongues.html)

Daniel Fernandez discusses the challenges in measuring individual ion levels in hydroponic solutions, highlighting issues with Ion Selective Electrodes (ISEs) due to interference from other ions. He introduces electronic tongues as a potential solution using multiple ISEs and statistical modeling tools to accurately measure ion concentrations in real-time, which could revolutionize nutrient absorption monitoring in hydroponics.

#### [2017-04-02 — Using Peat Moss in Hydroponic Culture](https://scienceinhydroponics.com/2017/04/using-peat-moss-in-hydroponic-culture.html)

Daniel Fernandez discusses using peat moss in hydroponic culture, highlighting its organic nature and low pH which requires treatment to make suitable for plants. He explains how to assess the decomposition level of peat using a von Post scale and provides methods to adjust pH and cation exchange capacity, emphasizing the importance of proper preparation to avoid nutrient imbalances.

#### [2017-04-01 — Automated media moisture monitoring in hydroponic crops](https://scienceinhydroponics.com/2017/04/automated-media-moisture-monitoring.html)

Daniel Fernandez discusses automated media moisture monitoring in hydroponic crops using capacitive sensors for accurate irrigation control. He highlights the importance of proper moisture levels for plant health, suggesting that monitoring around 10-20% of the crop is sufficient to guide watering decisions effectively and prevent overwatering or underwatering.

#### [2017-03-31 — Hydrobuddy v1.60: A new update with important changes](https://scienceinhydroponics.com/2017/03/hydrobuddy-v1-60-a-new-update-with-important-changes.html)

Daniel Fernandez updated Hydrobuddy v1.60 by simplifying its structure, removing unnecessary libraries, and eliminating installer files for easier compilation and portability on Windows/Linux systems. He also introduced a feature allowing multiple substance additions/deletions at once and added a 'Zero all targets' button.

#### [2017-03-30 — Do you really need to be using RO water?](https://scienceinhydroponics.com/2017/03/do-you-really-need-ro-water.html)

Daniel Fernandez discusses whether reverse osmosis (RO) water is necessary for hydroponics, highlighting its energy-intensive nature and potential to remove essential minerals. He explains that RO water can lead to suboptimal results if the initial water contains significant amounts of certain ions like calcium or magnesium, but it ensures a clean base for nutrient solutions. The author also addresses practical implications such as analyzing tap water hardness and adjusting pH levels based on temperature and mineral content.

#### [2017-03-29 — Hydroponic micro and macro nutrient sufficiency ranges](https://scienceinhydroponics.com/2017/03/hydroponic-micro-and-macro-nutrient-sufficiency-ranges.html)

The post discusses different sufficiency ranges of hydroponic nutrients, highlighting variations based on plant species, nutrient form, and cultivation media. It emphasizes that while macro-nutrient sufficiency ranges are more consistent across studies, micro-nutrients have greater variability due to differences in media contributions and specific absorption rates.

#### [2017-03-28 — What is the effect of chloride in hydroponics?](https://scienceinhydroponics.com/2017/03/what-is-the-effect-of-chloride-in-hydroponics.html)

Chloride, a micro-nutrient ion in hydroponics, behaves similarly to ammonium and can strongly compete with other anions like nitrate and phosphate. This leads to reduced absorption of these essential nutrients, causing symptoms of deficiency even when they are present in solution. The effect is more pronounced than sodium ions due to chloride's lower concentration threshold for causing issues.

#### [2017-03-27 — Some things you should know about sodium in hydroponics](https://scienceinhydroponics.com/2017/03/some-things-you-should-know-about-sodium-in-hydroponics.html)

Daniel Fernandez discusses the role and potential issues of sodium in hydroponic systems. Sodium, while not essential for most plants, can cause significant problems when present at high concentrations, affecting plant growth and yield. He outlines thresholds and practical solutions to mitigate these effects, emphasizing the importance of monitoring sodium levels especially in recirculating systems.

#### [2017-03-26 — Using UV sterilization in your recirculating hydroponic crop](https://scienceinhydroponics.com/2017/03/using-uv-sterilization-in-your-recirculating-hydroponic-crop.html)

Daniel Fernandez discusses UV sterilization for maintaining sterility in recirculating hydroponic setups, highlighting its effectiveness in reducing bacterial and fungal populations. However, he notes that it can affect beneficial root bacteria and advises using chelates like Fe-EDDHA to mitigate iron stability issues.

#### [2017-03-25 — What is an ORP meter and why is it useful in hydroponics?](https://scienceinhydroponics.com/2017/03/what-is-an-orp-meter-and-why-is-it-useful-in-hydroponics.html)

Daniel Fernandez explains that an ORP meter measures the oxidation-reduction potential of a solution, which is crucial for understanding its chemical environment. This tool helps hydroponic growers maintain conditions safe from harmful microorganisms while also monitoring oxygenation and biological activity within their nutrient solutions.

#### [2017-03-24 — How to prepare your own solutions for EC meter calibration](https://scienceinhydroponics.com/2017/03/how-to-prepare-your-own-solutions-for-ec-meter-calibration.html)

Daniel Fernandez explains how to prepare homemade EC meter calibration solutions, emphasizing the importance of using NaCl and ensuring they remain stable. He recommends starting with a 1g/liter solution that measures between 1.5-2.5 mS/cm for general use in hydroponics, while also suggesting an alternative 0.5g/liter solution for two-point calibration.

#### [2017-03-22 — Preparing your own buffer solutions for pH calibration](https://scienceinhydroponics.com/2017/03/preparing-your-own-buffer-solutions-for-ph-calibration.html)

Daniel Fernandez explains how to make buffer solutions for pH calibration in hydroponics without expensive commercial products, detailing a method using mono potassium phosphate and citric acid with KOH adjustments. The key is adding substances close to the desired pH values (phosphate for 7, citric acid for 4) and adjusting with KOH to achieve precise pH levels suitable for accurate meter calibration.

#### [2017-03-21 — Automating a hydroponic system: Sensors and monitoring](https://scienceinhydroponics.com/2017/03/automating-a-hydroponic-system-sensors-and-monitoring.html)

Daniel Fernandez discusses automating sensors in his hydroponic system, emphasizing the benefits of storing sensor readings for analysis and diagnosis. He recommends purchasing pH, EC, ambient temperature, solution temperature, humidity, carbon dioxide, and dissolved oxygen sensors to monitor as many variables as possible within budget constraints.

#### [2017-03-20 — Is ortho-silicic acid worth the additional expense in hydroponics?](https://scienceinhydroponics.com/2017/03/is-ortho-silicic-acid-worth-the-additional-expense-in-hydroponics.html)

The author discusses whether ortho-silicic acid (OSA) is worth the additional expense in hydroponics, highlighting that silicon supplementation offers benefits such as increased photosynthesis and resistance to stress. However, OSA lacks scientific evidence showing it provides greater benefits than traditional potassium silicate, which has been proven effective at a lower cost.

#### [2017-03-18 — Nitrate, Ammonium and pH in hydroponics](https://scienceinhydroponics.com/2017/03/nitrate-ammonium-and-ph-in-hydroponics.html)

Plants balance ion uptake by exchanging charged species with the root zone: nitrate-dominant anion uptake tends to raise pH, whereas readily absorbed ammonium tends to lower it. Adjusting the ammonium:nitrate ratio can alter drift, but a ratio that makes pH stable may reduce yield; crop-specific performance takes priority over a universal ratio.

### 2016

#### [2016-03-30 — HydroBuddy v1.100 : The First Free Open Source Hydroponic Nutrient Calculator Program Available Online](https://scienceinhydroponics.com/2016/03/the-first-free-hydroponic-nutrient-calculator-program-o.html)

Daniel Fernandez released HydroBuddy v1.100, a free open-source hydroponic nutrient calculator software built on Lazarus programming suite and AlgLib algorithms. It calculates salt weights for specific concentrations of elements, features include library with fertilizer salts, leaf tissue database, and empirical EC prediction model. The program is available for Linux, MacOS, and Windows under GPL license.

### 2011

#### [2011-01-13 — Almost There Guys ! The New HydroBuddy v1.0 is Just Around the Corner :o)](https://scienceinhydroponics.com/2011/01/almost-there-guys-the-new-hydrobuddy-v1-0-is-just-around-the-corner-o.html)

Daniel Fernandez announces the imminent release of HydroBuddy v1.0, a significantly improved version coded from scratch in Lazarus for Linux and Mac, offering enhanced database management, flexible salt composition changes, and a powerful linear equation solver to optimize nutrient formulations.

### 2010

#### [2010-12-04 — Walking Towards v.1.0 : Why Development of HydroBuddy is Taking Its Time](https://scienceinhydroponics.com/2010/12/walking-towards-v-1-0-why-development-of-hydrobuddy-is-taking-its-time.html)

Daniel Fernandez discusses improvements planned for HydroBuddy, a free hydroponic nutrient calculator. He plans to switch from Delphi 2010 to Lazarus for cross-platform compatibility and implement a proper database engine to enhance accuracy and expand functionality.

#### [2010-10-01 — Instrument Precision : Its Importance in the Preparation of Hydroponic Nutrient Solutions](https://scienceinhydroponics.com/2010/10/instrument-precision-its-importance-in-hydroponic-solution-preparation.html)

Preparation accuracy is limited by scale resolution and final-volume uncertainty, not the calculator's decimal places. A 0.01 g scale creates a large relative error near a 0.05 g dose; larger stocks increase weighable masses but introduce their own volumetric error, so uncertainty should be evaluated against each dose and vessel.

#### [2010-09-27 — Understanding Reagent Purity and Its Importance in Hydroponics](https://scienceinhydroponics.com/2010/09/understanding-reagent-purity-and-its-importance-in-hydroponics.html)

Reagent purity is the fraction of material matching the stated compound, whereas nutrient percentage is the element's share of that pure compound or product; the two must not be conflated. Assay below 100% changes the required weighed mass, while unidentified impurities may be soluble, insoluble, benign, or nutritionally important.

#### [2010-09-24 — HydroBuddy’s Online Hydroponic Formulation Database](https://scienceinhydroponics.com/2010/09/hydrobuddys-online-hydroponic-formulation-database.html)

Daniel Fernandez created an online hydroponic nutrient database in HydroBuddy, allowing users to save and easily access various nutrient solutions. Users can contribute by sending detailed formulations via email, which will be added to the database for others to download.

#### [2010-09-23 — Hydroponic Nutrient Availability : What “Pushing Out an Element” Really Means](https://scienceinhydroponics.com/2010/09/hydroponic-nutrient-availability-what-pushing-out-an-element-really-means.html)

Daniel Fernandez explains how plants absorb elements dissolved in hydroponic solutions, emphasizing the importance of ionic forms for absorption. He discusses factors like environmental conditions and nutrient interactions that determine availability, with a focus on iron-phosphate interactions causing apparent deficiencies. The key to healthy plant growth is maintaining adequate ion concentrations and preventing precipitation, which can render nutrients unavailable.

#### [2010-09-22 — Preserving Fertilizers and Additives – How to Keep them from Going Bad](https://scienceinhydroponics.com/2010/09/preserving-fertilizers-and-additives-how-to-prevent-things-from-going-bad.html)

Daniel Fernandez discusses how chelating agents, sugars, and organic buffers can attract fungi and bacteria, leading to solution contamination. He recommends adding sodium benzoate as a preservative at 100-300 mg/L to prevent microbial growth in hydroponic solutions without causing phytotoxic effects.

#### [2010-09-21 — A Step Forward : Moving from AllHydroponics to ScienceinHydroponics.com](https://scienceinhydroponics.com/2010/09/a-step-forward-moving-from-allhydroponics-to-scienceinhydroponics-com.html)

Daniel Fernandez moves his hydroponics blog from Blogger to ScienceinHydroponics.com, aiming to enhance customization and professionalism. The new platform will allow for more extensive content creation and sharing features.

#### [2010-09-11 — Making Isotonic Solutions For Draining : Preparing Your Own – and better – Clearex](https://scienceinhydroponics.com/2010/09/making-isotonic-solutions-for-draining-preparing-your-own-and-better-clearex.html)

Daniel Fernandez explains how isotonic solutions like Clearex can effectively remove nutrients from hydroponic media without stressing plant roots, avoiding issues with hypo-tonic water. He suggests using a combination of salts and sugars to achieve similar osmotic pressure as Clearex, noting that this approach may be more effective for certain crops.

#### [2010-09-09 — Imitating Commercial Nutrients : A Tutorial Using HydroBuddy (my free Hydroponic Nutrient Calculator)](https://scienceinhydroponics.com/2010/09/imitating-commercial-nutrients-a-tutorial-using-hydrobuddy-my-free-hydroponic-nutrient-calculator.html)

Daniel Fernandez updates his HydroBuddy calculator, introducing a new feature allowing users to input the percentage composition and addition method of commercial fertilizers. This enables them to easily calculate and mimic these formulations by specifying volume or weight per unit volume, facilitating precise nutrient solutions for hydroponic systems.

#### [2010-09-01 — Bulding a World Without Hunger : The Massive and Passive Hydroponic System Project](https://scienceinhydroponics.com/2010/09/bulding-a-world-without-hunger-the-massive-and-passive-hydroponic-system-project.html)

Daniel Fernandez's project aims to study non-recirculating, totally passive hydroponic systems through an internet-based initiative. The goal is to gather data on their robustness and feasibility across various conditions worldwide, with the aim of making them a viable alternative for agricultural setups.

#### [2010-08-25 — Completely Passive, Non-Recirculating Hydroponic Systems : Some Tips for Large Plants](https://scienceinhydroponics.com/2010/08/completely-passive-non-recirculating-hydroponic-systems-some-tips-for-large-plants.html)

Daniel Fernandez discusses tips for using completely passive, non-recirculating hydroponic systems for large plants like tomatoes and cucumbers. He emphasizes the importance of a media filled container where nutrient solution is close to the surface, using highly absorbent capillary efficient media in small cups and gravel or other coarse media for the rest, ensuring proper air space around roots to prevent drowning.

#### [2010-08-24 — Completely Passive, Non-Recirculating Hydroponic Systems : Yes, Its Possible](https://scienceinhydroponics.com/2010/08/completely-passive-non-recirculating-hydroponic-systems-yes-its-possible.html)

Daniel Fernandez discusses how completely passive, non-recirculating hydroponic systems can grow plants without electricity. He explains that adequate space for roots, nutrient solution availability, and oxygen supply are key conditions for success, allowing the system to work effectively for all types of crops including large ones like tomatoes.

#### [2010-08-23 — Improving Seed Germination : The Science of Seed Priming](https://scienceinhydroponics.com/2010/08/improving-seed-germination-the-science-of-seed-priming.html)

Daniel Fernandez discusses seed priming, a technique used to increase seed germination speed without affecting its percentage. He explains that priming involves soaking seeds in various solutions like water, salt, or polyethylene glycol (PEG), which helps overcome inhibitory mechanisms and speeds up the germination process for difficult-to-germinate seeds such as parsley and coriander.

#### [2010-08-20 — My Hydroponics Calculator : Features and Objectives](https://scienceinhydroponics.com/2010/08/my-hydroponics-calculator-features-and-objectives.html)

Daniel Fernandez's hydroponics calculator simplifies the preparation of nutrient solutions by converting desired formulations into precise salt weights, addressing common confusion about ppm values. It offers features like calculating concentrated stock solutions and using a “straight addition” method for direct reservoir adjustments, aiding in maintaining optimal solution concentrations.

#### [2010-08-19 — My Hydroponic Calculator Tutorial : Saving and Loading Formulations and Recipes](https://scienceinhydroponics.com/2010/08/my-hydroponic-calculator-tutorial-saving-and-loading-formulations-and-recipes.html)

Daniel Fernandez's hydroponic calculator tutorial introduces features for saving and loading formulations and recipes. Formulations specify nutrient concentrations, while recipes detail exact salt weights needed for specific volumes. Users can save these using buttons or by sharing files, facilitating easy modification and sharing of nutrient preparation details.

#### [2010-08-18 — Cobalt in Hydroponics : Better or Worse ?](https://scienceinhydroponics.com/2010/08/cobalt-in-hydroponics-better-or-worse.html)

Daniel Fernandez discusses cobalt's role as a transition metal, noting its importance for vitamin B12 synthesis in plants. He highlights studies showing detrimental effects at 5 ppm concentration, questioning the necessity and safety of adding cobalt to hydroponic solutions.

#### [2010-08-17 — Silicon in Hydroponics : What Silicon is Good For and How it Should be Used](https://scienceinhydroponics.com/2010/08/silicon-in-hydroponics-what-silicon-is-good-for-and-how-it-should-be-used.html)

Daniel Fernandez discusses silicon's role in hydroponics, highlighting its abundance and insolubility at room temperature. He explains that sodium silicate (Na2SiO3) is used as a soluble form for plants to absorb silicon, which enhances plant growth and disease resistance when applied at around 100ppm concentration.

#### [2010-08-15 — The NPK Mystery – What Do These Numbers Mean and How are they Calculated ?](https://scienceinhydroponics.com/2010/08/the-npk-mistery-what-do-these-numbers-mean-and-how-are-they-calculated.html)

The post explains that NPK notation represents the percentage composition by weight of nitrogen (N), potassium (K as K2O5), and phosphorus (P as P2O5) in a fertilizer. It clarifies that these values are calculated based on the total weight of the solution, not just the ppm concentration ratios. The practical implication is understanding how much of each nutrient is contained within the solution for accurate fertilizer strength comparisons.

#### [2010-08-13 — Truly Cleaning Your Hydroponic System : The Fenton Process and Chemistry](https://scienceinhydroponics.com/2010/08/truly-cleaning-your-hydroponic-system-the-fenton-process-and-chemistry.html)

Daniel Fernandez discusses the limitations of traditional cleaning methods for hydroponic systems, highlighting how hypochloride or hydrogen peroxide washes can leave harmful substances intact. He introduces the Fenton process as a solution, explaining that it uses iron ions and hydrogen peroxide to oxidize organic molecules into harmless chemicals, effectively removing contaminants from the system.

#### [2010-08-12 — Iron Sources in Hydroponics : Which One is the Best ?](https://scienceinhydroponics.com/2010/08/iron-sources-in-hydroponics-which-one-is-the-best.html)

The main issue with iron in hydroponics is its tendency to form insoluble salts with other ions present. To solve this, chelating agents like EDDHA, EDTA, and DTPA are used; however, DTPA provides the best balance of stability and durability for use in nutrient solutions.

#### [2010-08-11 — Chemical Buffers in Hydroponics : What is the Best, Cheapest Buffer](https://scienceinhydroponics.com/2010/08/chemical-buffers-in-hydroponics-what-is-the-best-cheapest-buffer.html)

Daniel Fernandez discusses chemical buffers in hydroponics, highlighting their effectiveness and limitations. He explains how chemical buffers distribute themselves as different ionic species to react with acids or bases at specific pH levels, maintaining stable nutrient solution pH for weeks. However, he notes that while simple organic and inorganic substances are suitable, they have practical limits due to concentration constraints and potential phytotoxicity issues.

#### [2010-07-06 — Preparing Your Own Hydroponic Nutrients : A Complete Guide for Beginners](https://scienceinhydroponics.com/2010/07/preparing-your-own-hydroponic-nutrients-a-complete-guide-for-beginners.html)

Daniel Fernandez outlines how to prepare homemade nutrient solutions for hydroponics. He recommends using his calculator and provides essential materials like scales, containers, and chemicals such as calcium nitrate, magnesium sulfate, potassium nitrate, copper sulfate, and others. The summary emphasizes the significant cost savings over commercial products when making your own nutrients.

#### [2010-06-24 — Preparing A, B and C (three part) Concentrated Nutrient Solutions, a Tutorial for my Hydroponic Nutrient Calculator](https://scienceinhydroponics.com/2010/06/preparing-a-b-and-c-three-part-concentrated-nutrient-solutions-a-tutorial-for-my-hydroponic-nutrient-calculator.html)

Daniel Fernandez explains how to prepare three-part nutrient formulations for hydroponics. He outlines that plants require different ratios of nutrients at various stages, leading to the creation of A and B concentrated solutions with a constant C solution. This allows for varied nutrient ratios throughout the plant's growth cycle from vegetative to flowering.

#### [2010-06-22 — Preparing A and B Solutions Using My Hydroponics Nutrient Calculator](https://scienceinhydroponics.com/2010/06/preparing-a-and-b-solutions-using-my-hydroponics-nutrient-calculator.html)

The author describes how to prepare A and B solutions using a hydroponics nutrient calculator, focusing on avoiding incompatible ion pairs. They detail an alternative method for preparing concentrated A and B solutions at a 1:100 ratio, suitable for large reservoirs or commercial growers who can add all nutrients directly when levels exceed 4 cubic meters. The approach restricts the use of certain salts like calcium monobasic phosphate and iron sulfate but provides flexibility in choosing cheaper alternatives like iron EDTA and potassium salts.

#### [2010-06-21 — Using my Nutrient Calculator with Commercial Fertilizers : Part No.2](https://scienceinhydroponics.com/2010/06/using-my-nutrient-calculator-with_21.html)

In this tutorial, Daniel Fernandez uses his hydroponic nutrient calculator to correct deficiencies in commercial fertilizers for tomato growth, specifically addressing missing elements like Zn, B, and Cu. He calculates the required additional salts (Zinc Sulfate, Boric Acid, Copper Sulfate) and adjusts the formulation manually by tweaking N and S levels with Calcium Nitrate and Calcium Sulfate to achieve balanced nutrient ratios.

#### [2010-06-19 — Using my Nutrient Calculator with Commercial Fertilizers : Part No.1](https://scienceinhydroponics.com/2010/06/using-my-nutrient-calculator-with-commercial-fertilizers-part-no-1.html)

Daniel Fernandez explains how to use his nutrient calculator with commercial fertilizers, specifically showing how to add FloraBloom fertilizer from General Hydroponics. He calculates the ppm values for different nutrients added at 1 tablespoon per gallon and demonstrates how to adapt these formulations using other salts to achieve a balanced hydroponic solution.

#### [2010-06-13 — Possible New Features for my Hydroponics Calculator](https://scienceinhydroponics.com/2010/06/possible-new-features-for-my-hydroponics-calculator.html)

Daniel Fernandez updates his hydroponics calculator software, adding features like custom salts and water quality adjustments. He aims to make it a comprehensive tool for nutrient design and solution optimization, potentially renaming it 'hydroponic buddy' upon release.

#### [2010-06-07 — Building Your Own High-Power LED Grow Lights for Hydroponics](https://scienceinhydroponics.com/2010/06/building-your-own-high-power-led-grow-lights-for-hydroponics.html)

Daniel Fernandez discusses building high-power LED grow lights for hydroponics. He recommends using 5-3W high power LEDs per plant and one blue LED every ten red ones, based on empirical measurements rather than lumens. He provides detailed instructions on purchasing LEDs, mounting them safely with fans, and creating a custom power supply and voltage regulator to efficiently light plants.

#### [2010-06-06 — A Simple Home-Made PVC Hydroponic Growing System](https://scienceinhydroponics.com/2010/06/simple-home-made-pvc-hydroponics.html)

Daniel Fernandez describes a DIY continuous Ebb and Flow hydroponics setup using PVC pipes, gravel as media, and pumps for nutrient solution circulation. The system successfully grows basil plants efficiently, requiring minimal materials and providing consistent feeding to all parts of the growing tube.

#### [2010-06-04 — Understanding pH in Hydroponics – Part No.2](https://scienceinhydroponics.com/2010/06/understanding-ph-in-hydroponics-part-no-2.html)

Daniel Fernandez discusses the ideal range of 5.5 to 7 pH for plant growth, explaining that below this range certain nutrients become less available while above it they can be too readily absorbed causing stress. He emphasizes that plants adapt locally and advises against obsessing with precise pH levels, suggesting instead a balanced nutrient solution and adequate quantities per plant.

#### [2010-06-03 — Understanding pH in Hydroponics – Part No.1](https://scienceinhydroponics.com/2010/06/understanding-ph-in-hydroponics-part-no-1.html)

Understanding pH in hydroponics is crucial for maintaining neutral conditions as it determines how plants absorb nutrients. The concentration of H3O(+) ions inversely affects pH, with more OH(-) ions increasing pH and causing acidity; pH 7 indicates a neutral solution. Plants alter pH by absorbing or releasing ions like K(+), NO3(-), NH4(+). A balanced nutrient solution helps control pH variations influenced by nitrogen sources such as ammonia.

#### [2010-06-02 — Growing a Hydroponic Garden Without a pH or EC meter](https://scienceinhydroponics.com/2010/06/growing-a-hydroponic-garden-without-a-ph-or-ec-meter.html)

Daniel Fernandez discusses growing hydroponic crops successfully without using a pH or EC meter, sharing practical guidelines such as maintaining one gallon of nutrient solution per plant and adding fresh water to keep the EC level stable. He emphasizes that while monitoring these variables can lead to better results, it is possible to grow beautiful hydroponics without constant pH/EC checks.

#### [2010-05-26 — Is OceanGrown Fertilizer a Scam ? A Scientist’s Point of View](https://scienceinhydroponics.com/2010/05/is-oceangrown-fertilizer-scam.html)

OceanGrown fertilizer is marketed as a concentrated sea water solution for soil and hydroponics, claiming to replenish 90 elements essential for plant growth. However, it lacks reliable scientific evidence supporting its efficacy, with potential risks from excessive sodium enrichment in soil. A scientist's review finds the claims unsubstantiated and advises using established micro-nutrient blends instead.

#### [2010-05-24 — Fruit Quality and High EC values in Tomatoes](https://scienceinhydroponics.com/2010/05/fruit-quality-and-high-ec-values-in-tomatoes.html)

A 2006 study in the Journal of Agricultural and Food Chemistry found that tomatoes raised at an electrical conductivity (EC) value of 4.5 dS/m had improved nutritional quality, including higher concentrations of important nutrients like lycopene, vitamin C, carotenoids, and phenolics. This EC level also increased antioxidant capacity and total dissolved solids, contributing to better flavor. Despite lower yields, the overall fruit quality was enhanced, making tomatoes more competitive in markets.

#### [2010-05-23 — The Best Outdoor Hydroponic System. A Simple Way to Grow Large Amounts of Food](https://scienceinhydroponics.com/2010/05/the-best-outdoor-hydroponic-system-a-simple-way-to-grow-large-amounts-of-food.html)

Daniel Fernandez describes a simple continuous flow system for outdoor hydroponics using ground channels. This system uses minimal materials like PVC pipes and media, allowing plants to grow in various sizes with adequate drainage and nutrient supply without the need for complex engineering or protective enclosures.

#### [2010-05-21 — Crazy pH Swings – How Media and Bacteria Affect pH in Hydroponics](https://scienceinhydroponics.com/2010/05/crazy-ph-swings-how-media-and-bacteria-affect-ph-in-hydroponics.html)

Crazy pH Swings in Hydroponics: Media's Basic Sites Buffer pH, Caused by Acetic Acid Treatment. Wild swings towards acidic values are often due to bacterial activity or root disease; plant feeding can also cause these swings, requiring larger reservoirs and proper recirculation.

#### [2010-05-20 — Preparing your Own Chelates – Improving Your Hydroponic Nutrients](https://scienceinhydroponics.com/2010/05/preparing-your-own-chelates-improving-your-hydroponic-nutrients.html)

Daniel Fernandez explains how adding chelating agents like Ethylendiaminetetraacetic Acid (EDTA) as a salt can improve the solubility of metals such as iron in hydroponic solutions. He details that by ensuring enough EDTA is added, it effectively wraps around and stabilizes Fe ions, preventing precipitation and allowing for steady release of micro-nutrients to plants without risking other metal ions competing for binding sites.

#### [2010-05-20 — Urea in Hydroponics – Positive or Negative ?](https://scienceinhydroponics.com/2010/05/urea-in-hydroponics-positive-or-negative.html)

Daniel Fernandez discusses whether urea should be used in hydroponics. Research indicates that urea does not significantly improve crop yields, but small additions of ammonium salts can benefit plants without the need for urea supplementation.

#### [2010-05-20 — Hydroponic Tomato Formulations – Nutrients for Every Growth Stage](https://scienceinhydroponics.com/2010/05/hydroponic-tomato-formulations-nutrients-for-every-growth-stage.html)

Daniel Fernandez discusses designing specific feeding schedules for hydroponic tomatoes across different growth stages. He highlights how varying nutrient levels and ratios can optimize plant development and yield, referencing a study by the University of Florida that provides ppm values for various stages.

#### [2010-05-20 — How to Have a Constant pH in Hydroponics – No More Corrections!](https://scienceinhydroponics.com/2010/05/how-to-have-a-constant-ph-in-hydroponics-no-more-corrections-o.html)

Daniel Fernandez discusses using weakly acidic ion-exchange resins to maintain a constant pH in recirculating hydroponics systems. These resins, which are insoluble and require frequent solution contact, can stabilize pH levels without needing chemical buffers or manual adjustments. They offer high pH stability over time, especially when plants push the pH up through nutrient uptake.

#### [2010-05-20 — The Importance of Oxygen in Hydroponic Systems](https://scienceinhydroponics.com/2010/05/the-importance-of-oxygen-in-hydroponic-systems.html)

Daniel Fernandez highlights the critical role of oxygen in hydroponics, explaining how it is essential for ATP production within plant cells. He emphasizes that adequate oxygen supply is crucial for large plants, advocating for systems like ebb & flow and drip irrigation where roots are periodically exposed to air and water.

#### [2010-05-20 — Making Your Own Hydroponic Solutions – Download my Free Ebook](https://scienceinhydroponics.com/2010/05/making-your-own-hydroponic-solutions-download-my-free-ebook.html)

Daniel Fernandez's ebook provides detailed instructions on how to prepare hydroponic solutions using a spreadsheet, simplifying complex technical aspects for non-experts. It includes formulations for various growth stages and allows users to control the exact amount of nutrients in their solution, offering cost-effective and flexible management.

#### [2010-05-20 — Hydroponic Nutrients… Why Solid is Better than Liquid](https://scienceinhydroponics.com/2010/05/hydroponic-nutrients-why-solid-is-better-than-liquid.html)

Daniel Fernandez argues that solid hydroponic nutrients, rather than liquid ones, offer a more economical choice. He explains that while liquid fertilizers require water and additional salts for preparation, leading to higher costs, solid fertilizers can be directly dissolved in water without the need for concentration, allowing for greater variety of salts at lower prices.

#### [2010-05-20 — Hydroponic Solutions and Vitamins… NO real proof](https://scienceinhydroponics.com/2010/05/hydroponic-solutions-and-vitamins-no-real-proof.html)

Daniel Fernandez finds no scientific evidence supporting the addition of vitamins and other nutrients in hydroponic solutions, noting that plants do not need them as they produce their own. He concludes that adding these substances may merely inflate prices without providing any documented benefits.

#### [2010-05-19 — Choosing a LED Grow Light for your Hydroponic Crop](https://scienceinhydroponics.com/2010/05/choosing-a-led-grow-light-for-your-hydroponic-crop.html)

Daniel Fernandez discusses choosing the right LED grow lights for hydroponics. He explains how traditional full spectrum lamps are inefficient, wasting most of their energy as heat, while LEDs can be highly efficient and targeted in providing only what plants need, such as a 60W LED lamp being sufficient for growing tomatoes. However, he warns against cheap or ineffective LED panels that do not meet the needs of hydroponic crops.

### 2009

#### [2009-02-26 — Static Hydroponic Systems, Cons and Pros](https://scienceinhydroponics.com/2009/02/static-hydroponic-systems-cons-and-pros.html)

Static hydroponic systems are divided into open and closed categories. Open systems waste nutrient solution continuously, while closed systems recycle it but require monitoring to maintain ideal conditions. The main advantage of open systems is cost savings due to lack of pump usage, whereas closed systems offer better efficiency and do not contaminate the environment. Closed systems need additional equipment like air pumps for oxygenation and continuous monitoring, which can be costly and complex compared to simpler open systems.

#### [2009-02-20 — Easy Seed Germination with Polyurethane Foam](https://scienceinhydroponics.com/2009/02/easy-seed-germination-with-polyurethane-foam.html)

Daniel Fernandez describes a method to germinate seeds using polyurethane foam cubes with 0.015 g/cm³ density, which he claims is cheaper and less stressful than traditional media like perlite or rock-wool. He presoaks the foam cubes in water before inserting seeds, ensuring they absorb all available moisture without air exchange.

#### [2009-02-19 — Salt Concentrations in Hydroponic Tomato Cultivation, More or Less ?](https://scienceinhydroponics.com/2009/02/salt-concentrations-in-hydroponic-tomato-cultivation-more-or-less.html)

Daniel Fernandez's research on salt concentrations in hydroponic tomatoes found that a conductivity of 4.5 dS/m resulted in more flavorful and nutrient-rich fruits compared to 2.3 dS/m, highlighting the importance of ion composition over just conductivity levels for tomato taste and quality.

#### [2009-02-18 — Selenium in Hydroponic Growing of Lettuce](https://scienceinhydroponics.com/2009/02/selenium-in-hydroponic-growing-of-lettuce.html)

Daniel Fernandez's blog discusses how adding selenium to hydroponic lettuce crops can enhance their nutritional values. Research shows that concentrations from 2 to 6 ppm of selenate increase both lettuce and tomato Selenium content, providing a significant boost in antioxidants without relying on traditional dietary sources.

#### [2009-02-17 — Titanium Dioxide as a Disinfectant in Hydroponic Gardening](https://scienceinhydroponics.com/2009/02/titanium-dioxide-as-a-disinfectant-in-hydroponic-gardening.html)

Daniel Fernandez introduces titanium dioxide as an effective and cost-effective alternative for disinfecting hydroponic nutrient solutions. His research shows that when exposed to UV light, titanium dioxide can break down organic matter into harmless compounds without harming beneficial microorganisms or plant roots, making it suitable for small-scale growers.

#### [2009-02-16 — Checking the pH of your Hydroponic System, The Easy Way !](https://scienceinhydroponics.com/2009/02/checking-the-ph-of-your-hydroponic-system-the-easy-way.html)

Daniel Fernandez explains how to check the pH of hydroponic nutrient solutions using an acid base indicator like Chlorophenol Red without buying a digital meter, noting that indicators change color based on their proton affinity and are most effective around 5.5-6.0 pH range.

#### [2009-02-14 — Building a Cheap System to Grow Hydroponic Lettuce](https://scienceinhydroponics.com/2009/02/building-a-cheap-system-to-grow-hydroponic-lettuce.html)

Daniel Fernandez describes building a low-cost hydroponic lettuce system using inexpensive materials like nails, wooden boards, plastic, styrofoam, and silicon sealant. The key feature is an air space between the nutrient solution and plants, protected by painted wood and sealed Styrofoam cover to prevent light from reaching the solution.

#### [2009-02-13 — My pH Balancing System for Hydroponic Growing](https://scienceinhydroponics.com/2009/02/my-ph-balancing-system-for-hydroponic-growing.html)

Daniel Fernandez explains his carbonate/citrate buffering system for pH control in hydroponic nutrient solutions. He demonstrates that a mixture of citric acid and bicarbonate acts as an effective buffer, maintaining pH stability by reacting with acids or bases without producing harmful gases like carbon dioxide.

#### [2009-02-12 — One Plant Hydroponic System, Wick Growing](https://scienceinhydroponics.com/2009/02/one-plant-hydroponic-system-wick-growing.html)

Daniel Fernandez discusses the wick nutrient system for growing small hydroponic plants. This simple system uses absorbent fibers to deliver nutrients by capillary action; however, it faces limitations with larger plants due to fiber clogging and salt buildup leading to precipitation of insoluble compounds.

#### [2009-02-11 — Outdoor Hydroponics, Growing Without a Greenhouse](https://scienceinhydroponics.com/2009/02/outdoor-hydroponics-growing-without-a-greenhouse.html)

Daniel Fernandez discusses growing hydroponic plants outdoors, highlighting temperature changes, rain, snow, and excess light as main issues. He advises taking precautions like protecting crops from direct sunlight, monitoring EC levels due to rain, using hydro-gels for moisture retention, and cooling nutrient reservoirs in hot conditions.

#### [2009-02-10 — Ion Selective Electrodes in Hydroponic Culture](https://scienceinhydroponics.com/2009/02/ion-selective-electrodes-in-hydroponic-culture.html)

Daniel Fernandez discusses how adding ion selective electrodes enhances hydroponic gardening by accurately controlling nitrate ions and other elements. These electrodes, available for around $229, allow growers to monitor and resupply nutrients without disrupting the solution's balance.

#### [2009-02-09 — Growing Citrus Trees in a Hydroponic Garden](https://scienceinhydroponics.com/2009/02/growing-citrus-trees-in-a-hydroponic-garden.html)

Daniel Fernandez discusses growing citrus trees using hydroponics, noting they require warm weather and high light levels. He recommends using rice husk or perlite in 5 gallon containers with drip irrigation systems, and suggests starting from seeds which take 3-5 years to bear fruit.

#### [2009-02-08 — Beneficial Fungi in Hydroponic Gardening](https://scienceinhydroponics.com/2009/02/beneficial-fungi-in-hydroponic-gardening.html)

Daniel Fernandez introduces beneficial mycorrhizal fungi, specifically Trichoderma species, into his hydroponic solution to improve nutrient absorption and plant vigor. He notes that reducing phosphorus levels below 40 ppm enhances the growth of these fungi, which in turn boosts plant productivity by stimulating root defense mechanisms and increasing phosphorous assimilation.

#### [2009-02-07 — The NFT Hydroponic Growing System](https://scienceinhydroponics.com/2009/02/the-nft-hydroponic-growing-system.html)

The NFT system uses a PVC gutter with plants placed in small containers inside, where nutrient solution flows down due to gravity. Its main advantage lies in allowing roots to remain exposed to air and nutrients, benefiting plant growth. However, it has limitations like length restrictions and higher costs.

#### [2009-02-06 — Disinfecting your Hydroponic Solution with Hypochlorite](https://scienceinhydroponics.com/2009/02/disinfecting-your-hydroponic-solution-with-hypochlorite.html)

Daniel Fernandez discusses the effectiveness of sodium hypochlorite solutions in maintaining sterile hydroponic systems. He notes that concentrations of 5.5 ppm offer good protection against microorganisms without affecting crop quality, and provides a simple method for home gardeners to achieve this concentration using Clorox solution.

#### [2009-02-05 — Preparing Hydroponics Nutrient Solutions, From Concentrations to Weights](https://scienceinhydroponics.com/2009/02/preparing-hydroponics-nutrient-solutions-from-concentrations-to-weights.html)

Daniel Fernandez explains how to translate nutrient concentrations into actual salt weights needed in a 100L solution. He uses potassium nitrate (KNO₃) as an example, calculating the required amounts of K⁺ and NO₃⁻ ions based on desired concentrations, then determining the amount of KNO₃ needed for precise nitrogen and potassium additions.

#### [2009-02-05 — Describing Concentration in Hydroponics](https://scienceinhydroponics.com/2009/02/describing-concentration-in-hydroponics.html)

Daniel Fernandez explains that concentration in hydroponics can be expressed as moles per liter (molarity) or milligrams per liter (ppm). He notes that ppm is commonly used due to its ease of conversion to mass and the familiarity it provides, unlike molarity which requires more complex calculations. He plans to write about how to convert between these concentration units and the actual salt mass needed for hydroponic solutions.

#### [2009-02-04 — Nitrogen Fertilization in Hydroponics](https://scienceinhydroponics.com/2009/02/nitrogen-fertilization-in-hydroponics.html)

Daniel Fernandez highlights that while soil and hydroponics use the same forms of nitrogen, nitrate is preferred for hydroponics due to its slower absorption rate, preventing toxicity. He explains that bacteria within soil convert ammonium to nitrate, allowing plants in soil to tolerate higher concentrations of ammonium compared to hydroponic systems where ammonium can be toxic at low levels.

#### [2009-02-04 — Rooting Cuttings Naturally](https://scienceinhydroponics.com/2009/02/rooting-cuttings-naturally.html)

Daniel Fernandez describes a natural method for rooting cuttings without using root growth hormones, involving minimal light exposure and foliar feeding with either Hoagland's solution or an organic alternative. This approach allows the cutting to develop its own roots before being reintroduced into normal growing conditions.

#### [2009-02-04 — An Organic, Natural Insecticide for your Garden](https://scienceinhydroponics.com/2009/02/an-organic-natural-insecticide-for-your-garden.html)

Daniel Fernandez describes an effective organic insecticide using garlic, vegetable oil, and water. This mixture is applied directly to plants and can control most types of bad insects without harming beneficial ones, providing long-lasting protection from rain.

#### [2009-02-03 — FAQ – controlling, adjusting and knowing pH in Hydroponic Gardening](https://scienceinhydroponics.com/2009/02/faq-controlling-adjusting-and-knowing-ph-in-hydroponic-gardening.html)

Daniel Fernandez explains that pH is a measure indicating whether a solution is acidic or basic, with 7 being neutral. He emphasizes its importance in hydroponics as it determines the form of nutrients available to plants. He provides methods for measuring and correcting pH, noting that pH meters need calibration and specific acids/bases can be added to adjust pH values.

#### [2009-02-03 — A Natural, Organic Fungicide you can easily make!](https://scienceinhydroponics.com/2009/02/a-natural-organic-fungicide-you-can-make.html)

Daniel Fernandez describes a natural fungicide recipe based on US patent No. 6767562, combining sage leaves, red wine, and water to prevent and cure fungal diseases in various crops. The solution is effective but its effects are lost due to rain, requiring users to bottle it in an airtight container.

#### [2009-02-03 — What are Hydroponic nutrients ? The nature of nutrient salts](https://scienceinhydroponics.com/2009/02/what-are-hydroponic-nutrients-the-nature-of-nutrient-salts.html)

Daniel Fernandez explains that hydroponic nutrient solutions are often described in elemental concentration form, such as N 200 ppm. This does not mean the nutrients are present as pure elements like nitrogen (N2), but rather as ions such as NO3(-) or NH4(+) which are assimilated by plants. He emphasizes understanding that these elemental concentrations represent the total available forms of nutrients in solution, simplifying their management for growers.

#### [2009-02-03 — Keeping the pH of your hydroponic nutrient solution stable](https://scienceinhydroponics.com/2009/02/keeping-the-ph-of-your-hydroponic-nutrient-solution-stable.html)

Daniel Fernandez discusses maintaining stable pH levels in hydroponic nutrient solutions by using buffering agents like citric acid, ammonia, and carbonate. His simulations show that while citrate buffers against acids but not bases effectively, ammonia provides similar buffering to both acids and bases, and the combination of carbonate with citric acid offers superior buffering across all pH ranges, potentially extending solution longevity without adjustments.

#### [2009-02-02 — Hydroponic Nutrients, Are they Unnatural ?](https://scienceinhydroponics.com/2009/02/hydroponic-nutrients-are-they-unnatural.html)

The post clarifies that hydroponic nutrients are not unnatural as they have the same chemical form as soil nutrients, which plants can absorb without needing to break down organic matter or fight pathogens. The author argues against the notion of synthetic substances being inherently bad and emphasizes that both natural and unnatural things can be good or bad depending on their specific use.

#### [2009-02-02 — Hydroponic Gardening for Small Spaces](https://scienceinhydroponics.com/2009/02/hydroponic-gardening-for-small-spaces.html)

Daniel Fernandez discusses how hydroponic gardening can be adapted for small spaces, offering an alternative to traditional soil-based agriculture in crowded urban environments. He highlights that this method allows for higher plant densities and better quality produce compared to conventional methods, making it suitable for people with limited space.

#### [2009-02-02 — The Hoaglands Solution for Hydroponic Cultivation](https://scienceinhydroponics.com/2009/02/the-hoaglands-solution-for-hydroponic-cultivation.html)

The Hoagland solution, developed in 1933 by Hoagland and Snyder, provides essential nutrients for plant growth. It includes elements like N, K, Ca, P, S, Mg, B, Fe, Mn, Zn, Cu, and Mo at specific concentrations to support various plant species, especially large plants such as tomatoes and bell peppers. The solution can be diluted for use with lower-demand plants like lettuce or aquatic plants.

#### [2009-02-02 — Indoor Hydroponic gardening, the cheap way !](https://scienceinhydroponics.com/2009/02/indoor-hydroponic-gardening-the-cheap-way.html)

Daniel Fernandez discusses the use of LEDs in hydroponic gardening to reduce energy consumption by 20 times compared to traditional lighting. He highlights how two tomato plants can be grown with just 50 W of LED lights, whereas they would require over 1200 W with conventional halide lamps, addressing both cost and environmental concerns.

#### [2009-02-02 — Hydroponic Floating System for Lettuce Production](https://scienceinhydroponics.com/2009/02/hydroponic-floating-system-for-lettuce-production.html)

The floating raft hydroponic system produces higher dry weights of lettuce compared to traditional systems, as demonstrated by B. A. Kratky in 2005. By placing the raft a few centimeters above the nutrient solution, this method eliminates the need for mechanical aeration and pumps, achieving yields superior to any published literature without power usage.

#### [2009-02-01 — Hydroponic Nutrient Solution Toxicity](https://scienceinhydroponics.com/2009/02/hydroponic-nutrient-solution-toxicity.html)

Daniel Fernandez discusses the environmental impact of disposing hydroponic nutrient solutions improperly and proposes using them to grow plants with lower nutrient requirements for two months before disposal. He also suggests cultivating herbs or grass in these waste containers, highlighting papyrus as a solution plant.

#### [2009-02-01 — Preparing a Hydroponic Nutrient Solution](https://scienceinhydroponics.com/2009/02/preparing-a-hydroponic-nutrient-solution.html)

To save money and improve crop results, Daniel Fernandez explains how to prepare a hydroponic nutrient solution using the Hydroponic Buddy calculator. The tool helps determine the correct amount of each nutrient salt needed to achieve desired concentrations, facilitating experimentation with various nutrient levels.

#### [2009-02-01 — FAQ – Electrical Conductivity (EC) in Hydroponics](https://scienceinhydroponics.com/2009/02/faq-electrical-conductivity-ec-in-hydroponics.html)

Electrical conductivity (EC) measures how easily an electrical charge can flow through a solution, typically measured in S/cm. In hydroponics, EC is directly proportional to the amount of dissolved salts, including nutrients; however, it has limitations due to different ion conductivities and pH-dependent effects. Proper calibration at constant pH and regular measurements are crucial for accurate EC readings, which help monitor nutrient loss or changes in solution composition.

#### [2009-02-01 — Hydroponic Nutrient Solutions for Lettuce](https://scienceinhydroponics.com/2009/02/hydroponic-nutrient-solutions-for-lettuce.html)

Daniel Fernandez's blog post discusses the importance of custom nutrient solutions for lettuce hydroponics, emphasizing that using generic solutions can lead to suboptimal plant growth and quality. A peer-reviewed study by Karimaei et al (2004) found that the Hoagland solution yields better results in terms of dry weight and nutrient content compared to other tested solutions.

#### [2009-02-01 — Hydrogen Peroxide in Germination](https://scienceinhydroponics.com/2009/02/hydrogen-peroxide-in-germination.html)

Daniel Fernandez discusses how hydrogen peroxide aids in seed germination, particularly for eastern gamagrass seeds. Researchers found that using 15% hydrogen peroxide for 18 hours dissolves the outer coat of seeds, facilitating water access and effectively replacing four weeks of cold stratification.

#### [2009-02-01 — Using Hydrogen Peroxide in Hydroponic Crops](https://scienceinhydroponics.com/2009/02/using-hydrogen-peroxide-in-hydroponic-crops.html)

Daniel Fernandez discusses using hydrogen peroxide in hydroponic crops to combat algae growth, noting its effectiveness but warns about the risk of damaging plant roots if used 1mL of 3% v/v solution is applied weekly. He emphasizes that while no scientific studies confirm an exact optimum level, his personal experience suggests this dosage prevents algae without harming plants.

#### [2009-02-01 — FAQ – Growing media in hydroponics](https://scienceinhydroponics.com/2009/02/faq-growing-media-in-hydroponics.html)

The ideal growing media in hydroponics provides air, water, and support without altering nutrient solutions or pH. Perlite is highly water-retentive but expensive; vermiculite can alter solution composition; sand alone doesn’t provide enough airflow; rice husk with sand mixture offers good airflow and moisture retention, though it needs to be moistened before use. Choosing media depends on plant type and system (e.g., gravel for NFT systems). Media should be renovated annually if organic, treated between crops with hydrogen peroxide solution.

## Maintenance

To refresh the inventory, query `https://scienceinhydroponics.com/wp-json/wp/v2/posts` with pagination and compare the API total, oldest/newest dates, IDs, canonical links, and modified timestamps. Re-read modified posts before carrying their claims forward. Keep this file a research snapshot; update current-state behavior only in the owning subsystem documentation when code actually changes.
