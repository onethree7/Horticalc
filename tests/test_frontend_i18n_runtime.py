from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_locale_runtime_detects_browser_language_and_honors_saved_choice() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required for executable frontend tests"
    script = """
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
const runtime = pathToFileURL('./frontend/i18n/runtime.js').href;

async function loadRuntime(languages, storedLocale, suffix) {
  globalThis.document = {
    documentElement: { lang: '' },
    querySelector: () => null,
    querySelectorAll: () => [],
  };
  Object.defineProperty(globalThis, 'navigator', {
    value: { languages, language: languages[0] }, configurable: true,
  });
  globalThis.localStorage = {
    getItem: () => storedLocale,
    setItem: () => undefined,
  };
  return import(`${runtime}?case=${suffix}`);
}

assert.equal((await loadRuntime(['es-MX', 'en-US'], null, 1)).getLocale(), 'es');
assert.equal((await loadRuntime(['fr-FR'], null, 2)).getLocale(), 'en');
assert.equal((await loadRuntime(['de-DE'], 'zh', 3)).getLocale(), 'zh');
"""
    subprocess.run([node, "--input-type=module", "-e", script], cwd=ROOT, check=True)
