/** Quickstart P1 (US1): one dark, legible environment, whatever the system prefers. */
import type { Page } from "@playwright/test";
import { expect, expectNoCriticalA11yViolations, expectNoSeriousA11yViolations, signIn, test } from "../fixtures";

const CANVAS = "rgb(14, 16, 20)";

function background(page: Page, selector: string) {
  return page.locator(selector).first().evaluate((el) => getComputedStyle(el).backgroundColor);
}

for (const colorScheme of ["light", "dark"] as const) {
  test.describe(`with a ${colorScheme} system preference`, () => {
    test.use({ colorScheme });

    test("every surface follows the product theme", async ({ page }) => {
      await signIn(page);
      await expect.poll(() => background(page, "body")).toBe(CANVAS);

      await page.goto("/modules/llm-foundations");
      await expect(page.locator("figure.code-block .shiki").first()).toBeVisible({ timeout: 20_000 });
      await expect(page.locator(".diagram svg").first()).toBeVisible({ timeout: 20_000 });
      expect(await background(page, "body")).toBe(CANVAS);
      await expectNoSeriousA11yViolations(page);

      await page.goto("/challenges/apply-temperature");
      const editor = page.locator(".cm-editor");
      await expect(editor).toBeVisible();
      expect(await background(page, ".cm-editor")).not.toBe("rgb(255, 255, 255)");
      await expectNoSeriousA11yViolations(page);
    });
  });
}

test("the editor has an accessible name on its editable element", async ({ page }) => {
  await signIn(page);
  await page.goto("/challenges/apply-temperature");
  await expect(page.locator(".cm-content").first()).toHaveAttribute("aria-label", /sampling\.py/);
});

test("controls show distinct hover and focus states", async ({ page }) => {
  await page.goto("/sign-in");
  const button = page.getByRole("button", { name: "Sign in" });
  const rest = await button.evaluate((el) => getComputedStyle(el).backgroundColor);
  await button.hover();
  await expect.poll(() => button.evaluate((el) => getComputedStyle(el).backgroundColor)).not.toBe(rest);

  await page.mouse.move(0, 0);
  await page.getByLabel("Password").focus();
  await page.keyboard.press("Tab");
  await expect
    .poll(() => page.evaluate(() => getComputedStyle(document.activeElement as Element).outlineStyle))
    .toBe("solid");
});

test("screens that had no audit findings stay clean", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  await expectNoSeriousA11yViolations(page);
});
