FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY runner/sandbox-image /app/runner/sandbox-image
COPY backend/ ./
RUN uv sync --no-dev
RUN useradd --system --uid 10001 academy
USER academy
EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "academy.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
