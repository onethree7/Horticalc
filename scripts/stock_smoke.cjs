const assert = require("node:assert/strict");

async function assertStockWorkflow(page, assertNoPageOverflow) {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.locator(".rail-settings").evaluate((element) => { element.open = true; });
  await page.locator("#languageSelect").selectOption("en");
  await page.locator("#configVolumeUnit").selectOption("liter");
  await page.locator("#configSolidDoseUnit").selectOption("gram");
  await page.locator("#profileSelect").selectOption("reference_calcinit_epso_top_1g_per_l_each.yml");
  await page.locator("#loadProfile").click();
  await page.waitForFunction(() => {
    const names = Array.from(document.querySelectorAll("#fertilizerSelectTable .searchable-combobox-input")).map((input) => input.value);
    return names.join("|") === "Yara Tera CALCINIT|K+S EPSO Top Bittersalz 16-39";
  });
  await page.waitForFunction(() => !document.querySelector("#makeCalculatorStocks").disabled);
  await page.locator("#makeCalculatorStocks").click();
  await page.locator("#stockIngredients tbody tr").first().waitFor();
  assert.equal(await page.locator("#copyStocks").isDisabled(), true);
  await page.locator("#suggestStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(await page.locator("#stockTankCards .stock-tank").count(), 2);
  assert.match(await page.locator("#stockBatchDose").innerText(), /100 mL A \+ 100 mL B/);
  assert.equal(await page.locator("#stockIngredients tbody tr td:last-child").first().innerText(), "100 g");
  assert.equal(await page.locator("#calculatorTable").isVisible(), false);

  await page.locator("#stockFactor").fill("50");
  assert.equal(await page.locator("#copyStocks").isDisabled(), true);
  assert.equal(await page.locator("#stockOutput").isVisible(), false);
  await page.locator("#updateStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.match(await page.locator("#stockBatchDose").innerText(), /200 mL A \+ 200 mL B/);

  await page.locator('#stockIngredients select[data-material="K+S EPSO Top Bittersalz 16-39"]').selectOption("A");
  await page.locator("#updateStocks").click();
  await page.locator('#stockFindings [data-severity="review"]').waitFor();
  await page.locator("#copyStocks").click();
  await page.locator("#stockStatus", { hasText: /copied/i }).waitFor();
  await page.evaluate(() => { globalThis.print = () => {}; });
  await page.locator("#printStocks").click();
  const printed = await page.locator("#stockPrintSheet").textContent();
  assert.match(printed, /Calcium and sulfate come from different products/);
  assert.match(printed, /1000\/|FINAL|final/);
  assert.ok(printed.split("\n").includes("Science in Hydroponics: https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html"));
  assert.doesNotMatch(printed, /Water contribution|No modeled nutrient difference/);

  await page.locator("#addStockC").click();
  await page.locator('#stockIngredients select[data-material="K+S EPSO Top Bittersalz 16-39"]').selectOption("C");
  await page.locator("#updateStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.match(await page.locator("#stockTankCards").innerText(), /C ·/);

  let savedRecipe;
  const collectionHandler = async (route) => {
    if (route.request().method() === "POST") {
      savedRecipe = route.request().postDataJSON();
      await route.fulfill({ json: { status: "ok", filename: "Browser_stock_plan.yml" } });
    } else {
      const response = await route.fetch();
      const recipes = await response.json();
      await route.fulfill({ response, json: [...recipes, { name: "Browser stock plan", filename: "Browser_stock_plan.yml" }] });
    }
  };
  await page.route("**/recipes", collectionHandler);
  await page.route("**/recipes/Browser_stock_plan.yml", (route) => route.fulfill({ json: savedRecipe }));
  await page.locator("#profileName").fill("Browser stock plan");
  await page.locator("#saveProfile").click();
  await page.locator('#profileSelect option[value="Browser_stock_plan.yml"]').waitFor({ state: "attached" });
  assert.equal(savedRecipe.stock_solution.tanks.A.factor, 50);
  assert.equal(savedRecipe.stock_solution.assignments["K+S EPSO Top Bittersalz 16-39"], "C");
  assert.equal(savedRecipe.stock_solution.source_water.osmosis_percent, 100);
  savedRecipe.stock_solution.source_water = { mg_per_l: { Ca: 80 }, osmosis_percent: 0 };
  await page.locator("#stockFactor").fill("75");
  await page.locator("#profileSelect").selectOption("Browser_stock_plan.yml");
  await page.locator("#loadProfile").click();
  await page.locator("#stockSolutionPanel").waitFor({ state: "hidden" });
  await page.waitForFunction(() => !document.querySelector("#makeCalculatorStocks").disabled);
  const restoredPlan = page.waitForResponse((response) => response.url().endsWith("/stock-solutions/plan"));
  await page.locator("#makeCalculatorStocks").click();
  const mineralPlan = await (await restoredPlan).json();
  await page.locator("#stockIngredients tbody tr").first().waitFor();
  if (await page.locator("#copyStocks").isDisabled()) await page.locator("#suggestStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(await page.locator("#stockFactor").inputValue(), "50");
  assert.ok(Math.abs(mineralPlan.final_solution.water_elements_mg_per_l.Ca - 76.8) < 0.000001);
  assert.equal(await page.locator("#stockSidebarLabel").innerText(), "Expected diluted result");
  assert.equal(await page.locator("#stockOutput table").count(), 0);
  assert.doesNotMatch(await page.locator("#stockOutput").innerText(), /Water contribution/);
  await page.locator("#printStocks").click();
  const mineralSheet = await page.locator("#stockPrintSheet").textContent();
  assert.match(mineralSheet, /200 mL A \+ 200 mL C/);
  assert.doesNotMatch(mineralSheet, /Water contribution|Recipe \(mg\/L\)|After stock dosing|Difference \(mg\/L\)/);
  await page.locator('#stockIngredients select[data-material="K+S EPSO Top Bittersalz 16-39"]').selectOption("");
  await page.locator("#updateStocks").click();
  await page.locator("#stockStatus", { hasText: "Assign every ingredient" }).waitFor();
  assert.equal(await page.locator("#stockSidebarLabel").innerText(), "");
  assert.equal(await page.locator("#copyStocks").isDisabled(), true);
  await page.locator('#stockIngredients select[data-material="K+S EPSO Top Bittersalz 16-39"]').selectOption("C");
  await page.locator("#updateStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(await page.locator("#stockSidebarLabel").innerText(), "Expected diluted result");
  await page.unroute("**/recipes", collectionHandler);
  await page.unroute("**/recipes/Browser_stock_plan.yml");

  for (const [locale, title] of [["de", "Stammlösungen"], ["nl", "Stockoplossingen"], ["es", "Soluciones madre"], ["zh", "母液"], ["en", "Stock solutions"]]) {
    await page.locator('[data-shell-view="water"]').click();
    await page.locator("#languageSelect").selectOption(locale);
    await page.locator('[data-shell-view="fertilizers"]').click();
    assert.equal(await page.locator("#stockTitle").innerText(), title);
    assert.equal(await page.locator("#copyStocks").isDisabled(), false);
  }
  await page.locator("#configVolumeUnit").selectOption("us_gallon");
  assert.ok(Math.abs(Number(await page.locator("#stockVolume").inputValue()) - 0.2642) < 0.0001);
  assert.match(await page.locator("#stockTankCards").innerText(), /0.2642/);
  await page.locator("#configVolumeUnit").selectOption("liter");
  await page.locator("#stockDetails > summary").click();
  await assertStockCopyAndControls(page);
  await page.locator("#stockIndependent").check();
  await page.locator('input[data-tank="C"][data-field="factor"]').fill("200");
  await page.locator("#updateStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.match(await page.locator("#stockBatchDose").innerText(), /200 mL A \+ 50 mL C/);

  for (const width of [1920, 1280, 960, 640]) {
    await page.setViewportSize({ width, height: 900 });
    await assertNoPageOverflow(page, `${width}px stock preparation`);
  }
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.locator("#uiScaleSelect").selectOption("125");
  await assertNoPageOverflow(page, "stock preparation at 125% scale");
  await page.locator("#uiScaleSelect").selectOption("100");

  await page.evaluate(() => {
    const snapshot = JSON.parse(globalThis.localStorage.getItem("last_solution_calculated"));
    snapshot.stock_solution = { ...snapshot.stock_solution, schema_version: 1,
      preparation_water: { mg_per_l: {}, osmosis_percent: 0 }, temperature_c: 20, evidence_revision: "old" };
    globalThis.localStorage.setItem("last_solution_calculated", JSON.stringify(snapshot));
  });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => !document.querySelector("#makeCalculatorStocks").disabled);
  await page.locator("#makeCalculatorStocks").click();
  await page.locator("#stockIngredients tbody tr").first().waitFor();
  if (await page.locator("#copyStocks").isDisabled()) await page.locator("#suggestStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(await page.locator('input[data-tank="C"][data-field="factor"]').inputValue(), "200");
  assert.deepEqual(await page.evaluate(() => ({
    current: JSON.parse(globalThis.localStorage.getItem("last_solution_calculated")).stock_solution.schema_version,
    backup: JSON.parse(globalThis.localStorage.getItem("last_solution_calculated_stock_backup")).stock_solution.schema_version,
  })), { current: 2, backup: 1 });
  await page.locator("#closeStocks").click();
  await assertStockReviewAndScaling(page);
  await page.locator("#profileSelect").selectOption("reference_calcinit_1g_per_l.yml");
  const resetCalculation = page.waitForResponse((response) => response.url().endsWith("/calculate") && response.request().postDataJSON().liters === 10);
  await page.locator("#loadProfile").click();
  await resetCalculation;
  await page.waitForFunction(() => document.querySelectorAll("#fertilizerSelectTable .searchable-combobox-input").length === 1);
  await page.waitForFunction(() => !document.querySelector("#makeCalculatorStocks").disabled);
  await page.locator("#makeCalculatorStocks").click();
  await page.locator("#stockIngredients tbody tr").first().waitFor();
  if (await page.locator("#copyStocks").isDisabled()) await page.locator("#suggestStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(await page.locator("#stockFactor").inputValue(), "100");
  assert.equal(await page.locator("#stockIngredients tbody tr").count(), 1);
  await page.locator("#closeStocks").click();
}

async function assertStockReviewAndScaling(page) {
  await page.locator(".rail-settings").evaluate((element) => { element.open = true; });
  await page.locator("#languageSelect").selectOption("en");
  await page.evaluate(() => { globalThis.print = () => {}; });
  const material = "Yara Tera CALCINIT";
  const oldFingerprint = "0".repeat(64);
  const recipeHandler = async (route) => {
    const response = await route.fetch();
    const recipe = await response.json();
    await route.fulfill({ response, json: { ...recipe, stock_solution: {
      schema_version: 2, tanks: { C: { liters: 1, factor: 100 } }, assignments: { [material]: "C" },
      source_water: { mg_per_l: {}, osmosis_percent: 100 }, material_fingerprints: { [material]: oldFingerprint },
    } } });
  };
  const recipeUrl = "**/recipes/reference_calcinit_1g_per_l.yml";
  await page.route(recipeUrl, recipeHandler);
  await page.locator("#profileSelect").selectOption("reference_calcinit_1g_per_l.yml");
  await page.locator("#loadProfile").click();
  await page.waitForFunction(() => document.querySelectorAll("#fertilizerSelectTable .searchable-combobox-input").length === 1);
  await page.waitForFunction(() => !document.querySelector("#makeCalculatorStocks").disabled);
  await page.locator("#makeCalculatorStocks").click();
  await page.locator("#stockFindings button", { hasText: "Assignment reviewed" }).waitFor();
  assert.equal(await page.locator("#copyStocks").isDisabled(), true);
  assert.equal(await page.locator("#addStockC").isDisabled(), true);
  await page.locator("#addStockC").evaluate((button) => button.click());
  assert.deepEqual(await page.evaluate(() => Object.keys(JSON.parse(globalThis.localStorage.getItem("last_solution_calculated")).stock_solution.tanks)), ["C"]);
  const repeated = page.waitForResponse((response) => response.url().endsWith("/stock-solutions/plan"));
  await page.locator("#updateStocks").click();
  const repeatedPlan = await (await repeated).json();
  assert.equal(repeatedPlan.settings.material_fingerprints[material], oldFingerprint);
  assert.equal(repeatedPlan.exportable, false);
  await page.locator("#stockFindings button", { hasText: "Assignment reviewed" }).click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(await page.locator("#stockFindings button").count(), 0);
  assert.notEqual(await page.evaluate((name) => JSON.parse(globalThis.localStorage.getItem("last_solution_calculated")).stock_solution.material_fingerprints[name], material), oldFingerprint);

  const scaled = page.waitForResponse((response) => response.url().endsWith("/stock-solutions/plan") && response.request().postDataJSON().recipe.liters === 20);
  await page.locator("#configLiters").fill("20");
  const scaledPlan = await (await scaled).json();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.equal(scaledPlan.ingredients[0].recipe_amount, 20);
  assert.equal(scaledPlan.ingredients[0].stock_amount, 100);
  assert.equal(await page.locator("#stockVolume").inputValue(), "1");
  assert.match(await page.locator("#stockBatchDose").innerText(), /200 mL C/);

  let release;
  const releaseResponse = new Promise((resolve) => { release = resolve; });
  const delayedPlan = async (route) => {
    if (route.request().postDataJSON().recipe.liters !== 40) return route.continue();
    const response = await route.fetch();
    await releaseResponse;
    await route.fulfill({ response });
  };
  await page.route("**/stock-solutions/plan", delayedPlan);
  const delayedRequest = page.waitForRequest((request) => request.url().endsWith("/stock-solutions/plan") && request.postDataJSON().recipe.liters === 40, { timeout: 5000 });
  await page.locator("#configLiters").fill("40");
  await delayedRequest;
  const returned = page.waitForResponse((response) => response.url().endsWith("/stock-solutions/plan") && response.request().postDataJSON().recipe.liters === 20);
  await page.locator("#configLiters").fill("20");
  await returned;
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  const outdated = page.waitForResponse((response) => response.url().endsWith("/stock-solutions/plan") && response.request().postDataJSON().recipe.liters === 40);
  release();
  await (await outdated).finished();
  await page.evaluate(() => new Promise((resolve) => globalThis.requestAnimationFrame(resolve)));
  assert.match(await page.locator("#stockContext").innerText(), /20 L/);
  assert.match(await page.locator("#stockBatchDose").innerText(), /200 mL C/);
  await page.unroute("**/stock-solutions/plan", delayedPlan);

  await page.locator("#configLiters").fill("200");
  await page.locator("#stockStatus", { hasText: "Export blocked" }).waitFor();
  assert.equal(await page.locator("#copyStocks").isDisabled(), true);
  assert.equal(await page.locator("#printStocks").isDisabled(), true);
  assert.match(await page.locator("#stockFindings").innerText(), /less stock/);
  await page.locator("#stockVolume").fill("2");
  await page.locator("#updateStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  assert.match(await page.locator("#stockBatchDose").innerText(), /2000 mL C/);
  await page.locator("#printStocks").click();
  assert.match(await page.locator("#stockPrintSheet").textContent(), /2000 mL C.*200 L FINAL/);
  await page.locator("#closeStocks").click();
  await page.unroute(recipeUrl, recipeHandler);
}

async function assertStockCopyAndControls(page) {
  assert.equal(await page.locator("#stockWater, #stockTemperature, #stockSources, #stockReferences").count(), 0);
  const readingUrls = [
    "https://scienceinhydroponics.com/2017/09/five-things-you-should-know-when-mixing-your-own-hydroponic-liquid-nutrients.html",
    "https://www.frontiersin.org/journals/agronomy/articles/10.3389/fagro.2026.1823187/full",
  ];
  const readingHandler = (route) => route.fulfill({ contentType: "text/html", body: "<p>Reading source</p>" });
  for (const url of readingUrls) await page.context().route(url, readingHandler);
  const opened = [];
  const capture = (tab) => opened.push(tab);
  page.context().on("page", capture);
  const openedBoth = page.waitForEvent("popup", { predicate: () => opened.length === 2, timeout: 5000 });
  await page.locator("#stockReading").click();
  await openedBoth;
  assert.equal(opened.length, 2);
  await Promise.all(opened.map((tab) => tab.waitForLoadState()));
  assert.deepEqual(opened.map((tab) => tab.url()).sort(), [...readingUrls].sort());
  for (const tab of opened) {
    assert.equal(await tab.evaluate(() => globalThis.opener), null);
    await tab.close();
  }
  page.context().off("page", capture);
  for (const url of readingUrls) await page.context().unroute(url, readingHandler);
  await page.locator("#stockFactor").fill("0");
  await page.locator("#updateStocks").click();
  assert.match(await page.locator("#stockStatus").innerText(), /positive stock volumes/);
  assert.equal(await page.locator("#copyStocks").isDisabled(), true);
  await page.locator("#stockFactor").fill("50");
  await page.locator("#updateStocks").click();
  await page.waitForFunction(() => !document.querySelector("#copyStocks").disabled);
  const copied = await page.locator("#stockSolutionPanel").evaluate((panel) => {
    panel.focus();
    const selection = globalThis.getSelection();
    const range = document.createRange();
    range.selectNodeContents(panel);
    selection.removeAllRanges();
    selection.addRange(range);
    const data = new globalThis.DataTransfer();
    document.dispatchEvent(new globalThis.ClipboardEvent("copy", { clipboardData: data, cancelable: true }));
    selection.removeAllRanges();
    return { types: [...data.types], text: data.getData("text/plain") };
  });
  assert.deepEqual(copied.types, ["text/plain"]);
  assert.match(copied.text, /Stock solutions/);
  assert.doesNotMatch(copied.text, /Choose…AB|Saved preparation-water analysis/);
}

async function assertSolverStockHandoff(page) {
  const response = page.waitForResponse((response) => response.url().endsWith("/stock-solutions/plan"));
  await page.locator("#makeSolverStocks").click();
  const result = await (await response).json();
  assert.ok(result.ingredients.length > 0);
  await page.locator("#stockSolutionPanel").waitFor({ state: "visible" });
  assert.equal(await page.locator("#calculatorTable").isVisible(), false);
  await page.locator("#closeStocks").click();
  await page.locator('[data-shell-view="water"]').click();
  await page.locator("#osmosisPercent").fill("99");
  assert.equal(await page.locator("#makeSolverStocks").isDisabled(), true);
  await page.locator('[data-shell-view="solver"]').click();
}

module.exports = { assertStockWorkflow, assertSolverStockHandoff };
