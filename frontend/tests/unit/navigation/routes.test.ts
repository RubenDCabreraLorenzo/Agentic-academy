/** The route table (routes contract). T077 and T099 add /privacy, /terms and the check history. */
import i18n from "../../../src/i18n";
import { redirects, routes, shellFor } from "../../../src/app/routes";

const EXPECTED = [
  { path: "/", auth: false, shell: "session" },
  { path: "/curriculum", auth: false, shell: "session" },
  { path: "/paths/:pathId", auth: false, shell: "session" },
  { path: "/sign-in", auth: false, shell: "public" },
  { path: "/register", auth: false, shell: "public" },
  { path: "/check-email", auth: false, shell: "public" },
  { path: "/forgot-password", auth: false, shell: "public" },
  { path: "/verify-email", auth: false, shell: "public" },
  { path: "/reset-password", auth: false, shell: "public" },
  { path: "/dashboard", auth: true, shell: "learning" },
  { path: "/dashboard/competencies", auth: true, shell: "learning" },
  { path: "/account", auth: true, shell: "learning" },
  { path: "/modules/:moduleId", auth: true, shell: "learning" },
  { path: "/knowledge-checks/:checkId", auth: true, shell: "learning" },
  { path: "/challenges/:challengeId", auth: true, shell: "learning" },
  { path: "/lab/:scenarioId", auth: true, shell: "learning" },
];

describe("route table", () => {
  it("has exactly the contract's paths, access and shells", () => {
    const actual = routes.map(({ path, auth, shell }) => ({ path, auth, shell }));
    const byPath = (a: { path: string }, b: { path: string }) => a.path.localeCompare(b.path);
    expect([...actual].sort(byPath)).toEqual([...EXPECTED].sort(byPath));
  });

  it("gives every route a unique title that exists in the strings", () => {
    const keys = routes.map((r) => r.titleKey);
    expect(new Set(keys).size).toBe(keys.length);
    const titles = keys.map((key) => {
      expect(i18n.exists(key), key).toBe(true);
      return i18n.t(key);
    });
    expect(new Set(titles).size).toBe(titles.length);
  });

  it("keeps the addresses that emails link to", () => {
    const paths = routes.map((r) => r.path);
    expect(paths).toContain("/verify-email");
    expect(paths).toContain("/reset-password");
  });

  it("redirects the old sign-up address, which has no shell or title of its own", () => {
    expect(redirects).toEqual([{ from: "/sign-up", to: "/register" }]);
    expect(routes.map((r) => r.path)).not.toContain("/sign-up");
  });

  it("resolves the shell of a location, and uses the session's shell for unknown addresses", () => {
    expect(shellFor("/modules/llm-foundations")).toBe("learning");
    expect(shellFor("/sign-in")).toBe("public");
    expect(shellFor("/curriculum")).toBe("session");
    expect(shellFor("/does-not-exist")).toBe("session");
  });
});
