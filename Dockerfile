# Multi-stage build for production AutoArr container
# This builds both frontend and backend into a single container (like Sonarr/Radarr)

# Stage 1: Build frontend
FROM node:24-alpine AS frontend-builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

# Copy frontend package files
COPY autoarr/ui/package.json autoarr/ui/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY autoarr/ui ./

# Build frontend for production
RUN pnpm run build

# Stage 2: Build backend with frontend assets
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual env (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies (production only)
RUN poetry install --no-interaction --no-ansi --without dev

# Copy application code
COPY autoarr/ ./autoarr/
COPY scripts/ ./scripts/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/dist ./autoarr/ui/dist

# Create data directory
RUN mkdir -p /data

# Create non-root user for security
RUN groupadd -r autoarr --gid=1001 && \
    useradd -r -g autoarr --uid=1001 --home=/app autoarr && \
    chown -R autoarr:autoarr /app /data

# Switch to non-root user
USER autoarr

# Expose API port
EXPOSE 8088

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1

# Run the application
CMD ["uvicorn", "autoarr.api.main:app", "--host", "0.0.0.0", "--port", "8088"]
