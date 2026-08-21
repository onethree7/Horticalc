# Using Horticalc

Horticalc opens as a native desktop application. Its four workflows share the
same batch volume, water, fertilizer catalogue, units, and saved profiles.

## Calculator

Use **Calculator** when fertilizer doses are already known.

1. Set the batch volume in **Configuration**.
2. Choose a water profile or enter the water analysis.
3. Add fertilizer components and their doses.
4. Select **Calculate**.

The result separates fertilizer and water contributions and reports elemental
and oxide concentrations, ions, ion balance, EC, and NPK ratios. Changing a
display unit converts the visible quantity without changing the stored batch or
dose.

Saved calculator recipes contain their batch, fertilizer doses, water profile,
RO-water proportion, urea setting, and optional solver configuration. The star
beside the recipe selector marks favorites and moves them to the top of the
list without changing their files.

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
language, and Solver-history retention. Horticalc provides German, English,
Dutch, Spanish, and Simplified Chinese UI text. Data keys, element symbols,
file formats, and API fields remain unchanged when the language changes.

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
  a writable location; do not run it inside an archive or from Program Files.
- **Unexpected startup failure:** inspect `logs/launcher.log` and include the
  relevant excerpt when reporting the issue.
