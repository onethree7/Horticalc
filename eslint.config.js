import { defineConfig } from "eslint/config";

export default defineConfig([
  {
    files: ["frontend/**/*.js", "tests/frontend/**/*.mjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        AbortController: "readonly",
        Blob: "readonly",
        console: "readonly",
        document: "readonly",
        Event: "readonly",
        fetch: "readonly",
        FormData: "readonly",
        localStorage: "readonly",
        navigator: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        URL: "readonly",
        window: "readonly",
      },
    },
    rules: {
      "complexity": ["error", 30],
      "max-lines": ["error", { max: 1000, skipBlankLines: true, skipComments: true }],
      "no-undef": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", caughtErrorsIgnorePattern: "^_" }],
    },
  },
  {
    files: ["scripts/*.cjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "commonjs",
      globals: {
        console: "readonly",
        document: "readonly",
        process: "readonly",
        setTimeout: "readonly",
      },
    },
    rules: {
      "complexity": ["error", 30],
      "max-lines": ["error", { max: 1000, skipBlankLines: true, skipComments: true }],
      "no-undef": "error",
      "no-unused-vars": "error",
    },
  },
]);
