/** SC-008 / quickstart V7.3: with the runner stopped, learning keeps working and evaluation reports
 * "unavailable" while the learner's code is kept. The runner is restarted afterwards. */
import { existsSync, readFileSync } from "node:fs";
import { RUNNER_PID_FILE, startRunner } from "./global-setup";
import { expect, test } from "./fixtures";

test("learning continues while code evaluation is unavailable", async ({ signedIn: page }, info) => {
  test.skip(info.project.name !== "desktop", "stops the shared runner; run once");
  test.skip(!existsSync(RUNNER_PID_FILE), "runner not managed by this test run");
  test.setTimeout(150_000);
  const pid = Number(readFileSync(RUNNER_PID_FILE, "utf8"));
  try {
    process.kill(-pid, "SIGTERM");
    await expect
      .poll(async () => (await (await page.request.get("/api/v1/health")).json()).evaluation, { timeout: 60_000, intervals: [2_000] })
      .toBe("unavailable");

    await page.goto("/modules/llm-foundations");
    await expect(page.getByRole("heading", { name: "How language models generate text" })).toBeVisible();
    await page.goto("/knowledge-checks/llm-foundations-check");
    await expect(page.getByText("Question 1 of 7")).toBeVisible();
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Active path" })).toBeVisible();

    await page.goto("/challenges/apply-temperature");
    await page.getByRole("button", { name: "Submit", exact: true }).click();
    await expect(page.getByText(/Code evaluation is unavailable right now/)).toBeVisible();
    await page.reload();
    await expect(page.locator(".cm-content").first()).toContainText("apply_temperature");
  } finally {
    startRunner();
  }
  await expect
    .poll(async () => (await (await page.request.get("/api/v1/health")).json()).evaluation, { timeout: 60_000, intervals: [2_000] })
    .toBe("available");
});
