const { chromium } = require("playwright");
const fs = require("node:fs");

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

(async () => {
  if (!executablePath) {
    throw new Error("Chrome or Chromium is required; set HORTICALC_BROWSER_PATH if it is installed elsewhere");
  }
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  const dialogs = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource:")) {
      errors.push(message.text());
    }
  });
  page.on("dialog", async (dialog) => {
    dialogs.push(dialog.message());
    await dialog.dismiss();
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

  try {
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    await page.locator("#apiStatus:not([data-state='loading'])").waitFor();
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    const apiState = await page.locator("#apiStatus").getAttribute("data-state");
    if (apiState !== "ready") {
      throw new Error(`API startup state was ${apiState}: ${await page.locator("#apiStatus").innerText()}`);
    }
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();
    await assertNoPageOverflow(page, "desktop calculator");

    await page.locator("#calculateBtn").click();
    await page.locator("#copyCalculatorResults:not([disabled])").waitFor();

    const volumeUnit = page.locator("#configVolumeUnit");
    if (await volumeUnit.locator("option").count() > 1) {
      await volumeUnit.selectOption({ index: 1 }, { force: true });
      if (await volumeUnit.inputValue() === "") throw new Error("Volume unit selection was not applied");
    }

    const themes = [
      "horticalc-dark", "horticalc-light", "high-contrast", "soil",
      "gch-classic", "vt-green", "blue-matrix",
    ];
    for (const theme of themes) {
      await page.locator("#themeSelect").selectOption(theme, { force: true });
      const appliedTheme = await page.locator("body").getAttribute("data-theme");
      if (appliedTheme !== theme) throw new Error(`Theme ${theme} was not applied`);
    }

    await page.locator("[data-shell-view='water']").click();
    await page.locator("#waterSection:not(.is-hidden)").waitFor();

    await page.locator("[data-shell-view='editor']").click();
    await page.locator("#fertilizerEditorMode:not(.is-hidden)").waitFor();
    await page.locator("#fertEditorAddRow").click();
    await page.locator("#fertEditorDeleteRow").click();

    await page.locator("[data-shell-view='solver']").focus();
    await page.keyboard.press("Enter");
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await page.locator("#loadProfile").click();
    await page.locator("#solverAllowedFromRecipe").click();

    let solveRequestCount = 0;
    await page.route("**/solve", async (route) => {
      solveRequestCount += 1;
      const requestNumber = solveRequestCount;
      const response = await route.fetch();
      if (requestNumber === 1) await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({ response });
    });
    const potassiumInput = page.locator("#solverTargetsTable tbody tr")
      .filter({ has: page.locator("td:first-child", { hasText: /^K$/ }) })
      .locator("input");
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
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();

    for (const width of [900, 600, 500]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(50);
      await assertNoPageOverflow(page, `${width}px layout`);
    }

    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
