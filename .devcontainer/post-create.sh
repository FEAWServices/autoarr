#!/bin/bash
set -e

echo "🚀 Running post-create setup..."

# Install Node.js if not already installed
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
    echo "✅ Node.js installed: $(node --version)"
fi

# Install pnpm if not already installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    curl -fsSL https://get.pnpm.io/install.sh | sh -
    export PNPM_HOME="/root/.local/share/pnpm"
    export PATH="$PNPM_HOME:$PATH"
    echo "✅ pnpm installed: $(pnpm --version)"
fi

# Install Claude CLI if not already installed
if ! command -v claude &> /dev/null; then
    echo "🤖 Installing Claude CLI..."
    if command -v npm &> /dev/null; then
        npm install -g @anthropic-ai/claude-code
        echo "✅ Claude CLI installed"
    else
        echo "⚠️ npm is not available. Cannot install Claude CLI."
    fi
fi

# Install GitHub CLI if not already installed
if ! command -v gh &> /dev/null; then
    echo "🐙 Installing GitHub CLI..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    apt-get update
    apt-get install -y gh
    echo "✅ GitHub CLI installed: $(gh --version)"
fi

# Install Poetry
echo "📦 Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"

# Configure Git credentials and GitHub CLI
if [ -f ".env" ]; then
    echo "🔧 Configuring Git credentials..."
    source .env
    if [ ! -z "$GIT_EMAIL" ] && [ ! -z "$GIT_NAME" ]; then
        git config --global user.email "$GIT_EMAIL"
        git config --global user.name "$GIT_NAME"
        echo "✅ Git configured: $GIT_NAME <$GIT_EMAIL>"
    fi

    # Configure GitHub CLI authentication
    if [ ! -z "$GH_TOKEN" ]; then
        echo "🔑 Configuring GitHub CLI authentication..."
        # Add GH_TOKEN export to bash profile for persistent authentication
        if ! grep -q "export GH_TOKEN" ~/.bashrc 2>/dev/null; then
            echo "" >> ~/.bashrc
            echo "# GitHub CLI authentication (auto-configured by devcontainer)" >> ~/.bashrc
            echo "if [ -f /app/.env ]; then" >> ~/.bashrc
            echo "    source /app/.env" >> ~/.bashrc
            echo "    export GH_TOKEN" >> ~/.bashrc
            echo "fi" >> ~/.bashrc
        fi
        # Authenticate gh CLI using the token
        echo "$GH_TOKEN" | gh auth login --with-token
        # Verify authentication
        if gh auth status > /dev/null 2>&1; then
            echo "✅ GitHub CLI authenticated as $(gh api user -q .login)"
        else
            echo "⚠️  GitHub CLI authentication check failed"
        fi
    else
        echo "⚠️  GH_TOKEN not found in .env - GitHub CLI not authenticated"
        echo "   Add GH_TOKEN=your_token to .env to enable GitHub CLI features"
    fi
fi

# Configure Poetry
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.in-project true

# Install Python dependencies
echo "📚 Installing Python dependencies..."
poetry install

# Set up pre-commit hooks (optional)
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Setting up pre-commit hooks..."
    poetry run pre-commit install || true
fi

# Install frontend dependencies and Playwright
if [ -d "autoarr/ui" ]; then
    echo "📦 Installing frontend dependencies..."
    cd autoarr/ui
    export PNPM_HOME="/root/.local/share/pnpm"
    export PATH="$PNPM_HOME:$PATH"
    pnpm install
    echo "🎭 Installing Playwright browsers..."
    pnpm exec playwright install --with-deps chromium
    cd /app
    echo "✅ Frontend dependencies and Playwright installed"
fi

# Display versions
echo ""
echo "✅ Setup complete!"
echo ""
echo "📌 Installed versions:"
python --version
poetry --version
node --version 2>/dev/null || echo "Node.js: not installed"
claude --version 2>/dev/null || echo "Claude CLI: not installed"
gh --version 2>/dev/null || echo "GitHub CLI: not installed"
echo ""
echo "🎯 Next steps:"
echo "  - Run Python tests: poetry run pytest"
echo "  - Run Playwright tests: cd autoarr/ui && pnpm exec playwright test"
echo "  - Run post-deployment tests: bash run-post-deployment-tests.sh"
echo "  - Start API: poetry run python -m api.main"
echo "  - Access API docs: http://localhost:8088/docs"
echo ""
