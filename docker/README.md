# AutoArr Docker Configuration

This directory contains all Docker configurations for AutoArr deployment and local testing.

## 📁 Directory Structure

```
docker/
├── Dockerfile.production        # Multi-stage production build (CI/users)
├── Dockerfile.local-test        # Lightweight local testing image
├── docker-compose.production.yml # Production deployment
├── docker-compose.local-test.yml # Local testing with host network
├── docker-compose.synology.yml   # Synology NAS deployment
├── README.md                     # This file
└── QUICK-START.md               # Quick reference
```

## 🚀 Quick Start

### For Users (Production Deployment)

```bash
# Pull and run the pre-built image
docker-compose -f docker/docker-compose.production.yml up -d
```

### For Developers (Local Testing)

```bash
# Run with hot-reload, connects to services on localhost
docker-compose -f docker/docker-compose.local-test.yml up -d
```

### For VS Code Development

Open the repo in VS Code and use "Reopen in Container" (uses `.devcontainer/`).

## 📦 Docker Configurations

### 1. Production (`docker-compose.production.yml`)

**Purpose**: End-user deployment

- Pre-built image from GitHub Container Registry
- Self-contained with SQLite database (like Sonarr/Radarr)
- No external dependencies required
- Resource limits and health checks

```bash
# Using pre-built image
docker-compose -f docker/docker-compose.production.yml up -d

# Or build locally
docker build -f docker/Dockerfile.production -t autoarr:latest ..
```

### 2. Local Testing (`docker-compose.local-test.yml`)

**Purpose**: Fast developer iteration

- Host network mode (connects to localhost services)
- Volume mounts for hot-reload
- Same folder structure as devcontainer
- Quick builds

```bash
docker-compose -f docker/docker-compose.local-test.yml up -d

# View logs
docker-compose -f docker/docker-compose.local-test.yml logs -f
```

### 3. Synology NAS (`docker-compose.synology.yml`)

**Purpose**: Synology NAS deployment

- Optimized paths for Synology (`/volume1/docker/`)
- Pre-configured for Container Manager
- Resource limits for NAS hardware

### 4. VS Code DevContainer (`.devcontainer/`)

**Purpose**: Full IDE integration

- Located in repo root at `.devcontainer/`
- Docker-in-Docker support
- Pre-installed extensions and tools
- Open repo in VS Code → "Reopen in Container"

## 🗄️ Database Architecture

AutoArr uses **SQLite** by default - the same self-contained approach as Sonarr and Radarr:

- **Location**: `/data/autoarr.db` (inside container)
- **Persistence**: Mount `./data:/data` volume
- **No external database required**

Optional: PostgreSQL can be configured via `DATABASE_URL` for high-availability setups.

## 🌐 Network Configuration

| Configuration | Network Mode     | Use Case                  |
| ------------- | ---------------- | ------------------------- |
| Production    | Bridge (default) | Isolated container        |
| Local Testing | Host             | Access localhost services |
| DevContainer  | Bridge           | VS Code integration       |

### Connecting to Media Services

**Production/Bridge mode** - Use Docker network names or IP addresses:

```yaml
SONARR_URL: http://sonarr:8989
RADARR_URL: http://radarr:7878
```

**Local Testing/Host mode** - Use localhost:

```yaml
SONARR_URL: http://localhost:8989
RADARR_URL: http://localhost:7878
```

## 🔌 Ports

| Port | Service         | Notes             |
| ---- | --------------- | ----------------- |
| 8088 | AutoArr API     | Main application  |
| 3000 | Vite Dev Server | Frontend dev only |

## 🛠️ Common Commands

### View Logs

```bash
docker-compose -f docker/docker-compose.local-test.yml logs -f
```

### Rebuild Image

```bash
docker-compose -f docker/docker-compose.local-test.yml up -d --build
```

### Stop Container

```bash
docker-compose -f docker/docker-compose.local-test.yml down
```

### Shell Access

```bash
docker exec -it autoarr-local-test /bin/bash
```

### Run Tests

```bash
docker exec autoarr-local-test poetry run pytest
```

## 📋 Environment Variables

Required environment variables (set in `.env` file):

```env
# Media Service URLs and API Keys
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=your_key_here

SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_key_here

RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_key_here

# Optional
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_token_here

# AI Features (optional)
ANTHROPIC_API_KEY=your_key_here
```

## 🆘 Troubleshooting

### Container won't start

```bash
docker-compose -f docker/docker-compose.local-test.yml logs
```

### Port already in use

Edit the compose file to change the port mapping:

```yaml
ports:
  - "8089:8088" # Use 8089 instead
```

### Can't connect to localhost services (local testing)

Ensure you're using `network_mode: host` in the compose file.

### Changes not reflecting

For local testing, the volume mounts enable hot-reload. If changes aren't showing:

1. Check the container is running: `docker ps`
2. View logs: `docker logs autoarr-local-test`
3. Restart: `docker-compose -f docker/docker-compose.local-test.yml restart`

## 📚 Related Documentation

- **Project README**: `/app/README.md`
- **Architecture**: `/app/docs/ARCHITECTURE.md`
- **Deployment Guide**: `/app/docs/DEPLOYMENT.md`
- **Synology Setup**: `/app/docs/SYNOLOGY_DEPLOYMENT.md`
