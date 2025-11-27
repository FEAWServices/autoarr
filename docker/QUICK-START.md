# AutoArr Dev Container - Quick Start

Get the app running with live code reloading in 2 minutes.

## 1️⃣ Start the Container

```bash
cd /app/docker
bash start-dev-container.sh
```

Choose option **1** for fast startup (or **2** for Redis + PostgreSQL).

## 2️⃣ Open a Terminal in the Container

```bash
docker exec -it autoarr-dev /bin/bash
```

## 3️⃣ Run the App

**Backend only** (with hot-reload):

```bash
poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload
```

**Frontend only** (with hot-reload):

```bash
cd autoarr/ui
pnpm dev
```

**Both at once**:

```bash
./run_dev.sh
```

## 4️⃣ Access the App

- **API**: http://localhost:8088
- **API Docs**: http://localhost:8088/docs
- **UI**: http://localhost:3000

## 💡 Key Features

✅ **Live Reload**: Code changes appear instantly
✅ **Mounted Files**: Edit code on your OS, runs in Docker
✅ **Isolated Dependencies**: Python venv & node_modules in Docker
✅ **All Tools Included**: Poetry, Node, pnpm, Playwright, etc.
✅ **Same as Devcontainer**: Identical setup to VS Code devcontainer

## 🔨 Common Commands

```bash
# Run tests
poetry run pytest

# Format code
poetry run format

# Install new Python package
poetry add package_name

# Install new Node package
cd autoarr/ui && pnpm add package_name

# View container logs
docker logs -f autoarr-dev

# Stop container
docker-compose -f docker/docker-compose.dev.yml down
```

## 📋 Available Files

- **docker-compose.dev.yml** - Full setup with Redis & PostgreSQL
- **docker-compose.dev-simple.yml** - Simple setup (faster startup)
- **start-dev-container.sh** - Interactive startup script
- **DEV-CONTAINER-GUIDE.md** - Complete reference guide

## ⚡ Performance Tips

- Use **simple** setup for faster startup
- Code changes appear instantly (bind mount)
- Use `--reload` flag on backend for auto-restart
- Keep container running (fast restart)

## 🐛 Troubleshooting

**Container won't start?**

```bash
docker logs autoarr-dev
```

**Code changes not showing?**

- Backend: Restart the dev server (Ctrl+C, then re-run)
- Frontend: Hot-reload should work automatically

**Port already in use?**
Edit `docker-compose.dev-simple.yml` and change the port mapping.

## 📚 Full Documentation

See **DEV-CONTAINER-GUIDE.md** for complete guide with:

- Advanced configuration
- Using PostgreSQL/Redis
- Connecting to external services
- Multi-terminal development
- Performance optimization

---

**That's it!** You now have a fully functional development environment with live code reloading. 🎉
