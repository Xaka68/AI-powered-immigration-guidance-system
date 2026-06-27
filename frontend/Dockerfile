# Frontend: TanStack Start (Vite + Nitro SSR), built for a Node server.
# Build context: the frontend/ directory.
#   docker build -t compass-frontend \
#     --build-arg VITE_API_URL=https://<backend>.awsapprunner.com frontend/
#
# VITE_* is compiled into the bundle at build time, so the backend URL must be
# passed as a build-arg here (not a runtime env var).
FROM node:20-slim AS builder

WORKDIR /app

# Install dependencies (layer cache).
COPY package.json package-lock.json ./
RUN npm ci

# Point the app at the live backend, and force Nitro to emit a Node server
# (default preset is cloudflare, which would NOT produce server/index.mjs).
ARG VITE_API_URL
ARG VITE_USE_MOCK=false
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_USE_MOCK=$VITE_USE_MOCK
ENV NITRO_PRESET=node-server

# Copy source and build.
COPY . ./
RUN npm run build

# --- Production stage ---
FROM node:20-slim AS runtime

WORKDIR /app

# Copy the Nitro node-server output (server bundle + assets).
COPY --from=builder /app/.output ./

ENV PORT=3000
ENV HOST=0.0.0.0
EXPOSE 3000

# Nitro node-server entry point.
CMD ["node", "server/index.mjs"]
