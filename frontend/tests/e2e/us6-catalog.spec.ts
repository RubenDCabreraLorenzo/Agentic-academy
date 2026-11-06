/** Quickstart V1 step 1 (US6): public catalog with planned paths. */
import { expect, expectNoCriticalA11yViolations, expectNoHorizontalScroll, test } from "./fixtures";

test("visitor browses the catalog and inspects a planned path", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Curriculum" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Foundational" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Foundations of Agentic AI Engineering", exact: true })).toBeVisible();
  await expect(page.getByText("Not yet available").first()).toBeVisible();
  await expectNoHorizontalScroll(page);
  await expectNoCriticalA11yViolations(page);

  await page.getByRole("link", { name: "Multi-agent architectures", exact: true }).click();
  await expect(page.getByText("This path is planned and cannot be started yet.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Modules" })).toHaveCount(0);
});
