/** Quickstart V2 (US2): feedback, failing, retrying and passing a knowledge check. */
import type { Page } from "@playwright/test";
import { expect, expectNoCriticalA11yViolations, test } from "./fixtures";

const CORRECT: Record<string, string[]> = {
  "A language model produces its answer by…": ["repeatedly predicting and sampling the next token"],
  "consistent as possible": ["A low temperature, plus validation of the returned category"],
  "Which tasks should agent code do": ["Counting the characters in an order id", "Checking whether two long ids are identical"],
  "unknown priority value": ["Retry once with the validation error, then raise a clear error"],
  "output schema allow": ["So the model is not forced to invent a value"],
};
const ORDER = [
  "Ask for JSON with explicit fields and allowed values",
  "Parse the response as JSON",
  "Validate fields and values against the schema",
  "Use the validated data in your code",
];
const MATCH: Record<string, string> = {
  "The model mentions an order id that does not exist": "Verify the value in code before acting on it",
  "The model describes last year's pricing": "Fetch current information with a tool",
  "Key instructions are ignored in a very long prompt": "Pass only the relevant parts of the documents",
};

async function answerCurrent(page: Page, correctly: boolean) {
  const card = page.locator(".question");
  const text = await card.innerText();
  if (text.includes("Put the steps")) {
    if (correctly) {
      for (let target = 0; target < ORDER.length; target++) {
        const items = await card.locator("ol.ordering li").allInnerTexts();
        let index = items.findIndex((t) => t.includes(ORDER[target] as string));
        while (index > target) {
          await card.locator("ol.ordering li").nth(index).getByRole("button", { name: /Move up/ }).click();
          index--;
        }
      }
    }
  } else if (text.includes("Match each failure mode")) {
    for (const [left, right] of Object.entries(MATCH)) {
      const options = Object.values(MATCH);
      const choice = correctly ? right : (options.find((o) => o !== right) as string);
      await card.getByLabel(`Match “${left}” with`).selectOption({ label: choice });
    }
  } else {
    const key = Object.keys(CORRECT).find((k) => text.includes(k)) as string;
    const options = await card.locator("label.option").allInnerTexts();
    const wanted = correctly ? (CORRECT[key] as string[]) : [options.find((o) => !(CORRECT[key] as string[]).includes(o.trim())) as string];
    for (const label of wanted) await card.getByLabel(label.trim(), { exact: true }).check();
  }
  await card.getByRole("button", { name: "Check answer" }).click();
  await expect(card.getByRole("status")).toBeVisible();
}

async function goNext(page: Page) {
  const next = page.getByRole("button", { name: "Next question" });
  if (await next.isVisible()) await next.click();
}

test("learner fails, reviews and passes the Module 1 check", async ({ signedIn: page }) => {
  await page.goto("/knowledge-checks/llm-foundations-check");
  await expect(page.getByText("7 questions. Pass with 70% or more.")).toBeVisible();
  await expect(page.getByText("Question 1 of 7")).toBeVisible();

  for (let i = 0; i < 7; i++) {
    await answerCurrent(page, i < 2);
    if (i === 0) {
      await expect(page.getByText(/Correct|Not quite/).first()).toBeVisible();
      await expect(page.getByRole("link", { name: "Review in the lesson" })).toBeVisible();
    }
    await goNext(page);
  }
  await page.getByRole("button", { name: "Submit answers" }).click();
  await expect(page.getByRole("heading", { name: "Not passed yet" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Objectives to review" })).toBeVisible();
  await expectNoCriticalA11yViolations(page);

  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByRole("radiogroup", { name: "Question 1 of 7" }).or(page.getByRole("group", { name: "Question 1 of 7" })).first()).toBeVisible();
  for (let i = 0; i < 7; i++) {
    await answerCurrent(page, true);
    await goNext(page);
  }
  await page.getByRole("button", { name: "Submit answers" }).click();
  await expect(page.getByRole("heading", { name: "Passed" })).toBeVisible();
  await expect(page.getByText("Score: 100%")).toBeVisible();
  await expect(page.getByText(/Complete the module's code challenge/)).toBeVisible();
});
