import assert from "node:assert/strict";
import test from "node:test";

import {
  buildAlignedRows,
  buildDoseTable,
  formatNumber,
  parseDecimalInput,
  sidebarRatioRows,
} from "../../frontend/app/formatting.js";
import { createUnitService } from "../../frontend/app/units.js";

test("decimal parsing accepts both supported separators and rejects invalid values", () => {
  assert.equal(parseDecimalInput(" 12,5 "), 12.5);
  assert.equal(parseDecimalInput("12.5"), 12.5);
  assert.equal(parseDecimalInput(""), null);
  assert.equal(parseDecimalInput("Infinity"), null);
});

test("fertilizer tables align names, amounts and units through one formatter", () => {
  const units = createUnitService();
  const t = (key) => ({ "common.fertilizer": "Dünger", "common.amount": "Menge", "common.unit": "Einheit" })[key];
  assert.deepEqual(buildDoseTable([
    { name: "A", grams: 63.558 }, { name: "Liquid", grams: 2 },
  ], { t, units, fertilizerKinds: { Liquid: "liquid" } }), [
    "Dünger   Menge  Einheit",
    "A       63.558  g",
    "Liquid       2  mL",
  ]);
  units.setSolidDoseUnit("kilogram");
  assert.equal(units.formatDoseDisplay(0.000001, "A"), "1.0000e-9");
  assert.equal(units.formatDoseInput(0.000001, "A"), "1.0000e-9");
  assert.equal(units.formatDoseDisplay(0, "A"), "0");
});

test("sidebar ratio rows retain domain values and label nitrogen shares", () => {
  const rows = sidebarRatioRows({
    npk_ratios_ion: { "Ca:Mg": "Ca:Mg=1:0.4", "N:K": "N:K=1:2", "Fe:Mg": "Fe:Mg=1:20" },
    n_form_pct: { no3: 90, nh4: 7, urea: 3 },
  });
  assert.deepEqual(rows, [
    ["Ca:Mg", "2.5 Ca : 1 Mg"], ["N:K", "1:2"], ["Ca:K", "-"],
    ["NO3:NH4:UR (%)", "90:7:3", "live.nitrogenFormsHint"],
    ["SO4:P", "-"], ["P:K", "-"], ["Fe:Mg", "1:20"],
  ]);
  assert.equal(sidebarRatioRows()[0][1], "-");
  assert.equal(sidebarRatioRows({ npk_ratios_ion: { "Ca:Mg": "Ca:Mg=0:0" } })[0][1], "0 Ca : 0 Mg");
  assert.equal(sidebarRatioRows({ npk_ratios_ion: { "Ca:Mg": "Ca:Mg=1:0" } })[0][1], "1 Ca : 0 Mg");
});

test("number and clipboard formatting are deterministic", () => {
  assert.equal(formatNumber(1.23456), "1.235");
  assert.equal(formatNumber(Number.NaN), "-");
  assert.deepEqual(
    buildAlignedRows(["name", "g"], [["A", "2"], ["long", "10"]], [1]),
    ["name   g", "A      2", "long  10"],
  );
});
