import AxeBuilder from "@axe-core/playwright";
import { expect, test as base, type Page } from "@playwright/test";

export const DEMO = { email: "demo@example.com", password: "demo-password-123" };

export async function signIn(page: Page) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(DEMO.email);
  await page.getByLabel("Password").fill(DEMO.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}

/** Fails on critical accessibility violations (NFR-001, SC-007). */
export async function expectNoCriticalA11yViolations(page: Page) {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  const critical = results.violations.filter((v) => v.impact === "critical");
  expect(critical, JSON.stringify(critical.map((v) => ({ id: v.id, nodes: v.nodes.length })), null, 2)).toEqual([]);
}

/** NFR-002: no horizontal page scroll at the current viewport. */
export async function expectNoHorizontalScroll(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
}

/** Resets the demo learner's progress in the introductory path through the real reset API (FR-043). */
export async function resetProgress(page: Page) {
  const csrf = (await page.context().cookies()).find((c) => c.name === "aa_csrf")?.value ?? "";
  const r = await page.request.delete("/api/v1/me/paths/foundations-of-agentic-ai-engineering/progress", {
    data: { confirm: "RESET" },
    headers: { "X-CSRF-Token": csrf },
  });
  expect(r.status()).toBe(204);
}

export const test = base.extend<{ signedIn: Page }>({
  signedIn: async ({ page }, use) => {
    await signIn(page);
    await resetProgress(page);
    await use(page);
  },
});
export { expect };
