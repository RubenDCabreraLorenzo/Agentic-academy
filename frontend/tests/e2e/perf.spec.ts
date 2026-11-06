/** NFR-003: module page readable < 2 s p95; knowledge-check feedback < 1 s p95 (local measurement). */
import { expect, test } from "./fixtures";

function p95(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil(0.95 * sorted.length) - 1)] ?? 0;
}

test("module pages become readable and feedback returns within budget", async ({ signedIn: page }, info) => {
  test.skip(info.project.name !== "desktop", "measured once, on the desktop project");
  const readable: number[] = [];
  for (let i = 0; i < 10; i++) {
    const start = Date.now();
    await page.goto("/modules/llm-foundations");
    await expect(page.getByRole("heading", { name: "How language models generate text" })).toBeVisible();
    readable.push(Date.now() - start);
  }
  const feedback: number[] = [];
  await page.goto("/knowledge-checks/llm-foundations-check");
  for (let i = 0; i < 7; i++) {
    const card = page.locator(".question");
    await expect(card.getByText(`Question ${i + 1} of 7`)).toBeVisible();
    const first = card.locator("input").first();
    if (await first.count()) await first.check();
    const selects = card.locator("select");
    for (let j = 0; j < (await selects.count()); j++) await selects.nth(j).selectOption({ index: 1 });
    const start = Date.now();
    await card.getByRole("button", { name: "Check answer" }).click();
    await expect(card.getByRole("status")).toBeVisible();
    feedback.push(Date.now() - start);
    const next = page.getByRole("button", { name: "Next question" });
    if (await next.isVisible()) await next.click();
  }
  const result = { module_readable_p95_ms: p95(readable), feedback_p95_ms: p95(feedback) };
  console.log("PERF", JSON.stringify(result));
  expect(result.module_readable_p95_ms).toBeLessThan(2000);
  expect(result.feedback_p95_ms).toBeLessThan(1000);
});
