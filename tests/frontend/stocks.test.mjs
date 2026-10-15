import assert from "node:assert/strict";
import test from "node:test";
import en from "../../frontend/i18n/en.js";
import { buildStockPrintableText } from "../../frontend/app/stocks.js";
import { createUnitService } from "../../frontend/app/units.js";

const t = (key, params = {}) => en[key].replace(/\{(\w+)\}/g, (_, name) => params[name]);

test("stock sheets retain small doses and distinguish stock water from final batch water", () => {
  const units = createUnitService();
  units.setFertilizers([{ name: "Trace", liquid: false }, { name: "Liquid", liquid: true }]);
  units.setSolidDoseUnit("kilogram");
  const solid = { name: "Trace", stock_amount: 0.000001 };
  const liquid = { name: "Liquid", assignment: "separate", recipe_amount: 2 };
  const plan = {
    complete: true,
    exportable: true,
    liters: 10,
    tanks: [{ id: "A", liters: 1, factor: 100, ingredients: [solid], dose_ml: 100, dose_ml_per_l: 10, capacity_liters: 100 }],
    ingredients: [solid, liquid],
    settings: { source_water: { mg_per_l: { Ca: 106.99999999999999, KH: 2 }, osmosis_percent: 66 } },
    findings: [{ code: "pair_risk", tank: "A", materials: ["Trace", "Liquid"], severity: "review", risks: ["magnesium_phosphorus"] }],
    final_solution: { elements_mg_per_l: { Ca: 99.6362 } },
  };
  const sheet = buildStockPrintableText(plan, t, units);
  assert.match(sheet, /Trace: 1\.0000e-9 kg/);
  assert.match(sheet, /Liquid — 2 mL/);
  assert.match(sheet, /100 mL A/);
  assert.match(sheet, /Final batch water before RO mixing: Ca 107 mg\/L, KH 2 °dKH/);
  assert.match(sheet, /RO-water proportion \(%\): 66/);
  assert.equal(sheet.match(/RO-water proportion/g).length, 1);
  assert.match(sheet, /Prepare stocks with RO\/distilled water, modeled as mineral-free/);
  assert.doesNotMatch(sheet, /106\.999|Saved preparation|Reference temperature/);
  assert.match(sheet, /Needs review: A/);
  assert.match(sheet, /Precipitation depends on pH and concentration/);
  assert.doesNotMatch(sheet, /Metal form|chelator|not recorded/);
  assert.doesNotMatch(sheet, /Water contribution|Recipe \(mg\/L\)|After stock dosing|Difference \(mg\/L\)/);
  assert.ok(sheet.split("\n").includes("Science in Hydroponics: https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html"));
  assert.ok(sheet.split("\n").includes("Frontiers in Agronomy: https://www.frontiersin.org/journals/agronomy/articles/10.3389/fagro.2026.1823187/full"));
  assert.equal(buildStockPrintableText({ ...plan, complete: false, exportable: false }, t, units), "");
  assert.equal(buildStockPrintableText({ ...plan, exportable: false }, t, units), "");
});
