# Release Management Guide

This document explains how AutoArr's automated release process works and how maintainers can create new releases.

## Overview

AutoArr uses [Release Please](https://github.com/googleapis/release-please) for automated release management. The process is fully automated - you just need to follow conventional commit messages and merge to main.

## Automated Release Process

### How It Works

1. **Conventional Commits** → Release Please scans commit messages
2. **Automatic PR Creation** → Creates a release PR with updated changelog
3. **Merge to Main** → Triggers automated release workflow
4. **Release Artifacts** → Builds and publishes:
   - Docker images (GHCR + Docker Hub)
   - Native executables (Linux, Windows, macOS)
   - Checksums and security scans

### Version Bumping

Release Please automatically determines version bumps based on conventional commits:

- `feat:` → Minor version bump (0.8.0 → 0.9.0)
- `fix:` → Patch version bump (0.8.0 → 0.8.1)
- `feat!:` or `BREAKING CHANGE:` → Major version bump (0.8.0 → 1.0.0)
- `chore:`, `docs:`, `test:` → No version bump (included in next release)

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Examples:**

```bash
feat: add download retry with exponential backoff
fix: resolve authentication timeout in Radarr integration
feat!: migrate from SQLite to PostgreSQL by default

BREAKING CHANGE: PostgreSQL is now the default database.
Users must set DATABASE_URL environment variable.
```

**Common Types:**

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks
- `refactor:` - Code refactoring
- `test:` - Test updates
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

## Creating a Release (Step by Step)

### 1. Develop with Conventional Commits

Work on features/fixes using conventional commit messages:

```bash
git checkout -b feature/new-feature
# Make changes
git commit -m "feat: add intelligent content classification"
git push origin feature/new-feature
```

### 2. Merge Feature Branch to Main

```bash
# Create PR and merge to main
gh pr create --title "feat: add intelligent content classification"
# Review and merge
```

### 3. Release Please Creates Release PR

After merging to main, Release Please automatically:

- Analyzes commits since last release
- Determines version bump (patch/minor/major)
- Updates `CHANGELOG.md` with commit history
- Updates version in:
  - `pyproject.toml`
  - `autoarr/ui/package.json`
  - `sonar-project.properties`
  - `.release-please-manifest.json`
- Creates PR titled: `chore: release X.Y.Z`

### 4. Review and Merge Release PR

**Check the release PR:**

1. Verify version bump is correct
2. Review CHANGELOG.md entries
3. Ensure all version files are updated
4. Add any manual release notes if needed

**Merge the release PR:**

```bash
gh pr merge <release-pr-number> --squash
```

### 5. Automated Release Workflow

Once the release PR is merged, GitHub Actions automatically:

**Docker Images:**

- Builds multi-arch images (linux/amd64, linux/arm64)
- Pushes to GitHub Container Registry (ghcr.io)
- Pushes to Docker Hub (docker.io)
- Tags: `latest`, `X.Y.Z`, `X.Y`

**Native Executables:**

- Builds standalone executables for:
  - Linux (x64)
  - Windows (x64)
  - macOS (x64, ARM64)
- Uploads to GitHub release

**Security & Verification:**

- Generates SHA256 checksums
- Runs Trivy security scan
- Creates GitHub release with all artifacts

### 6. Verify Release

After the workflow completes (15-30 minutes):

1. **Check GitHub Release:** https://github.com/YOUR_ORG/autoarr/releases

   - Verify version tag (vX.Y.Z)
   - Confirm all native executables are attached
   - Check SHA256SUMS.txt is present

2. **Verify Docker Hub:** https://hub.docker.com/r/YOUR_USERNAME/autoarr

   - Confirm `latest` tag is updated
   - Verify version tags (X.Y.Z, X.Y)
   - Check both amd64 and arm64 manifests

3. **Verify GHCR:** https://github.com/YOUR_ORG/autoarr/pkgs/container/autoarr

   - Confirm image is published
   - Check multi-arch support

4. **Test Installation:**

   ```bash
   # Test Docker Hub
   docker pull YOUR_USERNAME/autoarr:latest
   docker run --rm YOUR_USERNAME/autoarr:latest --version

   # Test GHCR
   docker pull ghcr.io/YOUR_ORG/autoarr:latest
   docker run --rm ghcr.io/YOUR_ORG/autoarr:latest --version
   ```

## Required GitHub Secrets

The following secrets must be configured in GitHub repository settings:

### Docker Hub Secrets

1. **DOCKERHUB_USERNAME** - Your Docker Hub username

   - Navigate to: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `DOCKERHUB_USERNAME`
   - Value: Your Docker Hub username

2. **DOCKERHUB_TOKEN** - Docker Hub access token
   - Create token at: https://hub.docker.com/settings/security
   - Select "Read, Write, Delete" permissions
   - Name: `DOCKERHUB_TOKEN`
   - Value: The generated token

### Automatic Secrets

These are automatically available:

- `GITHUB_TOKEN` - Provided by GitHub Actions (no setup needed)

## Troubleshooting

### Release PR Not Created

**Problem:** No release PR appears after merging to main.

**Solutions:**

1. Check commit messages use conventional commit format
2. Verify commits include user-facing changes (not just chore/test)
3. Check Release Please workflow logs in Actions tab
4. Ensure `.release-please-manifest.json` exists and is valid

### Docker Hub Push Fails

**Problem:** Docker release job fails with authentication error.

**Solutions:**

1. Verify `DOCKERHUB_USERNAME` secret is set correctly
2. Verify `DOCKERHUB_TOKEN` is valid and not expired
3. Check Docker Hub token has "Read, Write, Delete" permissions
4. Ensure repository name matches: `YOUR_USERNAME/autoarr`

### Native Build Fails

**Problem:** Native executable build fails on specific platform.

**Solutions:**

1. Check PyInstaller compatibility with Python version
2. Review platform-specific build logs in Actions
3. Verify dependencies are compatible with target platform
4. Consider marking platform as `continue-on-error: true` if optional

### Version Not Bumped Correctly

**Problem:** Version bump is too small/large.

**Solutions:**

1. Review commit messages - ensure correct prefixes
2. Use `feat!:` or `BREAKING CHANGE:` footer for major bumps
3. Close the release PR and amend commits with correct types
4. Re-push to main to trigger new release PR

## Manual Release (Emergency)

In rare cases, you may need to create a manual release:

### 1. Update Version Manually

```bash
# Edit version in all files
vim .release-please-manifest.json  # Set version
vim pyproject.toml                  # Update version
vim autoarr/ui/package.json        # Update version
vim sonar-project.properties       # Update version

# Update CHANGELOG.md
vim CHANGELOG.md  # Add release notes

# Commit changes
git add .
git commit -m "chore: release X.Y.Z"
git push origin main
```

### 2. Create Git Tag

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

### 3. Trigger GitHub Release

Push the tag to trigger the release workflow, or create release manually:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes "Release notes here" \
  --draft
```

## Release Checklist

Use this checklist when creating a release:

- [ ] All features merged to main with conventional commits
- [ ] Release PR created by Release Please
- [ ] CHANGELOG.md entries reviewed
- [ ] Version bump is correct (patch/minor/major)
- [ ] Release PR merged to main
- [ ] Docker images published to Docker Hub and GHCR
- [ ] Native executables built for all platforms
- [ ] SHA256 checksums generated
- [ ] GitHub release created with all artifacts
- [ ] Installation tested with Docker Hub image
- [ ] Release notes include breaking changes (if any)
- [ ] Documentation updated for new version
- [ ] Announcement posted (if major release)

## Release Schedule

AutoArr follows semantic versioning:

- **Patch releases (0.8.X)** - Bug fixes, security patches (as needed)
- **Minor releases (0.X.0)** - New features, enhancements (monthly)
- **Major releases (X.0.0)** - Breaking changes, major refactors (quarterly)

## Resources

- [Release Please Documentation](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Docker Hub Publishing](https://docs.docker.com/docker-hub/)
- [GitHub Actions Workflows](.github/workflows/)

## Support

If you encounter issues with the release process:

1. Check GitHub Actions logs for errors
2. Review this guide for troubleshooting steps
3. Open an issue: https://github.com/YOUR_ORG/autoarr/issues
4. Contact maintainers in discussions

---

_Last Updated: 2025-12-08_
_Version: 1.0_
