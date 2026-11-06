/** Quickstart V3 (US3): progress persists across sessions and browsers. */
import { expect, expectNoCriticalA11yViolations, expectNoHorizontalScroll, signIn, test } from "./fixtures";

test("dashboard shows persistent, competency-based progress", async ({ signedIn: page, browser }) => {
  await page.goto("/modules/llm-foundations");
  await expect(page.getByRole("heading", { level: 1, name: "LLM foundations for agent engineers" })).toBeVisible();

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { level: 1, name: "My progress" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Active path" })).toBeVisible();
  await expect(page.getByText(/of \d+ competencies demonstrated/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Continue where you left off" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Next step" })).toBeVisible();
  await expectNoHorizontalScroll(page);
  await expectNoCriticalA11yViolations(page);
  const summary = await page.getByText(/of \d+ competencies demonstrated/).innerText();

  // Same learner in a fresh browser context (another device): identical progress.
  const other = await browser.newContext();
  const page2 = await other.newPage();
  await signIn(page2);
  await page2.goto("/dashboard");
  await expect(page2.getByText(summary)).toBeVisible();
  await expect(page2.getByRole("link", { name: "Continue where you left off" })).toBeVisible();

  await page2.getByRole("link", { name: "View competencies and evidence" }).click();
  await expect(page2.getByRole("heading", { level: 1, name: "Competencies" })).toBeVisible();
  await expect(page2.getByRole("rowheader", { name: /Explain how LLMs generate text/ })).toBeVisible();
  await other.close();
});
