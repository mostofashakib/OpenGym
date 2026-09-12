## Multi-stage build for Next.js app
FROM --platform=linux/amd64 node:20-bookworm AS deps
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund

FROM --platform=linux/amd64 node:20-bookworm AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM --platform=linux/amd64 node:20-bookworm AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=80

# System dependencies for python simulator and health checks
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
     bash curl python3 python3-pip \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/package.json ./
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/.next ./.next
COPY --from=deps /app/node_modules ./node_modules
COPY scripts ./scripts
COPY environment ./environment
COPY tools ./tools
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x docker-entrypoint.sh scripts/*.py

EXPOSE 80

ENTRYPOINT ["./docker-entrypoint.sh"]
