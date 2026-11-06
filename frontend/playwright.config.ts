import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests run against the real API and the Vite dev server (quickstart "Run", option B).
 * DATABASE_URL must point to a migrated database; global setup migrates, builds content and seeds.
 *
 * The `production` project tests the nginx image under its real security policy, because the
 * development server applies no policy (research R4). It brings its own servers, as does any run
 * with PLAYWRIGHT_NO_SERVERS=1.
 */
const apiEnv = {
  APP_ENV: "test",
  EMAIL_BACKEND: process.env.EMAIL_BACKEND ?? "console",
  COOKIE_SECURE: "false",
  RATE_LIMIT_ENABLED: "false",
  SESSION_SECRET: process.env.SESSION_SECRET ?? "e2e-session-secret-0123456789abcdef",
  CONTENT_DIR: process.env.CONTENT_DIR ?? "../dist/content",
  DATABASE_URL: process.env.DATABASE_URL ?? "postgresql+psycopg://academy:academy@localhost:5432/academy",
  CHALLENGES_ENABLED: process.env.CHALLENGES_ENABLED ?? (process.env.E2E_START_RUNNER === "0" ? "false" : "true"),
};

const noServers = process.env.PLAYWRIGHT_NO_SERVERS === "1" || process.argv.includes("--project=production");
const separateRuns = ["**/csp.spec.ts", "**/visual.spec.ts"];

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  globalSetup: "./tests/e2e/global-setup.ts",
  globalTeardown: "./tests/e2e/global-teardown.ts",
  use: { baseURL: "http://localhost:5173", trace: "off" },
  projects: [
    { name: "desktop", testIgnore: separateRuns, use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-360", testIgnore: separateRuns, use: { ...devices["Desktop Chrome"], viewport: { width: 360, height: 780 } } },
    {
      name: "production",
      testMatch: "**/csp.spec.ts",
      use: { ...devices["Desktop Chrome"], baseURL: process.env.PROD_BASE_URL ?? "http://localhost:5173" },
    },
    { name: "visual", testMatch: "**/visual.spec.ts", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: noServers
    ? []
    : [
        {
          command: "uv run --project ../backend uvicorn academy.main:create_app --factory --port 8000",
          url: "http://localhost:8000/api/v1/health",
          env: apiEnv,
          reuseExistingServer: true,
          timeout: 60_000,
          stdout: "pipe",
        },
        {
          command: "pnpm dev --strictPort",
          url: "http://localhost:5173",
          reuseExistingServer: true,
          timeout: 60_000,
        },
      ],
});
