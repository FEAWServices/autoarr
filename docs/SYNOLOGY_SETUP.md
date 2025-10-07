# AutoArr - Synology NAS Setup Guide

Complete guide for installing and running AutoArr on Synology NAS with Container Manager (formerly Docker).

## Prerequisites

### Required

- Synology NAS with DSM 7.0 or higher
- Container Manager package installed (from Package Center)
- At least 2GB free RAM
- Internet connection

### Existing Services (at least one required)

- SABnzbd (download client)
- Sonarr (TV show management)
- Radarr (movie management)
- Plex (media server)

## Quick Start (Container Manager UI)

### Step 1: Prepare Directories

1. Open **File Station** on your Synology
2. Navigate to `/docker/` (create if it doesn't exist)
3. Create the following folders:
   ```
   /docker/autoarr/
   /docker/autoarr/data/
   /docker/autoarr/logs/
   ```

### Step 2: Deploy Container First (Configuration Comes Later)

You'll configure your services through the AutoArr web UI after deployment. This is easier and more user-friendly than editing environment variables!

### Step 3: Deploy Container

#### Option A: Using Container Manager UI (Recommended for Synology)

1. Open **Container Manager** from DSM
2. Go to **Project** tab
3. Click **Create**
4. Name it `autoarr`
5. Set path to `/docker/autoarr/`
6. Use this docker-compose.yml content:

```yaml
version: "3.8"

services:
  autoarr:
    image: ghcr.io/feawservices/autoarr:latest
    container_name: autoarr
    restart: unless-stopped
    ports:
      - "8088:8088"
    volumes:
      - /volume1/docker/autoarr/data:/data
      - /volume1/docker/autoarr/logs:/app/logs
    environment:
      APP_ENV: production
      LOG_LEVEL: INFO
      DATABASE_URL: sqlite:////data/autoarr.db
      REDIS_URL: memory://

      # SABnzbd
      SABNZBD_ENABLED: "true"
      SABNZBD_URL: http://YOUR_NAS_IP:8080
      SABNZBD_API_KEY: YOUR_SABNZBD_API_KEY

      # Sonarr
      SONARR_ENABLED: "true"
      SONARR_URL: http://YOUR_NAS_IP:8989
      SONARR_API_KEY: YOUR_SONARR_API_KEY

      # Radarr
      RADARR_ENABLED: "true"
      RADARR_URL: http://YOUR_NAS_IP:7878
      RADARR_API_KEY: YOUR_RADARR_API_KEY

      # Plex
      PLEX_ENABLED: "true"
      PLEX_URL: http://YOUR_NAS_IP:32400
      PLEX_TOKEN: YOUR_PLEX_TOKEN
```

7. Click **Build** and wait for the image to download (no need to edit environment variables!)

#### Option B: Using SSH/Command Line

1. SSH into your Synology: `ssh admin@YOUR_NAS_IP`
2. Switch to root: `sudo -i`
3. Create directory: `mkdir -p /volume1/docker/autoarr/{data,logs}`
4. Download the compose file:
   ```bash
   cd /volume1/docker/autoarr
   curl -O https://raw.githubusercontent.com/FEAWServices/autoarr/main/docker-compose.synology.yml
   mv docker-compose.synology.yml docker-compose.yml
   ```
5. Edit with your API keys: `nano docker-compose.yml`
6. Start the container: `docker-compose up -d`

### Step 4: Configure Services Through the UI

1. Wait 30-60 seconds for the container to start
2. Open your browser and navigate to: `http://YOUR_NAS_IP:8088`
3. You should see the AutoArr dashboard
4. Go to **Settings** (or visit `http://YOUR_NAS_IP:8088/settings`)
5. Configure each service you want to use:

#### Getting Your API Keys

**SABnzbd API Key:**

1. Open SABnzbd web UI (usually `http://YOUR_NAS_IP:8080`)
2. Go to Config → General
3. Copy the "API Key"

**Sonarr API Key:**

1. Open Sonarr web UI (usually `http://YOUR_NAS_IP:8989`)
2. Go to Settings → General → Security
3. Copy the "API Key"

**Radarr API Key:**

1. Open Radarr web UI (usually `http://YOUR_NAS_IP:7878`)
2. Go to Settings → General → Security
3. Copy the "API Key"

**Plex Token:**

1. Follow this guide: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
2. Or use this URL while logged in: https://plex.tv/pms/servers.xml
3. Look for `token="YOUR_TOKEN_HERE"`

#### Configuring Each Service

1. In the AutoArr Settings UI, for each service:

   - Enter the **URL** (e.g., `http://192.168.1.100:8989` for Sonarr)
   - Enter the **API Key** or **Token**
   - Click **Test Connection** to verify
   - Click **Save** to apply the configuration

2. AutoArr will automatically save your settings to `/data/autoarr.db`
3. Your settings persist across container restarts
4. Check the health endpoint to verify: `http://YOUR_NAS_IP:8088/health`

## Configuration Details

### Settings Storage

**Persistent Database Storage:**

- ✅ All service settings configured through the UI are **automatically saved** to SQLite database
- ✅ Database located at `/volume1/docker/autoarr/data/autoarr.db`
- ✅ Settings **persist across container restarts**
- ✅ Easy to backup (just backup the `/data` folder)
- ✅ No need to edit docker-compose.yml for service configuration

**How It Works:**

1. Start the container with minimal configuration (just `DATABASE_URL`)
2. Access the Settings UI at `http://YOUR_NAS_IP:8088/settings`
3. Configure your services (SABnzbd, Sonarr, Radarr, Plex)
4. Click "Save" - settings are immediately written to the database
5. Settings automatically load from database on container restart

**Priority:** Database settings always take priority over environment variables

### Alternative: Environment Variables (Optional)

If you prefer to use environment variables instead of the UI, you can uncomment the service configuration section in your docker-compose.yml:

| Variable          | Description               | Example                      |
| ----------------- | ------------------------- | ---------------------------- |
| `SABNZBD_URL`     | SABnzbd web interface URL | `http://192.168.1.100:8080`  |
| `SABNZBD_API_KEY` | SABnzbd API key           | `1234567890abcdef`           |
| `SONARR_URL`      | Sonarr web interface URL  | `http://192.168.1.100:8989`  |
| `SONARR_API_KEY`  | Sonarr API key            | `abcdef1234567890`           |
| `RADARR_URL`      | Radarr web interface URL  | `http://192.168.1.100:7878`  |
| `RADARR_API_KEY`  | Radarr API key            | `fedcba0987654321`           |
| `PLEX_URL`        | Plex Media Server URL     | `http://192.168.1.100:32400` |
| `PLEX_TOKEN`      | Plex authentication token | `xyzABC123`                  |

**Note:** Settings configured via the UI will override environment variables.

### Optional AI Features

To enable AI-powered assistance, configure through the UI or add environment variable:

1. Get an Anthropic API key: https://console.anthropic.com/
2. Add to docker-compose.yml:
   ```yaml
   ANTHROPIC_API_KEY: your-api-key-here
   ```
3. Restart the container

## Network Configuration

### Same NAS (All Services on Synology)

Use the Synology's IP address for all service URLs:

```yaml
SABNZBD_URL: http://192.168.1.100:8080
SONARR_URL: http://192.168.1.100:8989
RADARR_URL: http://192.168.1.100:7878
PLEX_URL: http://192.168.1.100:32400
```

### Docker Network (Services in Containers)

If your services are also Docker containers on the same NAS:

1. In Container Manager, go to **Network** tab
2. Create or use an existing network (e.g., `media-stack`)
3. Connect all containers to this network
4. Use container names instead of IP addresses:
   ```yaml
   SABNZBD_URL: http://sabnzbd:8080
   SONARR_URL: http://sonarr:8989
   RADARR_URL: http://radarr:7878
   PLEX_URL: http://plex:32400
   ```

### Mixed Environment

Some services on NAS, others elsewhere - use appropriate URLs:

```yaml
SABNZBD_URL: http://192.168.1.100:8080 # On this NAS
SONARR_URL: http://192.168.1.50:8989 # Different machine
RADARR_URL: http://radarr:7878 # Docker container
PLEX_URL: http://192.168.1.100:32400 # On this NAS
```

## Resource Management

### Recommended Settings

For typical Synology NAS (DS920+, DS1522+, etc.):

```yaml
resources:
  limits:
    cpus: "2"
    memory: 1G
  reservations:
    cpus: "0.5"
    memory: 512M
```

For lower-end models (DS220+, DS418, etc.):

```yaml
resources:
  limits:
    cpus: "1"
    memory: 512M
  reservations:
    cpus: "0.25"
    memory: 256M
```

## Updates

AutoArr uses GitHub Container Registry with auto-pull support.

### Automatic Updates (Recommended)

1. Open **Container Manager**
2. Go to **Registry** tab
3. Find `ghcr.io/feawservices/autoarr`
4. Enable **Auto Update**
5. Set update schedule (e.g., weekly)

### Manual Update

```bash
# SSH into Synology
ssh admin@YOUR_NAS_IP
sudo -i

# Navigate to compose directory
cd /volume1/docker/autoarr

# Pull latest image and restart
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

1. Check Container Manager logs:

   - Go to **Container** tab
   - Select `autoarr` container
   - Click **Logs**

2. Common issues:
   - Port 8088 already in use → Change to different port (e.g., `8089:8088`)
   - Volume paths don't exist → Create directories in File Station
   - Invalid API keys → Verify keys are correct and have no extra spaces

### Can't Connect to Services

1. Test connectivity from inside the container:

   ```bash
   docker exec -it autoarr curl http://YOUR_NAS_IP:8989/api/v3/system/status
   ```

2. Check firewall rules on Synology:

   - Control Panel → Security → Firewall
   - Ensure ports are allowed

3. Verify service URLs are accessible from your browser

### Health Check Failing

1. Check if the app is running:

   ```bash
   docker exec -it autoarr curl http://localhost:8088/health
   ```

2. Check application logs:

   ```bash
   docker logs autoarr
   ```

3. View log files:
   - Open File Station
   - Navigate to `/docker/autoarr/logs/`
   - Check recent log files

### Database Issues

If the SQLite database gets corrupted:

1. Stop the container
2. Backup `/volume1/docker/autoarr/data/autoarr.db`
3. Delete the database file
4. Restart container (it will create a new database)

## Advanced Configuration

### External Database (PostgreSQL)

For high-performance setups:

1. Install PostgreSQL in Container Manager
2. Change `DATABASE_URL`:
   ```yaml
   DATABASE_URL: postgresql://user:password@postgres:5432/autoarr
   ```

### Redis Cache

For better performance with multiple instances:

1. Install Redis in Container Manager
2. Change `REDIS_URL`:
   ```yaml
   REDIS_URL: redis://redis:6379/0
   ```

### Reverse Proxy (NGINX/Traefik)

Access AutoArr via subdomain (e.g., `autoarr.yourdomain.com`):

1. Configure reverse proxy in DSM (Control Panel → Login Portal → Advanced)
2. Or use NGINX Proxy Manager container
3. Point to `http://YOUR_NAS_IP:8088`

## Security Best Practices

1. **Don't expose port 8088 to the internet** - Use VPN or reverse proxy with authentication
2. **Keep API keys secure** - Don't commit them to version control
3. **Regular backups** - Backup `/volume1/docker/autoarr/data/` directory
4. **Update regularly** - Enable auto-updates or check weekly for new versions
5. **Monitor logs** - Check `/volume1/docker/autoarr/logs/` periodically

## Support

- **Documentation**: https://github.com/FEAWServices/autoarr/tree/main/docs
- **Issues**: https://github.com/FEAWServices/autoarr/issues
- **Discussions**: https://github.com/FEAWServices/autoarr/discussions

## Next Steps

Once AutoArr is running:

1. Explore the web UI at `http://YOUR_NAS_IP:8088`
2. Check service connectivity in the Health page
3. Review the [User Guide](./USER_GUIDE.md) for features
4. Set up [automation workflows](./AUTOMATION_GUIDE.md)
