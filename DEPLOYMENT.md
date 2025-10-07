# AutoArr Deployment Guide

AutoArr is designed as a **single, self-contained Docker container** - just like Sonarr and Radarr! No external database required.

## Quick Start

### Local Development (DevContainer)

Test the API locally in your browser:

```bash
./run_dev.sh
```

Then open:

- **API**: http://localhost:8088
- **API Docs**: http://localhost:8088/docs
- **Health Check**: http://localhost:8088/health

### Production Deployment Options

#### Option 1: Synology NAS (Recommended)

See [Synology Deployment Guide](docs/SYNOLOGY_DEPLOYMENT.md) for detailed instructions.

**Quick Deploy:**

1. Create folders: `/volume1/docker/autoarr/{data,logs}`
2. Create your own `docker-compose.yml` based on the example in docs
3. Configure `.env` with your API keys
4. Deploy via Container Manager or SSH

#### Option 2: Docker Compose (Any Linux/macOS)

```bash
# Create your docker-compose.yml and .env file
# Then start the container
docker compose up -d
```

#### Option 3: Docker CLI

```bash
docker run -d \
  --name autoarr \
  -p 8088:8088 \
  -v ./data:/data \
  -e SABNZBD_URL=http://sabnzbd:8080 \
  -e SABNZBD_API_KEY=your_key \
  -e SONARR_URL=http://sonarr:8989 \
  -e SONARR_API_KEY=your_key \
  -e RADARR_URL=http://radarr:7878 \
  -e RADARR_API_KEY=your_key \
  -e PLEX_URL=http://plex:32400 \
  -e PLEX_TOKEN=your_token \
  ghcr.io/yourusername/autoarr:latest
```

## Architecture

AutoArr is a **single container** that includes:

- ✅ FastAPI backend
- ✅ React frontend (pre-built, served by backend)
- ✅ SQLite database (no PostgreSQL needed!)
- ✅ In-memory Redis (optional external Redis for clustering)
- ✅ All MCP servers (SABnzbd, Sonarr, Radarr, Plex)

**Just like Sonarr/Radarr:**

- Uses embedded SQLite for data storage
- No external database required
- Single Docker container deployment
- Data persisted in `/data` volume

## Image Registry

Docker images are automatically published to GitHub Container Registry (GHCR) on every push to `main`:

- **Latest**: `ghcr.io/yourusername/autoarr:latest`
- **Version**: `ghcr.io/yourusername/autoarr:v1.0.0`
- **SHA**: `ghcr.io/yourusername/autoarr:sha-abc123`

### Building the Image

The GitHub Actions workflow automatically builds and publishes multi-platform images:

- `linux/amd64` (Intel/AMD)
- `linux/arm64` (ARM/Apple Silicon/Synology with ARM)

## Configuration

### Required Environment Variables

```bash
# SABnzbd (Usenet downloader)
SABNZBD_URL=http://sabnzbd:8080
SABNZBD_API_KEY=your_sabnzbd_api_key

# Sonarr (TV shows)
SONARR_URL=http://sonarr:8989
SONARR_API_KEY=your_sonarr_api_key

# Radarr (Movies)
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your_radarr_api_key

# Plex (Media server)
PLEX_URL=http://plex:32400
PLEX_TOKEN=your_plex_token
```

### Optional Environment Variables

```bash
# AI Features (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Web Search
BRAVE_API_KEY=...

# Application Settings
APP_ENV=production
LOG_LEVEL=INFO
PORT=8088

# Database (defaults to SQLite)
DATABASE_URL=sqlite:////data/autoarr.db

# Redis (defaults to in-memory)
REDIS_URL=memory://
```

## Data Persistence

AutoArr stores all data in `/data`:

```
/data/
├── autoarr.db          # SQLite database (like Sonarr/Radarr)
├── config/             # Application configuration
└── cache/              # Temporary cache files
```

**Backup**: Simply backup the `/data` directory!

```bash
# Backup
tar czf autoarr-backup.tar.gz /volume1/docker/autoarr/data/

# Restore
tar xzf autoarr-backup.tar.gz -C /
```

## Updating

### Update from GHCR (Synology)

**Via Container Manager:**

1. Project > autoarr > Action > Pull
2. Action > Restart

**Via SSH:**

```bash
cd /volume1/docker/autoarr
docker compose pull
docker compose up -d
```

### Update from Local Build

```bash
# Rebuild and restart
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

### Container Won't Start

Check logs:

```bash
docker logs autoarr
# or
docker compose logs -f
```

### Can't Connect to Services

1. Verify URLs are correct (use IP addresses if hostnames don't resolve)
2. Test connectivity from inside container:

```bash
docker exec autoarr curl http://sabnzbd:8080/api?mode=version
```

### Health Check Fails

```bash
curl http://localhost:8088/health
```

If services are not configured, you'll see:

```json
{
  "status": "unhealthy",
  "services": {},
  "timestamp": "..."
}
```

This is normal if API keys aren't configured yet.

### Database Issues

AutoArr uses SQLite by default (just like Sonarr/Radarr). If you have database issues:

```bash
# Check database file
docker exec autoarr ls -lh /data/autoarr.db

# Reset database (caution: deletes all data!)
docker exec autoarr rm /data/autoarr.db
docker restart autoarr
```

## Network Configuration

### Same Docker Network as \*arr Stack

To communicate with Sonarr/Radarr/etc by hostname:

**Edit docker-compose.yml:**

```yaml
networks:
  media-stack:
    external: true
    name: your_existing_network_name
```

**Or use Synology Container Manager UI:**

1. Container Manager > Network
2. Select your network
3. Click "Join" > Select autoarr container

### Firewall / Port Forwarding

- **Internal Access**: Only port 8088 needs to be exposed
- **External Access**: Use reverse proxy (Nginx, Traefik, Synology reverse proxy)
- **HTTPS**: Configure SSL in reverse proxy

## Security Best Practices

1. **Don't expose AutoArr directly to the internet** - Use reverse proxy
2. **Keep API keys secure** - Store in `.env` file, not in docker-compose.yml
3. **Regular updates** - Pull latest image monthly
4. **Monitor logs** - Check for suspicious activity
5. **Backup regularly** - Backup `/data` directory weekly

## CI/CD Pipeline

The GitHub Actions workflow:

1. **Triggers**: On push to `main`, tags, or PRs
2. **Builds**: Multi-platform Docker image (amd64, arm64)
3. **Tests**: Runs linters and tests (if passing)
4. **Publishes**: Pushes to ghcr.io with multiple tags
5. **Attestation**: Signs image with build provenance

**Workflow file**: `.github/workflows/docker-publish.yml`

## Performance

### Resource Usage

Default limits (adjust in docker-compose.yml):

- **CPU**: 2 cores max, 0.5 reserved
- **Memory**: 1GB max, 512MB reserved

### Scaling

For high-traffic deployments:

- Use external Redis: `REDIS_URL=redis://redis:6379`
- Use PostgreSQL: `DATABASE_URL=postgresql://...`
- Increase workers: `CMD ["uvicorn", "api.main:app", "--workers", "4"]`

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/autoarr/issues)
- **Docs**: [Documentation](https://github.com/yourusername/autoarr/docs)
- **Synology Guide**: [Synology Deployment](docs/SYNOLOGY_DEPLOYMENT.md)

## License

MIT License - See [LICENSE](LICENSE) for details.
