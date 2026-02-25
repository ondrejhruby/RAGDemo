FROM node:20-alpine AS base

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./ 

RUN pnpm run build

EXPOSE 3000

ENV NODE_ENV=production

CMD ["pnpm", "start", "--", "-H", "0.0.0.0", "-p", "3000"]

