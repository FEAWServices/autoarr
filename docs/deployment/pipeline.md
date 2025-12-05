# AutoArr Deployment Pipeline

## Overview

AutoArr uses GitHub Actions to automatically build and publish Docker images to GitHub Container Registry (GHCR) whenever code is pushed to the `main` branch.

## Pipeline Workflow

### Trigger Events

The pipeline runs on:

- **Push to main** - Builds and publishes `latest` tag
- **Version tags** (`v*.*.*`) - Builds and publishes versioned tags
- **Pull requests** - Builds only (doesn't publish)
- **Manual trigger** - Via GitHub Actions UI

### Build Process

1. **Multi-stage Docker build**:

   - Stage 1: Build React frontend (Node.js)
   - Stage 2: Build Python backend + copy frontend assets

2. **Multi-platform images**:

   - `linux/amd64` (Intel/AMD processors)
   - `linux/arm64` (ARM processors, Apple Silicon, Synology ARM NAS)

3. **Image tags**:
   - `latest` - Always points to latest main branch
   - `v1.2.3` - Semantic version tags
   - `sha-abc123` - Git commit SHA tags

### Published Registry

Images are published to:

```
ghcr.io/yourusername/autoarr:latest
ghcr.io/yourusername/autoarr:v1.0.0
ghcr.io/yourusername/autoarr:sha-abc123
```

## Using the Images

### Pull Latest Image

```bash
docker pull ghcr.io/yourusername/autoarr:latest
```

### Use in docker-compose.yml

```yaml
services:
  autoarr:
    image: ghcr.io/yourusername/autoarr:latest
    # ... rest of config
```

## Synology NAS Setup

### Auto-Pull Updates

Synology Container Manager can automatically pull and update images:

1. **Container Manager** > **Registry**
2. Search for `ghcr.io/yourusername/autoarr`
3. Right-click > **Download Image**
4. Select `latest` tag
5. Enable **Auto-update** (checks for new images periodically)

### Manual Update

Via Container Manager UI:

1. **Project** > Select `autoarr`
2. **Action** > **Pull** (downloads latest image)
3. **Action** > **Restart** (recreates container with new image)

Via SSH:

```bash
cd /volume1/docker/autoarr
docker compose pull
docker compose up -d
```

## CI/CD Configuration

The pipeline is configured in `.github/workflows/docker-publish.yml`:

```yaml
on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
  pull_request:
    branches: [main]
```

### Required Secrets

The pipeline uses GitHub's built-in `GITHUB_TOKEN` for authentication to GHCR. No additional secrets needed.

### Build Cache

GitHub Actions cache is used to speed up builds:

- Frontend node_modules
- Backend Python packages
- Docker layer cache

## Versioning

### Creating a Release

To publish a versioned image:

1. Tag the commit:

   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. Pipeline automatically:
   - Builds image
   - Publishes with tags: `v1.0.0`, `v1.0`, `v1`, `latest`

### Version Format

Follow semantic versioning: `vMAJOR.MINOR.PATCH`

Example:

- `v1.0.0` - Initial release
- `v1.1.0` - New features (backward compatible)
- `v1.1.1` - Bug fixes
- `v2.0.0` - Breaking changes

## Monitoring Builds

### GitHub Actions

View build status:

1. Go to repository on GitHub
2. Click **Actions** tab
3. Select **Build and Publish Docker Image** workflow
4. View recent runs

### Build Artifacts

Each build creates:

- Docker image in GHCR
- Build attestation (provenance)
- Build logs

## Troubleshooting

### Build Fails

Check the Actions logs:

1. **Actions** > Failed workflow run
2. Expand failed step
3. Review error message

Common issues:

- Missing files (check Dockerfile COPY paths)
- Test failures (fix tests first)
- Node/Python dependency issues

### Image Not Pulling

Verify image exists:

```bash
docker pull ghcr.io/yourusername/autoarr:latest
```

If authentication required:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Synology Can't Find Image

Make sure you're using the full image path:

```
ghcr.io/yourusername/autoarr:latest
```

Not just:

```
yourusername/autoarr:latest  ❌
```

## Local Testing

Test the Dockerfile locally before pushing:

```bash
# Build image
docker build -t autoarr:test .

# Run container
docker run -p 8088:8088 \
  -e SABNZBD_URL=http://sabnzbd:8080 \
  -e SABNZBD_API_KEY=test \
  autoarr:test

# Access UI
open http://localhost:8088
```

## Resources

- **Dockerfile**: `/Dockerfile`
- **Workflow**: `/.github/workflows/docker-publish.yml`
- **Example Compose**: `/docker-compose.example.yml`
- **Docker Setup Guide**: `/docs/DOCKER_SETUP.md`
