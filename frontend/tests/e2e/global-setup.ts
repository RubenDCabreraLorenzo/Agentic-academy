import { execFileSync, spawn } from "node:child_process";
import { openSync, writeFileSync } from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../../..");
export const RUNNER_PID_FILE = path.join(root, "frontend/test-results/.runner.pid");

export default function globalSetup() {
  const env = {
    ...process.env,
    APP_ENV: "test",
    DATABASE_URL: process.env.DATABASE_URL ?? "postgresql+psycopg://academy:academy@localhost:5432/academy",
    RUNNER_DB_PASSWORD: process.env.RUNNER_DB_PASSWORD ?? "runner",
  };
  const run = (args: string[]) => execFileSync("uv", ["run", "--project", "backend", ...args], { cwd: root, env, stdio: "inherit" });
  run(["alembic", "-c", "backend/alembic.ini", "upgrade", "head"]);
  run(["academy", "content", "build", "--root", "content", "--lang", "en", "--out", "dist/content"]);
  run(["academy", "dev", "seed", "--reset"]);

  if (process.env.E2E_START_RUNNER !== "0") {
    // The runner evaluates challenge code (US4). RUNNER_RUNTIME defaults to runsc; machines without
    // gVisor may set RUNNER_RUNTIME=runc (development exception, not valid security evidence).
    execFileSync("mkdir", ["-p", path.join(root, "frontend/test-results")]);
    const log = openSync(path.join(root, "frontend/test-results/runner.log"), "w");
    const child = spawn("uv", ["run", "--project", "runner", "academy-runner"], {
      cwd: root,
      detached: true,
      stdio: ["ignore", log, log],
      env: {
        ...process.env,
        APP_ENV: "test",
        RUNNER_DATABASE_URL: process.env.RUNNER_DATABASE_URL ?? "postgresql://academy_runner:runner@localhost:5432/academy",
        CONTENT_DIR: path.join(root, "dist/content"),
        RUNNER_RUNTIME: process.env.RUNNER_RUNTIME ?? "runsc",
        RUNNER_OUT_DIR: process.env.RUNNER_OUT_DIR ?? path.join(root, ".runner-out"),
        RUNNER_WORKER_ID: "e2e-runner",
      },
    });
    child.unref();
    writeFileSync(RUNNER_PID_FILE, String(child.pid));
  }
}
