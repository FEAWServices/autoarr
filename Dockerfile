# =============================================================================
# Multi-stage build for production AutoArr container
# =============================================================================
# This Dockerfile creates a production-ready container with both frontend and
# backend in a single image (similar to Sonarr/Radarr architecture).
#
# Build stages:
#   1. frontend-builder: Compiles React/TypeScript UI with Vite
#   2. Production image: Python 3.11 backend with compiled frontend assets
#
# Security features:
#   - Non-root user (autoarr:1001)
#   - Minimal base images (alpine for Node, slim for Python)
#   - No development dependencies in final image
#   - Health check for container orchestration
#
# Build: docker build -t autoarr:latest -f Dockerfile .
# Run:   docker run -p 8088:8088 -v /data:/data autoarr:latest
# =============================================================================

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
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files and README (required by Poetry for package installation)
# Note: README.md must be included (not excluded in .dockerignore) for Poetry to install the package
COPY pyproject.toml poetry.lock* README.md ./

# Configure poetry to not create virtual env (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies first (without the root package) for better layer caching
# This layer will only rebuild when dependencies change, not when source code changes
# --no-root: Skip installing the autoarr package itself (only dependencies)
# --without dev: Exclude development dependencies (pytest, black, mypy, etc.)
RUN poetry install --no-interaction --no-ansi --without dev --no-root

# Copy application code
# This comes AFTER dependency installation to optimize Docker layer caching
COPY autoarr/ ./autoarr/
COPY scripts/ ./scripts/

# Now install the root package (autoarr) using the copied source code
# --only-root: Only install the package itself, not dependencies (already installed above)
# This allows Poetry to properly install the autoarr package in editable mode
RUN poetry install --no-interaction --no-ansi --only-root

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
