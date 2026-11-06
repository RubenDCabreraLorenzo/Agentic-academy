import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "build", "coverage", "node_modules", "src/api/schema.ts", "test-results", "playwright-report", "*.min.js"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.strict],
    files: ["**/*.{ts,tsx}"],
    languageOptions: { ecmaVersion: 2022, globals: { ...globals.browser, ...globals.node } },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // Visual values come from tokens. The only allowed exception is a value computed from data and
      // passed as a custom property (for example --progress), with an inline eslint-disable comment.
      "no-restricted-syntax": [
        "error",
        { selector: "JSXAttribute[name.name='style']", message: "Use tokens and shared classes instead of inline styles (design tokens contract, rule 1)." },
      ],
    },
  },
  { files: ["tests/e2e/**/*.ts"], rules: { "react-hooks/rules-of-hooks": "off" } },
);
