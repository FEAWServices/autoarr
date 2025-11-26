# AutoArr Docker Development Setup

This directory contains Docker configurations for running AutoArr with live code reloading (hot-reload) on your host OS.

## 📁 Files Overview

### Development Compose Files

- **docker-compose.dev-simple.yml** - ⚡ **START HERE** - Simple setup (fastest)
  - Just the dev container
  - SQLite database
  - ~30 seconds startup
  - Perfect for most development

- **docker-compose.dev.yml** - Full production-like setup
  - Includes Redis cache
  - Includes PostgreSQL database
  - Good for testing with external services
  - ~2 minutes startup

### Scripts & Documentation

- **start-dev-container.sh** - 🚀 Interactive startup script
  - Menu-driven options
  - Handles all common tasks
  - Recommended for beginners

- **QUICK-START.md** - ⚡ 2-minute quick reference
  - Essential commands
  - Common tasks
  - Troubleshooting

- **DEV-CONTAINER-GUIDE.md** - 📚 Complete reference
  - Detailed explanation
  - All configuration options
  - Advanced usage
  - Performance optimization

### Docker Images

- **Dockerfile.api** - Production API image (single service)
- **Dockerfile.ui** - Production UI image (single service)
- **docker-compose.example.yml** - Example production setup
- **docker-compose.synology.yml** - Synology NAS specific setup

## 🚀 Quick Start (Choose One)

### Option 1: Interactive Script (Recommended)

```bash
bash start-dev-container.sh
```

Then select option 1 or 2 and follow the prompts.

### Option 2: Manual Docker Compose

```bash
# Simple setup
docker-compose -f docker-compose.dev-simple.yml up -d autoarr-dev

# Full setup with Redis & PostgreSQL
docker-compose -f docker-compose.dev.yml up -d
```

### Option 3: One-Liner for Impatient

```bash
cd /app/docker && docker-compose -f docker-compose.dev-simple.yml up -d && sleep 3 && docker exec -it autoarr-dev /bin/bash
```

## 📖 How It Works

### Key Concept: Bind Mounts with Live Reload

Instead of copying code into the image, we **mount your local files** into the container:

```
Your Computer          →  Docker Container
├── /app/autoarr/    →  /app/autoarr/ (same location)
├── /app/pyproject.toml → /app/pyproject.toml
└── Code changes visible instantly!
```

### Auto-Reload

The development servers use `--reload` flag:

**Backend**:

```bash
poetry run python -m uvicorn autoarr.api.main:app --reload
```

- Watches Python files
- Restarts server on changes
- Takes ~2 seconds

**Frontend**:

```bash
cd autoarr/ui && pnpm dev
```

- Vite hot module replacement
- Instant reload in browser
- No page refresh needed

## 🎯 Development Workflow

1. **Start the container once**:

   ```bash
   bash start-dev-container.sh
   # Choose option 1
   ```

2. **Keep it running**, open a new terminal:

   ```bash
   docker exec -it autoarr-dev /bin/bash
   ```

3. **Run backend with auto-reload**:

   ```bash
   poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload
   ```

4. **In another terminal, run frontend**:

   ```bash
   docker exec -it autoarr-dev bash -c "cd autoarr/ui && pnpm dev"
   ```

5. **Edit code in your editor**:
   - Changes appear instantly
   - Backend restarts automatically
   - Frontend hot-reloads

## 🌐 Access Points

| Component | URL                          | Notes        |
| --------- | ---------------------------- | ------------ |
| API       | http://localhost:8088        | REST API     |
| API Docs  | http://localhost:8088/docs   | OpenAPI docs |
| UI        | http://localhost:3000        | React app    |
| Health    | http://localhost:8088/health | Health check |

## 🔧 Common Tasks

### Run Tests

```bash
docker exec autoarr-dev poetry run pytest
```

### Run Tests with Coverage

```bash
docker exec autoarr-dev poetry run pytest --cov
```

### Format Code

```bash
docker exec autoarr-dev poetry run format
```

### Install Package (Python)

```bash
docker exec autoarr-dev poetry add package_name
```

### Install Package (Node.js)

```bash
docker exec autoarr-dev bash -c "cd autoarr/ui && pnpm add package_name"
```

### View Live Logs

```bash
docker logs -f autoarr-dev
```

### Stop Container

```bash
docker-compose -f docker/docker-compose.dev-simple.yml down
```

### Remove Everything (Clean Slate)

```bash
docker-compose -f docker/docker-compose.dev-simple.yml down -v
```

## 📋 What's Mounted Inside?

| Host Path             | Container Path                 | Type  | Purpose                    |
| --------------------- | ------------------------------ | ----- | -------------------------- |
| `/app`                | `/app`                         | Bind  | Your code (live changes)   |
| `node_modules` volume | `/app/autoarr/ui/node_modules` | Named | Dependencies (isolated)    |
| `venv` volume         | `/app/.venv`                   | Named | Python venv (fast restart) |

## 🔌 Ports

| Port | Service          | Purpose             |
| ---- | ---------------- | ------------------- |
| 8088 | AutoArr API      | Main API            |
| 3000 | React Dev Server | Frontend (with HMR) |
| 8000 | Alternative API  | Optional            |

## 🆘 Troubleshooting

### Container won't start

```bash
docker logs autoarr-dev
```

### Code changes not showing

- **Backend**: Restart the dev server (Ctrl+C, re-run)
- **Frontend**: Check browser console, refresh if needed

### Port in use

Edit `docker-compose.dev-simple.yml`:

```yaml
ports:
  - "8089:8088" # Use 8089 instead of 8088
```

### High memory usage

Keep frontend and backend in same container (they share memory).

### "No such file or directory"

Ensure you're running docker commands from `/app/docker/` directory.

## 📚 Next Steps

1. **Quick start**: See `QUICK-START.md`
2. **Full reference**: See `DEV-CONTAINER-GUIDE.md`
3. **Production deploy**: See `docker-compose.example.yml` or `docker-compose.synology.yml`

## 🎓 Comparison

| Setup                  | Startup | Reload Speed | Files Synced | Best For              |
| ---------------------- | ------- | ------------ | ------------ | --------------------- |
| Devcontainer (VS Code) | ~1 min  | 2-3 sec      | ✓ Native     | Full IDE integration  |
| dev-simple.yml         | ~30 sec | 2-3 sec      | ✓ Bind mount | Fast iteration        |
| dev.yml                | ~2 min  | 2-3 sec      | ✓ Bind mount | Production-like setup |
| Production             | ~1 min  | N/A          | ✗ Image      | Deployment            |

## 💡 Tips

1. **Keep container running** between sessions - faster restart
2. **Use separate terminals** - one for backend, one for frontend
3. **Monitor logs** - `docker logs -f autoarr-dev` in another terminal
4. **Check mounted files** - `docker exec autoarr-dev ls -la /app`

## 📞 Need Help?

- **Quick reference**: `QUICK-START.md`
- **Detailed guide**: `DEV-CONTAINER-GUIDE.md`
- **Project docs**: `/app/docs/`
- **Issues**: Check project issue tracker

---

**Ready to start?** Run `bash start-dev-container.sh` and choose option 1! 🚀
