/** Quickstart P2 (US2): the landing page, live data and what it must not claim. */
import { existsSync } from "node:fs";
import path_ from "node:path";
import { expect, expectNoHorizontalScroll, expectNoSeriousA11yViolations, signIn, test } from "../fixtures";

interface Path {
  id: string;
  title: string;
  status: "available" | "planned";
  estimated_hours: number;
  competencies: { id: string; title: string }[];
}

test("all sections and both actions exist, in the required order", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("Learn to engineer reliable AI agents · Agentic Academy");
  await expect(page.locator(".public-hero")).toBeVisible();
  const headings = await page.getByRole("heading", { level: 2 }).allInnerTexts();
  expect(headings).toEqual([
    "How you learn",
    "Curriculum and paths",
    "Code challenges",
    "Laboratories",
    "Skills and competencies",
    "What you need to know already",
    "Start building",
  ]);
  await expect(page.getByRole("link", { name: "Create account" }).first()).toBeVisible();
  await expect(page.getByRole("contentinfo").getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Curriculum and paths" }).getByRole("listitem").first()).toBeVisible();
  await expectNoHorizontalScroll(page);
  await expectNoSeriousA11yViolations(page);
});

test("the first viewport has the value proposition and both actions", async ({ page }) => {
  await page.goto("/");
  const hero = page.locator(".public-hero");
  await expect(hero.getByRole("heading", { level: 1 })).toBeInViewport({ ratio: 1 });
  await expect(hero.getByRole("link", { name: "Create account" })).toHaveAttribute("href", "/register");
  await expect(hero.getByRole("link", { name: "Create account" })).toBeInViewport({ ratio: 1 });
  await expect(hero.getByRole("link", { name: "Explore the curriculum" })).toHaveAttribute("href", "/curriculum");
  await expect(hero.getByRole("link", { name: "Explore the curriculum" })).toBeInViewport({ ratio: 1 });
});

test("curriculum data comes from the catalog", async ({ page }) => {
  const paths = (await (await page.request.get("/api/v1/catalog")).json()) as Path[];
  expect(paths.length).toBeGreaterThan(0);
  await page.goto("/");
  const section = page.getByRole("region", { name: "Curriculum and paths" });
  for (const path of paths) {
    const row = section.getByRole("listitem").filter({ has: page.getByRole("link", { name: path.title, exact: true }) });
    await expect(row.getByRole("link", { name: path.title, exact: true })).toHaveAttribute("href", `/paths/${path.id}`);
    await expect(row).toContainText(path.status === "available" ? "Available" : "Not yet available");
    await expect(row).toContainText(`About ${path.estimated_hours} hours`);
    const n = path.competencies.length;
    await expect(row).toContainText(n === 1 ? "1 competency" : `${n} competencies`);
  }

  const competencies = page.getByRole("region", { name: "Skills and competencies" });
  for (const path of paths.filter((p) => p.status === "available")) {
    for (const c of path.competencies) await expect(competencies).toContainText(c.title);
  }
  for (const path of paths.filter((p) => p.status === "planned")) {
    for (const c of path.competencies) {
      if (!paths.some((p) => p.status === "available" && p.competencies.some((a) => a.id === c.id))) {
        await expect(competencies).not.toContainText(c.title);
      }
    }
  }
});

test("entry prerequisites come from the first available path", async ({ page }) => {
  const paths = (await (await page.request.get("/api/v1/catalog")).json()) as Path[];
  const first = paths.find((p) => p.status === "available") as Path;
  const detail = (await (await page.request.get(`/api/v1/paths/${first.id}`)).json()) as { entry_prerequisites: { label: string }[] };
  expect(detail.entry_prerequisites.length).toBeGreaterThan(0);
  await page.goto("/");
  const section = page.getByRole("region", { name: "What you need to know already" });
  for (const p of detail.entry_prerequisites) await expect(section).toContainText(p.label);
});

test("the laboratory says that it replays recordings and calls no model", async ({ page }) => {
  await page.goto("/");
  const section = page.getByRole("region", { name: "Laboratories" });
  await expect(section).toContainText("replays curated recordings");
  await expect(section).toContainText("No language model is called");
  await expect(page.getByRole("region", { name: "How you learn" })).toContainText("No language model is called");
});

test("showcases are read-only excerpts with text alternatives", async ({ page }) => {
  await page.goto("/");
  for (const name of ["Code challenges", "Laboratories"]) {
    const section = page.getByRole("region", { name });
    await expect(section.getByRole("figure")).toBeVisible();
    await expect(section.getByRole("figure").locator("figcaption")).not.toBeEmpty();
    await expect(section.getByRole("figure").getByRole("button")).toHaveCount(0);
    await expect(section.getByRole("figure").getByRole("textbox")).toHaveCount(0);
  }
});

test("with the catalog blocked, other sections remain and a retry appears", async ({ page }) => {
  await page.route("**/api/v1/catalog", (route) => route.abort());
  await page.goto("/");
  const section = page.getByRole("region", { name: "Curriculum and paths" });
  await expect(section.getByRole("button", { name: "Try again" })).toBeVisible({ timeout: 15_000 });
  await expect(section.getByRole("link", { name: "Explore the curriculum" })).toHaveAttribute("href", "/curriculum");

  await expect(page.locator(".public-hero").getByRole("link", { name: "Create account" })).toBeVisible();
  await expect(page.getByRole("region", { name: "How you learn" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Laboratories" })).toContainText("No language model is called");
  await expect(page.getByRole("region", { name: "Skills and competencies" }).getByRole("link", { name: "Explore the curriculum" })).toBeVisible();
  await expect(page.getByRole("region", { name: "What you need to know already" }).getByRole("link", { name: "Explore the curriculum" })).toBeVisible();

  await page.unroute("**/api/v1/catalog");
  await section.getByRole("button", { name: "Try again" }).click();
  await expect(section.getByRole("link", { name: "Foundations of Agentic AI Engineering" })).toBeVisible();
});

test("a signed-in learner stays on the page and is offered their progress", async ({ page }) => {
  await signIn(page);
  await page.goto("/");
  await expect(page).toHaveURL(/:\d+\/$/);
  const hero = page.locator(".public-hero");
  await expect(hero.getByRole("link", { name: "Go to my progress" })).toHaveAttribute("href", "/dashboard");
  await expect(hero.getByRole("link", { name: "Explore the curriculum" })).toBeVisible();
  await expect(hero.getByRole("link", { name: "Create account" })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Start building" }).getByRole("link", { name: "Go to my progress" })).toBeVisible();
});

for (const [file, path, name] of [
  ["privacy.md", "/privacy", "Privacy notice"],
  ["terms.md", "/terms", "Terms"],
] as const) {
  test(`${name}: its link and page exist only with its file`, async ({ page }) => {
    const present = existsSync(path_.resolve(import.meta.dirname, "../../../src/legal/en", file));
    for (const where of ["/", "/register"]) {
      await page.goto(where);
      await expect(page.getByRole("contentinfo")).toBeVisible();
      const link = page.getByRole("main").or(page.getByRole("contentinfo")).getByRole("link", { name, exact: true });
      await expect(link.first()).toBeVisible({ visible: present });
      if (present) await expect(link.first()).toHaveAttribute("href", path);
    }
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(present ? name : "We could not find this page.");
    await expect(page).toHaveTitle(`${present ? name : "We could not find this page."} · Agentic Academy`);
  });
}

test("no publisher details are shown without their file", async ({ page }) => {
  test.skip(existsSync(path_.resolve(import.meta.dirname, "../../../src/legal/en/publisher.json")), "the file exists");
  await page.goto("/");
  await expect(page.getByRole("contentinfo").getByRole("link", { name: "Contact" })).toHaveCount(0);
});

test("the footer identifies the product and links to its entry points", async ({ page }) => {
  await page.goto("/");
  const footer = page.getByRole("contentinfo");
  await expect(footer).toContainText("Agentic Academy");
  await expect(footer.getByRole("link", { name: "Curriculum" })).toHaveAttribute("href", "/curriculum");
  await expect(footer.getByRole("link", { name: "Create account" })).toHaveAttribute("href", "/register");
  await expect(footer.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/sign-in");
});

test("the page loads no heavy content engine", async ({ page }) => {
  const scripts: string[] = [];
  page.on("request", (r) => {
    if (r.resourceType() === "script") scripts.push(r.url());
  });
  await page.goto("/");
  await expect(page.locator(".public-hero")).toBeVisible();
  await page.waitForLoadState("networkidle");
  expect(scripts.filter((s) => /codemirror|mermaid|shiki|Markdown|highlighter/i.test(s))).toEqual([]);
});
