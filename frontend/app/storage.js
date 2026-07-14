export function storageGet(key, fallback, storage = globalThis.localStorage) {
  try {
    const raw = storage?.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function storageSet(key, value, storage = globalThis.localStorage) {
  try {
    storage?.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}
