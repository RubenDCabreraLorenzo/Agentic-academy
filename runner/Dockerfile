FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app/runner
COPY runner/ ./
RUN uv sync --no-dev
CMD ["uv", "run", "--no-dev", "academy-runner"]
