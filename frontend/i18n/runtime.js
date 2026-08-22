import de from "./de.js";
import en from "./en.js";
import es from "./es.js";
import nl from "./nl.js";
import zh from "./zh.js";

export const DEFAULT_LOCALE = "en";
export const LOCALE_STORAGE_KEY = "horticalc.locale";
const catalogs = { de, en, es, nl, zh };
export let supportedLocales = Object.keys(catalogs);
const listeners = new Set();

export function configureSupportedLocales(locales) {
  if (!Array.isArray(locales)) return;
  const configured = locales.filter((locale) => typeof locale === "string" && catalogs[locale]);
  if (configured.length) supportedLocales = configured;
}

function isSupportedLocale(locale) {
  return supportedLocales.includes(locale) && catalogs[locale];
}

function readStoredLocale() {
  try {
    return localStorage.getItem(LOCALE_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredLocale(locale) {
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // The active page language still changes when storage is unavailable.
  }
}

export function normalizeLocale(locale) {
  return isSupportedLocale(locale) ? locale : DEFAULT_LOCALE;
}

export function detectBrowserLocale(languages = navigator.languages, language = navigator.language) {
  const browserLocales = Array.isArray(languages) && languages.length ? languages : [language];
  for (const locale of browserLocales) {
    const candidate = String(locale || "").trim().toLowerCase().split(/[-_]/, 1)[0];
    if (isSupportedLocale(candidate)) return candidate;
  }
  return DEFAULT_LOCALE;
}

let currentLocale = normalizeLocale(readStoredLocale() || detectBrowserLocale());

function interpolate(text, params) {
  return String(text).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(params || {}, key) ? String(params[key]) : match
  );
}

export function t(key, params = {}) {
  const activeCatalog = catalogs[currentLocale] || {};
  const fallbackCatalog = catalogs[DEFAULT_LOCALE] || {};
  const value = Object.prototype.hasOwnProperty.call(activeCatalog, key)
    ? activeCatalog[key]
    : fallbackCatalog[key] || key;
  return interpolate(value, params);
}

export function applyDomTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((element) => {
    const params = element.dataset.i18nCount ? { count: element.dataset.i18nCount } : {};
    element.textContent = t(element.dataset.i18n, params);
  });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const params = element.dataset.i18nCount ? { count: element.dataset.i18nCount } : {};
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder, params));
  });
  root.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
  root.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.setAttribute("title", t(element.dataset.i18nTitle));
  });
}

export function setLocale(locale, { persist = true } = {}) {
  currentLocale = normalizeLocale(locale);
  document.documentElement.lang = currentLocale;
  if (persist) writeStoredLocale(currentLocale);
  const select = document.querySelector("#languageSelect");
  if (select) select.value = currentLocale;
  applyDomTranslations();
  listeners.forEach((listener) => listener(currentLocale));
}

export function getLocale() {
  return currentLocale;
}

export function onLocaleChange(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

document.documentElement.lang = currentLocale;
