const assert = require("node:assert/strict");
const fs = require("node:fs");
const { URL } = require("node:url");
const { chromium } = require("playwright");

const browserCandidates = process.platform === "win32"
  ? ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"]
  : ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"];
const executablePath = process.env.HORTICALC_BROWSER_PATH
  || browserCandidates.find((candidate) => fs.existsSync(candidate));
const selectedFertilizer = "Yara Tera CALCINIT";
const allowedStorageKey = "last_fertilizers_allowed::global";

async function calculationReady(page) {
  await page.locator("#copyCalculatorResults:not([disabled])").waitFor({ state: "attached" });
}

async function assertSolverSelection(page) {
  await page.locator('[data-shell-view="solver"]').click();
  assert.deepEqual(await page.locator("#solverAllowedFertilizers input:checked")
    .evaluateAll((inputs) => inputs.map((input) => input.value)), [selectedFertilizer]);
  const selected = page.locator(`#solverAllowedFertilizers input[value="${selectedFertilizer}"]`);
  await selected.uncheck();
  assert.deepEqual(await page.evaluate((key) => JSON.parse(globalThis.localStorage.getItem(key)), allowedStorageKey), []);
  await selected.check();
  await page.reload();
  await page.locator('#apiStatus[data-state="ready"]').waitFor();
  await page.locator('[data-shell-view="solver"]').click();
  assert.equal(await selected.isChecked(), true);
}

async function assertCatalogPruning(page) {
  const catalog = await (await page.request.get("/fertilizers")).json();
  const withoutSelected = catalog.filter(({ name }) => name !== selectedFertilizer);
  const handler = (route) => route.fulfill({ json: withoutSelected });
  await page.route("**/fertilizers", handler);
  await page.locator('[data-shell-view="editor"]').click();
  await page.locator("#fertEditorLoad").click();
  await page.waitForFunction(() => !Array.from(document.querySelectorAll(
    '#fertilizerEditorTable input[data-field="name"]',
  )).some((input) => input.value === "Yara Tera CALCINIT"));
  assert.deepEqual(await page.evaluate((key) => JSON.parse(globalThis.localStorage.getItem(key)), allowedStorageKey), []);
  await page.unroute("**/fertilizers", handler);
  await page.locator("#fertEditorLoad").click();
  await page.waitForFunction(() => Array.from(document.querySelectorAll(
    '#fertilizerEditorTable input[data-field="name"]',
  )).some((input) => input.value === "Yara Tera CALCINIT"));
  await page.locator('[data-shell-view="solver"]').click();
  await page.locator(`#solverAllowedFertilizers input[value="${selectedFertilizer}"]`).check();
}

async function assertTraceScaling(page) {
  await page.locator('[data-shell-view="fertilizers"]').click();
  await page.locator(".rail-settings").evaluate((details) => { details.open = true; });
  const volume = page.locator("#configLiters");
  await volume.fill("1");
  const fertilizer = page.locator("#fertilizerSelectTable .searchable-combobox-input").first();
  await fertilizer.fill("Calcinit");
  await fertilizer.press("Enter");
  const amount = page.locator("#calculatorTable tbody input").first();
  await amount.fill("0.0002");
  await calculationReady(page);
  await page.locator("#calculatorScaleUp").click();
  await calculationReady(page);
  assert.ok(Math.abs(Number(await amount.inputValue()) / 0.00021 - 1) < 1e-10);
  await volume.fill("2");
  await calculationReady(page);
  assert.ok(Math.abs(Number(await amount.inputValue()) / 0.00042 - 1) < 1e-10);
  await volume.fill("1");
  await calculationReady(page);
  await page.locator("#calculatorScaleDown").click();
  await calculationReady(page);
  assert.equal(Number(await amount.inputValue()), 0.0002);
}

async function assertWaterEditing(page) {
  await page.locator('[data-shell-view="water"]').click();
  await page.locator("#osmosisPercent").fill("0");
  await calculationReady(page);
  const ordinary = page.waitForResponse((response) => response.url().endsWith("/calculate")
    && response.request().postDataJSON().water_mg_l.Ca === 123);
  await page.locator('[data-water-key="Ca"]').fill("123");
  assert.equal(await page.locator("#copyCalculatorResults").isDisabled(), true);
  const result = await (await ordinary).json();
  assert.ok(Math.abs(result.water_elements_mg_per_l.Ca - 123) < 1e-10);
  await calculationReady(page);
  const masses = await (await page.request.get("/molar-masses")).json();
  const bicarbonate = 2 * 17.848 * masses.HCO3 / (masses.CaCO3 / 2);
  const helper = page.waitForResponse((response) => response.url().endsWith("/calculate")
    && Math.abs(response.request().postDataJSON().water_mg_l.HCO3 - bicarbonate) < 1e-10);
  const hardness = page.locator('[data-water-key="KH"]');
  await hardness.fill("2");
  await hardness.press("Enter");
  await helper;
  await calculationReady(page);
  assert.equal(Number(await hardness.inputValue()), 0);
  const selected = await page.locator("#waterProfileSelect").inputValue();
  await page.locator("#languageSelect").selectOption("de");
  assert.equal(await page.locator("#waterProfileSelect").inputValue(), selected);
  assert.equal(Number(await page.locator('[data-water-key="Ca"]').inputValue()), 123);
  await page.locator("#languageSelect").selectOption("en");

  const profiles = await (await page.request.get("/water-profiles")).json();
  let updatedProfiles = [...profiles, { name: "Refresh", filename: "Refresh.yml" }];
  const collectionHandler = (route) => route.fulfill({
    json: route.request().method() === "GET" ? updatedProfiles : { status: "ok" },
  });
  await page.route("**/water-profiles", collectionHandler);
  await page.locator("#waterProfileName").fill("State test");
  await page.locator("#saveWaterProfile").click();
  await page.locator('#waterProfileSelect option[value="Refresh.yml"]').waitFor({ state: "attached" });
  assert.equal(await page.locator("#waterProfileSelect").inputValue(), selected);
  updatedProfiles = [];
  await page.locator("#saveWaterProfile").click();
  await page.waitForFunction(() => document.querySelector("#waterProfileSelect").options.length === 1);
  assert.equal(await page.locator("#waterProfileSelect").inputValue(), "");
  updatedProfiles = profiles;
  await page.locator("#saveWaterProfile").click();
  await page.locator('#waterProfileSelect option[value="default.yml"]').waitFor({ state: "attached" });
  await page.unroute("**/water-profiles", collectionHandler);
  await page.locator("#waterProfileSelect").selectOption("default.yml");
  await page.locator("#loadWaterProfile").click();
  await calculationReady(page);
}

async function assertWaterPhosphorus(page) {
  const masses = await (await page.request.get("/molar-masses")).json();
  const cases = [
    { P: 5 },
    { PO4: 5 * masses.PO4 / masses.P },
    { P: 2, PO4: 3 * masses.PO4 / masses.P },
    { P2O5: 5 * masses.P2O5 / (2 * masses.P) },
  ];
  for (const [index, mgPerL] of cases.entries()) {
    const saved = await page.request.post("/water-profiles", {
      data: { name: `Phosphorus ${index}`, mg_per_l: mgPerL, osmosis_percent: 25 },
    });
    assert.equal(saved.ok(), true, await saved.text());
  }
  await page.reload();
  await page.locator('#apiStatus[data-state="ready"]').waitFor();
  await page.locator('[data-shell-view="water"]').click();
  const assertLoaded = async (name) => {
    await page.locator("#waterProfileSelect").selectOption({ label: name });
    const calculated = page.waitForResponse((response) => response.url().endsWith("/calculate")
      && response.request().postDataJSON().water_mg_l.P > 0);
    await page.locator("#loadWaterProfile").click();
    const response = await calculated;
    const request = response.request().postDataJSON();
    assert.ok(Math.abs(request.water_mg_l.P - 5) < 1e-10);
    assert.equal(request.water_mg_l.PO4, 0);
    assert.ok(Math.abs((await response.json()).water_elements_mg_per_l.P - 3.75) < 1e-10);
    await calculationReady(page);
  };
  for (const index of cases.keys()) {
    await assertLoaded(`Phosphorus ${index}`);
    const name = `Phosphorus roundtrip ${index}`;
    await page.locator("#waterProfileName").fill(name);
    await page.locator("#saveWaterProfile").click();
    await page.locator("#waterProfileSelect option").filter({ hasText: name }).waitFor({ state: "attached" });
    await assertLoaded(name);
  }
  await page.locator("#waterProfileSelect").selectOption("default.yml");
  await page.locator("#loadWaterProfile").click();
  await calculationReady(page);
}

async function assertSolverInvalidation(page) {
  await page.locator('[data-shell-view="solver"]').click();
  await page.locator("#solverMode details.solver-advanced-config").evaluate((details) => { details.open = true; });
  await page.locator("#solverAutoApply").uncheck();
  await page.locator("#solverTargetsTable tbody input").first().fill("155");
  await page.locator("#solveBtn").click();
  await page.locator("#copySolverResults:not([disabled])").waitFor();
  await page.locator("#solverTargetScaleUp").click();
  for (const id of ["copySolverResults", "saveSolverAsRecipe", "applySolverToCalculatorInline", "makeSolverStocks"]) {
    assert.equal(await page.locator(`#${id}`).isDisabled(), true, id);
  }
  let release;
  const held = new Promise((resolve) => { release = resolve; });
  const handler = async (route) => {
    const response = await route.fetch();
    const targets = route.request().postDataJSON().targets;
    assert.equal(targets.N_NH4, 0);
    assert.equal(targets.N_UREA, 0);
    await held;
    await route.fulfill({ response });
  };
  await page.route("**/solve", handler);
  const requested = page.waitForRequest("**/solve");
  await page.locator("#solveBtn").click();
  await requested;
  await page.locator("#solverTargetScaleDown").click();
  const response = page.waitForResponse((item) => item.url().endsWith("/solve"));
  release();
  await (await response).finished();
  await page.waitForTimeout(100);
  assert.equal(await page.locator("#copySolverResults").isDisabled(), true);
  assert.equal(await page.locator("#solverTargetsResultsTable tbody tr").count(), 0);
  await page.unroute("**/solve", handler);
  await page.locator("#solveBtn").click();
  await page.locator("#copySolverResults:not([disabled])").waitFor();
}

async function assertProfileLoadIdentity(page, getPreferences) {
  const waterSaved = await page.request.post("/water-profiles", {
    data: { name: "Delayed water", mg_per_l: { Ca: 43 } },
  });
  assert.equal(waterSaved.ok(), true, await waterSaved.text());
  const waterFile = (await waterSaved.json()).filename;
  const recipeFiles = [];
  for (const [index, label] of ["A", "B"].entries()) {
    const saved = await page.request.post("/recipes", { data: {
      name: `Delayed recipe ${label}`,
      liters: (index + 1) * 11,
      water_profile: index === 0 ? waterFile : "default",
      fertilizers: [{ name: selectedFertilizer, grams: index + 1 }],
      fertilizers_allowed: index === 0 ? [selectedFertilizer] : [],
    } });
    assert.equal(saved.ok(), true, await saved.text());
    recipeFiles.push((await saved.json()).filename);
  }
  await page.reload();
  await page.locator('#apiStatus[data-state="ready"]').waitFor();
  await calculationReady(page);
  const origin = new URL(page.url()).origin;
  const withDelayedResponse = async (path, start, changeSelection) => {
    let markRequested;
    let release;
    const requested = new Promise((resolve) => { markRequested = resolve; });
    const held = new Promise((resolve) => { release = resolve; });
    const url = `${origin}${path}`;
    const handler = async (route) => {
      const response = await route.fetch();
      markRequested();
      await held;
      await route.fulfill({ response });
    };
    await page.route(url, handler);
    await start();
    await requested;
    await changeSelection();
    const received = page.waitForResponse(url);
    release();
    await (await received).finished();
    await page.evaluate(() => new Promise((resolve) => {
      globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(resolve));
    }));
    await page.unroute(url, handler);
  };
  const beforeLiters = await page.locator("#configLiters").inputValue();
  const beforeName = await page.locator("#profileName").inputValue();
  const startRecipe = async () => {
    await page.locator("#profileSelect").selectOption(recipeFiles[0]);
    await page.locator("#loadProfile").click();
  };
  for (const path of [`/recipes/${recipeFiles[0]}`, `/water-profiles/${waterFile}`]) {
    await withDelayedResponse(path, startRecipe, () => page.locator("#profileSelect").selectOption(recipeFiles[1]));
    assert.equal(await page.locator("#configLiters").inputValue(), beforeLiters);
    assert.equal(await page.locator("#profileName").inputValue(), beforeName);
    assert.equal(await page.evaluate((key) => globalThis.localStorage.getItem(key),
      `last_fertilizers_allowed::${recipeFiles[0]}`), null);
  }
  await page.locator('[data-shell-view="solver"]').click();
  await page.locator("#includeSolverSetup").check();
  const solutions = await (await page.request.get("/nutrient-solutions")).json();
  const first = solutions.find(({ name }) => name === "Ignored objectives mass_nnls").filename;
  const second = solutions.find(({ name }) => name === "Ignored objectives hierarchical").filename;
  const beforeTarget = await page.locator("#solverTargetsTable tbody input").first().inputValue();
  const beforeSolutionName = await page.locator("#profileName").inputValue();
  const startSolution = async () => {
    await page.locator("#profileSelect").selectOption(first);
    await page.locator("#loadProfile").click();
  };
  for (const path of [`/nutrient-solutions/${first}`, "/water-profiles/default"]) {
    await withDelayedResponse(path, startSolution, () => page.locator("#profileSelect").selectOption(second));
    assert.equal(await page.locator("#solverTargetsTable tbody input").first().inputValue(), beforeTarget);
    assert.equal(await page.locator("#profileName").inputValue(), beforeSolutionName);
  }
  await page.locator('[data-shell-view="water"]').click();
  const beforeCalcium = await page.locator('[data-water-key="Ca"]').inputValue();
  const beforePreference = getPreferences().last_water_profile;
  await withDelayedResponse(`/water-profiles/${waterFile}`, async () => {
    await page.locator("#waterProfileSelect").selectOption(waterFile);
    await page.locator("#loadWaterProfile").click();
  }, () => page.locator("#waterProfileSelect").selectOption("default.yml"));
  assert.equal(await page.locator('[data-water-key="Ca"]').inputValue(), beforeCalcium);
  assert.equal(getPreferences().last_water_profile, beforePreference);
  await page.locator('[data-shell-view="fertilizers"]').click();
  for (const [index, filename] of recipeFiles.entries()) {
    await page.locator("#profileSelect").selectOption(filename);
    await page.locator("#loadProfile").click();
    await page.waitForFunction((liters) => Number(document.querySelector("#configLiters").value) === liters,
      (index + 1) * 11);
    assert.equal(await page.locator("#profileName").inputValue(), `Delayed recipe ${index === 0 ? "A" : "B"}`);
    assert.deepEqual(await page.evaluate((key) => JSON.parse(globalThis.localStorage.getItem(key)),
      `last_fertilizers_allowed::${filename}`), index === 0 ? [selectedFertilizer] : []);
  }
  await calculationReady(page);
}

async function assertHistoryDialogRequests(page) {
  const entries = ["A", "B", "C", "D"].map((id, index) => ({
    id,
    created_at: "2026-01-01T00:00:00Z",
    liters: (index + 1) * 10,
    targets_mg_per_l: { N_total: 101 + index },
  }));
  const pending = new Map();
  for (const id of ["A", "C", "D"]) {
    let markRequested;
    let release;
    const requested = new Promise((resolve) => { markRequested = resolve; });
    const response = new Promise((resolve) => { release = resolve; });
    pending.set(id, { requested, response, markRequested, release });
  }
  const origin = new URL(page.url()).origin;
  await page.route(`${origin}/solver-history`, (route) => route.fulfill({ json: { entries, limit: 1000 } }));
  await page.route(`${origin}/solver-history/*`, async (route) => {
    const id = new URL(route.request().url()).pathname.split("/").at(-1);
    const held = pending.get(id);
    if (held) {
      held.markRequested();
      await held.response;
    }
    if (id === "C") {
      await route.fulfill({ status: 500, json: { detail: "obsolete history failure" } });
      return;
    }
    const entry = entries.find((item) => item.id === id);
    await route.fulfill({ json: {
      setup: {
        liters: entry.liters,
        targets: entry.targets_mg_per_l,
        fertilizers_allowed: [selectedFertilizer],
        water_profile: { mg_per_l: {} },
      },
      result: { targets_mg_per_l: entry.targets_mg_per_l },
    } });
  });
  await page.mouse.move(0, 0);
  await page.reload();
  await page.locator('#apiStatus[data-state="ready"]').waitFor();
  const open = (id) => page.locator(`[data-history-id="${id}"]`).click();
  const close = () => page.locator("#solverHistoryDialog form button").click();
  const settle = async (id) => {
    const received = page.waitForResponse(`${origin}/solver-history/${id}`);
    pending.get(id).release();
    await (await received).finished();
    await page.evaluate(() => new Promise((resolve) => {
      globalThis.requestAnimationFrame(() => globalThis.requestAnimationFrame(resolve));
    }));
  };
  await open("A");
  await pending.get("A").requested;
  await close();
  await open("B");
  await page.locator("#restoreSolverHistoryEntry:not([disabled])").waitFor();
  const expected = await page.locator("#solverHistoryDialogOutput").innerText();
  await settle("A");
  assert.equal(await page.locator("#solverHistoryDialogOutput").innerText(), expected);
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.locator("#copySolverHistoryEntry").click();
  await page.locator("#solverHistoryDialogStatus:not(:empty)").waitFor();
  const copied = await page.evaluate(() => globalThis.navigator.clipboard.readText());
  assert.equal(copied.replaceAll("\r\n", "\n"), expected);
  await page.locator("#restoreSolverHistoryEntry").click();
  assert.equal(Number(await page.locator("#configLiters").inputValue()), 20);
  assert.equal(Number(await page.locator("#solverTargetsTable tbody input").first().inputValue()), 102);
  for (const id of ["C", "D"]) {
    await open(id);
    await pending.get(id).requested;
    await close();
    await settle(id);
    assert.equal(await page.locator("#solverHistoryDialog").evaluate((dialog) => dialog.open), false);
    assert.equal(await page.locator("#copySolverHistoryEntry").isDisabled(), true);
    assert.equal(await page.locator("#restoreSolverHistoryEntry").isDisabled(), true);
  }
  await page.locator("#solverHistoryDialog").evaluate((dialog) => {
    Object.defineProperty(dialog, "showModal", { value: undefined, configurable: true });
    Object.defineProperty(dialog, "open", { value: undefined, configurable: true });
  });
  await open("B");
  await page.locator("#restoreSolverHistoryEntry:not([disabled])").waitFor();
  assert.equal(await page.locator("#solverHistoryDialogOutput").innerText(), expected);
  await close();
  await page.locator("#solverHistoryDialog").evaluate((dialog) => {
    delete dialog.showModal;
    delete dialog.open;
  });
  await page.unroute(`${origin}/solver-history`);
  await page.unroute(`${origin}/solver-history/*`);
}

async function assertIgnoredObjectives(page, setConfig) {
  setConfig({ solver_model: "mass_nnls", ignored_elements: ["Cu"] });
  await page.reload();
  await page.locator('#apiStatus[data-state="ready"]').waitFor();
  for (const model of ["mass_nnls", "nnls_tuning", "hierarchical"]) {
    await page.locator('[data-shell-view="solver"]').click();
    await page.locator("#solverMode details.solver-advanced-config").evaluate((details) => { details.open = true; });
    await page.locator("#solverAutoApply").uncheck();
    await page.locator("#solverTargetsTable tbody input").first().fill("100");
    await page.locator("#solverTargetsTable tbody tr").filter({ hasText: /^Cu/ }).locator("input").fill("1");
    const persisted = page.waitForResponse((response) => response.url().endsWith("/preferences")
      && response.request().method() === "PUT");
    await page.locator("#solverConfigModel").selectOption(model);
    assert.deepEqual((await (await persisted).json()).solver_config.ignored_elements, ["Cu"]);
    const solved = page.waitForResponse((response) => response.url().endsWith("/solve"));
    await page.locator("#solveBtn").click();
    const response = await solved;
    const config = response.request().postDataJSON().solver_config;
    assert.deepEqual(config.ignored_elements, ["Cu"]);
    assert.equal(Object.hasOwn(config.target_priorities, "Cu"), false);
    assert.equal((await response.json()).objective_elements.includes("Cu"), false);
    await page.locator("#includeSolverSetup").check();
    await page.locator("#profileName").fill(`Ignored objectives ${model}`);
    const saved = page.waitForResponse((item) => item.url().endsWith("/nutrient-solutions")
      && item.request().method() === "POST");
    await page.locator("#saveProfile").click();
    assert.deepEqual((await saved).request().postDataJSON().solver_config.ignored_elements, ["Cu"]);
    await page.locator("#profileSelect option").filter({ hasText: `Ignored objectives ${model}` })
      .waitFor({ state: "attached" });
    await page.reload();
    await page.locator('#apiStatus[data-state="ready"]').waitFor();
  }
  await page.locator('[data-shell-view="solver"]').click();
  const copper = page.locator("#solverTargetsTable tbody tr").filter({ hasText: /^Cu/ });
  await copper.locator("input").fill("1");
  const persisted = page.waitForResponse((response) => response.url().endsWith("/preferences")
    && response.request().method() === "PUT");
  await copper.locator("select").first().selectOption("3");
  const config = (await (await persisted).json()).solver_config;
  assert.deepEqual(config.ignored_elements, []);
  assert.deepEqual(config.target_priorities.Cu, { under: 3, over: 0 });
  await page.locator("#solverMode details.solver-advanced-config").evaluate((details) => { details.open = true; });
  const reset = page.waitForResponse((response) => response.url().endsWith("/preferences")
    && response.request().method() === "PUT");
  await page.locator("#solverConfigResetDefaults").click();
  assert.deepEqual((await (await reset).json()).solver_config, {});
  await page.locator("#includeSolverSetup").check();
  await page.locator("#profileSelect").selectOption({ label: "Ignored objectives mass_nnls" });
  await page.locator("#loadProfile").click();
  await page.waitForFunction(() => document.querySelector("#solverConfigModel").value === "mass_nnls");
  const solved = page.waitForResponse((response) => response.url().endsWith("/solve"));
  await page.locator("#solveBtn").click();
  const response = await solved;
  assert.deepEqual(response.request().postDataJSON().solver_config.ignored_elements, ["Cu"]);
  assert.equal((await response.json()).objective_elements.includes("Cu"), false);
}

async function assertPreferenceFailures(page, dialogs, failWrites) {
  await page.locator(".rail-settings").evaluate((details) => { details.open = true; });
  failWrites(true);
  const limit = page.locator("#solverHistoryLimit");
  await limit.fill("25");
  await limit.press("Tab");
  await page.waitForFunction(() => document.querySelector("#solverHistoryLimit").value === "1000"
    && !document.querySelector("#solverHistoryLimit").disabled);
  assert.equal(await page.locator("#solverHistorySettingsStatus").innerText(), "");
  assert.equal(dialogs.pop(), "disk unavailable");
  const themeFailure = page.waitForEvent("dialog");
  await page.locator("#themeSelect").selectOption("soil");
  await themeFailure;
  assert.equal(await page.locator("body").getAttribute("data-theme"), "soil");
  assert.equal(dialogs.pop(), "disk unavailable");
  failWrites(false);
  await limit.fill("25");
  await limit.press("Tab");
  await page.locator("#solverHistorySettingsStatus:not(:empty)").waitFor();
  assert.equal(await limit.inputValue(), "25");
  await page.locator('[data-shell-view="fertilizers"]').click();
  await page.locator("#profileSelect").selectOption({ index: 1 });
  const favorite = page.locator("#favoriteProfile");
  const previous = await favorite.getAttribute("aria-pressed");
  failWrites(true);
  await favorite.click();
  await page.waitForFunction((value) => {
    const button = document.querySelector("#favoriteProfile");
    return !button.disabled && button.getAttribute("aria-pressed") === value;
  }, previous);
  assert.equal(dialogs.pop(), "disk unavailable");
  failWrites(false);
  await favorite.click();
  await page.waitForFunction((value) => {
    const button = document.querySelector("#favoriteProfile");
    return !button.disabled && button.getAttribute("aria-pressed") !== value;
  }, previous);
}

(async () => {
  assert.ok(executablePath, "Chrome or Chromium is required; set HORTICALC_BROWSER_PATH");
  const browser = await chromium.launch({ headless: true, executablePath });
  try {
    const baseURL = process.env.HORTICALC_TEST_URL || "http://127.0.0.1:8765";
    const page = await browser.newPage({ baseURL, viewport: { width: 1280, height: 900 } });
    const errors = [];
    const dialogs = [];
    let preferences = {};
    let failPreferences = false;
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("dialog", async (dialog) => { dialogs.push(dialog.message()); await dialog.dismiss(); });
    await page.addInitScript(({ key, fertilizer }) => {
      if (globalThis.localStorage.getItem(key) === null) {
        globalThis.localStorage.setItem(key, JSON.stringify([fertilizer, "Removed fertilizer"]));
      }
    }, { key: allowedStorageKey, fertilizer: selectedFertilizer });
    await page.route(`${new URL(baseURL).origin}/preferences`, async (route) => {
      if (route.request().method() === "PUT") {
        if (failPreferences) {
          await route.fulfill({ status: 500, json: { detail: "disk unavailable" } });
          return;
        }
        preferences = { ...preferences, ...route.request().postDataJSON() };
      }
      await route.fulfill({ json: preferences });
    });
    await page.goto(baseURL);
    await page.locator('#apiStatus[data-state="ready"]').waitFor();
    await assertSolverSelection(page);
    await assertCatalogPruning(page);
    await assertTraceScaling(page);
    await assertWaterEditing(page);
    await assertWaterPhosphorus(page);
    await assertSolverInvalidation(page);
    await assertPreferenceFailures(page, dialogs, (value) => { failPreferences = value; });
    await assertIgnoredObjectives(page, (config) => { preferences.solver_config = config; });
    await assertHistoryDialogRequests(page);
    await assertProfileLoadIdentity(page, () => preferences);
    assert.equal(await page.locator("#apiStatus").getAttribute("data-state"), "ready");
    assert.deepEqual(dialogs, []);
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
