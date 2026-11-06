/** Legal text is owner-supplied, and its links exist only with the files (FR-022a, SC-019). */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { resolveLegal } from "../../../src/features/legal/availability";

const load = () => Promise.resolve("# Text");
const DIR = "../../legal/en";

describe("resolveLegal", () => {
  it("reports everything as unavailable when no file exists", () => {
    expect(resolveLegal({}, {})).toEqual({ privacy: null, terms: null, publisher: null });
  });

  it("offers each document whose file exists, on its own", () => {
    const legal = resolveLegal({ [`${DIR}/privacy.md`]: load }, {});
    expect(legal.privacy).toBe(load);
    expect(legal.terms).toBeNull();
  });

  it("reads the publisher when it has a name and a contact email", () => {
    const publisher = { name: "Fixture Ltd", contact_email: "hello@example.com", address: "1 Fixture Street" };
    expect(resolveLegal({}, { [`${DIR}/publisher.json`]: publisher }).publisher).toEqual(publisher);
  });

  it.each([[{ name: "No contact" }], [{ contact_email: "no-name@example.com" }], [{ name: "", contact_email: "" }], [null], ["text"]])(
    "shows no publisher for the incomplete file %j",
    (publisher) => {
      expect(resolveLegal({}, { [`${DIR}/publisher.json`]: publisher }).publisher).toBeNull();
    },
  );
});

describe("the files in the repository", () => {
  const dir = path.resolve(import.meta.dirname, "../../../src/legal/en");

  it("say who may supply them", () => {
    expect(readFileSync(path.join(dir, "README.md"), "utf8")).toMatch(/only the owner/i);
  });

  it("include a valid publisher, if there is one", () => {
    const file = path.join(dir, "publisher.json");
    if (!existsSync(file)) return;
    const parsed: unknown = JSON.parse(readFileSync(file, "utf8"));
    expect(resolveLegal({}, { [`${DIR}/publisher.json`]: parsed }).publisher).not.toBeNull();
  });
});
