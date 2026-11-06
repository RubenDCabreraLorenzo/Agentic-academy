import { execFileSync } from "node:child_process";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../../..");

export default function globalSetup() {
  const env = {
    ...process.env,
    APP_ENV: "test",
    DATABASE_URL: process.env.DATABASE_URL ?? "postgresql+psycopg://academy:academy@localhost:5432/academy",
  };
  const run = (args: string[]) => execFileSync("uv", ["run", "--project", "backend", ...args], { cwd: root, env, stdio: "inherit" });
  run(["alembic", "-c", "backend/alembic.ini", "upgrade", "head"]);
  run(["academy", "content", "build", "--root", "content", "--lang", "en", "--out", "dist/content"]);
  run(["academy", "dev", "seed"]);
}
