/** Quickstart P3 (US4): shells, redirects, titles, focus and scroll on navigation. */
import type { Page } from "@playwright/test";
import { expect, expectNoHorizontalScroll, signIn, test } from "../fixtures";

const h1 = (page: Page) => page.getByRole("heading", { level: 1 });
const nav = (page: Page) => page.getByRole("navigation", { name: "Main" });
const h1IsFocused = (page: Page) => page.evaluate(() => document.activeElement?.tagName === "H1");

test("the old sign-up address redirects and keeps its query", async ({ page }) => {
  await page.goto("/sign-up?x=1");
  await expect(page).toHaveURL(/\/register\?x=1$/);
  await expect(h1(page)).toHaveText("Create your account");
  await expect(page).toHaveTitle("Create account · Agentic Academy");
});

test("navigation links reach their contract destinations", async ({ page }) => {
  await page.goto("/sign-in");
  await nav(page).getByRole("link", { name: "Curriculum" }).click();
  await expect(page).toHaveURL(/\/curriculum$/);
  await nav(page).getByRole("link", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/register$/);
  await nav(page).getByRole("link", { name: "Agentic Academy" }).click();
  await expect(page).toHaveURL(/:\d+\/$/);
});

test("a first load does not move focus, and in-app navigation does", async ({ page }) => {
  await page.goto("/curriculum");
  await expect(h1(page)).toBeVisible();
  expect(await h1IsFocused(page)).toBe(false);
  await expect(page).toHaveTitle("Curriculum · Agentic Academy");

  await nav(page).getByRole("link", { name: "Sign in" }).click();
  await expect(page).toHaveTitle("Sign in · Agentic Academy");
  await expect(h1(page)).toHaveText("Sign in");
  await expect(h1(page)).toBeFocused();
});

test("a redirect on first load does not move focus", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/sign-in\?next=/);
  await expect(h1(page)).toBeVisible();
  expect(await h1IsFocused(page)).toBe(false);
});

test("pages with content titles use them", async ({ page }) => {
  await signIn(page);
  await page.goto("/modules/llm-foundations");
  await expect(h1(page)).toBeVisible();
  const title = await h1(page).innerText();
  await expect(page).toHaveTitle(`${title} · Agentic Academy`);
});

test("scroll resets on new navigation, and back leaves it to the browser", async ({ page }) => {
  await signIn(page);
  await page.goto("/modules/llm-foundations");
  await expect(page.locator(".diagram svg").first()).toBeVisible({ timeout: 20_000 });

  const back = page.getByRole("link", { name: "Back to path" }).last();
  await back.scrollIntoViewIfNeeded();
  const before = await page.evaluate(() => window.scrollY);
  expect(before).toBeGreaterThan(0);
  await back.click();
  await expect(page).toHaveURL(/\/paths\//);
  await expect(h1(page)).toBeFocused();
  expect(await page.evaluate(() => window.scrollY)).toBe(0);

  await page.goBack();
  await expect(page).toHaveURL(/\/modules\/llm-foundations$/);
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  expect(await h1IsFocused(page)).toBe(false);
});

test("every shell has the skip link, main landmark and offline notice", async ({ page, context }) => {
  const check = async (path: string, expectedNav: string) => {
    await page.goto(path);
    await expect(nav(page).getByRole(expectedNav === "Sign out" ? "button" : "link", { name: expectedNav })).toBeVisible();
    await expect(page.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main");
    await expect(page.locator("main#main")).toHaveCount(1);
    await expect(page.getByRole("contentinfo")).toBeVisible();
    await context.setOffline(true);
    await expect(page.getByText("You are offline.")).toBeVisible();
    await context.setOffline(false);
    await expect(page.getByText("You are offline.")).toHaveCount(0);
  };
  await check("/sign-in", "Create account"); // public
  await check("/curriculum", "Sign in"); // session, signed out
  await signIn(page);
  await check("/dashboard", "Sign out"); // learning
  await check("/curriculum", "Sign out"); // session, signed in
});

test("the session-expiry warning survives the move to the public shell", async ({ page }) => {
  await signIn(page);
  await page.goto("/curriculum");
  await expect(nav(page).getByRole("button", { name: "Sign out" })).toBeVisible();
  await page.route("**/api/v1/me/dashboard", (route) => route.fulfill({ status: 401, json: { code: "not_authenticated" } }));
  await nav(page).getByRole("link", { name: "My progress" }).click();
  await expect(page.getByRole("alert")).toContainText("Your session expired");
  await expect(page.getByRole("alert").getByRole("link", { name: "Sign in" })).toHaveAttribute("href", /\/sign-in\?next=/);
});

test("a signed-in learner does not see the signed-out navigation flash", async ({ page }) => {
  await signIn(page);
  let release: () => void = () => {};
  const held = new Promise<void>((resolve) => (release = resolve));
  await page.route("**/api/v1/me", async (route) => {
    await held;
    await route.continue();
  });
  await page.goto("/curriculum");
  await expect(h1(page)).toBeVisible();
  await expect(nav(page).getByRole("link", { name: "Sign in" })).toHaveCount(0);
  await expect(nav(page).getByRole("link", { name: "Create account" })).toHaveCount(0);
  const pending = await page.locator(".app-header").boundingBox();

  release();
  await expect(nav(page).getByRole("button", { name: "Sign out" })).toBeVisible();
  await expect(nav(page).getByRole("link", { name: "Sign in" })).toHaveCount(0);
  const settled = await page.locator(".app-header").boundingBox();
  // At narrow widths the signed-in navigation wraps; the empty state keeps one full line.
  expect(Math.abs((settled?.height ?? 0) - (pending?.height ?? 0)) <= 1 || (page.viewportSize()?.width ?? 0) < 600).toBe(true);
  expect(pending?.height ?? 0).toBeGreaterThanOrEqual(56);
});

test("a failed session check shows no error on a public page", async ({ page }) => {
  await page.route("**/api/v1/me", (route) => route.abort());
  await page.goto("/curriculum");
  await expect(h1(page)).toBeVisible();
  await expect(nav(page).getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("every navigation control stays visible at this width", async ({ page }) => {
  await page.goto("/sign-in");
  for (const name of ["Agentic Academy", "Curriculum", "Sign in", "Create account"]) {
    await expect(nav(page).getByRole("link", { name, exact: true })).toBeInViewport();
  }
  await expectNoHorizontalScroll(page);

  await signIn(page);
  await page.goto("/dashboard");
  for (const name of ["Agentic Academy", "My progress", "Curriculum", "Account"]) {
    await expect(nav(page).getByRole("link", { name, exact: true })).toBeInViewport();
  }
  await expect(nav(page).getByRole("button", { name: "Sign out" })).toBeInViewport();
  await expectNoHorizontalScroll(page);
});

test("the not-found page links to the landing page and the curriculum", async ({ page }) => {
  await page.goto("/does-not-exist");
  await expect(h1(page)).toHaveText("We could not find this page.");
  await expect(page).toHaveTitle("We could not find this page. · Agentic Academy");
  const main = page.getByRole("main");
  await expect(main.getByRole("link", { name: "Go to the home page" })).toHaveAttribute("href", "/");
  await expect(main.getByRole("link", { name: "Curriculum" })).toHaveAttribute("href", "/curriculum");
});

test("sign-in returns to the requested page", async ({ page }) => {
  await page.goto("/modules/llm-foundations");
  await expect(page).toHaveURL(/\/sign-in\?next=/);
  await page.getByLabel("Email").fill("demo@example.com");
  await page.getByLabel("Password").fill("demo-password-123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/modules\/llm-foundations$/);
  await expect(h1(page)).toBeVisible();
});

test("sign-out lands on the landing address with the public navigation", async ({ page }) => {
  await signIn(page);
  await page.goto("/dashboard");
  await nav(page).getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/:\d+\/$/);
  await expect(nav(page).getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(nav(page).getByRole("button", { name: "Sign out" })).toHaveCount(0);
});

test("a signed-in learner gets a link to the dashboard in place of the sign-in and register forms", async ({ page }) => {
  await signIn(page);
  for (const path of ["/sign-in", "/register"]) {
    await page.goto(path);
    await expect(page.getByRole("main").getByRole("link", { name: "Go to my progress" })).toHaveAttribute("href", "/dashboard");
    await expect(page.getByLabel("Password")).toHaveCount(0);
  }
});
