/**
 * Code highlighting with the JavaScript regex engine, because the production policy (`script-src 'self'`)
 * blocks WebAssembly. Colors are CSS variables, so that tokens.css stays their only source (research R4).
 * If lessons add other languages, repeat the output comparison recorded in R4.
 */
import { createCssVariablesTheme, createHighlighterCore, type HighlighterCore, type LanguageInput } from "shiki/core";
import { createJavaScriptRegexEngine } from "shiki/engine/javascript";

const THEME = "academy";
const theme = createCssVariablesTheme({ name: THEME, variablePrefix: "--code-", fontStyle: true });

const LANGUAGES: Record<string, LanguageInput> = {
  python: () => import("shiki/langs/python.mjs"),
  json: () => import("shiki/langs/json.mjs"),
  bash: () => import("shiki/langs/bash.mjs"),
  yaml: () => import("shiki/langs/yaml.mjs"),
  typescript: () => import("shiki/langs/typescript.mjs"),
};

export const SUPPORTED_LANGUAGES = Object.keys(LANGUAGES);

let instance: Promise<HighlighterCore> | undefined;

export async function highlight(code: string, language: string): Promise<string> {
  instance ??= createHighlighterCore({ themes: [theme], langs: [], engine: createJavaScriptRegexEngine() });
  const highlighter = await instance;
  const grammar = LANGUAGES[language];
  if (!grammar) return highlighter.codeToHtml(code, { lang: "text", theme: THEME });
  if (!highlighter.getLoadedLanguages().includes(language)) await highlighter.loadLanguage(grammar);
  return highlighter.codeToHtml(code, { lang: language, theme: THEME });
}
