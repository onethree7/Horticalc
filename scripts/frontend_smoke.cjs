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
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await assertNoPageOverflow(page, "desktop calculator");

    const profileFavorite = page.locator("#favoriteProfile");
    await page.locator("#favoriteProfile:disabled").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await profileFavorite.click();
    await page.locator("#favoriteProfile[aria-pressed='true']").waitFor();
    await profileFavorite.click();

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
      "monokai-classic", "windows-95", "commodore-64", "nord", "amber-crt",
    ];
    const newThemePalettes = {
      "solarized-light": { panel: "#fdf6e3", text: "#073642", solver: "#6c71c4" },
      dracula: { panel: "#282a36", text: "#f8f8f2", solver: "#ff79c6" },
      "gruvbox-dark": { panel: "#282828", text: "#fbf1c7", solver: "#d3869b" },
      "catppuccin-mocha": { panel: "#1e1e2e", text: "#cdd6f4", solver: "#cba6f7" },
      "monokai-classic": { panel: "#272822", text: "#f8f8f2", solver: "#ae81ff" },
      "windows-95": { panel: "#c0c0c0", text: "#000", solver: "#800080" },
      "commodore-64": { panel: "#40318d", text: "#c8c1ff", solver: "#c181d2" },
      nord: { panel: "#2e3440", text: "#eceff4", solver: "#b48ead" },
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

    await page.locator("[data-shell-view='editor']").click();
    await page.locator("#fertilizerEditorMode:not(.is-hidden)").waitFor();
    await page.locator("#fertilizerEditorTable thead th:last-child[title]:not([title=''])").waitFor();
    await page.locator("#fertEditorAddRow").click();
    await page.locator("#fertEditorDeleteRow").click();

    await page.locator("[data-shell-view='solver']").focus();
    await page.keyboard.press("Enter");
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    await page.locator("#favoriteProfile:disabled").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await profileFavorite.click();
    await page.locator("#favoriteProfile[aria-pressed='true']").waitFor();
    await profileFavorite.click();
    await page.locator("#loadProfile").click();
    await page.locator("#solverAllowedFromRecipe").click();

    let savedTargetPayload = null;
    let acceptedOverwriteCount = 0;
    await page.route("**/nutrient-solutions/Browser_solver_setup*", async (route) => {
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
        profiles.push({ name: savedTargetPayload.name, filename: "Browser_solver_setup.yml" });
      }
      await route.fulfill({ response, json: profiles });
    });

    await page.locator("#solverOverrides").evaluate((element) => { element.open = true; });
    const firstFixedAmount = page.locator("#solverFixedTable input").first();
    await firstFixedAmount.fill("2");
    await page.locator("#saveSolverSetup").uncheck();
    await page.locator("#solverSetupSaveWarning:not(.is-hidden)").waitFor();
    await page.locator("#profileName").fill("Browser solver setup");
    await page.locator("#saveProfile").click();
    if (dialogs.length !== 1 || !dialogs[0].includes("1")) {
      throw new Error(`Expected fixed-amount save warning, got: ${JSON.stringify(dialogs)}`);
    }
    dialogs.length = 0;
    if (savedTargetPayload) throw new Error("Dismissed target-only warning still saved the profile");

    await page.locator("#saveSolverSetup").check();
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
    await page.locator("#profileSelect").selectOption("Browser_solver_setup.yml");
    await page.locator("#loadProfile").click();
    await page.waitForFunction(() => Array.from(
      document.querySelectorAll("#solverFixedTable input"),
      (input) => Number(input.value),
    ).some((value) => value === 2));
    await page.locator("#saveSolverSetup:checked").waitFor();
    const restoredFixedValues = await page.locator("#solverFixedTable input")
      .evaluateAll((inputs) => inputs.map((input) => input.value));
    if (!restoredFixedValues.some((value) => Number(value) === 2)) {
      throw new Error(
        `Loading a target profile did not restore its fixed amount: ${JSON.stringify({
          saved: savedTargetPayload.fixed_grams,
          restored: restoredFixedValues,
        })}`,
      );
    }

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
    await page.locator("#saveSolverSetup").uncheck();
    await page.locator("#saveProfile").click();
    await waitForSmokeCondition(page, () => dialogs.length > 0, "Expected stored-setup removal warning");
    if (dialogs.length !== 1 || !dialogs[0].toLowerCase().includes("setup")) {
      throw new Error(`Expected stored-setup removal warning, got: ${JSON.stringify(dialogs)}`);
    }
    dialogs.length = 0;
    await page.locator("#saveSolverSetup").check();
    await page.locator("#solverFixedTable input").first().fill("2");

    const litersInput = page.locator("#configLiters");
    const previousVolume = Number(await litersInput.inputValue());
    await litersInput.fill(String(previousVolume * 2));
    const scaledFixedValues = (await page.locator("#solverFixedTable input")
      .evaluateAll((inputs) => inputs.map((input) => input.value))).map(Number);
    if (!scaledFixedValues.some((value) => Math.abs(value - 4) <= 0.0001)) {
      throw new Error(`Fixed amount did not scale from 2 to 4: ${JSON.stringify(scaledFixedValues)}`);
    }

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
      .filter({ has: page.locator("td:first-child", { hasText: /^K$/ }) });
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
