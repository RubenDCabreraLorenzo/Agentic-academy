"""Create .env from .env.example (if missing) and write a random SESSION_SECRET into it."""

import secrets
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
env = root / ".env"
if not env.exists():
    shutil.copyfile(root / ".env.example", env)

lines = env.read_text().splitlines()
secret = secrets.token_urlsafe(32)
out = [f"SESSION_SECRET={secret}" if line.startswith("SESSION_SECRET=") else line for line in lines]
if not any(line.startswith("SESSION_SECRET=") for line in lines):
    out.append(f"SESSION_SECRET={secret}")
env.write_text("\n".join(out) + "\n")
print("SESSION_SECRET written to .env")
