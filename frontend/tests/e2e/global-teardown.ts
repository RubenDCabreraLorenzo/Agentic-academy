import { existsSync, readFileSync } from "node:fs";
import { RUNNER_PID_FILE } from "./global-setup";

export default function globalTeardown() {
  if (!existsSync(RUNNER_PID_FILE)) return;
  const pid = Number(readFileSync(RUNNER_PID_FILE, "utf8"));
  try {
    process.kill(-pid, "SIGTERM");
  } catch {
    /* already stopped */
  }
}
