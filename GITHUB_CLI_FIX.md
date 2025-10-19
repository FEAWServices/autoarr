# GitHub CLI Authentication Fix

## Problem

The `gh` CLI was installed in the devcontainer but **not authenticated**, causing commands like `gh pr list` to fail with:

```
To get started with GitHub CLI, please run:  gh auth login
```

## Root Cause Analysis

### What Was Missing

1. **No `GH_TOKEN` in `.env` file**
   - The `.env` file only contained Git credentials (`GIT_EMAIL`, `GIT_NAME`)
   - Missing: `GH_TOKEN=ghp_your_token_here`

2. **No authentication logic in `post-create.sh`**
   - The script installed `gh` CLI ✅
   - But never authenticated it using the token ❌

3. **No documentation**
   - `.env.example` didn't mention `GH_TOKEN`
   - DevContainer README didn't explain GitHub CLI setup

## Solution Implemented

### Files Modified

#### 1. `.devcontainer/post-create.sh`

**Added authentication logic after Git configuration:**

```bash
# Authenticate GitHub CLI if GH_TOKEN is set
if [ ! -z "$GH_TOKEN" ]; then
    echo "🔑 Authenticating GitHub CLI..."
    echo "$GH_TOKEN" | gh auth login --with-token
    gh auth status && echo "✅ GitHub CLI authenticated"
else
    echo "⚠️  GH_TOKEN not found in .env - GitHub CLI not authenticated"
    echo "   Add GH_TOKEN=your_token to .env to enable GitHub CLI features"
fi
```

#### 2. `.devcontainer/devcontainer.json`

**Added `GH_TOKEN` to remote environment variables:**

```json
"remoteEnv": {
  "PYTHONPATH": "/app:/app/mcp-servers",
  "PATH": "/root/.local/bin:${containerEnv:PATH}",
  "GH_TOKEN": "${localEnv:GH_TOKEN}"  // NEW
}
```

This allows the token to be passed from:

- Host machine environment variables, OR
- `.env` file in the container

#### 3. `.env.example`

**Added documentation for GH_TOKEN:**

```bash
# Git Configuration (for devcontainer)
GIT_EMAIL=your.email@example.com
GIT_NAME=Your Name

# GitHub Token (for devcontainer - optional)
# Create a Personal Access Token at: https://github.com/settings/tokens
# Scopes needed: repo, read:org, workflow
GH_TOKEN=
```

#### 4. `.devcontainer/README.md`

**Added comprehensive GitHub CLI section with:**

- Setup instructions
- Token creation guide
- Usage examples
- Troubleshooting tips

## How to Use the Fix

### Option 1: Add Token to `.env` (Recommended for Containers)

1. Create a GitHub Personal Access Token:
   - https://github.com/settings/tokens
   - Scopes: `repo`, `read:org`, `workflow`

2. Edit `/app/.env`:

   ```bash
   GIT_EMAIL=rob.duncan@feaw.co.uk
   GIT_NAME="Rob Duncan"
   GH_TOKEN=ghp_your_token_here  # ADD THIS LINE
   ```

3. Rebuild the devcontainer:
   - Press `F1` → "Dev Containers: Rebuild Container"

4. Verify:
   ```bash
   gh auth status
   ```

### Option 2: Set in Host Environment (More Secure)

1. Add to `~/.bashrc` or `~/.zshrc` on your HOST machine:

   ```bash
   export GH_TOKEN=ghp_your_token_here
   ```

2. Reload shell:

   ```bash
   source ~/.bashrc
   ```

3. Rebuild devcontainer (it will inherit the env var)

### Option 3: Manual Authentication (Temporary)

If you don't want to rebuild:

```bash
# Inside the container
gh auth login

# Follow prompts:
# 1. GitHub.com
# 2. HTTPS
# 3. Paste authentication token
# 4. Enter your GH_TOKEN
```

## Managing Pull Requests

Now that `gh` is authenticated, you can manage PRs:

```bash
# List all open PRs
gh pr list

# List only Dependabot PRs
gh pr list --author "app/dependabot"

# Close a specific PR
gh pr close <number>

# Bulk close all Dependabot PRs
gh pr list --author "app/dependabot" --json number --jq '.[].number' | \
  xargs -I {} gh pr close {}

# Close PR with comment
gh pr close <number> --comment "Closing outdated dependency update"
```

## Security Best Practices

- ✅ `.env` is in `.gitignore` - Won't be committed
- ✅ Use minimal token scopes (only what's needed)
- ✅ Rotate tokens every 90 days
- ✅ Consider using host environment variables instead of `.env`
- ✅ Delete tokens when no longer needed

## Testing the Fix

```bash
# Check if gh is installed
which gh
# Output: /usr/bin/gh

# Check version
gh --version
# Output: gh version 2.82.0 (2025-10-15)

# Check authentication
gh auth status
# Before fix: ✗ Not logged in
# After fix:  ✓ Logged in to github.com as YOUR_USERNAME
```

## What Happens on Next Rebuild

When you rebuild the devcontainer with `GH_TOKEN` in `.env`:

1. Container starts
2. `post-create.sh` runs
3. Sources `/app/.env`
4. Finds `GH_TOKEN`
5. Authenticates `gh` CLI automatically
6. Shows: "✅ GitHub CLI authenticated"

You'll never need to manually authenticate again (as long as token is valid).

## Troubleshooting

### "authentication token: invalid format"

- Token format: `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
- Check for extra spaces or newlines in `.env`

### "Bad credentials"

- Token might be expired or revoked
- Generate a new token at https://github.com/settings/tokens

### Authentication succeeds but `gh pr list` fails with 404

- Repository might be private
- Token needs `repo` scope (not just `public_repo`)
- Verify you have access to the repository

## Summary

The fix adds **automatic GitHub CLI authentication** during devcontainer creation by:

1. Reading `GH_TOKEN` from `.env` or host environment
2. Running `gh auth login --with-token` in `post-create.sh`
3. Providing clear documentation and troubleshooting

No more manual `gh auth login` required!
