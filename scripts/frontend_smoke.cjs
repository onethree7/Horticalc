const { chromium } = require("playwright");
const fs = require("node:fs");
const { URL } = require("node:url");

const baseUrl = process.env.HORTICALC_TEST_URL || "http://127.0.0.1:8765";
const browserCandidates = process.platform === "win32"
  ? [
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    ]
  : ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"];
const executablePath = process.env.HORTICALC_BROWSER_PATH
  || browserCandidates.find((candidate) => fs.existsSync(candidate));

async function assertNoPageOverflow(page, label) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  if (dimensions.scrollWidth > dimensions.clientWidth + 1) {
    throw new Error(`${label} has horizontal page overflow: ${JSON.stringify(dimensions)}`);
  }
}

async function assertProfilePickerLayout(page, selector, expectedStacked, label) {
  const layout = await page.locator(selector).evaluate((select) => {
    const row = select.closest(".profile-picker-row");
    const actions = row?.querySelector(".profile-picker-actions");
    if (!row || !actions) return null;
    const rowRect = row.getBoundingClientRect();
    const selectRect = select.getBoundingClientRect();
    const actionsRect = actions.getBoundingClientRect();
    return {
      contained: selectRect.left >= rowRect.left - 1 && selectRect.right <= rowRect.right + 1,
      rowClientWidth: row.clientWidth,
      rowScrollWidth: row.scrollWidth,
      stacked: actionsRect.top >= selectRect.bottom - 1,
    };
  });
  if (!layout || !layout.contained || layout.rowScrollWidth > layout.rowClientWidth + 1) {
    throw new Error(`${label} overflows its picker row: ${JSON.stringify(layout)}`);
  }
  if (layout.stacked !== expectedStacked) {
    throw new Error(`${label} stacked state was ${layout.stacked}, expected ${expectedStacked}`);
  }
}

async function assertSelectedOptionTooltip(page, selector, label) {
  const select = page.locator(selector);
  const selectedText = (await select.locator("option:checked").innerText()).trim();
  const title = await select.getAttribute("title");
  if (title !== selectedText) {
    throw new Error(`${label} tooltip was ${JSON.stringify(title)}, expected ${JSON.stringify(selectedText)}`);
  }
}

async function assertProfilePickerBreakpoints(page, selector, label) {
  for (const [width, expectedStacked] of [[1280, false], [960, true], [640, true]]) {
    await page.setViewportSize({ width, height: 900 });
    await assertProfilePickerLayout(
      page,
      selector,
      expectedStacked,
      `${label} at ${width}px`,
    );
  }
  await page.setViewportSize({ width: 1280, height: 900 });
}

async function assertHistoryPreviewLayout(page, historyEntry) {
  if (await historyEntry.getAttribute("title")) {
    throw new Error("Solver history row still exposes a competing native tooltip");
  }
  await historyEntry.hover();
  const historyPreview = page.locator(".solver-history-preview:not(.is-hidden)");
  await historyPreview.waitFor();
  const previewLayout = await historyPreview.evaluate((element) => ({
    overflow: element.ownerDocument.defaultView.getComputedStyle(element).overflow,
    scrollHeight: element.scrollHeight,
    clientHeight: element.clientHeight,
  }));
  if (previewLayout.overflow !== "hidden" || previewLayout.scrollHeight > previewLayout.clientHeight + 1) {
    throw new Error(`Solver history hover preview is scrollable: ${JSON.stringify(previewLayout)}`);
  }
}

async function assertThemePalette(page, theme, expected) {
  const palette = await page.locator("body").evaluate((element) => {
    const styles = element.ownerDocument.defaultView.getComputedStyle(element);
    return {
      panel: styles.getPropertyValue("--app-panel").trim(),
      text: styles.getPropertyValue("--app-text").trim(),
      solver: styles.getPropertyValue("--app-solver").trim(),
    };
  });
  if (Object.entries(expected).some(([token, value]) => palette[token] !== value)) {
    throw new Error(`${theme} palette was not applied: ${JSON.stringify(palette)}`);
  }
}

async function waitForSmokeCondition(page, predicate, errorMessage) {
  for (let attempt = 0; attempt < 20 && !predicate(); attempt += 1) {
    await page.waitForTimeout(25);
  }
  if (!predicate()) {
    throw new Error(typeof errorMessage === "function" ? errorMessage() : errorMessage);
  }
}

async function exerciseProfileFavorite(page, button) {
  if (await button.getAttribute("aria-pressed") === "true") {
    await button.click();
    await page.locator("#favoriteProfile[aria-pressed='false']").waitFor();
  }
  await button.click();
  await page.locator("#favoriteProfile[aria-pressed='true']").waitFor();
  await button.click();
}

async function assertCrossViewLocalization(page) {
  const languageSelect = page.locator("#languageSelect");
  const originalLocale = await languageSelect.inputValue();
  const calculatorTypeCell = page.locator("#fertilizerSelectTable tbody td:nth-child(3)").first();

  await languageSelect.selectOption("zh");
  const chineseType = (await calculatorTypeCell.innerText()).trim();
  const germanType = new Map([
    ["固体", "Fest"],
    ["液体", "Flüssig"],
  ]).get(chineseType);
  if (!germanType) {
    throw new Error(`Calculator type was not localized in Chinese: ${JSON.stringify(chineseType)}`);
  }

  await page.locator("[data-shell-view='solver']").click();
  await page.locator("#solverMode:not(.is-hidden)").waitFor();
  await languageSelect.selectOption("de");
  await page.locator("[data-shell-view='fertilizers']").click();
  await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
  const refreshedType = (await calculatorTypeCell.innerText()).trim();
  if (refreshedType !== germanType) {
    throw new Error(`Calculator type stayed stale after returning from Solver: ${JSON.stringify({
      expected: germanType,
      actual: refreshedType,
    })}`);
  }

  await languageSelect.selectOption("zh");
  await page.locator("[data-shell-view='solver']").click();
  await page.locator("#solverMode:not(.is-hidden)").waitFor();
  const firstPriority = (await page.locator("#solverTargetsTable select").first()
    .locator("option").first().innerText()).trim();
  if (firstPriority !== "1 · 必须") {
    throw new Error(`Solver priority stayed stale after returning from Calculator: ${JSON.stringify(firstPriority)}`);
  }

  await languageSelect.selectOption(originalLocale);
  await page.locator("[data-shell-view='fertilizers']").click();
  await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
}

async function exerciseTargetProfileLoadModes(page, getLoadCount, savedFixedGrams) {
  await page.locator("#profileSelect").selectOption("Browser_solver_setup.yml");
  await page.locator("#includeSolverSetup").uncheck();
  await page.locator("#loadProfile").click();
  await waitForSmokeCondition(
    page,
    () => getLoadCount() === 1,
    "Target-only profile load did not complete",
  );
  if (await page.locator("#solverFixedTable input").count()) {
    throw new Error("Target-only profile load unexpectedly restored the Solver setup");
  }
  if (await page.locator("#includeSolverSetup").isChecked()) {
    throw new Error("Target-only profile load changed the setup checkbox");
  }

  await page.locator("#includeSolverSetup").check();
  await page.locator("#loadProfile").click();
  await page.waitForFunction(() => Array.from(
    document.querySelectorAll("#solverFixedTable input"),
    (input) => Number(input.value),
  ).some((value) => value === 2));
  if (getLoadCount() !== 2) {
    throw new Error(`Setup profile load count was ${getLoadCount()}, expected 2`);
  }
  const restoredFixedValues = await page.locator("#solverFixedTable input")
    .evaluateAll((inputs) => inputs.map((input) => input.value));
  if (!restoredFixedValues.some((value) => Number(value) === 2)) {
    throw new Error(
      `Loading a target profile did not restore its fixed amount: ${JSON.stringify({
        saved: savedFixedGrams,
        restored: restoredFixedValues,
      })}`,
    );
  }
}

(async () => {
  if (!executablePath) {
    throw new Error("Chrome or Chromium is required; set HORTICALC_BROWSER_PATH if it is installed elsewhere");
  }
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  const dialogs = [];
  const smokeHistory = [];
  let acceptNextDialog = false;
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource:")) {
      errors.push(message.text());
    }
  });
  page.on("dialog", async (dialog) => {
    dialogs.push(dialog.message());
    if (acceptNextDialog) {
      acceptNextDialog = false;
      await dialog.accept();
    } else {
      await dialog.dismiss();
    }
  });

  await page.route("**/preferences", async (route) => {
    if (route.request().method() !== "PUT") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: route.request().postData() || "{}",
    });
  });
  await page.route("**/solver-history**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (request.method() === "DELETE") {
      smokeHistory.splice(0, smokeHistory.length, ...smokeHistory.filter((entry) => entry.pinned));
      await route.fulfill({ status: 200, contentType: "application/json", body: '{"status":"ok"}' });
      return;
    }
    if (request.method() === "PUT") {
      const entryId = decodeURIComponent(pathname.split("/").pop());
      const entry = smokeHistory.find(({ id }) => id === entryId);
      if (entry) entry.pinned = Boolean(request.postDataJSON().pinned);
      await route.fulfill({
        status: entry ? 200 : 404,
        contentType: "application/json",
        body: JSON.stringify(entry ? { status: "ok", pinned: entry.pinned } : { detail: "not found" }),
      });
      return;
    }
    if (pathname === "/solver-history") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          limit: 1000,
          entries: [...smokeHistory].sort((left, right) => Number(right.pinned) - Number(left.pinned)).map((entry) => ({
            id: entry.id,
            created_at: entry.created_at,
            pinned: Boolean(entry.pinned),
            liters: entry.result.liters,
            solver_model: entry.result.solver_model,
            targets_mg_per_l: {
              N_total: entry.result.targets_mg_per_l.N_total || 0,
              P: entry.result.targets_mg_per_l.P || 0,
              K: entry.result.targets_mg_per_l.K || 0,
            },
            fertilizer_count: entry.result.fertilizers.length,
          })),
        }),
      });
      return;
    }
    const entryId = decodeURIComponent(pathname.split("/").pop());
    const entry = smokeHistory.find(({ id }) => id === entryId);
    await route.fulfill({
      status: entry ? 200 : 404,
      contentType: "application/json",
      body: JSON.stringify(entry || { detail: "not found" }),
    });
  });

  try {
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    await page.locator("#apiStatus[data-state]:not([data-state='loading'])").waitFor();
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    const apiState = await page.locator("#apiStatus").getAttribute("data-state");
    if (apiState !== "ready") {
      throw new Error(`API startup state was ${apiState}: ${await page.locator("#apiStatus").innerText()}`);
    }
    const health = await page.evaluate(() => globalThis.fetch("/health").then((response) => response.json()));
    const displayedVersion = await page.locator("#appVersion").innerText();
    if (displayedVersion !== `v${health.version}`) {
      throw new Error(`Displayed version was ${displayedVersion}, expected v${health.version}`);
    }
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await assertNoPageOverflow(page, "desktop calculator");

    const profileFavorite = page.locator("#favoriteProfile");
    await page.locator("#favoriteProfile:disabled").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await assertSelectedOptionTooltip(page, "#profileSelect", "calculator profile picker");
    await assertProfilePickerBreakpoints(page, "#profileSelect", "calculator profile picker");
    await exerciseProfileFavorite(page, profileFavorite);
    await page.locator("#loadProfile").click();

    await page.locator("#calculateBtn").click();
    await page.locator("#copyCalculatorResults:not([disabled])").waitFor();

    const volumeUnit = page.locator("#configVolumeUnit");
    if (await volumeUnit.locator("option").count() > 1) {
      await volumeUnit.selectOption({ index: 1 }, { force: true });
      if (await volumeUnit.inputValue() === "") throw new Error("Volume unit selection was not applied");
    }

    const themes = [
      "horticalc-dark", "horticalc-light", "high-contrast", "soil",
      "gch-classic", "vt-green", "blue-matrix", "tokyo-night",
      "solarized-light", "dracula", "gruvbox-dark", "catppuccin-mocha",
      "monokai-classic", "windows-95", "amber-crt",
    ];
    const newThemePalettes = {
      "solarized-light": { panel: "#fdf6e3", text: "#073642", solver: "#6c71c4" },
      dracula: { panel: "#282a36", text: "#f8f8f2", solver: "#ff79c6" },
      "gruvbox-dark": { panel: "#282828", text: "#fbf1c7", solver: "#d3869b" },
      "catppuccin-mocha": { panel: "#1e1e2e", text: "#cdd6f4", solver: "#cba6f7" },
      "monokai-classic": { panel: "#272822", text: "#f8f8f2", solver: "#ae81ff" },
      "windows-95": { panel: "#c0c0c0", text: "#000", solver: "#800080" },
      "amber-crt": { panel: "#0b0700", text: "#ffc247", solver: "#ff8f1f" },
    };
    for (const theme of themes) {
      await page.locator("#themeSelect").selectOption(theme, { force: true });
      const appliedTheme = await page.locator("body").getAttribute("data-theme");
      if (appliedTheme !== theme) throw new Error(`Theme ${theme} was not applied`);
      if (newThemePalettes[theme]) await assertThemePalette(page, theme, newThemePalettes[theme]);
    }

    await page.locator("[data-shell-view='water']").click();
    await page.locator("#waterSection:not(.is-hidden)").waitFor();
    await page.locator("#waterProfileSelect").selectOption({ index: 1 });
    await assertSelectedOptionTooltip(page, "#waterProfileSelect", "water profile picker");
    await assertProfilePickerBreakpoints(page, "#waterProfileSelect", "water profile picker");

    await page.locator("[data-shell-view='editor']").click();
    await page.locator("#fertilizerEditorMode:not(.is-hidden)").waitFor();
    await page.locator("#fertilizerEditorTable thead th:last-child[title]:not([title=''])").waitFor();
    await page.locator("#fertEditorAddRow").click();
    await page.locator("#fertEditorDeleteRow").click();

    await page.locator("[data-shell-view='solver']").focus();
    await page.keyboard.press("Enter");
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await page.locator("#deleteProfile:disabled").waitFor();
    await exerciseProfileFavorite(page, profileFavorite);
    await page.locator("#loadProfile").click();
    await page.locator("#solverAllowedFromRecipe").click();

    let savedTargetPayload = null;
    let savedTargetLoadCount = 0;
    let acceptedOverwriteCount = 0;
    await page.route("**/nutrient-solutions/Browser_solver_setup*", async (route) => {
      if (route.request().method() === "DELETE") {
        savedTargetPayload = null;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok", filename: "Browser_solver_setup.yml" }),
        });
        return;
      }
      savedTargetLoadCount += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(savedTargetPayload || {}),
      });
    });
    await page.route("**/nutrient-solutions", async (route) => {
      if (route.request().method() === "POST") {
        const requestPayload = route.request().postDataJSON();
        if (savedTargetPayload && !requestPayload.overwrite) {
          await route.fulfill({
            status: 409,
            contentType: "application/json",
            body: JSON.stringify({
              detail: {
                code: "nutrient_solution_exists",
                name: savedTargetPayload.name,
                filename: "Browser_solver_setup.yml",
                has_solver_setup: true,
              },
            }),
          });
          return;
        }
        const storedPayload = { ...requestPayload };
        delete storedPayload.overwrite;
        if (requestPayload.overwrite) acceptedOverwriteCount += 1;
        savedTargetPayload = storedPayload;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ok", filename: "Browser_solver_setup.yml" }),
        });
        return;
      }
      const response = await route.fetch();
      const profiles = await response.json();
      if (savedTargetPayload) {
        profiles.push({
          name: savedTargetPayload.name,
          filename: "Browser_solver_setup.yml",
          deletable: true,
        });
      }
      await route.fulfill({ response, json: profiles });
    });

    await page.locator("#solverOverrides").evaluate((element) => { element.open = true; });
    const firstFixedAmount = page.locator("#solverFixedTable input").first();
    await firstFixedAmount.fill("2");
    await page.locator("#includeSolverSetup").uncheck();
    await page.locator("#solverSetupSaveWarning:not(.is-hidden)").waitFor();
    await page.locator("#profileName").fill("Browser solver setup");
    await page.locator("#saveProfile").click();
    if (dialogs.length !== 1 || !dialogs[0].includes("1")) {
      throw new Error(`Expected fixed-amount save warning, got: ${JSON.stringify(dialogs)}`);
    }
    dialogs.length = 0;
    if (savedTargetPayload) throw new Error("Dismissed target-only warning still saved the profile");

    await page.locator("#includeSolverSetup").check();
    await page.locator("#saveProfile").click();
    await page.locator("#profileSelect option", { hasText: "Browser solver setup" })
      .waitFor({ state: "attached" });
    if (!savedTargetPayload?.water_profile || savedTargetPayload.liters <= 0) {
      throw new Error(`Saved Solver setup is incomplete: ${JSON.stringify(savedTargetPayload)}`);
    }
    if (Object.values(savedTargetPayload.fixed_grams || {}).length !== 1) {
      throw new Error(`Saved fixed amounts are incomplete: ${JSON.stringify(savedTargetPayload)}`);
    }

    await page.locator("#solverAllowedClear").click();
    if (await page.locator("#solverFixedTable input").count()) {
      throw new Error("Clearing allowed fertilizers did not clear the fixed-amount table");
    }
    await exerciseTargetProfileLoadModes(
      page,
      () => savedTargetLoadCount,
      savedTargetPayload.fixed_grams,
    );

    dialogs.length = 0;
    acceptNextDialog = true;
    await page.locator("#saveProfile").click();
    await waitForSmokeCondition(
      page,
      () => acceptedOverwriteCount === 1 && dialogs.length === 1,
      () => `Confirmed profile overwrite did not resubmit safely: ${JSON.stringify({
        acceptedOverwriteCount,
        dialogs,
      })}`,
    );
    dialogs.length = 0;

    await page.locator("#solverFixedTable input").first().fill("0");
    await page.locator("#includeSolverSetup").uncheck();
    await page.locator("#saveProfile").click();
    await waitForSmokeCondition(page, () => dialogs.length > 0, "Expected stored-setup removal warning");
    if (dialogs.length !== 1 || !dialogs[0].toLowerCase().includes("setup")) {
      throw new Error(`Expected stored-setup removal warning, got: ${JSON.stringify(dialogs)}`);
    }
    dialogs.length = 0;
    await page.locator("#includeSolverSetup").check();
    await page.locator("#solverFixedTable input").first().fill("2");

    const litersInput = page.locator("#configLiters");
    const previousVolume = Number(await litersInput.inputValue());
    await litersInput.fill(String(previousVolume * 2));
    const scaledFixedValues = (await page.locator("#solverFixedTable input")
      .evaluateAll((inputs) => inputs.map((input) => input.value))).map(Number);
    if (!scaledFixedValues.some((value) => Math.abs(value - 4) <= 0.0001)) {
      throw new Error(`Fixed amount did not scale from 2 to 4: ${JSON.stringify(scaledFixedValues)}`);
    }

    dialogs.length = 0;
    acceptNextDialog = true;
    await page.locator("#deleteProfile:not(:disabled)").click();
    await waitForSmokeCondition(
      page,
      () => savedTargetPayload === null && dialogs.length === 1,
      "Confirmed profile deletion did not remove the saved target",
    );
    await page.locator("#profileSelect option[value='Browser_solver_setup.yml']")
      .waitFor({ state: "detached" });
    await page.locator("#deleteProfile:disabled").waitFor();
    dialogs.length = 0;

    let solveRequestCount = 0;
    await page.route("**/solve", async (route) => {
      solveRequestCount += 1;
      const requestNumber = solveRequestCount;
      const requestPayload = route.request().postDataJSON();
      const response = await route.fetch();
      const responsePayload = await response.json();
      smokeHistory.unshift({
        schema_version: 1,
        id: `smoke-${requestNumber}`,
        created_at: new Date().toISOString(),
        setup: {
          liters: requestPayload.liters,
          targets: requestPayload.targets,
          water_profile: requestPayload.water_profile,
          fertilizers_allowed: requestPayload.fertilizers_allowed,
          fixed_grams: requestPayload.fixed_grams,
          urea_as_nh4: requestPayload.urea_as_nh4,
          solver_config: requestPayload.solver_config,
        },
        result: responsePayload,
        fertilizer_kinds: Object.fromEntries(responsePayload.fertilizers.map(({ name }) => [name, "solid"])),
        calculation: {},
        pinned: false,
      });
      if (requestNumber === 1) await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({ response, json: responsePayload });
    });
    const potassiumInput = page.locator("#solverTargetsTable tbody tr")
      .filter({ has: page.locator("td:first-child", { hasText: /^K$/ }) })
      .locator('input[type="text"]');
    await potassiumInput.fill("50");
    await page.locator("#solveBtn").click();
    await potassiumInput.fill("100");
    await page.locator("#solveBtn").click();
    await page.locator("#copySolverResults:not([disabled])").waitFor();
    const potassiumResult = page.locator("#solverTargetsResultsTable tbody tr")
      .filter({ has: page.locator("td:first-child > span", { hasText: /^K$/ }) });
    await potassiumResult.locator("td:nth-child(2)").filter({ hasText: "100" }).waitFor();
    await page.waitForTimeout(650);
    if (!(await potassiumResult.locator("td:nth-child(2)").innerText()).includes("100")) {
      throw new Error("A stale solver response replaced the latest result");
    }
    await page.locator("#applySolverToCalculatorInline").click();
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await page.locator("[data-shell-view='solver']").click();
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    const firstHistoryRow = page.locator("#solverHistoryList .rail-history-row").first();
    await firstHistoryRow.locator(".rail-history-pin").click();
    await firstHistoryRow.locator(".rail-history-pin[aria-pressed='true']").waitFor();
    const historyEntry = page.locator("#solverHistoryList .rail-history-entry").first();
    await historyEntry.waitFor();
    await assertHistoryPreviewLayout(page, historyEntry);
    await potassiumInput.fill("1");
    await historyEntry.click();
    await page.locator("#solverHistoryDialog[open]").waitFor();
    await page.locator("#solverHistoryDialogOutput", { hasText: "100" }).waitFor();
    await page.locator("#copySolverHistoryEntry").click();
    await page.locator("#solverHistoryDialogStatus:not(:empty)").waitFor();
    await page.locator("#restoreSolverHistoryEntry").click();
    await page.waitForFunction(() => {
      const row = Array.from(document.querySelectorAll("#solverTargetsTable tbody tr"))
        .find((candidate) => candidate.querySelector("td")?.textContent.trim() === "K");
      return Number(row?.querySelector('input[type="text"]')?.value) === 100;
    });
    if (!(await page.locator("#copySolverResults").isDisabled())) {
      throw new Error("Restoring solver history unexpectedly retained a solved result");
    }
    dialogs.length = 0;
    acceptNextDialog = true;
  await page.locator(".rail-settings").evaluate((element) => { element.open = true; });
  await page.locator("#clearSolverHistory").click();
  await page.locator("#solverHistoryCount", { hasText: /^1$/ }).waitFor();
  await page.locator("#solverHistoryList .rail-history-pin[aria-pressed='true']").waitFor();
    dialogs.length = 0;
    await page.locator("[data-shell-view='fertilizers']").click();
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await assertCrossViewLocalization(page);

    for (const width of [900, 600, 500]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(50);
      await assertNoPageOverflow(page, `${width}px layout`);
      if (width === 500) {
        await page.locator("#solverHistoryList .rail-history-entry").first().click();
        await page.locator("#solverHistoryDialog[open]").waitFor();
        await page.locator("#solverHistoryDialog form button[value='close']").click();
        await page.locator("#solverHistoryDialog").waitFor({ state: "hidden" });
      }
    }

    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
