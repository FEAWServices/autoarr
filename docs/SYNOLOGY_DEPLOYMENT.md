# AutoArr Synology Deployment Guide

This guide will help you deploy AutoArr on your Synology NAS using Docker Compose and the GitHub Container Registry (GHCR) image.

## Prerequisites

### 1. Synology Setup

- Synology NAS with DSM 7.0 or later
- Container Manager package installed (from Package Center)
- SSH access enabled (optional, for command-line deployment)

### 2. Existing Services

AutoArr requires the following services to be running:

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
- Plex Token: [See instructions in .env.synology.example](.env.synology.example)

## Quick Start

### Method 1: Using File Station & Container Manager UI

#### Step 1: Create Directory Structure

1. Open **File Station**
2. Navigate to `/docker/` (create if it doesn't exist)
3. Create the following folders:
   ```
   /docker/autoarr/
   /docker/autoarr/data/
   /docker/autoarr/logs/
   ```

#### Step 2: Upload Configuration Files

1. Download these files from the AutoArr repository:
   - `docker-compose.synology.yml`
   - `.env.synology.example`
2. Upload both files to `/docker/autoarr/`
3. Rename `.env.synology.example` to `.env`
4. Edit `.env` with your API keys and service URLs

#### Step 3: Deploy with Container Manager

1. Open **Container Manager**
2. Go to **Project** tab
3. Click **Create**
4. Configure:
   - **Project Name**: `autoarr`
   - **Path**: `/docker/autoarr`
   - **Source**: Select `docker-compose.synology.yml`
5. Click **Next**, review settings, then **Done**

The container will automatically pull the image from GitHub Container Registry and start.

### Method 2: Using SSH (Advanced)

#### Step 1: SSH into Synology

```bash
ssh admin@your-synology-ip
sudo -i
```

#### Step 2: Create Directory and Download Files

```bash
# Create directory
mkdir -p /volume1/docker/autoarr/{data,logs}
cd /volume1/docker/autoarr

# Download docker-compose file
curl -O https://raw.githubusercontent.com/yourusername/autoarr/main/docker-compose.synology.yml

# Download environment template
curl -O https://raw.githubusercontent.com/yourusername/autoarr/main/.env.synology.example
mv .env.synology.example .env
```

#### Step 3: Configure Environment

```bash
# Edit the .env file with your settings
vi .env
```

#### Step 4: Deploy

```bash
# Pull and start the container
docker compose -f docker-compose.synology.yml up -d

# Check status
docker compose -f docker-compose.synology.yml ps

# View logs
docker compose -f docker-compose.synology.yml logs -f
```

## Configuration

### Environment Variables

Edit `/volume1/docker/autoarr/.env` with your configuration:

```bash
# Required: Service URLs (adjust IPs to match your setup)
SABNZBD_URL=http://192.168.1.100:8080
SABNZBD_API_KEY=your_actual_sabnzbd_api_key

SONARR_URL=http://192.168.1.100:8989
SONARR_API_KEY=your_actual_sonarr_api_key

RADARR_URL=http://192.168.1.100:7878
RADARR_API_KEY=your_actual_radarr_api_key

PLEX_URL=http://192.168.1.100:32400
PLEX_TOKEN=your_actual_plex_token

# Optional: AI Features
ANTHROPIC_API_KEY=sk-ant-...  # Leave empty to disable
```

### Network Configuration

**Option 1: Default Bridge Network** (Recommended for beginners)

- Services are accessed by IP address
- No changes needed to docker-compose.synology.yml

**Option 2: Join Existing Docker Network** (Advanced)
If your \*arr stack is already running in a Docker network:

1. Edit `docker-compose.synology.yml`
2. Uncomment the `media-stack` network section
3. Update the network name to match your existing network

```yaml
networks:
  media-stack:
    external: true
    name: your_existing_network_name
```

## Accessing AutoArr

Once deployed, access AutoArr at:

- **Web UI**: `http://your-synology-ip:8088`
- **API Docs**: `http://your-synology-ip:8088/docs`
- **Health Check**: `http://your-synology-ip:8088/health`

## Updating AutoArr

### Via Container Manager UI

1. Open **Container Manager**
2. Go to **Project** > `autoarr`
3. Click **Action** > **Pull**
4. After pull completes, click **Action** > **Restart**

### Via SSH

```bash
cd /volume1/docker/autoarr
docker compose -f docker-compose.synology.yml pull
docker compose -f docker-compose.synology.yml up -d
```

## Troubleshooting

### Container Won't Start

1. Check logs in Container Manager or via SSH:
   ```bash
   docker compose -f docker-compose.synology.yml logs
   ```
2. Verify all API keys are correct in `.env`
3. Ensure service URLs are accessible from the Synology

### Can't Connect to Services

1. Verify service URLs use correct IP addresses
2. Test connectivity:
   ```bash
   docker exec autoarr curl http://192.168.1.100:8080/api?mode=version
   ```
3. If using Docker networks, ensure services are in the same network

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R 1000:1000 /volume1/docker/autoarr/data
sudo chmod -R 755 /volume1/docker/autoarr/data
```

### View Live Logs

```bash
docker compose -f docker-compose.synology.yml logs -f autoarr
```

## Resource Usage

Default resource limits:

- **CPU**: 2 cores max, 0.5 cores reserved
- **Memory**: 1GB max, 512MB reserved

To adjust, edit `docker-compose.synology.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "4" # Increase for better performance
      memory: 2G
```

## Backup and Restore

### Backup

```bash
# Backup database and config
cd /volume1/docker/autoarr
tar czf autoarr-backup-$(date +%Y%m%d).tar.gz data/
```

### Restore

```bash
# Stop container
docker compose -f docker-compose.synology.yml down

# Restore data
tar xzf autoarr-backup-YYYYMMDD.tar.gz

# Start container
docker compose -f docker-compose.synology.yml up -d
```

## Advanced Configuration

### Using PostgreSQL Instead of SQLite

If you have PostgreSQL running:

```bash
# In .env
DATABASE_URL=postgresql://user:password@postgres:5432/autoarr
```

### Using Redis for Caching

If you have Redis running:

```bash
# In .env
REDIS_URL=redis://redis:6379/0
```

### Custom Port

Change the port in `.env`:

```bash
AUTOARR_PORT=9999  # Use any available port
```

## Security Recommendations

1. **Use Reverse Proxy**: Consider using Synology's built-in reverse proxy or Nginx Proxy Manager
2. **Enable HTTPS**: Configure SSL certificates through DSM or reverse proxy
3. **Firewall**: Restrict access to AutoArr port to your local network
4. **API Keys**: Keep your `.env` file secure and don't share it

## Support

- **GitHub Issues**: [https://github.com/yourusername/autoarr/issues](https://github.com/yourusername/autoarr/issues)
- **Documentation**: [https://github.com/yourusername/autoarr/docs](https://github.com/yourusername/autoarr/docs)
- **Discord**: [Your Discord Link]

## Uninstalling

### Via Container Manager

1. Open **Container Manager**
2. Go to **Project** > `autoarr`
3. Click **Action** > **Stop**
4. Click **Action** > **Delete**

### Via SSH

```bash
cd /volume1/docker/autoarr
docker compose -f docker-compose.synology.yml down -v
rm -rf /volume1/docker/autoarr  # Remove all data
```

## License

AutoArr is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
