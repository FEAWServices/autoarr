# Multi-stage build for AutoArr single container deployment
# This creates a production-ready container with frontend + backend

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/ui

# Install pnpm
RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

# Copy frontend package files
COPY ui/package.json ui/pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY ui/ ./

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
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual env
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --only main

# Stage 3: Production Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application code
COPY api/ ./api/
COPY mcp-servers/ ./mcp-servers/
COPY shared/ ./shared/

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/ui/dist ./ui/dist

# Create directories for data persistence
RUN mkdir -p /data /app/logs

# Environment variables with defaults
ENV DATABASE_URL=sqlite:////data/autoarr.db \
    REDIS_URL=memory:// \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    APP_ENV=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Volume for persistent data
VOLUME ["/data"]

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
