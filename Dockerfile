# Multi-stage build for AutoArr single container deployment
# This creates a production-ready container with frontend + backend
# Optimized for GHCR (GitHub Container Registry) deployment

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/ui

# Install pnpm
RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

# Copy frontend package files
COPY autoarr/ui/package.json autoarr/ui/pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY autoarr/ui/ ./

# Build frontend for production
RUN pnpm run build

# Stage 2: Build Backend
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy dependency files
COPY autoarr/pyproject.toml autoarr/poetry.lock* ./

# Configure poetry to not create virtual env
RUN poetry config virtualenvs.create false

# Install dependencies (production only)
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Stage 3: Production Image
FROM python:3.11-slim

# Add metadata labels for GHCR
LABEL org.opencontainers.image.source="https://github.com/yourusername/autoarr"
LABEL org.opencontainers.image.description="AutoArr - Intelligent media automation orchestrator"
LABEL org.opencontainers.image.licenses="MIT"

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r autoarr && useradd -r -g autoarr autoarr

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application code
COPY autoarr/api/ ./api/
COPY autoarr/mcp-servers/ ./mcp-servers/
COPY shared/ ./shared/

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/ui/dist ./ui/dist

# Create directories for data persistence
RUN mkdir -p /data /app/logs && \
    chown -R autoarr:autoarr /data /app/logs

# Environment variables with defaults
ENV DATABASE_URL=sqlite:////data/autoarr.db \
    REDIS_URL=memory:// \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=INFO \
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8088

# Expose port (changed to 8088 to match config)
EXPOSE 8088

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1

# Volume for persistent data
VOLUME ["/data"]

# Switch to non-root user
USER autoarr

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8088"]
