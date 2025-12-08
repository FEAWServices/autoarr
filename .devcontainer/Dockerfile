# =============================================================================
# AutoArr Development Base Image
# =============================================================================
# Shared base image for both DevContainer and Local Test Container.
# Ensures consistent environment across development and testing.
#
# Used by:
#   - .devcontainer/devcontainer.json (VS Code development)
#   - docker/docker-compose.local-test.yml (local testing)
# =============================================================================

FROM python:3.11-slim-bookworm

# Version pins for reproducibility
ARG NODE_MAJOR=20
ARG PNPM_VERSION=8.15.0
ARG POETRY_VERSION=1.7.1

LABEL maintainer="AutoArr Team"
LABEL description="AutoArr development environment"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    gcc \
    g++ \
    build-essential \
    # Database clients
    libpq-dev \
    # Utilities
    curl \
    git \
    ca-certificates \
    gnupg \
    # For Playwright
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (pinned major version)
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version

# Install pnpm (pinned version)
RUN npm install -g pnpm@${PNPM_VERSION} \
    && pnpm --version

# Install Poetry (pinned version)
RUN pip install --no-cache-dir poetry==${POETRY_VERSION} \
    && poetry --version

# Configure Poetry to create virtualenv in project
RUN poetry config virtualenvs.in-project true

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/* \
    && gh --version

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-code \
    && claude --version || true

# Set up pnpm global bin path
ENV PNPM_HOME="/root/.local/share/pnpm"
ENV PATH="${PNPM_HOME}:${PATH}"

# Expose common ports
EXPOSE 8088 5173 3000 6006

# Default command for interactive use
CMD ["/bin/bash"]
