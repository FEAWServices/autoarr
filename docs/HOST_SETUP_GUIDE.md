# AutoArr Host Machine Setup Guide

## Quick Setup (Automated)

1. **Copy the setup script to your host machine:**
   Copy `/app/setup-host.sh` to your AutoArr project directory on the host machine.

2. **Make it executable and run:**
   ```bash
   chmod +x setup-host.sh
   ./setup-host.sh
   ```

## Manual Setup (Step by Step)

If you prefer to set up manually, follow these steps:

### Prerequisites

- Docker Desktop installed and running
- Terminal/Command Prompt access

### Step 1: Navigate to Project Directory

```bash
cd /path/to/your/autoarr/project
```

### Step 2: Create Configuration Files

**Create .env file:**

```bash
# Copy the content from /app/.env.host to your host machine .env file
cp .env.host .env
```

**Create docker-compose.yml:**

```bash
# Copy the content from /app/docker-compose.host.yml to your host machine
cp docker-compose.host.yml docker-compose.yml
```

### Step 3: Create Data Directories

```bash
mkdir -p data
mkdir -p logs
```

### Step 4: Build and Start

```bash
# Build the container
docker-compose build

# Start the application
docker-compose up -d

# Check status
docker-compose ps
```

### Step 5: Verify Installation

```bash
# Check if the application is responding
curl http://localhost:8088/health

# View logs
docker-compose logs -f
```

## Access URLs

Once running:

- **Main Application**: http://localhost:8088
- **API Documentation**: http://localhost:8088/docs
- **Health Check**: http://localhost:8088/health

## Useful Commands

```bash
# View real-time logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Check container status
docker-compose ps

# Access container shell (for debugging)
docker-compose exec autoarr bash
```

## Troubleshooting

### Container won't start

1. Check logs: `docker-compose logs`
2. Verify Docker is running: `docker info`
3. Check port conflicts: `netstat -an | grep 8088`

### Application not responding

1. Wait 30-60 seconds for startup
2. Check health endpoint: `curl http://localhost:8088/health`
3. Review application logs: `docker-compose logs autoarr`

### Build failures

1. Ensure you're in the correct directory
2. Check Docker has enough resources
3. Clean Docker cache: `docker system prune -f`

## Configuration

### Adding Media Services Later

Edit your `.env` file to enable and configure media services:

```bash
# Enable SABnzbd
SABNZBD_ENABLED=true
SABNZBD_URL=http://your-sabnzbd:8080
SABNZBD_API_KEY=your_api_key

# Enable Sonarr
SONARR_ENABLED=true
SONARR_URL=http://your-sonarr:8989
SONARR_API_KEY=your_api_key

# Enable Radarr
RADARR_ENABLED=true
RADARR_URL=http://your-radarr:7878
RADARR_API_KEY=your_api_key
```

Then restart: `docker-compose restart`

## Next Steps

1. **Test the API**: Visit http://localhost:8088/docs
2. **Configure Services**: Add your media server details to `.env`
3. **Enable AI Features**: Add your Anthropic API key for intelligent recommendations
4. **Monitor Logs**: Use `docker-compose logs -f` to watch application activity
