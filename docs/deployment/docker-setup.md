# Docker Setup Guide

## Quick Start

### 1. Create docker-compose.yml

Copy the example compose file:

```bash
cp docker-compose.example.yml docker-compose.yml
```

### 2. Create .env file

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# SABnzbd
SABNZBD_API_KEY=your_actual_key

# Sonarr
SONARR_API_KEY=your_actual_key

# Radarr
RADARR_API_KEY=your_actual_key

# Plex
PLEX_TOKEN=your_actual_token
```

### 3. Create data directories

```bash
mkdir -p data logs
```

### 4. Start the container

```bash
docker compose up -d
```

### 5. Access the UI

Open your browser to: http://localhost:8088

## Synology NAS Setup

### Using Container Manager UI

1. **Open Container Manager** in Synology DSM
2. **Registry** > Search for `ghcr.io/yourusername/autoarr`
3. **Download** the `latest` tag
4. **Image** > Select autoarr > **Launch**
5. Configure:
   - **Container Name**: `autoarr`
   - **Port**: 8088 → 8088
   - **Volume**: Add folder `/docker/autoarr/data` → `/data`
   - **Environment**: Add your API keys (see below)

### Environment Variables for Synology

In Container Manager, add these environment variables:

| Variable          | Value                 |
| ----------------- | --------------------- |
| `SABNZBD_URL`     | `http://sabnzbd:8080` |
| `SABNZBD_API_KEY` | Your SABnzbd API key  |
| `SONARR_URL`      | `http://sonarr:8989`  |
| `SONARR_API_KEY`  | Your Sonarr API key   |
| `RADARR_URL`      | `http://radarr:7878`  |
| `RADARR_API_KEY`  | Your Radarr API key   |
| `PLEX_URL`        | `http://plex:32400`   |
| `PLEX_TOKEN`      | Your Plex token       |

### Using SSH (Advanced)

1. SSH into your Synology NAS
2. Create directories:

   ```bash
   mkdir -p /volume1/docker/autoarr/data
   mkdir -p /volume1/docker/autoarr/logs
   cd /volume1/docker/autoarr
   ```

3. Create `docker-compose.yml` (copy content from example)
4. Create `.env` file with your API keys
5. Start container:
   ```bash
   docker compose up -d
   ```

## Networking

### Connect to Existing Media Stack Network

If your \*arr apps are on a custom network, add this to your `docker-compose.yml`:

```yaml
networks:
  media-stack:
    external: true
    name: your_network_name
```

Then add to the autoarr service:

```yaml
services:
  autoarr:
    # ... other config ...
    networks:
      - media-stack
```

### Using Synology Container Manager

1. **Container Manager** > **Network**
2. Select your media network
3. Click **Join** > Select `autoarr` container

## Updating

### Pull Latest Image

```bash
docker compose pull
docker compose up -d
```

### Synology Container Manager

1. **Project** > Select `autoarr`
2. **Action** > **Pull**
3. **Action** > **Restart**

## Troubleshooting

### Container Won't Start

Check logs:

```bash
docker compose logs -f autoarr
```

### Can't Connect to Services

Verify service URLs and API keys in your environment variables.

Test connectivity from inside container:

```bash
docker exec autoarr curl http://sabnzbd:8080/api?mode=version
```

### Health Check Fails

```bash
curl http://localhost:8088/health
```

Expected response when services are configured:

```json
{
  "status": "healthy",
  "services": {
    "sabnzbd": { "healthy": true },
    "sonarr": { "healthy": true },
    "radarr": { "healthy": true },
    "plex": { "healthy": true }
  }
}
```

## Backup

Simply backup the `/data` directory:

```bash
# Backup
tar czf autoarr-backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar xzf autoarr-backup-YYYYMMDD.tar.gz
```

## Advanced Configuration

### External PostgreSQL (Optional)

```yaml
environment:
  DATABASE_URL: postgresql://user:password@postgres:5432/autoarr
```

### External Redis (Optional)

```yaml
environment:
  REDIS_URL: redis://redis:6379/0
```

### Multiple Workers (High Traffic)

Edit `docker-compose.yml` CMD:

```yaml
command:
  [
    "uvicorn",
    "autoarr.api.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8088",
    "--workers",
    "4",
  ]
```

## Support

- **Documentation**: [GitHub Docs](https://github.com/yourusername/autoarr/docs)
- **Issues**: [GitHub Issues](https://github.com/yourusername/autoarr/issues)
- **Deployment Guide**: [DEPLOYMENT.md](../DEPLOYMENT.md)
