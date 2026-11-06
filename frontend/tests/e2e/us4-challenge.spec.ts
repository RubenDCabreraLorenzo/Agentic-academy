/** Quickstart V4 (US4): hints, visible run, contained failures, passing submission. */
import type { Page } from "@playwright/test";
import { expect, expectNoCriticalA11yViolations, test } from "./fixtures";

const SOLUTION = `import math


def apply_temperature(scores, temperature):
    if temperature <= 0:
        raise ValueError("temperature must be greater than 0")
    if not scores:
        raise ValueError("scores must not be empty")
    scaled = {t: s / temperature for t, s in scores.items()}
    top = max(scaled.values())
    exps = {t: math.exp(v - top) for t, v in scaled.items()}
    total = sum(exps.values())
    return {t: v / total for t, v in exps.items()}


def most_likely(scores):
    return max(scores, key=scores.__getitem__)
`;

async function setCode(page: Page, code: string) {
  const editor = page.locator(".cm-content").first();
  await editor.click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(code);
}

async function submitAndWait(page: Page, button: "Run tests" | "Submit") {
  const before = await page.locator("#result").count();
  if (before) await expect(page.locator("#result")).not.toHaveText(/Queued|Running/);
  const prefix = button === "Submit" ? "Submission" : "Test run";
  const previous = before ? await page.locator("#result").innerText() : "";
  await page.getByRole("button", { name: button, exact: true }).click();
  // Wait until a new run has been queued, then until it reaches a final state.
  await expect(page.locator("#result")).not.toHaveText(previous, { timeout: 10_000 });
  const heading = page.getByRole("heading", { name: new RegExp(`^${prefix}: (Passed|Not passed|Stopped|Evaluation error)$`) });
  await expect(heading).toBeVisible({ timeout: 45_000 });
  return (await heading.innerText()).split(": ")[1];
}

test("learner completes the temperature challenge", async ({ signedIn: page }) => {
  const health = await (await page.request.get("/api/v1/health")).json();
  test.skip(!health.challenges_enabled, "challenge evaluation is not enabled in this environment");
  await expect.poll(async () => (await (await page.request.get("/api/v1/health")).json()).evaluation, { timeout: 30_000 }).toBe("available");

  await page.goto("/challenges/apply-temperature");
  await expect(page.getByRole("heading", { level: 1, name: "Turn model scores into sampling probabilities" })).toBeVisible();
  for (const name of ["Scenario", "Problem", "Expected outcome", "Instructions", "Evaluation criteria"]) {
    await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  }

  await page.getByRole("button", { name: "Show hint 1 of 2" }).click();
  await expect(page.getByText(/Softmax of x_i/)).toBeVisible();

  // Visible run on the starter code: criteria fail with feedback.
  expect(await submitAndWait(page, "Run tests")).toBe("Not passed");
  await expect(page.getByText(/Apply softmax to the scaled scores/)).toBeVisible();

  // Infinite loop is stopped at the time limit.
  await setCode(page, "while True:\n    pass\n");
  expect(await submitAndWait(page, "Submit")).toBe("Stopped");
  await expect(page.getByText(/ran longer than the time limit/).first()).toBeVisible();

  // Network access is a forbidden operation.
  await setCode(page, "import socket\nsocket.create_connection(('1.1.1.1', 80), timeout=1)\n");
  expect(await submitAndWait(page, "Submit")).toBe("Stopped");
  await expect(page.getByText(/forbidden operation was attempted/).first()).toBeVisible();

  // Correct solution passes and completes the challenge.
  await setCode(page, SOLUTION);
  expect(await submitAndWait(page, "Submit")).toBe("Passed");
  await expect(page.getByText("All mandatory criteria are met. The challenge is completed.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Reference explanation" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Submission 3 · Passed/ })).toBeVisible();
  await expectNoCriticalA11yViolations(page);
});
