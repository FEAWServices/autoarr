# GitHub Repository Setup Guide

This guide explains how to configure GitHub secrets and settings for AutoArr's automated release and deployment workflows.

## Table of Contents

- [Required Secrets](#required-secrets)
- [Optional Secrets](#optional-secrets)
- [Setting Up Docker Hub](#setting-up-docker-hub)
- [Configuring GitHub Actions](#configuring-github-actions)
- [Verifying Setup](#verifying-setup)
- [Troubleshooting](#troubleshooting)

---

## Required Secrets

These secrets are **required** for the automated release process to work correctly.

### 1. Docker Hub Authentication

#### `DOCKERHUB_USERNAME`

**Purpose:** Your Docker Hub username for pushing images during releases.

**Setup:**

1. If you don't have a Docker Hub account, create one at https://hub.docker.com/signup
2. Note your username (this is what you'll use in the secret)

**How to Set:**

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `DOCKERHUB_USERNAME`
5. Value: Your Docker Hub username (e.g., `myusername`)
6. Click **Add secret**

#### `DOCKERHUB_TOKEN`

**Purpose:** Access token for authenticating to Docker Hub (more secure than using password).

**Setup:**

1. Log in to Docker Hub: https://hub.docker.com/
2. Click your profile icon → **Account Settings**
3. Go to **Security** → **Personal Access Tokens** (or **Access Tokens**)
4. Click **New Access Token**
5. Configure:
   - **Description:** `AutoArr GitHub Actions` (or similar)
   - **Access permissions:** Select **Read, Write, Delete**
   - **Expiration:** Choose based on your preference (no expiration recommended for automation)
6. Click **Generate**
7. **IMPORTANT:** Copy the token immediately (you won't be able to see it again!)

**How to Set:**

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `DOCKERHUB_TOKEN`
5. Value: Paste the token you copied from Docker Hub
6. Click **Add secret**

**Security Notes:**

- Never share this token or commit it to your repository
- If you suspect it's been compromised, immediately revoke it in Docker Hub and create a new one
- Update the GitHub secret with the new token

---

## Optional Secrets

These secrets are optional and can be added for additional functionality in the future.

### Synology Deployment (Future)

#### `SYNOLOGY_HOST`

**Purpose:** Hostname or IP address of your Synology NAS for automated deployment.

#### `SYNOLOGY_USER`

**Purpose:** SSH username for Synology NAS access.

#### `SYNOLOGY_SSH_KEY`

**Purpose:** Private SSH key for authenticating to Synology NAS.

_Note: These are currently commented out in the workflow but can be enabled for automated Synology deployments._

---

## Setting Up Docker Hub

### Creating a Repository

1. Log in to Docker Hub: https://hub.docker.com/
2. Click **Create Repository**
3. Configure:
   - **Name:** `autoarr`
   - **Visibility:** Public (recommended for open-source projects)
   - **Description:** "Intelligent orchestration layer for media automation stacks"
4. Click **Create**

Your Docker Hub repository URL will be: `https://hub.docker.com/r/YOUR_USERNAME/autoarr`

### Verifying Repository Access

```bash
# Test login locally
echo $DOCKERHUB_TOKEN | docker login -u YOUR_USERNAME --password-stdin

# Test pulling (after first release)
docker pull YOUR_USERNAME/autoarr:latest
```

---

## Configuring GitHub Actions

### Branch Protection Rules (Recommended)

Protect your `main` branch to ensure code quality:

1. Go to **Settings** → **Branches**
2. Click **Add rule** or edit existing rule for `main`
3. Configure:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
     - Select: `Python CI`, `Frontend CI`
   - ✅ **Require branches to be up to date before merging**
   - ✅ **Include administrators** (optional but recommended)
4. Click **Save changes**

### Workflow Permissions

Ensure GitHub Actions has sufficient permissions:

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**:
   - Select: **Read and write permissions**
   - ✅ Enable: **Allow GitHub Actions to create and approve pull requests**
3. Click **Save**

### Enabling GitHub Container Registry (GHCR)

GHCR is automatically enabled, but ensure packages are public:

1. After first release, go to your repository's **Packages** tab
2. Click on the `autoarr` package
3. Click **Package settings**
4. Under **Danger Zone** → **Change visibility**
5. Select **Public** and confirm

---

## Verifying Setup

### Pre-Flight Checklist

Before creating your first release, verify:

- [ ] `DOCKERHUB_USERNAME` secret is set
- [ ] `DOCKERHUB_TOKEN` secret is set and valid
- [ ] Docker Hub repository `YOUR_USERNAME/autoarr` exists
- [ ] GitHub Actions has read/write permissions
- [ ] Branch protection rules configured for `main`
- [ ] Workflow files are present in `.github/workflows/`
- [ ] `release-please-config.json` and `.release-please-manifest.json` exist

### Testing the Workflow

You can test without creating a release:

1. **Test Docker Login** (locally):

   ```bash
   echo $DOCKERHUB_TOKEN | docker login -u YOUR_USERNAME --password-stdin
   docker pull python:3.11-slim
   docker tag python:3.11-slim YOUR_USERNAME/autoarr:test
   docker push YOUR_USERNAME/autoarr:test
   docker rmi YOUR_USERNAME/autoarr:test
   ```

2. **Test GitHub Actions Syntax**:

   ```bash
   # Install actionlint (GitHub Actions linter)
   brew install actionlint  # macOS
   # or
   go install github.com/rhysd/actionlint/cmd/actionlint@latest

   # Run linter
   actionlint .github/workflows/*.yml
   ```

3. **Trigger a Test Run**:
   - Create a feature branch
   - Add a conventional commit: `feat: test release workflow`
   - Push to GitHub and create a PR
   - Merge to main
   - Check **Actions** tab for workflow execution

---

## Troubleshooting

### Docker Hub Push Fails

**Error:** `denied: requested access to the resource is denied`

**Solution:**

1. Verify `DOCKERHUB_USERNAME` matches your actual Docker Hub username (case-sensitive)
2. Verify `DOCKERHUB_TOKEN` is valid and not expired
3. Ensure Docker Hub repository exists: `YOUR_USERNAME/autoarr`
4. Check token permissions include "Read, Write, Delete"

**How to Fix:**

```bash
# Revoke old token in Docker Hub
# Create new token with correct permissions
# Update GitHub secret with new token
```

### Release Please Not Triggering

**Error:** No release PR created after merging to main.

**Solution:**

1. Verify commits use conventional commit format:
   ```bash
   git log --oneline main
   # Should see: feat: description, fix: description
   ```
2. Check Release Please workflow logs in **Actions** tab
3. Ensure `.release-please-manifest.json` exists and is valid JSON
4. Check branch name is exactly `main` (not `master`)

### GitHub Actions Permission Denied

**Error:** `Resource not accessible by integration`

**Solution:**

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Enable **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### Docker Build Takes Too Long

**Error:** Workflow timeout or slow builds.

**Solution:**

1. GitHub Actions caching is enabled (`cache-from: type=gha`)
2. First build takes longer (15-30 minutes)
3. Subsequent builds use cache and are much faster (5-10 minutes)
4. If still slow, consider using self-hosted runners

---

## Security Best Practices

1. **Never Commit Secrets**

   - Always use GitHub Secrets for sensitive data
   - Never hardcode tokens in workflow files
   - Add `.env*` to `.gitignore`

2. **Rotate Tokens Regularly**

   - Update Docker Hub tokens every 90 days
   - Monitor Docker Hub security alerts
   - Revoke unused tokens immediately

3. **Limit Token Permissions**

   - Use minimal required permissions
   - Create separate tokens for different purposes
   - Document token purpose in Docker Hub description

4. **Monitor Workflow Runs**

   - Review failed workflow runs in Actions tab
   - Check for suspicious activity
   - Enable GitHub security alerts

5. **Audit Access**
   - Regularly review repository collaborators
   - Check who has access to secrets
   - Use branch protection rules

---

## Additional Resources

- **Docker Hub Documentation**: https://docs.docker.com/docker-hub/
- **GitHub Actions Secrets**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Release Please**: https://github.com/googleapis/release-please
- **Conventional Commits**: https://www.conventionalcommits.org/

---

## Quick Reference

### Required Secrets Summary

| Secret Name          | Purpose                 | Where to Get                          |
| -------------------- | ----------------------- | ------------------------------------- |
| `DOCKERHUB_USERNAME` | Docker Hub username     | Your Docker Hub account               |
| `DOCKERHUB_TOKEN`    | Docker Hub access token | Docker Hub → Security → Access Tokens |

### Common Commands

```bash
# Create Docker Hub token
# Visit: https://hub.docker.com/settings/security

# Test Docker Hub login
echo $DOCKERHUB_TOKEN | docker login -u YOUR_USERNAME --password-stdin

# Test GitHub Actions locally (using act)
act -j docker-release --secret-file .secrets

# Trigger manual workflow run
gh workflow run release-please.yml
```

---

## Support

If you encounter issues:

1. Check GitHub Actions logs: **Actions** tab → Select workflow run
2. Review this guide's troubleshooting section
3. Search existing issues: https://github.com/FEAWServices/autoarr/issues
4. Create new issue with:
   - Workflow run link
   - Error message
   - Steps to reproduce

---

_Last Updated: 2025-12-08_
_Version: 1.0_
