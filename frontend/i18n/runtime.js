(function () {
  const DEFAULT_LOCALE = "de";
  const LOCALE_STORAGE_KEY = "horticalc.locale";
  const catalogs = window.HORTICALC_I18N || {};
  const supportedLocales = ["de", "en", "nl", "es", "zh"];
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => root.querySelectorAll(selector);

  function isSupportedLocale(locale) {
    return supportedLocales.includes(locale) && catalogs[locale];
  }

  function readStoredLocale() {
    try {
      return localStorage.getItem(LOCALE_STORAGE_KEY) || DEFAULT_LOCALE;
    } catch (error) {
      return DEFAULT_LOCALE;
    }
  }

  function writeStoredLocale(locale) {
    try {
      localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    } catch (error) {
      // Ignore unavailable localStorage; the active page language still changes.
    }
  }

  function normalizeLocale(locale) {
    return isSupportedLocale(locale) ? locale : DEFAULT_LOCALE;
  }

  let currentLocale = normalizeLocale(readStoredLocale());

  function interpolate(text, params) {
    return String(text).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, key) =>
      Object.prototype.hasOwnProperty.call(params || {}, key) ? String(params[key]) : match
    );
  }

  function t(key, params = {}) {
    const activeCatalog = catalogs[currentLocale] || {};
    const fallbackCatalog = catalogs[DEFAULT_LOCALE] || {};
    const value = Object.prototype.hasOwnProperty.call(activeCatalog, key)
      ? activeCatalog[key]
      : fallbackCatalog[key] || key;
    return interpolate(value, params);
  }

  function applyDomTranslations(root = document) {
    qsa("[data-i18n]", root).forEach((element) => {
      element.textContent = t(element.dataset.i18n);
    });
    qsa("[data-i18n-placeholder]", root).forEach((element) => {
      element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
    });
    qsa("[data-i18n-aria-label]", root).forEach((element) => {
      element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
    });
    qsa("[data-i18n-title]", root).forEach((element) => {
      element.setAttribute("title", t(element.dataset.i18nTitle));
    });
  }

  function setLocale(locale, { persist = true } = {}) {
    currentLocale = normalizeLocale(locale);
    document.documentElement.lang = currentLocale;
    if (persist) {
      writeStoredLocale(currentLocale);
    }
    const select = qs("#languageSelect");
    if (select) {
      select.value = currentLocale;
    }
    applyDomTranslations();
    window.dispatchEvent(new CustomEvent("horticalc:localechange", { detail: { locale: currentLocale } }));
  }

  function getLocale() {
    return currentLocale;
  }

  function validateCatalogs() {
    const baseKeys = Object.keys(catalogs[DEFAULT_LOCALE] || {}).sort();
    const results = {};
    supportedLocales.forEach((locale) => {
      const keys = Object.keys(catalogs[locale] || {}).sort();
      results[locale] = {
        missing: baseKeys.filter((key) => !keys.includes(key)),
        extra: keys.filter((key) => !baseKeys.includes(key)),
      };
    });
    return results;
  }

  window.HorticalcI18n = {
    DEFAULT_LOCALE,
    LOCALE_STORAGE_KEY,
    supportedLocales,
    t,
    setLocale,
    getLocale,
    applyDomTranslations,
    validateCatalogs,
  };

  document.documentElement.lang = currentLocale;
})();
