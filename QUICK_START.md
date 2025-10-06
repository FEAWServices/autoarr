# AutoArr Quick Start Guide

## 🚀 Get Started in 3 Minutes

AutoArr is now ready to run with a **web-based admin interface** for configuration!

### Step 1: Install Dependencies

```bash
cd C:\Git\autoarr
poetry install
```

### Step 2: Start the Server

```bash
poetry run python -m api.main
```

You'll see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8088
```

### Step 3: Open Admin Interface

Open your browser to:
```
http://localhost:8088/static/admin.html
```

You'll see a beautiful admin interface with cards for each service:
- 📺 **SABnzbd** - Download manager
- 📺 **Sonarr** - TV show manager
- 🎬 **Radarr** - Movie manager
- 📺 **Plex** - Media server

---

## ⚙️ Configure Your Services

For each service, you can:

1. **Enable/Disable** - Toggle the service on/off
2. **Set URL** - Enter your service URL (e.g., `http://localhost:8080`)
3. **Add API Key** - Paste your API key or token
4. **Set Timeout** - Configure connection timeout (default: 30s)

### Where to Find API Keys:

#### SABnzbd
1. Go to `http://localhost:8080`
2. Config → General → Security → API Key

#### Sonarr
1. Go to `http://localhost:8989`
2. Settings → General → Security → API Key

#### Radarr
1. Go to `http://localhost:7878`
2. Settings → General → Security → API Key

#### Plex
1. Go to `https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/`
2. Follow instructions to get your X-Plex-Token

---

## 🧪 Test Connections

For each service in the admin interface:

1. Fill in the URL and API key
2. Click **"Test"** button
3. See instant feedback:
   - ✅ Green = Connected successfully
   - ❌ Red = Connection failed

This lets you verify credentials **before** saving!

---

## 💾 Save Settings

### Option 1: Save Individual Service
Click **"Save"** on each service card to save just that service.

### Option 2: Save All to .env File
Click the **"💾 Save All Settings to .env File"** button at the bottom to persist all settings.

This writes settings to `.env` so they survive restarts.

---

## 📊 View API Documentation

Once the server is running:

- **OpenAPI Docs**: http://localhost:8088/docs
- **ReDoc**: http://localhost:8088/redoc
- **Admin Panel**: http://localhost:8088/static/admin.html

---

## 🎯 What You Can Do Now

Once configured, you have access to **50 API endpoints**:

### Health & Status
```bash
curl http://localhost:8088/health
curl http://localhost:8088/health/sabnzbd
curl http://localhost:8088/health/sonarr
```

### SABnzbd Operations
```bash
# Get download queue
curl http://localhost:8088/api/v1/downloads/queue

# Get history
curl http://localhost:8088/api/v1/downloads/history

# Retry a failed download
curl -X POST http://localhost:8088/api/v1/downloads/retry/SABnzbd_nzo_abc123
```

### Sonarr Operations
```bash
# List all TV shows
curl http://localhost:8088/api/v1/shows/

# Get upcoming episodes
curl http://localhost:8088/api/v1/shows/calendar

# Search for a show
curl http://localhost:8088/api/v1/shows/search?term=Breaking+Bad
```

### Radarr Operations
```bash
# List all movies
curl http://localhost:8088/api/v1/movies/

# Get wanted movies
curl http://localhost:8088/api/v1/movies/wanted

# Search for a movie
curl http://localhost:8088/api/v1/movies/lookup?term=Inception
```

### Plex Operations
```bash
# List libraries
curl http://localhost:8088/api/v1/media/libraries

# Get recently added
curl http://localhost:8088/api/v1/media/recently-added

# See what's playing
curl http://localhost:8088/api/v1/media/sessions
```

---

## 🔧 Configuration Files

### Runtime (In-Memory)
Settings are stored in memory and can be updated via the admin interface.

### Persistent (.env file)
Click "Save All to .env" to persist settings:

```env
# SABnzbd Configuration
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=your_api_key_here
SABNZBD_ENABLED=true

# Sonarr Configuration
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_api_key_here
SONARR_ENABLED=true

# Radarr Configuration
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_api_key_here
RADARR_ENABLED=true

# Plex Configuration
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_token_here
PLEX_ENABLED=true
```

---

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build the container
docker build -t autoarr:latest .

# Run the container
docker run -d \
  --name autoarr \
  -p 8000:8000 \
  -v autoarr-data:/data \
  autoarr:latest

# Access admin interface
# http://localhost:8088/static/admin.html
```

### Using Docker Compose

```bash
# Use the production compose file
docker-compose -f docker-compose.prod.yml up -d

# Access admin interface
# http://localhost:8088/static/admin.html
```

---

## ✅ Features Available NOW

✅ **Web-based admin interface** - No .env editing needed!
✅ **Live connection testing** - Test before you save
✅ **Real-time status monitoring** - See connection health
✅ **50 REST API endpoints** - Full programmatic access
✅ **OpenAPI documentation** - Interactive API explorer
✅ **MCP orchestration** - Unified interface to all services
✅ **Docker deployment** - Single container, easy setup
✅ **Persistent configuration** - Save to .env file

---

## ❌ Features Coming in Phase 2

❌ Configuration auditing (AI-powered)
❌ LLM intelligence (natural language)
❌ Full React UI dashboard
❌ Automatic monitoring & recovery
❌ Activity logging & history

---

## 🎓 Next Steps

1. **Configure your services** using the admin interface
2. **Test connections** to verify everything works
3. **Explore the API** at `/docs`
4. **Build custom automation** using the 50 endpoints
5. **Deploy to Docker** for production use

---

## 🆘 Troubleshooting

### "Connection failed" error
- Verify the URL is correct
- Check the API key is valid
- Ensure the service is running
- Check firewall rules

### Admin page won't load
- Make sure server is running
- Check http://localhost:8088 returns JSON
- Try http://localhost:8088/static/admin.html

### Settings won't save
- Check server logs for errors
- Verify you have write permissions for .env file
- Try saving individual services first

---

## 📞 Support

- **Documentation**: http://localhost:8088/docs
- **GitHub Issues**: https://github.com/autoarr/autoarr/issues
- **Admin Interface**: http://localhost:8088/static/admin.html

---

**Enjoy your automated media management! 🎬📺**
