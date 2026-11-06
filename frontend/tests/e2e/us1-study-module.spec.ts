/** Quickstart V1 steps 2–4 (US1). */
import { expect, expectNoCriticalA11yViolations, expectNoHorizontalScroll, test } from "./fixtures";

test("signed-in learner studies Module 1", async ({ signedIn: page }) => {
  await page.goto("/paths/foundations-of-agentic-ai-engineering");
  await expect(page.getByRole("heading", { level: 1, name: "Foundations of Agentic AI Engineering" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What you will be able to do" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Before you start" })).toBeVisible();
  await expectNoCriticalA11yViolations(page);

  await page.getByRole("link", { name: "LLM foundations for agent engineers" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "LLM foundations for agent engineers" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Learning objectives" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "How language models generate text" })).toBeVisible();

  // Code example with language label and copy action (FR-009)
  const code = page.locator("figure.code-block").first();
  await expect(code).toContainText("temperature.py");
  await expect(code.getByRole("button", { name: "Copy" })).toBeVisible();

  // Diagram with text alternative (FR-014) and maturity label (FR-010)
  await expect(page.getByRole("img", { name: /Generation loop/ }).first()).toBeVisible();
  await expect(page.getByText("Established practice").first()).toBeVisible();
  await expect(page.getByText("Vendor-specific: Model providers").first()).toBeVisible();

  // References and navigation (FR-015)
  await expect(page.getByRole("heading", { name: "References" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Back to path overview" })).toBeVisible();
  await expect(page.getByText(/challenge available in a later release/)).toBeVisible();

  await expectNoHorizontalScroll(page);
  await expectNoCriticalA11yViolations(page);
});

test("modules require an account", async ({ page }) => {
  await page.goto("/modules/llm-foundations");
  await expect(page).toHaveURL(/\/sign-in\?next=/);
});
