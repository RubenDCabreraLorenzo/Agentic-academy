/**
 * Typed fetch client for /api/v1 (contracts/openapi.yaml).
 * - Sends cookies (same origin), adds X-CSRF-Token from the aa_csrf cookie on state changes.
 * - Parses RFC 9457 problem details into ApiError.
 * - Emits a re-authentication event on 401 so drafts can be replayed after sign-in (FR-045b).
 */
import type { components } from "./schema";

export type Schemas = components["schemas"];

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail?: string;
  readonly body: Record<string, unknown>;

  constructor(status: number, body: Record<string, unknown>) {
    super(String(body.title ?? `Request failed (${status})`));
    this.status = status;
    this.code = String(body.code ?? "error");
    this.detail = typeof body.detail === "string" ? body.detail : undefined;
    this.body = body;
  }
}

export class NetworkError extends Error {}

export const AUTH_REQUIRED_EVENT = "academy:auth-required";
const BASE = "/api/v1";

export function readCookie(name: string): string {
  const match = document.cookie.split("; ").find((c) => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : "";
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

export async function api<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["X-CSRF-Token"] = readCookie("aa_csrf");
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new NetworkError("Network unavailable");
  }
  if (response.status === 401) {
    window.dispatchEvent(new CustomEvent(AUTH_REQUIRED_EVENT, { detail: { path } }));
  }
  if (!response.ok) {
    let parsed: Record<string, unknown> = {};
    try {
      parsed = (await response.json()) as Record<string, unknown>;
    } catch {
      parsed = { title: response.statusText };
    }
    throw new ApiError(response.status, parsed);
  }
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const get = <T>(path: string) => api<T>("GET", path);
export const post = <T>(path: string, body?: unknown) => api<T>("POST", path, body ?? {});
export const put = <T>(path: string, body?: unknown) => api<T>("PUT", path, body ?? {});
export const del = <T>(path: string, body?: unknown) => api<T>("DELETE", path, body);
