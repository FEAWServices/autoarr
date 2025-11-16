# AutoArr Dev Container

This directory contains the configuration for the Visual Studio Code Dev Container.

## What's Included

- **Python 3.11** - Pre-installed
- **Poetry** - Pre-installed and configured
- **Node.js 18** - For UI development
- **Docker-in-Docker** - For building and testing containers
- **VS Code Extensions** - Python, Pylance, Black, Ruff, GitLens, Docker

## Getting Started

1. **Install Prerequisites**
   - [Visual Studio Code](https://code.visualstudio.com/)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in Container**
   - Open VS Code
   - Press `F1` or `Ctrl+Shift+P`
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build (first time takes 2-5 minutes)

3. **Verify Poetry Installation**

   ```bash
   poetry --version
   ```

4. **Install Dependencies** (done automatically via postCreateCommand)

   ```bash
   poetry install
   ```

5. **Run Tests**

   ```bash
   poetry run pytest
   ```

6. **Start the API Server**
   ```bash
   poetry run python -m api.main
   ```

## Ports

The following ports are automatically forwarded:

- **8088** - AutoArr API
- **3000** - AutoArr UI
- **8080** - SABnzbd
- **8989** - Sonarr
- **7878** - Radarr
- **32400** - Plex
- **5432** - PostgreSQL
- **6379** - Redis

## Python Path

The `PYTHONPATH` is automatically set to include:

- `/app` - Project root
- `/app/mcp-servers` - MCP server modules

## VS Code Settings

The container includes pre-configured settings for:

- Black code formatting on save
- Ruff linting
- Import organization on save
- Python interpreter pointing to Poetry venv

## GitHub CLI Authentication

The GitHub CLI (`gh`) is pre-installed but requires authentication to manage PRs and issues.

### Setup GitHub Token

1. **Create a Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Required scopes: `repo`, `read:org`, `workflow`
   - Copy the token (starts with `ghp_`)

2. **Add Token to .env**

   ```bash
   # Edit /app/.env
   GIT_EMAIL=your.email@example.com
   GIT_NAME=Your Name
   GH_TOKEN=ghp_your_token_here
   ```

3. **Rebuild Container**
   - Press `F1` → "Dev Containers: Rebuild Container"

4. **Verify Authentication**
   ```bash
   gh auth status
   # Should show: ✓ Logged in to github.com
   ```

### Using GitHub CLI

```bash
# List pull requests
gh pr list

# Close a PR
gh pr close <number>

# Bulk close Dependabot PRs
gh pr list --author "app/dependabot" --json number --jq '.[].number' | \
  xargs -I {} gh pr close {}
```

## Troubleshooting

### "gh: To get started with GitHub CLI, please run: gh auth login"

**Fix**: Add `GH_TOKEN` to `/app/.env` and rebuild container

### Poetry not found

If Poetry is not found after rebuild:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/opt/poetry/bin:$PATH"
```

### Dependencies not installed

```bash
poetry install
```

### Python interpreter not detected

1. Press `F1`
2. Type "Python: Select Interpreter"
3. Choose `/app/.venv/bin/python`
