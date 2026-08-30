import {
  DEFAULT_LITERS,
  DEFAULT_THEME,
  DEFAULT_UI_SCALE,
  FALLBACK_UI_SCALES,
  THEME_STORAGE_KEY,
} from "./constants.js";
import { qs } from "./dom.js";
import { storageGet, storageSet } from "./storage.js";

export function createSettingsController({
  units,
  i18n,
  persistPreferences,
  onLocaleChange,
  onUnitsChange = () => {},
  clearSolverHistory = async () => {},
  onSolverHistoryChange = () => {},
  reportError = () => {},
}) {
  const litersInput = qs("#configLiters");
  const litersStatus = qs("#configLitersStatus");
  const volumeUnitSymbol = qs("#configVolumeUnitSymbol");
  const unitSummary = qs("#configUnitSummary");
  const volumeUnitSelect = qs("#configVolumeUnit");
  const solidDoseUnitSelect = qs("#configSolidDoseUnit");
  const liquidDoseUnitSelect = qs("#configLiquidDoseUnit");
  const themeSelect = qs("#themeSelect");
  const languageSelect = qs("#languageSelect");
  const uiScaleSelect = qs("#uiScaleSelect");
  const solverHistoryLimitInput = qs("#solverHistoryLimit");
  const clearSolverHistoryButton = qs("#clearSolverHistory");
  const solverHistorySettingsStatus = qs("#solverHistorySettingsStatus");
  let mounted = false;
  let solverHistoryLimit = 1000;
  let themeOptions = new Set([DEFAULT_THEME]);
  let defaultTheme = DEFAULT_THEME;
  let uiScales = [...FALLBACK_UI_SCALES];
  let defaultUiScale = DEFAULT_UI_SCALE;
  let uiScale = DEFAULT_UI_SCALE;

  const normalizeTheme = (theme) => themeOptions.has(theme) ? theme : defaultTheme;

  function themeTranslationKey(theme) {
    return `theme.${theme.split("-").map((part, index) => index === 0 ? part : `${part[0].toUpperCase()}${part.slice(1)}`).join("")}`;
  }

  function renderPreferenceOptions(options = {}) {
    const themes = Array.isArray(options.themes) && options.themes.length ? options.themes : [DEFAULT_THEME];
    themeOptions = new Set(themes);
    defaultTheme = themeOptions.has(options.defaultTheme) ? options.defaultTheme : themes[0];
    themeSelect?.replaceChildren(...themes.map((theme) => {
      const option = document.createElement("option");
      option.value = theme;
      option.dataset.i18n = themeTranslationKey(theme);
      option.textContent = i18n.t(option.dataset.i18n);
      return option;
    }));
    const locales = Array.isArray(options.locales) && options.locales.length
      ? options.locales
      : i18n.supportedLocales;
    languageSelect?.replaceChildren(...locales.map((locale) => {
      const option = document.createElement("option");
      option.value = locale;
      option.dataset.i18n = `language.${locale}`;
      option.textContent = i18n.t(option.dataset.i18n);
      return option;
    }));
    const configuredUiScales = Array.isArray(options.uiScales)
      ? options.uiScales.filter((scale) => Number.isInteger(scale) && scale > 0)
      : [];
    uiScales = configuredUiScales.length ? configuredUiScales : [...FALLBACK_UI_SCALES];
    defaultUiScale = options.defaultUiScale;
    if (!uiScales.includes(defaultUiScale)) {
      defaultUiScale = uiScales.includes(DEFAULT_UI_SCALE) ? DEFAULT_UI_SCALE : uiScales[0];
    }
    uiScaleSelect?.replaceChildren(...uiScales.map((scale) => {
      const option = document.createElement("option");
      option.value = String(scale);
      option.textContent = `${scale}%`;
      return option;
    }));
  }

  function applyTheme(theme) {
    const nextTheme = normalizeTheme(theme);
    document.body.dataset.theme = nextTheme;
    if (themeSelect) themeSelect.value = nextTheme;
    storageSet(THEME_STORAGE_KEY, nextTheme);
    return nextTheme;
  }

  function applyUiScale(scale) {
    const numericScale = Number(scale);
    uiScale = uiScales.includes(numericScale) ? numericScale : defaultUiScale;
    document.documentElement.style.setProperty("--app-ui-scale", String(uiScale / 100));
    if (uiScaleSelect) uiScaleSelect.value = String(uiScale);
    return uiScale;
  }

  function changeUiScale(direction) {
    const currentIndex = uiScales.indexOf(uiScale);
    const nextIndex = Math.min(uiScales.length - 1, Math.max(0, currentIndex + direction));
    const nextScale = uiScales[nextIndex];
    if (nextScale === uiScale) return;
    persistPreferences({ ui_scale: applyUiScale(nextScale) });
  }

  function handleUiScaleShortcut(event) {
    if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
    const isReset = event.key === "0";
    const isIncrease = event.key === "+" || event.key === "=" || event.code === "NumpadAdd";
    const isDecrease = event.key === "-" || event.key === "_" || event.code === "NumpadSubtract";
    if (!isReset && !isIncrease && !isDecrease) return;
    event.preventDefault();
    if (isReset) {
      persistPreferences({ ui_scale: applyUiScale(defaultUiScale) });
    } else {
      changeUiScale(isIncrease ? 1 : -1);
    }
  }

  function handleUiScaleWheel(event) {
    if (!(event.ctrlKey || event.metaKey) || event.altKey || event.deltaY === 0) return;
    event.preventDefault();
    changeUiScale(event.deltaY < 0 ? 1 : -1);
  }

  function renderOptions(select, definitions, selected) {
    if (!select) return;
    select.replaceChildren(...definitions.map((definition) => {
      const option = document.createElement("option");
      option.value = definition.key;
      option.textContent = definition.symbol;
      option.title = definition.label;
      return option;
    }));
    select.value = selected;
  }

  function render() {
    const volumeDefinition = units.getVolumeUnitDefinition();
    const displayValue = units.formatVolumeValue(units.litersToDisplayVolume(units.liters));
    if (litersInput) litersInput.value = displayValue;
    if (litersStatus) {
      litersStatus.setAttribute(
        "aria-label",
        `${i18n.t("config.solutionLiters")} ${displayValue} ${volumeDefinition.symbol}`,
      );
    }
    if (volumeUnitSymbol) volumeUnitSymbol.textContent = volumeDefinition.symbol;
    if (unitSummary) {
      unitSummary.textContent = [
        volumeDefinition.symbol,
        units.getMassUnitDefinition().symbol,
        units.getLiquidVolumeUnitDefinition().symbol,
      ].join(" · ");
    }
    renderOptions(volumeUnitSelect, units.volumeUnits, units.volumeUnit);
    renderOptions(solidDoseUnitSelect, units.massUnits, units.solidDoseUnit);
    renderOptions(liquidDoseUnitSelect, units.liquidVolumeUnits, units.liquidDoseUnit);
  }

  function bindEvents() {
    if (mounted) return;
    mounted = true;
    themeSelect?.addEventListener("change", (event) => {
      persistPreferences({ theme: applyTheme(event.target.value) });
    });
    languageSelect?.addEventListener("change", (event) => {
      i18n.setLocale(event.target.value);
      persistPreferences({ locale: i18n.getLocale() });
    });
    uiScaleSelect?.addEventListener("change", (event) => {
      persistPreferences({ ui_scale: applyUiScale(event.target.value) });
    });
    window.addEventListener("keydown", handleUiScaleShortcut);
    window.addEventListener("wheel", handleUiScaleWheel, { passive: false });
    litersInput?.addEventListener("input", (event) => {
      const liters = units.displayVolumeToLiters(event.target.value);
      if (liters === null || liters <= 0) return;
      units.setLiters(liters, { scaleBatch: true, recalculate: true, invalidateSolver: true });
      persistPreferences({ default_liters: liters });
      render();
    });
    litersInput?.addEventListener("change", render);
    volumeUnitSelect?.addEventListener("change", (event) => {
      units.setVolumeUnit(event.target.value);
      persistPreferences({ volume_unit: units.volumeUnit });
      render();
      onUnitsChange();
    });
    solidDoseUnitSelect?.addEventListener("change", (event) => {
      units.setSolidDoseUnit(event.target.value, true);
      persistPreferences({ solid_dose_unit: units.solidDoseUnit });
      render();
    });
    liquidDoseUnitSelect?.addEventListener("change", (event) => {
      units.setLiquidDoseUnit(event.target.value, true);
      persistPreferences({ liquid_dose_unit: units.liquidDoseUnit });
      render();
    });
    solverHistoryLimitInput?.addEventListener("change", async (event) => {
      const rawValue = String(event.target.value).trim();
      const value = Number(rawValue);
      if (!rawValue || !Number.isInteger(value) || value < 0 || value > 10000) {
        event.target.value = String(solverHistoryLimit);
        return;
      }
      if (value === 0 && solverHistoryLimit !== 0 && !window.confirm(i18n.t("history.confirmDisable"))) {
        event.target.value = String(solverHistoryLimit);
        return;
      }
      solverHistoryLimit = value;
      await persistPreferences({ solver_history_limit: value });
      solverHistorySettingsStatus.textContent = i18n.t("history.limitSaved");
      onSolverHistoryChange();
    });
    clearSolverHistoryButton?.addEventListener("click", async () => {
      if (!window.confirm(i18n.t("history.confirmClear"))) return;
      try {
        await clearSolverHistory(i18n.t("errors.clearSolverHistory"));
        solverHistorySettingsStatus.textContent = i18n.t("history.cleared");
        onSolverHistoryChange();
      } catch (error) {
        reportError(error, i18n.t("errors.clearSolverHistory"));
      }
    });
    i18n.onLocaleChange(() => {
      render();
      onLocaleChange();
    });
  }

  function mount(preferences = {}, definitions = {}, preferenceOptions = {}) {
    renderPreferenceOptions(preferenceOptions);
    units.configure(definitions);
    units.setVolumeUnit(preferences.volume_unit);
    units.setSolidDoseUnit(preferences.solid_dose_unit);
    units.setLiquidDoseUnit(preferences.liquid_dose_unit);
    units.setLiters(preferences.default_liters || DEFAULT_LITERS, {
      scaleBatch: false,
      recalculate: false,
      invalidateSolver: false,
    });
    applyTheme(preferences.theme || storageGet(THEME_STORAGE_KEY, DEFAULT_THEME));
    applyUiScale(preferences.ui_scale ?? defaultUiScale);
    i18n.setLocale(preferences.locale || i18n.getLocale(), { persist: Boolean(preferences.locale) });
    if (languageSelect) languageSelect.value = i18n.getLocale();
    solverHistoryLimit = Number.isInteger(preferences.solver_history_limit)
      ? preferences.solver_history_limit
      : 1000;
    if (solverHistoryLimitInput) solverHistoryLimitInput.value = String(solverHistoryLimit);
    bindEvents();
    render();
  }

  return { mount, render, applyTheme };
}
