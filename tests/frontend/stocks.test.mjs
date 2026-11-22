import assert from "node:assert/strict";
import test from "node:test";
import en from "../../frontend/i18n/en.js";
import { buildStockClipboardText } from "../../frontend/app/stocks.js";
import { createUnitService } from "../../frontend/app/units.js";

const t = (key, params = {}) => en[key].replace(/\{(\w+)\}/g, (_, name) => params[name]);

test("stock clipboard uses aligned doses and keeps preparation water in the instructions", () => {
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
  const sheet = buildStockClipboardText(plan, t, units);
  assert.match(sheet, /Trace\s+1\.0000e-9\s+kg/);
  assert.match(sheet, /Liquid\s+2\s+mL/);
  assert.match(sheet, /100 mL A/);
  assert.match(sheet, /100× the recipe dose per litre/);
  assert.match(sheet, /Dose into final nutrient solution\s+10 mL\/L/);
  assert.match(sheet, /Final nutrient solution yield\s+100 L/);
  assert.doesNotMatch(sheet, /Final batch water|RO-water proportion|Ca 107|KH 2/);
  assert.match(sheet, /Prepare all stocks with distilled, RO or other mineral-free water/);
  assert.ok(sheet.indexOf("Prepare all stocks") > sheet.indexOf("Preparation and dosing"));
  assert.doesNotMatch(sheet, /106\.999|Saved preparation|Reference temperature/);
  assert.match(sheet, /Needs review: A/);
  assert.match(sheet, /Precipitation depends on pH and concentration/);
  assert.doesNotMatch(sheet, /Metal form|chelator|not recorded/);
  assert.doesNotMatch(sheet, /Water contribution|Recipe \(mg\/L\)|After stock dosing|Difference \(mg\/L\)/);
  assert.ok(sheet.split("\n").includes("Science in Hydroponics: https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html"));
  assert.ok(sheet.split("\n").includes("Frontiers in Agronomy: https://www.frontiersin.org/journals/agronomy/articles/10.3389/fagro.2026.1823187/full"));
  assert.equal(buildStockClipboardText({ ...plan, complete: false, exportable: false }, t, units), "");
  assert.equal(buildStockClipboardText({ ...plan, exportable: false }, t, units), "");
});
