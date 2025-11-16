# AutoArrX - Azure-optimized Production Dockerfile
# Proprietary - All Rights Reserved

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 autoarrx

WORKDIR /app

# Install Poetry
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# ============================================
# Development Stage
# ============================================
FROM base AS development

COPY pyproject.toml poetry.lock ./
RUN poetry install --with dev,test

COPY . .

USER autoarrx

CMD ["uvicorn", "autoarrx.api.main:app", "--host", "0.0.0.0", "--port", "8765", "--reload"]

# ============================================
# Production Dependencies Stage
# ============================================
FROM base AS dependencies

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

# ============================================
# Production Stage
# ============================================
FROM python:3.11-slim AS production

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 autoarrx

WORKDIR /app

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=autoarrx:autoarrx . .

# Security: Remove write permissions
RUN chmod -R 555 /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

# Switch to non-root user
USER autoarrx

# Expose WebSocket port
EXPOSE 8765

# Azure Container Instances labels
LABEL com.microsoft.aci.app="autoarrx" \
      com.microsoft.aci.version="0.1.0" \
      com.microsoft.aci.license="proprietary"

# Production command
CMD ["uvicorn", "autoarrx.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8765", \
     "--workers", "4", \
     "--log-level", "info"]
