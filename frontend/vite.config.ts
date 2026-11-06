
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";

/** Share tags need absolute addresses. Without a known origin they are omitted, not guessed (research R15). */
function shareTags(): Plugin {
  return {
    name: "share-tags",
    transformIndexHtml(html) {
      const origin = process.env.VITE_PUBLIC_ORIGIN?.replace(/\/$/, "");
      if (!origin) return html;
      const meta = (property: string, content: string) => ({ tag: "meta", attrs: { property, content }, injectTo: "head" as const });
      return { html, tags: [meta("og:url", `${origin}/`), meta("og:image", `${origin}/og-image.png`)] };
    },
  };
}

// The SPA and the API share one origin (research R2): in development Vite proxies /api to the
// backend so SameSite=Lax session cookies and CSRF protection work without CORS.
export default defineConfig({
  plugins: [react(), shareTags()],
  server: {
    port: 5173,
    proxy: { "/api": { target: process.env.API_URL ?? "http://localhost:8000", changeOrigin: false } },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["tests/unit/**/*.test.{ts,tsx}"],
    setupFiles: ["tests/unit/setup.ts"],
  },
});
