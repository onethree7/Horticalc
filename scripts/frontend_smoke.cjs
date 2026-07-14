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

(async () => {
  if (!executablePath) {
    throw new Error("Chrome or Chromium is required; set HORTICALC_BROWSER_PATH if it is installed elsewhere");
  }
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage();
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

    await page.locator("#calculateBtn").click();
    await page.locator("#copyCalculatorResults:not([disabled])").waitFor();

    await page.locator("[data-shell-view='water']").click();
    await page.locator("#waterSection:not(.is-hidden)").waitFor();

    await page.locator("[data-shell-view='editor']").click();
    await page.locator("#fertilizerEditorMode:not(.is-hidden)").waitFor();
    await page.locator("#fertEditorAddRow").click();
    await page.locator("#fertEditorDeleteRow").click();

    await page.locator("[data-shell-view='solver']").click();
    await page.locator("#solverMode:not(.is-hidden)").waitFor();
    await page.locator("#profileSelect").selectOption({ index: 1 });
    await page.locator("#loadProfile").click();
    await page.locator("#solverAllowedFromRecipe").click();
    await page.locator("#solveBtn").click();
    await page.locator("#copySolverResults:not([disabled])").waitFor();
    await page.locator("#applySolverToCalculatorInline").click();
    await page.waitForTimeout(250);
    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
    if (dialogs.length) throw new Error(`Application dialogs:\n${dialogs.join("\n")}`);
    await page.locator("#calculatorMode:not(.is-hidden)").waitFor();

    if (errors.length) throw new Error(`Browser errors:\n${errors.join("\n")}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
