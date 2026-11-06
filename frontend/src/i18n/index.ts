/** react-i18next setup (FR-054/FR-055): English only in the MVP, every string externalized. */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import common from "./en/common.json";

export const resources = { en: { common } } as const;

void i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  defaultNS: "common",
  interpolation: { escapeValue: false },
});

export function formatDate(value: string | Date, locale = i18n.language): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(value));
}

export function formatPercent(value: number, locale = i18n.language): string {
  return new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 }).format(value);
}

export default i18n;
