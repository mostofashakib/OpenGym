## Multi-stage build for Next.js app (Debian-based to avoid musl native binary issues)
FROM --platform=linux/amd64 node:20-bookworm AS deps
WORKDIR /app
# Install dependencies based on package.json (ignore host lockfile to avoid platform/version pinning)
COPY package.json ./
# Use npm install to resolve platform-specific optional binaries correctly in container
RUN npm install --no-audit --no-fund \
  && npm config set optional true \
  && npm install --no-audit --no-fund --include=optional lightningcss-linux-x64-gnu@1.30.1 @tailwindcss/oxide-linux-x64-gnu@4.1.12 || true \
  && echo "ignore-scripts=$(npm config get ignore-scripts)" && node -e "console.log('arch',process.arch,'platform',process.platform)" && ls -la node_modules/lightningcss || true

FROM --platform=linux/amd64 node:20-bookworm AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm rebuild lightningcss --force || true
RUN node -e "try{console.log('tailwindcss version:',require('tailwindcss/package.json').version)}catch(e){console.log('tailwindcss not found')}"
RUN npm run build

FROM --platform=linux/amd64 node:20-bookworm AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV DISABLE_AUTH=1
# System deps for seeding script and health checks
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
     bash curl python3 python3-pip \
  && rm -rf /var/lib/apt/lists/*
# Copy app source and build artifacts
COPY --from=builder /app/package.json ./
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=deps /app/node_modules ./node_modules

# Fixed clock configuration (Gmail only)
# These can be modified as needed; defaults to March 14, 2030 03:14 in Austin, TX
ENV FIXED_TIME_ENABLED=true \
    FIXED_TIME_ISO=2030-03-14T03:14:00-05:00 \
    FIXED_TIME_ZONE=America/Chicago \
    NEXT_PUBLIC_FIXED_TIME_ENABLED=true \
    NEXT_PUBLIC_FIXED_TIME_ISO=2030-03-14T03:14:00-05:00 \
    NEXT_PUBLIC_FIXED_TIME_ZONE=America/Chicago

# Preload server-side fixed time shim
COPY fake-time.js ./fake-time.js
ENV NODE_OPTIONS="--require /app/fake-time.js"

# Prune devDependencies from runtime image to reduce size
RUN npm prune --omit=dev || true

# Seeding scripts and entrypoint
COPY scripts ./scripts
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x docker-entrypoint.sh scripts/generate_rand_state/generate_state.sh \
  && pip3 install --no-cache-dir --break-system-packages -r scripts/requirements.txt || \
     pip3 install --no-cache-dir -r scripts/requirements.txt

# Serve web on 80
ENV PORT=80
EXPOSE 80

# Seed controls
ENV SEED_ON_STARTUP=false \
    SEED_SEED=gmail \
    SEED_THREADS=8 \
    SEED_SINGLES=12 \
    SEED_MAX_MESSAGES_PER_THREAD=4 \
    SEED_API_PATH=/api/state

ENTRYPOINT ["./docker-entrypoint.sh"]
