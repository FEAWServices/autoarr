# AutoArr Synology Deployment Guide

This guide will help you deploy AutoArr on your Synology NAS using Docker Compose and the GitHub Container Registry (GHCR) image.

## Fast Deployment Pipeline

AutoArr is configured for rapid deployment with automatic updates:

| Step                         | Duration     |
| ---------------------------- | ------------ |
| PR merged to main            | 0 min        |
| Docker build & push to GHCR  | ~3-5 min     |
| Watchtower detects new image | ~0-2 min     |
| Container restart            | ~30 sec      |
| **Total**                    | **~5-8 min** |

## Prerequisites

### 1. Synology Setup

- Synology NAS with DSM 7.0 or later
- Container Manager package installed (from Package Center)
- SSH access enabled (optional, for command-line deployment)

### 2. Existing Services

AutoArr works with your existing media automation stack:

- **SABnzbd** (Usenet downloader)
- **Sonarr** (TV show manager)
- **Radarr** (Movie manager)
- **Plex** (Media server)

> **Note**: These can be running on the same Synology NAS or on different machines on your network.

### 3. API Keys

You'll need API keys for each service:

- SABnzbd: Config > General > API Key
- Sonarr: Settings > General > Security > API Key
- Radarr: Settings > General > Security > API Key
- Plex Token: [See instructions below](#getting-your-plex-token)

## Quick Start (SSH)

```bash
# SSH into your Synology
ssh admin@your-synology-ip
sudo -i

# Create directory
mkdir -p /volume1/docker/autoarr/{data,logs}
cd /volume1/docker/autoarr

# Download docker-compose file (includes Watchtower for auto-updates)
curl -O https://raw.githubusercontent.com/FEAWServices/autoarr/main/docker/docker-compose.synology.yml

# Start the stack
docker compose -f docker-compose.synology.yml up -d
```

That's it! AutoArr will be available at `http://your-synology-ip:8088` and will automatically update when new versions are released.

## Container Manager UI Method

### Step 1: Create Directory Structure

1. Open **File Station**
2. Navigate to `/docker/` (create if it doesn't exist)
3. Create folders: `/docker/autoarr/data/` and `/docker/autoarr/logs/`

### Step 2: Download Configuration

1. Download `docker-compose.synology.yml` from:
   `https://raw.githubusercontent.com/FEAWServices/autoarr/main/docker/docker-compose.synology.yml`
2. Upload to `/docker/autoarr/`

### Step 3: Deploy with Container Manager

1. Open **Container Manager**
2. Go to **Project** tab
3. Click **Create**
4. Configure:
   - **Project Name**: `autoarr`
   - **Path**: `/docker/autoarr`
   - **Source**: Select `docker-compose.synology.yml`
5. Click **Next**, review settings, then **Done**

## Automatic Updates with Watchtower

The Synology compose file includes Watchtower, which automatically pulls new images when they're released.

**How it works:**

- Watchtower polls GHCR every 2 minutes
- When a new `staging` tag is detected, it pulls the image
- AutoArr container is automatically restarted with the new version

**Check Watchtower status:**

```bash
docker logs watchtower
```

**Force immediate update:**

```bash
docker exec watchtower /watchtower --run-once
```

See [WATCHTOWER.md](../WATCHTOWER.md) for more configuration options.

## Accessing AutoArr

Once deployed:

- **Web UI**: `http://your-synology-ip:8088`
- **API Docs**: `http://your-synology-ip:8088/docs`
- **Health Check**: `http://your-synology-ip:8088/health`

Configure your services (SABnzbd, Sonarr, Radarr, Plex) via the Settings page in the web UI.

## Configuration

### Environment Variables

The docker-compose file includes sensible defaults. To customize, edit the `environment` section:

```yaml
environment:
  - PUID=1026 # Your user ID
  - PGID=100 # Your group ID
  - TZ=Europe/London # Your timezone
  - LOG_LEVEL=INFO # DEBUG, INFO, WARNING, ERROR
```

### Network Configuration

**Default (Bridge Network)**: Services are accessed by IP address. No changes needed.

**Join Existing Network**: If your \*arr stack is in a Docker network:

```yaml
networks:
  media-stack:
    external: true
    name: your_existing_network_name
```

## Manual Updates

If you prefer manual updates over Watchtower:

### Via Container Manager

1. Go to **Project** > `autoarr`
2. Click **Action** > **Pull**
3. Click **Action** > **Restart**

### Via SSH

```bash
cd /volume1/docker/autoarr
docker compose -f docker-compose.synology.yml pull autoarr
docker compose -f docker-compose.synology.yml up -d autoarr
```

## Troubleshooting

### Container Won't Start

```bash
docker compose -f docker-compose.synology.yml logs autoarr
```

### Can't Connect to Services

Test connectivity from inside the container:

```bash
docker exec autoarr curl http://192.168.1.100:8080/api?mode=version
```

### Permission Issues

```bash
sudo chown -R 1026:100 /volume1/docker/autoarr/data
sudo chmod -R 755 /volume1/docker/autoarr/data
```

### View Live Logs

```bash
docker compose -f docker-compose.synology.yml logs -f autoarr
```

## Getting Your Plex Token

1. Go to Plex Web App (app.plex.tv)
2. Play any media
3. Click the "..." menu > "Get Info"
4. Click "View XML"
5. Look for `X-Plex-Token` in the URL

## Backup and Restore

### Backup

```bash
cd /volume1/docker/autoarr
tar czf autoarr-backup-$(date +%Y%m%d).tar.gz data/
```

### Restore

```bash
docker compose -f docker-compose.synology.yml down
tar xzf autoarr-backup-YYYYMMDD.tar.gz
docker compose -f docker-compose.synology.yml up -d
```

## Resource Usage

Default limits:

- **CPU**: 2 cores max, 0.5 cores reserved
- **Memory**: 1GB max, 512MB reserved

Adjust in `docker-compose.synology.yml` if needed.

## Security Recommendations

1. **Reverse Proxy**: Use Synology's built-in reverse proxy or Nginx Proxy Manager
2. **HTTPS**: Configure SSL certificates through DSM
3. **Firewall**: Restrict AutoArr port to your local network
4. **Network**: Keep AutoArr on the same network as your \*arr stack

## Uninstalling

```bash
cd /volume1/docker/autoarr
docker compose -f docker-compose.synology.yml down -v
rm -rf /volume1/docker/autoarr  # Remove all data
```

## Support

- **GitHub Issues**: https://github.com/FEAWServices/autoarr/issues
- **Documentation**: https://github.com/FEAWServices/autoarr/tree/main/docs
