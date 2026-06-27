# Frontend: TanStack Start (Vite + Nitro SSR)
# Build context: frontend/ directory. Build with: docker build -t compass-frontend frontend/
FROM node:20-slim AS builder

WORKDIR /app

# Install dependencies (layer cache)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . ./
RUN npm run build

# --- Production stage ---
FROM node:20-slim AS runtime

WORKDIR /app

# Copy the Nitro output (server bundle)
COPY --from=builder /app/.output ./

ENV PORT=3000
ENV HOST=0.0.0.0
EXPOSE 3000

# Nitro server entry point
CMD ["node", "server/index.mjs"]
