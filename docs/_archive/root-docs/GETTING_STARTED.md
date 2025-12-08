# Getting Started with AutoArr

This guide will get you up and running with AutoArr in **5 minutes**.

## What is AutoArr?

AutoArr is an intelligent orchestration layer for your media automation stack (SABnzbd, Sonarr, Radarr, Plex) that provides:

- 🧠 **AI-Powered Configuration Auditing** - Get smart recommendations to optimize your setup
- 🤖 **Natural Language Content Requests** - Just type "Add Inception in 4K"
- 📊 **Unified Dashboard** - Monitor all your services in one place
- ⚡ **Real-time Updates** - Live status via WebSocket

## Prerequisites

You need:

1. **Your existing media services** (SABnzbd, Sonarr, Radarr) already installed and running
2. **Docker Desktop** installed and running
3. **API keys** from each service
4. **Node.js 20+** and **pnpm** (for frontend)

## Quick Start

### 1. Verify Your Setup

```bash
# Run the verification script
./scripts/verify-setup.sh
```

This will check:

- ✅ Your .env file is configured
- ✅ Your services are accessible
- ✅ Docker is running
- ✅ Dependencies are installed

### 2. Configure Environment

```bash
# Copy the template
cp .env.local .env

# Edit and add your API keys
nano .env
```

**Required changes:**

```bash
# Your actual service URLs (adjust if not localhost)
SABNZBD_URL=http://localhost:8080
SONARR_URL=http://localhost:8989
RADARR_URL=http://localhost:7878

# Your actual API keys (CRITICAL!)
SABNZBD_API_KEY=<your_key_here>
SONARR_API_KEY=<your_key_here>
RADARR_API_KEY=<your_key_here>

# Optional: AI features (recommended)
ANTHROPIC_API_KEY=sk-ant-<your_key_here>
```

**How to get API keys:**

- **SABnzbd**: Config → General → API Key
- **Sonarr**: Settings → General → Security → API Key
- **Radarr**: Settings → General → Security → API Key
- **Anthropic**: https://console.anthropic.com/

### 3. Start AutoArr

```bash
# One-command setup
./scripts/quickstart.sh
```

This will:

- ✅ Build AutoArr backend Docker image
- ✅ Start the backend service
- ✅ Wait for everything to be ready
- ✅ Display access URLs

### 4. Start Frontend

```bash
# In a new terminal
cd autoarr/ui
pnpm install
pnpm dev
```

### 5. Access AutoArr

Open your browser:

- **Frontend UI**: http://localhost:3000
- **API Docs**: http://localhost:8088/docs
- **Health Check**: http://localhost:8088/health

## What Can I Test?

### Configuration Audit

1. Go to Dashboard
2. Click "Run Configuration Audit"
3. Review AI-powered recommendations
4. Apply optimizations with one click

### Natural Language Requests

1. Go to Chat interface
2. Type: "Add Dune Part 2 in 4K"
3. Watch AutoArr classify, search, and add the content
4. Get real-time status updates

### Service Monitoring

1. View Dashboard
2. See health status of all services
3. Browse movies (Radarr) and shows (Sonarr)
4. View download queue (SABnzbd)

## Common Issues

### "Cannot connect to services"

**Solutions:**

- Verify services are running: `curl http://localhost:8080` (SABnzbd)
- Check API keys are correct (no spaces)
- If services are in Docker, use `host.docker.internal` instead of `localhost`
- If services are on another machine, use IP address: `http://192.168.1.100:8080`

### "AI features not working"

**Solutions:**

- Get Anthropic API key: https://console.anthropic.com/
- Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-your-key`
- Restart backend: `docker-compose -f docker-compose.dev.yml restart`

### "Docker build fails"

**Solutions:**

- Clear cache: `docker-compose -f docker-compose.dev.yml build --no-cache`
- Check disk space: `docker system df`
- Update Docker Desktop

## Next Steps

1. **Explore the UI** - Try all features and provide feedback
2. **Test Configuration Audit** - Run on all your services
3. **Try Natural Language** - Request various movies and TV shows
4. **Read the Docs**:
   - [Complete Testing Guide](docs/LOCAL_TESTING_GUIDE.md)
   - [Architecture](docs/ARCHITECTURE.md)
   - [Build Plan](docs/BUILD-PLAN.md)
   - [API Reference](http://localhost:8088/docs)

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Restart backend
docker-compose -f docker-compose.dev.yml restart

# Stop everything
docker-compose -f docker-compose.dev.yml down

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d
```

## Getting Help

- **Full Testing Guide**: [docs/LOCAL_TESTING_GUIDE.md](docs/LOCAL_TESTING_GUIDE.md)
- **Troubleshooting**: Check logs with `docker-compose logs -f`
- **API Docs**: http://localhost:8088/docs
- **Issues**: Create GitHub issue with logs

## Project Status

AutoArr is currently at **v0.5 (85% complete)**:

✅ **Working:**

- Configuration intelligence with AI recommendations
- Service health monitoring
- Browse and manage movies/shows
- Manual content requests
- WebSocket real-time updates
- Full UI with Dashboard, Chat, Settings

⏳ **In Progress:**

- Autonomous download monitoring
- Automatic failure recovery
- Advanced retry strategies

See [DEPLOYMENT_READINESS.md](docs/DEPLOYMENT_READINESS.md) for details.

---

**Ready to get started?**

```bash
./scripts/verify-setup.sh && ./scripts/quickstart.sh
```

**Questions?** See [LOCAL_TESTING_GUIDE.md](docs/LOCAL_TESTING_GUIDE.md) for comprehensive documentation.

🚀 Happy testing!
