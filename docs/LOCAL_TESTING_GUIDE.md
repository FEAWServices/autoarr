# AutoArr Local Testing Guide

This guide will help you set up AutoArr for local testing with your **existing** SABnzbd, Sonarr, Radarr, and Plex installations.

## Overview

AutoArr connects to your existing media automation services and provides:

- 🧠 **AI-Powered Configuration Auditing** - Get intelligent recommendations for optimizing your setup
- 🤖 **Natural Language Content Requests** - Request movies/shows by typing "Add Inception in 4K"
- 📊 **Unified Dashboard** - Monitor all your services in one place
- ⚡ **Real-time Updates** - WebSocket-powered live status updates

## Prerequisites

### Required Software

- **Docker Desktop** (version 20.10+)
  - Windows/Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Linux: Install `docker` and `docker-compose`
- **Node.js** (version 20+) - For frontend development
  - [Download Node.js](https://nodejs.org/)
- **pnpm** - Node package manager
  ```bash
  npm install -g pnpm
  ```

### Required Services

AutoArr requires the following services to be **already installed and running**:

1. **SABnzbd** (Usenet downloader)
2. **Sonarr** (TV series management)
3. **Radarr** (Movie management)
4. **Plex** (Optional - Media server)

These services can be running:

- On the **same machine** as AutoArr (localhost)
- On a **different machine** on your network (LAN)
- In **Docker containers**

### API Keys Required

You'll need API keys from each service:

#### SABnzbd API Key

1. Open SABnzbd web interface (usually http://localhost:8080)
2. Go to **Config → General**
3. Find **API Key** in the Security section
4. Copy the key

#### Sonarr API Key

1. Open Sonarr web interface (usually http://localhost:8989)
2. Go to **Settings → General**
3. Scroll to **Security** section
4. Copy the **API Key**

#### Radarr API Key

1. Open Radarr web interface (usually http://localhost:7878)
2. Go to **Settings → General**
3. Scroll to **Security** section
4. Copy the **API Key**

#### Plex Token (Optional)

1. Follow [Plex's official guide](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
2. Or visit: https://www.plex.tv/claim/ while logged in

---

## Quick Start (5 Minutes)

### 1. Clone Repository (if you haven't already)

```bash
git clone https://github.com/YourUsername/autoarr.git
cd autoarr
```

### 2. Configure Environment

```bash
# Copy the template
cp .env.local .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required changes in `.env`:**

```bash
# Update these URLs if your services are NOT on localhost
SABNZBD_URL=http://localhost:8080
SONARR_URL=http://localhost:8989
RADARR_URL=http://localhost:7878

# Add your actual API keys (CRITICAL!)
SABNZBD_API_KEY=your_actual_sabnzbd_api_key_here
SONARR_API_KEY=your_actual_sonarr_api_key_here
RADARR_API_KEY=your_actual_radarr_api_key_here

# Optional: Add for AI features
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**If your services are on a different machine:**

```bash
# Example: Services running on 192.168.1.100
SABNZBD_URL=http://192.168.1.100:8080
SONARR_URL=http://192.168.1.100:8989
RADARR_URL=http://192.168.1.100:7878
```

### 3. Run Quickstart Script

```bash
./scripts/quickstart.sh
```

This script will:

- ✅ Check Docker is running
- ✅ Create necessary directories
- ✅ Build AutoArr backend
- ✅ Start the services
- ✅ Wait for everything to be ready
- ✅ Display access URLs

### 4. Start Frontend (New Terminal)

```bash
cd autoarr/ui
pnpm install
pnpm dev
```

### 5. Access AutoArr

- **Frontend UI**: http://localhost:3000
- **API Documentation**: http://localhost:8088/docs
- **API Health**: http://localhost:8088/health

---

## Detailed Setup

### Architecture

```
┌─────────────────────────────────────────┐
│  Your Browser                           │
│  http://localhost:3000                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  AutoArr Frontend (React)               │
│  Port: 3000                             │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  AutoArr Backend (FastAPI)              │
│  Port: 8088                             │
│  Running in Docker                      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Your Existing Services                 │
│  ├─ SABnzbd (port 8080)                │
│  ├─ Sonarr (port 8989)                 │
│  ├─ Radarr (port 7878)                 │
│  └─ Plex (port 32400)                  │
└─────────────────────────────────────────┘
```

### Step-by-Step Setup

#### Step 1: Verify Your Services are Accessible

Before starting AutoArr, verify your services are running and accessible:

```bash
# Test SABnzbd
curl http://localhost:8080/api?mode=version&apikey=YOUR_API_KEY

# Test Sonarr
curl http://localhost:8989/api/v3/system/status?apikey=YOUR_API_KEY

# Test Radarr
curl http://localhost:7878/api/v3/system/status?apikey=YOUR_API_KEY
```

If these work, AutoArr will be able to connect.

#### Step 2: Configure Service URLs

Edit `.env` to match your setup:

**Scenario 1: Services on Same Machine (localhost)**

```bash
SABNZBD_URL=http://localhost:8080
SONARR_URL=http://localhost:8989
RADARR_URL=http://localhost:7878
```

**Scenario 2: Services on Different Machine (LAN)**

```bash
SABNZBD_URL=http://192.168.1.100:8080
SONARR_URL=http://192.168.1.100:8989
RADARR_URL=http://192.168.1.100:7878
```

**Scenario 3: Services in Docker on Same Host**

```bash
# Use host.docker.internal to access host from container
SABNZBD_URL=http://host.docker.internal:8080
SONARR_URL=http://host.docker.internal:8989
RADARR_URL=http://host.docker.internal:7878
```

**Scenario 4: Mixed Setup**

```bash
# SABnzbd on localhost
SABNZBD_URL=http://localhost:8080

# Sonarr/Radarr on NAS
SONARR_URL=http://nas.local:8989
RADARR_URL=http://nas.local:7878
```

#### Step 3: Build and Start Backend

```bash
# Build the Docker image
docker-compose -f docker-compose.dev.yml build

# Start AutoArr backend
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

#### Step 4: Verify Backend is Running

```bash
# Check health
curl http://localhost:8088/health

# Should return:
# {"status":"healthy","services":{"sabnzbd":"unknown","sonarr":"unknown","radarr":"unknown","plex":"unknown"}}
```

#### Step 5: Start Frontend

```bash
cd autoarr/ui

# Install dependencies (first time only)
pnpm install

# Start development server
pnpm dev
```

Frontend will be available at: http://localhost:3000

---

## Test Scenarios

### Scenario 1: Configuration Audit

**Goal**: Get AI-powered recommendations for optimizing your setup

1. Open http://localhost:3000
2. Go to **Dashboard**
3. Click **"Run Configuration Audit"**
4. Wait for AI analysis (requires `ANTHROPIC_API_KEY`)
5. Review recommendations with priority scores (High/Medium/Low)
6. Click **"Apply"** on any recommendation to update the service

**What's Happening Behind the Scenes:**

- AutoArr fetches current configurations from all services
- Compares against best practices database
- Uses Claude AI to analyze and prioritize recommendations
- Generates actionable changes

### Scenario 2: Service Health Monitoring

**Goal**: Monitor connection status of all services

1. Open http://localhost:3000
2. Go to **Dashboard**
3. Observe service status cards:
   - 🟢 Green: Service connected and healthy
   - 🔴 Red: Service unreachable
   - 🟡 Yellow: Service degraded

4. Click on any service card to see details

**API Endpoint:**

```bash
curl http://localhost:8088/health/services
```

### Scenario 3: Natural Language Content Requests

**Goal**: Request movies/TV shows using plain English

1. Open http://localhost:3000
2. Go to **Chat** interface
3. Type a request:
   - "Add Dune Part 2 in 4K"
   - "I want to watch The Last of Us season 2"
   - "Download Inception"

4. AutoArr will:
   - Classify as movie or TV show
   - Search for the content
   - Add to Radarr or Sonarr
   - Trigger automatic search
   - Show real-time status updates

**API Endpoint:**

```bash
curl -X POST http://localhost:8088/api/v1/requests/content \
  -H "Content-Type: application/json" \
  -d '{"query": "Add Dune Part 2 in 4K"}'
```

### Scenario 4: Browse and Manage Content

**Goal**: View and manage your existing media

**Movies (Radarr):**

```bash
# List all movies
curl http://localhost:8088/api/v1/movies

# Search for a movie
curl http://localhost:8088/api/v1/movies/search?query=Dune

# Add a movie
curl -X POST http://localhost:8088/api/v1/movies \
  -H "Content-Type: application/json" \
  -d '{"title": "Dune Part Two", "year": 2024, "tmdbId": 693134}'
```

**TV Shows (Sonarr):**

```bash
# List all shows
curl http://localhost:8088/api/v1/shows

# Search for a show
curl http://localhost:8088/api/v1/shows/search?query="The Last of Us"

# Add a show
curl -X POST http://localhost:8088/api/v1/shows \
  -H "Content-Type: application/json" \
  -d '{"title": "The Last of Us", "year": 2023, "tvdbId": 392256}'
```

### Scenario 5: Real-time WebSocket Updates

**Goal**: Receive live updates via WebSocket

```javascript
// Connect to WebSocket
const ws = new WebSocket("ws://localhost:8088/ws");

ws.onopen = () => {
  console.log("Connected to AutoArr WebSocket");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received update:", data);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## Troubleshooting

### Problem: "Cannot connect to SABnzbd/Sonarr/Radarr"

**Symptoms:**

- Red status indicators in UI
- API returns connection errors
- Logs show "Connection refused"

**Solutions:**

1. **Verify service is running:**

   ```bash
   curl http://localhost:8080  # SABnzbd
   curl http://localhost:8989  # Sonarr
   curl http://localhost:7878  # Radarr
   ```

2. **Check API key is correct:**
   - Copy-paste the API key directly from the service UI
   - Ensure no extra spaces or characters

3. **Verify URL is correct:**
   - If services are in Docker: use `host.docker.internal` instead of `localhost`
   - If on different machine: use IP address, not hostname

4. **Check network connectivity:**

   ```bash
   # From AutoArr container
   docker-compose -f docker-compose.dev.yml exec autoarr-backend curl http://host.docker.internal:8080
   ```

5. **Check firewall:**
   - Ensure ports 8080, 8989, 7878 are not blocked

### Problem: "Docker build fails"

**Solutions:**

1. **Clear Docker cache:**

   ```bash
   docker-compose -f docker-compose.dev.yml build --no-cache
   ```

2. **Check disk space:**

   ```bash
   docker system df
   docker system prune  # Clean up if needed
   ```

3. **Update Docker:**
   - Ensure Docker Desktop is up to date

### Problem: "Frontend won't start"

**Solutions:**

1. **Clear node_modules and reinstall:**

   ```bash
   cd autoarr/ui
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   ```

2. **Check Node version:**

   ```bash
   node --version  # Should be 20+
   ```

3. **Try different port:**
   ```bash
   pnpm dev --port 3001
   ```

### Problem: "AI features not working"

**Symptoms:**

- Configuration audit fails
- Natural language requests don't work
- Logs show "Missing ANTHROPIC_API_KEY"

**Solutions:**

1. **Get Anthropic API key:**
   - Sign up at https://console.anthropic.com/
   - Create new API key
   - Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-your-key-here`

2. **Restart backend:**

   ```bash
   docker-compose -f docker-compose.dev.yml restart
   ```

3. **Check API key is valid:**
   ```bash
   # Check logs for errors
   docker-compose -f docker-compose.dev.yml logs | grep ANTHROPIC
   ```

### Problem: "WebSocket not connecting"

**Solutions:**

1. **Check browser console for errors**
2. **Verify WebSocket URL:**
   - Should be `ws://localhost:8088/ws` (not `wss://`)

3. **Check CORS settings:**
   - Backend should allow frontend origin

4. **Try curl:**
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
     http://localhost:8088/ws
   ```

---

## Useful Commands

### Docker Commands

```bash
# View all logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service logs
docker-compose -f docker-compose.dev.yml logs -f autoarr-backend

# Restart services
docker-compose -f docker-compose.dev.yml restart

# Stop services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose -f docker-compose.dev.yml down -v

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec autoarr-backend bash

# View container stats
docker stats
```

### Development Commands

```bash
# Backend (in container)
docker-compose -f docker-compose.dev.yml exec autoarr-backend poetry run pytest

# Frontend
cd autoarr/ui
pnpm test          # Run tests
pnpm lint          # Lint code
pnpm format        # Format code
pnpm build         # Production build
```

### API Testing

```bash
# Health check
curl http://localhost:8088/health

# Service health
curl http://localhost:8088/health/services

# Configuration audit
curl -X POST http://localhost:8088/api/v1/config/audit

# List recommendations
curl http://localhost:8088/api/v1/config/recommendations

# Content request
curl -X POST http://localhost:8088/api/v1/requests/content \
  -H "Content-Type: application/json" \
  -d '{"query": "Add Inception in 4K"}'

# List content requests
curl http://localhost:8088/api/v1/requests

# WebSocket test (with websocat)
websocat ws://localhost:8088/ws
```

---

## Advanced Configuration

### Custom Ports

If you need to change AutoArr's ports:

**Backend (edit `docker-compose.dev.yml`):**

```yaml
ports:
  - "9000:8088" # External:Internal
```

**Frontend (edit `autoarr/ui/vite.config.ts`):**

```typescript
server: {
  port: 4000;
}
```

### Enable Plex Integration

1. Get Plex token (see [Plex Token](#plex-token-optional))
2. Edit `.env`:
   ```bash
   PLEX_ENABLED=true
   PLEX_URL=http://localhost:32400
   PLEX_TOKEN=your_plex_token_here
   ```
3. Restart backend

### Debug Mode

Enable verbose logging:

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Restart
docker-compose -f docker-compose.dev.yml restart
```

### Development Without Docker

If you prefer to run the backend locally without Docker:

```bash
# Install dependencies
poetry install

# Set environment variables
export $(cat .env | xargs)

# Run backend
cd autoarr
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8088
```

---

## Getting Help

### Check Logs First

```bash
# Backend logs
docker-compose -f docker-compose.dev.yml logs -f autoarr-backend

# Look for errors (grep)
docker-compose -f docker-compose.dev.yml logs | grep ERROR
```

### Common Log Messages

**"Connection refused"** → Service URL is wrong or service is down
**"401 Unauthorized"** → API key is wrong
**"404 Not Found"** → Endpoint not implemented or wrong URL
**"Missing ANTHROPIC_API_KEY"** → AI features require API key

### Additional Resources

- **Documentation**: `/app/docs/`
- **API Reference**: http://localhost:8088/docs
- **Architecture**: `/app/docs/ARCHITECTURE.md`
- **Build Plan**: `/app/docs/BUILD-PLAN.md`
- **Bugs & Issues**: `/app/docs/BUGS.md`

### Report Issues

If you encounter bugs:

1. Check `/app/docs/BUGS.md` for known issues
2. Enable debug logging
3. Collect logs
4. Open GitHub issue with:
   - Description of problem
   - Steps to reproduce
   - Relevant logs
   - Environment details (OS, Docker version, etc.)

---

## Next Steps

Once you have AutoArr running:

1. **Explore the UI**
   - Try all the features
   - Provide feedback on UX

2. **Test Configuration Audit**
   - Run audits on all your services
   - Try applying recommendations

3. **Test Natural Language Requests**
   - Request various movies and TV shows
   - Test edge cases

4. **Review the Code**
   - Check `/app/autoarr/api/` for backend
   - Check `/app/autoarr/ui/` for frontend
   - Understand the architecture

5. **Contribute**
   - Fix bugs
   - Add features
   - Improve documentation
   - See `/app/docs/CONTRIBUTING.md`

---

## Appendix

### Service Default Ports

| Service          | Default Port | URL                    |
| ---------------- | ------------ | ---------------------- |
| SABnzbd          | 8080         | http://localhost:8080  |
| Sonarr           | 8989         | http://localhost:8989  |
| Radarr           | 7878         | http://localhost:7878  |
| Plex             | 32400        | http://localhost:32400 |
| AutoArr Backend  | 8088         | http://localhost:8088  |
| AutoArr Frontend | 3000         | http://localhost:3000  |

### Environment Variables Reference

See `.env.local` for complete list with descriptions.

### API Endpoint Quick Reference

| Endpoint                         | Method    | Description             |
| -------------------------------- | --------- | ----------------------- |
| `/health`                        | GET       | Overall health          |
| `/health/services`               | GET       | Service health          |
| `/api/v1/config/audit`           | POST      | Run configuration audit |
| `/api/v1/config/recommendations` | GET       | Get recommendations     |
| `/api/v1/requests/content`       | POST      | Request content (NL)    |
| `/api/v1/requests`               | GET       | List all requests       |
| `/api/v1/movies`                 | GET       | List movies             |
| `/api/v1/shows`                  | GET       | List TV shows           |
| `/api/v1/downloads`              | GET       | List downloads          |
| `/ws`                            | WebSocket | Real-time updates       |

---

**Happy Testing!** 🚀
