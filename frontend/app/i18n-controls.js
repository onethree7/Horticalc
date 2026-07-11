const t = (key, params) => i18n.t(key, params);
function normalizeTheme(theme) {
  return THEME_OPTIONS.has(theme) ? theme : DEFAULT_THEME;
}

function applyTheme(theme) {
  const nextTheme = normalizeTheme(theme);
  document.body.dataset.theme = nextTheme;
  if (themeSelect) {
    themeSelect.value = nextTheme;
  }
  return nextTheme;
}

async function initializeThemeControl() {
  let themeChanged = false;
  const activeTheme = applyTheme(lsGet(THEME_STORAGE_KEY, DEFAULT_THEME));
  lsSet(THEME_STORAGE_KEY, activeTheme);
  if (!themeSelect) {
    return;
  }
  themeSelect.addEventListener("change", (event) => {
    themeChanged = true;
    const nextTheme = applyTheme(event.target.value);
    lsSet(THEME_STORAGE_KEY, nextTheme);
    persistPreferences({ theme: nextTheme });
  });
  const preferences = await loadPreferences();
  if (themeChanged) {
    return;
  }
  const savedTheme = applyTheme(preferences.theme || activeTheme);
  lsSet(THEME_STORAGE_KEY, savedTheme);
}

async function initializeLanguageControl() {
  let localeChanged = false;
  i18n.setLocale(i18n.getLocale(), { persist: false });
  if (!languageSelect) {
    return;
  }
  languageSelect.value = i18n.getLocale();
  languageSelect.addEventListener("change", (event) => {
    localeChanged = true;
    i18n.setLocale(event.target.value);
    persistPreferences({ locale: i18n.getLocale() });
  });
  const preferences = await loadPreferences();
  if (!localeChanged && preferences.locale) {
    i18n.setLocale(preferences.locale);
  }
}

function refreshLocalizedUi() {
  updateLitersDisplay();
  refreshApiStatusLabel();
  updateLiveResultBar();
  setProfileMode(currentProfileMode);
  renderWaterProfileOptions();
  if (currentShellView === "editor") {
    renderFertilizerEditor();
  } else if (currentShellView === "solver") {
    renderSolverAllowedOptions();
    renderSolverFixedTable();
    renderSolverTargetsTable();
    renderSolverResults(lastSolveResult);
  } else if (currentShellView === "water") {
    renderWaterTable();
  } else {
    renderSelectionTable();
    renderCalculatorTable();
    if (lastCalculation) {
      renderCalculation(lastCalculation, { resultCurrent: calculatorResultCurrent });
    } else {
      renderWaterSummaryTable(waterSummaryTable, {});
      renderOxideSummaryTable(oxideSummaryTable, {});
      renderIonSummaryTable(ionSummaryTable, {});
    }
  }
}
