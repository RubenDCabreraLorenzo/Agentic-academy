FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY runner/sandbox-image /app/runner/sandbox-image
COPY backend/ ./
RUN uv sync --no-dev
RUN useradd --system --uid 10001 academy
USER academy
EXPOSE 8000
# Not `uv run`: it re-installs the project at start, and this user cannot write its cache or the root-owned .venv.
CMD [".venv/bin/uvicorn", "academy.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
