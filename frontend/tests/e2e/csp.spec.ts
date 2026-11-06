/**
 * Quickstart P10: the production build under the real security policy. The development server applies
 * no policy, which once hid that code highlighting failed (research R4). Run against the nginx image,
 * with the development server stopped: both use port 5173.
 */
import { expect, signIn, test } from "./fixtures";

test("highlighting, diagrams, editor and fonts work under the production policy", async ({ page }) => {
  const external: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (!["localhost", "127.0.0.1"].includes(url.hostname) && url.protocol.startsWith("http")) external.push(request.url());
  });
  await page.addInitScript(() => {
    const seen: string[] = [];
    (window as unknown as { __violations: string[] }).__violations = seen;
    document.addEventListener("securitypolicyviolation", (e) => seen.push(`${e.violatedDirective}: ${e.blockedURI}`));
  });
  const violations = () => page.evaluate(() => (window as unknown as { __violations: string[] }).__violations);

  const response = await page.goto("/sign-in");
  expect(response?.headers()["content-security-policy"], "this test must run against the production image").toContain("script-src 'self'");

  await page.goto("/");
  await expect(page.locator(".public-hero")).toBeVisible();
  await expect(page.getByRole("region", { name: "Curriculum and paths" }).getByRole("listitem").first()).toBeVisible();
  expect(await violations()).toEqual([]);

  await page.goto("/privacy");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible({ timeout: 20_000 });
  expect(await violations()).toEqual([]);

  await signIn(page);

  await page.goto("/modules/llm-foundations");
  await expect(page.locator("figure.code-block .shiki").first()).toBeVisible({ timeout: 20_000 });
  await expect(page.locator(".diagram svg").first()).toBeVisible({ timeout: 20_000 });
  expect(await violations()).toEqual([]);

  await expect
    .poll(() => page.evaluate(() => document.fonts.check('16px "Geist"') && [...document.fonts].some((f) => f.family.includes("Geist") && f.status === "loaded")))
    .toBe(true);

  await page.goto("/challenges/apply-temperature");
  await expect(page.locator(".cm-content").first()).toBeVisible();
  expect(await violations()).toEqual([]);
  expect(external).toEqual([]);
});
