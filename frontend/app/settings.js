import { DEFAULT_LITERS, DEFAULT_THEME, THEME_OPTIONS, THEME_STORAGE_KEY } from "./constants.js";
import { qs } from "./dom.js";
import { parseDecimalInput } from "./formatting.js";
import { storageGet, storageSet } from "./storage.js";

export function createSettingsController({ units, i18n, persistPreferences, onLocaleChange }) {
  const litersInput = qs("#configLiters");
  const litersStatus = qs("#configLitersStatus");
  const volumeUnitSymbol = qs("#configVolumeUnitSymbol");
  const unitSummary = qs("#configUnitSummary");
  const volumeUnitSelect = qs("#configVolumeUnit");
  const solidDoseUnitSelect = qs("#configSolidDoseUnit");
  const liquidDoseUnitSelect = qs("#configLiquidDoseUnit");
  const themeSelect = qs("#themeSelect");
  const languageSelect = qs("#languageSelect");
  let mounted = false;

  const normalizeTheme = (theme) => THEME_OPTIONS.has(theme) ? theme : DEFAULT_THEME;

  function applyTheme(theme) {
    const nextTheme = normalizeTheme(theme);
    document.body.dataset.theme = nextTheme;
    if (themeSelect) themeSelect.value = nextTheme;
    storageSet(THEME_STORAGE_KEY, nextTheme);
    return nextTheme;
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
    i18n.onLocaleChange(() => {
      render();
      onLocaleChange();
    });
  }

  function mount(preferences = {}, definitions = {}) {
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
    i18n.setLocale(preferences.locale || i18n.getLocale(), { persist: Boolean(preferences.locale) });
    if (languageSelect) languageSelect.value = i18n.getLocale();
    bindEvents();
    render();
  }

  return { mount, render, applyTheme };
}
