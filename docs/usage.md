# Using Horticalc

Horticalc opens as a native desktop application. Calculator, Solver, water
analysis, fertilizer editing and stock preparation share the same batch volume,
water, fertilizer catalogue, units, and saved profiles.

## Calculator

Use **Calculator** when fertilizer doses are already known.

1. Set the batch volume in **Configuration**.
2. Choose a water profile or enter the water analysis.
3. Add fertilizer components and their doses.
4. Select **Calculate**.

The fertilizer field searches the complete catalogue name as you type, so a
product fragment such as `haka`, `313`, or `special` works without knowing the
manufacturer. Select a component row and use minus to remove that exact row;
plus adds and selects a new row.

The result separates fertilizer and water contributions and reports elemental
and oxide concentrations, ions, ion balance, EC, and NPK ratios. Changing a
display unit converts the visible quantity without changing the stored batch or
dose. The sidebar shows nitrate, ammonium and urea shares as **NO3:NH4:UR
(%)**, calculated from their nitrogen contributions.

Saved calculator recipes contain their batch, fertilizer doses, water profile,
RO-water proportion, urea setting, optional solver configuration, and any stock
preparation settings. The star
beside the recipe selector marks favorites and moves them to the top of the
list without changing their files.

## Stock solutions

Calculate a recipe, then open **Stock solutions** in the main menu directly
below **Calculator**. Without a calculated recipe, preparation shows a prompt
to calculate one first. The **Make stock solutions** action on a
current Solver result transfers its recipe to Calculator and opens preparation.
**Back to recipe** returns to the normal Calculator tables.

Start with the finished volume of each stock and a concentration factor. The
defaults are 1 L and 100×. At 100×, dose **10 mL of each stock per litre of final
nutrient solution**: A and B together contribute 20 mL/L. The displayed batch
doses include every populated stock. Empty containers are omitted.

Choose **Suggest tank assignments** to fill open assignments from the existing
fertilizer composition, or assign products yourself. Suggestions compare
different products; an existing manufacturer blend stays together. They leave
liquids, products without composition and products that do not fit unresolved.
Existing choices are preserved. Add C if useful, or choose a separate addition
to the final batch. At least one container must remain. All ingredients need
an assignment and each populated container must hold enough stock for the batch
before copying or printing. Changed product data require explicit review through
**Assignment reviewed**; recalculating alone leaves the finding visible.
Potential mixing risks remain visible after manual assignment;
absence of a finding does not establish compatibility.

Under **Preparation details**, set different volumes or factors per stock.
Prepare all stocks with RO/distilled water, modeled as mineral-free. The water
analysis and its RO proportion still describe the final nutrient batch. For a
complete plan, the nutrient display includes the adjusted water contribution:
stocks displace some batch water, using an additive-volume estimate.
Fertilizer doses are unchanged.

Dissolve each product according to its instructions, then make up to the stated
**finished stock volume**. Dose the stocks separately into well-mixed water and
make up to the **final batch volume**. Do not pour concentrates together. Follow
product-specific preparation and storage instructions, particularly for
silicates and chelates. A small trial under the intended storage conditions is
useful; initial clarity does not establish shelf stability.

Check assignments and preparation conditions against the product instructions.
Calculated amounts do not confirm storage stability. **Stock solutions and
fertilizer compatibility** opens the Science in Hydroponics article and the
Frontiers in Agronomy review in the external browser from the desktop app.
When using the UI in a browser, allow popups to open both articles.
Use **Copy preparation sheet** for a formatted
export with selected assignments, rounded
water values and one RO proportion for the final batch. Ordinary text selection
over the stock panel copies plain text instead of hidden HTML form options.

Save through the existing recipe controls to keep the stock settings and source
water analysis. A saved stock-bearing recipe restores that water snapshot,
including unsaved analysis edits. Changing the batch volume scales recipe doses
and automatically recalculates an open stock view after the recipe calculation.
Stock volumes and concentration factors stay as configured: doubling the batch
doubles its stock dose, while the amounts for a fixed stock container remain
unchanged. Increase stock volume yourself if the larger batch exceeds its
capacity. Other recipe or preparation edits make the sheet stale; choose
**Update plan** before using or exporting new quantities.
The feature plans preparation; it does not track bottles already mixed.

## Water analysis

Use **Water analysis** to load, edit, and save the water used by Calculator and
Solver. Values describe the source water before reverse-osmosis mixing.

The **RO-water proportion** is the percentage of the final batch modelled as
pure RO water with `0 mg/L` dissolved input. At 25%, Horticalc uses 75% of every
entered source-water concentration.

## Fertilizer editor

Use **Fertilizer editor** to search and edit the effective catalogue. Composition
values are mass fractions: `0.14` means 14%. A liquid product uses its weight
factor as density when converting the displayed volume dose.

Select an editor row and use minus to delete it from the editable list.
The table fills the remaining workspace height at the selected interface scale;
scroll inside it to reach further products while keeping the controls visible.

**Solver max / L** limits the variable dose the Solver may select. An empty
value means unlimited; `0` prevents variable selection while still allowing a
fixed dose. Changes are written as user overrides, so the shipped catalogue is
not modified.

## Solver

Use **Solver** when nutrient targets are known but fertilizer doses are not.

1. Load a target profile or enter elemental targets in `mg/L`.
2. Select the fertilizers the Solver may use.
3. Add fixed amounts for doses that must not change.
4. Choose a solver model and, if needed, its advanced settings.
5. Select **Calculate** and compare target, achieved, and difference values.
6. Apply the result to Calculator or save it as a fertilizer recipe.

`NNLS + tuning (standard)` is the default model. **Mass balance** and
**Prioritized targets** are experimental. Their mathematical behavior is
described in [Solver](solver.md).

A target profile normally stores nutrient targets only. Enable **Save/load
Solver setup** to include batch volume, water profile, RO-water proportion,
allowed fertilizers, fixed doses, urea mode, and solver settings. Loading with
the option disabled changes only the targets. Horticalc checks referenced water
and fertilizer names before replacing the current setup.

The target-profile star is independent of recipe favorites. Delete is available
only for user-saved recipes and target profiles. Deleting a user override of a
shipped profile reveals the shipped profile again.

## Solver history

Successful API Solver runs appear in the collapsible history card. Select a row
to inspect or restore its inputs; restoring does not run the Solver. A star pins
a run above normal history and protects it from retention and the regular clear
action. The history limit counts unpinned runs; setting it to `0` retains pins
but stops normal history recording.

## Preferences and languages

Configuration controls volume, solid-dose and liquid-dose display units, theme,
language, UI scale, and Solver-history retention. Use `Ctrl`+`+` and `Ctrl`+`-`
to change the UI scale or `Ctrl`+`0` to return to 100%. `Ctrl` plus the mouse
wheel uses the same scale steps. Horticalc provides German, English, Dutch,
Spanish, and Simplified Chinese UI text. Data keys, element symbols, file
formats, and API fields remain unchanged when the language changes.

## Files and backups

Horticalc keeps shipped defaults in `data/` and `recipes/`. Your edits,
preferences, profiles, recipes, and Solver history are stored below `user/`;
logs are stored below `logs/`. These directories sit beside the executable in
a packaged application and below the repository root in development.

Back up `user/` to preserve your work. To test a clean state, close Horticalc,
rename `user/`, and start the application again. Restore the original directory
only while Horticalc is closed.

## Startup problems

- **Unknown publisher on Windows:** obtain the installer from the official
  GitHub release and verify it as described in [Releases](../RELEASE.md).
- **Portable ZIP blocked:** if the original ZIP's **Properties** shows
  **Unblock**, select it before extraction. Files already extracted from a
  blocked ZIP must be deleted and extracted again.
- **Missing desktop renderer:** install WebView2 on Windows or GTK/WebKitGTK on
  Linux using the commands in [README.md](../README.md#system-requirements-and-startup-help).
- **Application folder is not writable:** move the complete portable folder to
  a writable location; do not run it inside an archive or protected system Folders.
- **Unexpected startup failure:** inspect `logs/launcher.log` and include the
  relevant excerpt when reporting the issue.
