/**
 * Legal text and publisher details exist only as files supplied by the owner (FR-022a). Availability is
 * read at build time, so that it cannot disagree with what is deployed, and nothing is ever filled in.
 */
export type LegalLoader = () => Promise<string>;

export interface Publisher {
  name: string;
  contact_email: string;
  address?: string;
  registration?: string;
}

export interface Legal {
  privacy: LegalLoader | null;
  terms: LegalLoader | null;
  publisher: Publisher | null;
}

function validPublisher(value: unknown): Publisher | null {
  const p = value as Partial<Publisher> | null;
  return typeof p === "object" && p && typeof p.name === "string" && p.name && typeof p.contact_email === "string" && p.contact_email
    ? (p as Publisher)
    : null;
}

function find<T>(files: Record<string, T>, name: string): T | null {
  const key = Object.keys(files).find((path) => path.endsWith(`/${name}`));
  return key === undefined ? null : (files[key] as T);
}

export function resolveLegal(markdown: Record<string, LegalLoader>, json: Record<string, unknown>): Legal {
  return {
    privacy: find(markdown, "privacy.md"),
    terms: find(markdown, "terms.md"),
    publisher: validPublisher(find(json, "publisher.json")),
  };
}

export const legal = resolveLegal(
  // The text loads only on its own route; the publisher appears in every footer.
  import.meta.glob<string>(["../../legal/en/privacy.md", "../../legal/en/terms.md"], { query: "?raw", import: "default" }),
  import.meta.glob("../../legal/en/publisher.json", { eager: true, import: "default" }),
);
