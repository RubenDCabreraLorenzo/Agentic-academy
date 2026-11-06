/** Quickstart V5 (US5): laboratory replay without any request leaving the application origin. */
import { expect, expectNoCriticalA11yViolations, expectNoHorizontalScroll, test } from "./fixtures";

test("learner explores traces, compares patterns and handles an approval", async ({ signedIn: page }) => {
  const external: string[] = [];
  page.on("request", (r) => {
    const url = new URL(r.url());
    if (url.hostname !== "localhost") external.push(r.url());
  });

  await page.goto("/lab/prompt-injection-and-approval");
  await expect(page.getByRole("heading", { level: 1, name: /Prompt injection/ })).toBeVisible();
  await expect(page.getByText("No language model is called")).toBeVisible();
  await expect(page.getByText("close_ticket").first()).toBeVisible();
  await expect(page.getByText("destructive").first()).toBeVisible();

  const step = page.getByRole("button", { name: "Step →" });
  for (let i = 0; i < 7; i++) await step.click();
  await expect(page.getByText("Failure case: prompt injection").or(page.getByText("Failure case: invalid tool argument")).first()).toBeAttached();
  await expect(page.getByText("Educational explanation").first()).toBeVisible();
  await expect(page.getByRole("alertdialog", { name: "Human approval required" })).toBeVisible();
  await expect(step).toBeDisabled();
  await page.getByRole("button", { name: "Reject" }).click();
  for (let i = 0; i < 3; i++) await step.click();
  await expect(page.getByText("Summary delivered; ticket left open.")).toBeVisible();
  await page.getByRole("button", { name: "← Back" }).click();
  await expect(page.getByRole("status").filter({ hasText: /Step \d+ of \d+/ })).toBeVisible();
  await expectNoHorizontalScroll(page);
  await expectNoCriticalA11yViolations(page);

  await page.goto("/lab/workflow-vs-agent-loop");
  await expect(page.getByRole("heading", { name: "Compare executions" })).toBeVisible();
  await expect(page.getByLabel("Fixed workflow")).toContainText(/Tool calls\s*2/);
  await expect(page.getByLabel("Agent loop", { exact: true })).toContainText(/Tool calls\s*3/);
  await expect(page.getByLabel("Agent loop", { exact: true }).getByText(/step\(s\) appear only in this execution/)).toBeVisible();
  await page.getByRole("button", { name: "Agent loop", exact: true }).click();
  await expect(page.getByRole("button", { name: "Agent loop", exact: true })).toHaveAttribute("aria-pressed", "true");

  expect(external, "no request may leave the application origin (no model calls)").toEqual([]);
});
