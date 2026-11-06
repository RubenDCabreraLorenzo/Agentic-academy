FROM node:22-slim AS build
# Same major version as CI. Unpinned, Corepack takes the latest release, so builds would change without notice.
RUN corepack enable && corepack prepare pnpm@10 --activate
WORKDIR /app/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
COPY specs/001-agentic-academy-mvp/contracts /app/specs/001-agentic-academy-mvp/contracts
RUN pnpm build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 8080
