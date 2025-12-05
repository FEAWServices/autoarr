#!/bin/bash
# =============================================================================
# DevContainer Post-Create Script
# =============================================================================
# Runs after the devcontainer is created. Since all tools (Node.js, pnpm,
# Poetry, gh, claude) are now installed in the Dockerfile, this script
# only needs to:
#   1. Install project dependencies
#   2. Configure git/GitHub authentication
# =============================================================================

set -e

echo "🚀 Running post-create setup..."
echo ""

# -----------------------------------------------------------------------------
# Git Configuration
# -----------------------------------------------------------------------------

if [ -f ".env" ]; then
    echo "🔧 Loading environment from .env..."
    source .env

    # Configure Git user
    if [ -n "$GIT_EMAIL" ] && [ -n "$GIT_NAME" ]; then
        git config --global user.email "$GIT_EMAIL"
        git config --global user.name "$GIT_NAME"
        echo "✅ Git configured: $GIT_NAME <$GIT_EMAIL>"
    fi

    # Configure GitHub CLI authentication
    if [ -n "$GH_TOKEN" ]; then
        echo "🔑 Configuring GitHub CLI..."
        # Add to bashrc for persistent auth
        if ! grep -q "export GH_TOKEN" ~/.bashrc 2>/dev/null; then
            cat >> ~/.bashrc << 'EOF'

# GitHub CLI authentication (auto-configured by devcontainer)
if [ -f /app/.env ]; then
    source /app/.env
    export GH_TOKEN
fi
EOF
        fi

        # Verify authentication
        if gh auth status > /dev/null 2>&1; then
            echo "✅ GitHub CLI authenticated as $(gh api user -q .login 2>/dev/null || echo 'unknown')"
        else
            echo "$GH_TOKEN" | gh auth login --with-token 2>/dev/null || true
            if gh auth status > /dev/null 2>&1; then
                echo "✅ GitHub CLI authenticated"
            else
                echo "⚠️  GitHub CLI authentication failed"
            fi
        fi
    else
        echo "⚠️  GH_TOKEN not found in .env - GitHub CLI not authenticated"
    fi
else
    echo "ℹ️  No .env file found - skipping git/GitHub configuration"
fi

echo ""

# -----------------------------------------------------------------------------
# Python Dependencies
# -----------------------------------------------------------------------------

echo "📦 Installing Python dependencies..."
cd /app

# Poetry is pre-installed in Dockerfile
poetry install --no-interaction
echo "✅ Python dependencies installed"

echo ""

# -----------------------------------------------------------------------------
# Frontend Dependencies
# -----------------------------------------------------------------------------

if [ -d "autoarr/ui" ]; then
    echo "📦 Installing frontend dependencies..."
    cd autoarr/ui

    # pnpm is pre-installed in Dockerfile
    # --force avoids interactive prompt when node_modules needs reinstall
    pnpm install --force
    echo "✅ Frontend dependencies installed"

    cd /app
fi

echo ""

# -----------------------------------------------------------------------------
# Create pnpm store volume if it doesn't exist
# -----------------------------------------------------------------------------

echo "🗄️  Ensuring pnpm store volume exists..."
if command -v docker &> /dev/null; then
    docker volume create autoarr-pnpm-store 2>/dev/null || true
    echo "✅ pnpm store volume ready"
fi

echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo "============================================="
echo "✅ DevContainer setup complete!"
echo "============================================="
echo ""
echo "📌 Installed versions:"
echo "   Python:  $(python --version 2>&1 | cut -d' ' -f2)"
echo "   Poetry:  $(poetry --version 2>&1 | cut -d' ' -f3)"
echo "   Node.js: $(node --version 2>&1)"
echo "   pnpm:    $(pnpm --version 2>&1)"
echo "   gh:      $(gh --version 2>&1 | head -1 | cut -d' ' -f3)"
echo "   claude:  $(claude --version 2>&1 || echo 'not available')"
echo ""
echo "🎯 Quick commands:"
echo "   Run API:        cd /app && poetry run uvicorn autoarr.api.main:app --reload"
echo "   Run UI:         cd /app/autoarr/ui && pnpm dev"
echo "   Run tests:      poetry run pytest"
echo "   Run E2E tests:  ./scripts/run-e2e-tests.sh"
echo ""
echo "🐳 Test container:"
echo "   Start:  docker-compose -f docker/docker-compose.local-test.yml up -d"
echo "   Logs:   docker-compose -f docker/docker-compose.local-test.yml logs -f"
echo "   Stop:   docker-compose -f docker/docker-compose.local-test.yml down"
echo ""
