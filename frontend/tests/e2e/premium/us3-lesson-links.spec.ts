/** Quickstart P5 steps 1–2 (US3; SC-007): links reach their lesson, and it stays in place. */
import type { Page } from "@playwright/test";
import { expect, signIn, test } from "../fixtures";

const MODULE = "/modules/llm-foundations";

/** The target is at the top of the viewport, clear of anything fixed, and has focus. */
async function expectLessonInPlace(page: Page, id: string) {
  const section = page.locator(`section#${id}`);
  await expect(section).toBeFocused({ timeout: 15_000 });
  await expect.poll(async () => (await section.boundingBox())?.y ?? -1).toBeGreaterThanOrEqual(0);
  await expect.poll(async () => (await section.boundingBox())?.y ?? 999).toBeLessThan(40);
}

async function expectEveryDiagramDrawn(page: Page) {
  await expect(page.locator(".diagram").first()).toBeAttached({ timeout: 15_000 });
  const figures = await page.locator(".diagram").count();
  await expect(page.locator(".diagram svg")).toHaveCount(figures, { timeout: 12_000 });
}

test("every diagram is drawn, load after load", async ({ page }) => {
  // A race left a diagram on its placeholder on 10 of 25 loads, with no error.
  await signIn(page);
  for (let load = 0; load < 6; load++) {
    await page.goto(MODULE);
    await expectEveryDiagramDrawn(page);
  }
});

test("a direct load reaches the section and stays there as code and diagrams render", async ({ page }) => {
  await signIn(page);
  await page.goto(`${MODULE}#lesson-structured-output`);
  await expectLessonInPlace(page, "lesson-structured-output");
  await expect(page.locator(".diagram svg").first()).toBeAttached({ timeout: 20_000 });
  await page.waitForTimeout(3_200);
  await expectLessonInPlace(page, "lesson-structured-output");
});

test("the module's contents links follow the same path", async ({ page }) => {
  await signIn(page);
  await page.goto(MODULE);
  const link = page.getByRole("navigation", { name: "In this module" }).first().getByRole("link").last();
  const href = (await link.getAttribute("href")) as string;
  await link.click();
  await expect(page).toHaveURL(new RegExp(`${href}$`));
  await expectLessonInPlace(page, href.split("#")[1] as string);
});

test("Review in the lesson reaches the section", async ({ signedIn: page }) => {
  await page.goto("/knowledge-checks/llm-foundations-check");
  const card = page.locator(".question");
  await expect(card).toBeVisible();
  // Questions come in any order, and feedback links to the lesson whatever the answer was.
  const options = card.locator("label.option");
  if (await options.count()) await options.first().click();
  for (const select of await card.locator("select").all()) await select.selectOption({ index: 1 });
  await card.getByRole("button", { name: "Check answer" }).click();
  const review = page.getByRole("link", { name: "Review in the lesson" });
  const href = (await review.getAttribute("href")) as string;
  await review.click();
  await expect(page).toHaveURL(new RegExp(`${href}$`));
  await expectLessonInPlace(page, href.split("#")[1] as string);
});

test("the learner's own scrolling is not fought", async ({ page }) => {
  await signIn(page);
  await page.goto(`${MODULE}#lesson-structured-output`);
  await expectLessonInPlace(page, "lesson-structured-output");
  await page.mouse.move(100, 300);
  await page.mouse.wheel(0, 600);
  await expect.poll(async () => (await page.locator("section#lesson-structured-output").boundingBox())?.y ?? 0).toBeLessThan(-300);
  await page.waitForTimeout(1_000);
  expect((await page.locator("section#lesson-structured-output").boundingBox())?.y ?? 0).toBeLessThan(-300);
});

test("an unknown fragment raises no error", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await signIn(page);
  await page.goto(`${MODULE}#lesson-does-not-exist`);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.goto(`${MODULE}#%E0%A4%A`);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(errors).toEqual([]);
});

test("no identifier repeats on the module page, and each lesson is named by its heading", async ({ page }) => {
  await signIn(page);
  await page.goto(MODULE);
  await expectEveryDiagramDrawn(page);
  const repeated = await page.evaluate(() => {
    const ids = [...document.querySelectorAll("main [id]")].map((el) => el.id);
    return ids.filter((id, i) => ids.indexOf(id) !== i);
  });
  expect(repeated).toEqual([]);
  const section = page.locator("section#lesson-structured-output");
  await expect(section).toHaveAttribute("aria-labelledby", "lesson-structured-output-title");
  await expect(page.locator("h2#lesson-structured-output-title")).toHaveCount(1);
});
