# AutoArr Development Container Guide

This guide explains how to run AutoArr in a Docker container with live code reloading, just like the VS Code devcontainer but standalone on your OS.

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
cd /app/docker
bash ./start-dev-container.sh
```

This interactive script will:

- Check Docker/Docker Compose installation
- Offer options to start containers with different configurations
- Display ports and access URLs
- Show useful commands

### Option 2: Manual Docker Compose

```bash
cd /app/docker
docker-compose -f docker-compose.dev.yml up -d autoarr-dev
```

## How It Works

### Key Differences from Production

| Aspect       | Dev Container             | Production        |
| ------------ | ------------------------- | ----------------- |
| Code Mount   | Bind-mounted from host    | Copied into image |
| Hot Reload   | ✓ Enabled (via --reload)  | ✗ Disabled        |
| Dependencies | Poetry venv in volume     | Baked into image  |
| Database     | SQLite (in-memory option) | PostgreSQL        |
| Logging      | DEBUG level               | INFO level        |
| File Changes | Reflected immediately     | Requires rebuild  |

### Volume Setup

The dev container uses three key volumes:

1. **Code Mount** (`..:/app:cached`)
   - Entire project directory mounted
   - Changes visible immediately in container
   - `:cached` for better performance on Mac/Windows

2. **Node Modules** (`node_modules:/app/autoarr/ui/node_modules`)
   - Prevents host OS node_modules from interfering
   - Keeps dependencies inside container

3. **Poetry Venv** (`venv:/app/.venv`)
   - Preserves Python virtual environment
   - Avoids reinstalling packages on restart

## Accessing the Container

### Open a Shell

```bash
docker exec -it autoarr-dev /bin/bash
```

### Run Commands Inside

Once in the shell, you can:

**Backend (with hot-reload):**

```bash
poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload
```

**Frontend (with hot-reload):**

```bash
cd autoarr/ui
pnpm dev
```

**Run Both (if available):**

```bash
./run_dev.sh
```

**Run Tests:**

```bash
poetry run pytest
poetry run pytest tests/unit
poetry run pytest --cov
```

**Format Code:**

```bash
poetry run format
cd autoarr/ui && pnpm run format
```

## Ports Exposed

| Port  | Service           | URL                    |
| ----- | ----------------- | ---------------------- |
| 8088  | AutoArr API       | http://localhost:8088  |
| 8000  | API (alternative) | http://localhost:8000  |
| 3000  | React Frontend    | http://localhost:3000  |
| 8080  | SABnzbd           | http://localhost:8080  |
| 8989  | Sonarr            | http://localhost:8989  |
| 7878  | Radarr            | http://localhost:7878  |
| 32400 | Plex              | http://localhost:32400 |
| 5432  | PostgreSQL        | localhost:5432         |
| 6379  | Redis             | localhost:6379         |

## Configuration

### Environment Variables

Create `.env` in the project root:

```bash
# Service API Keys
SABNZBD_API_KEY=your_key
SONARR_API_KEY=your_key
RADARR_API_KEY=your_key
PLEX_TOKEN=your_token

# AI Features (optional)
ANTHROPIC_API_KEY=your_key
BRAVE_API_KEY=your_key

# GitHub (optional)
GITHUB_ADMIN_TOKEN=your_token

# Database
POSTGRES_PASSWORD=autoarr

# Git
GIT_NAME="Your Name"
GIT_EMAIL="your@email.com"
```

Copy from `.env.example.dev` if created by the startup script.

### Database Choice

**SQLite (default):**

- No additional setup
- Good for development
- Data stored in `/data/autoarr.db`

**PostgreSQL (included):**

- More production-like
- Included when starting with option 2
- Accessible at `localhost:5432`
- User: `autoarr`, Password: from `.env`

To use PostgreSQL, update `DATABASE_URL`:

```bash
DATABASE_URL=postgresql://autoarr:password@postgres:5432/autoarr
```

## Common Tasks

### View Logs

```bash
# All container logs
docker logs -f autoarr-dev

# Just the last 100 lines
docker logs -n 100 autoarr-dev
```

### Rebuild Dependencies

If you modify `pyproject.toml` or `package.json`:

```bash
# Python
docker exec -it autoarr-dev poetry install

# Node.js/Frontend
docker exec -it autoarr-dev bash -c "cd autoarr/ui && pnpm install"
```

### Run Tests

```bash
# Unit tests only
docker exec autoarr-dev poetry run pytest tests/unit

# With coverage
docker exec autoarr-dev poetry run pytest --cov

# Frontend tests
docker exec -it autoarr-dev bash -c "cd autoarr/ui && pnpm test"
```

### Install New Package

```bash
# Python
docker exec -it autoarr-dev poetry add package_name

# Node.js
docker exec -it autoarr-dev bash -c "cd autoarr/ui && pnpm add package_name"
```

### Stop Container

```bash
docker-compose -f docker/docker-compose.dev.yml down
```

### Clean Up Everything

```bash
# Remove container and volumes
docker-compose -f docker/docker-compose.dev.yml down -v

# Remove images
docker image rm autoarr_autoarr-dev
```

## Troubleshooting

### Container won't start

Check logs:

```bash
docker logs autoarr-dev
```

Common issues:

- Port already in use: Change port mapping in `docker-compose.dev.yml`
- Permission denied: Check file ownership
- Out of memory: Increase Docker memory limit

### Code changes not reflected

The container uses bind mounts, changes should be instant. If not:

1. Check the mount is active:

   ```bash
   docker inspect autoarr-dev | grep -A 5 Mounts
   ```

2. Restart the development server inside the container
3. Clear any caches (Redis, browser cache)

### High disk usage

Named volumes can grow large:

```bash
docker volume ls | grep autoarr
docker volume prune
```

### Can't access external services (SABnzbd, Sonarr, etc.)

Options:

1. Use container networking if services are also in Docker
2. Use `host.docker.internal` (Mac/Windows) instead of `localhost`
3. Update URLs in `.env` to point to actual external IPs

Example for external services:

```bash
SABNZBD_URL=http://192.168.1.100:8080
SONARR_URL=http://192.168.1.100:8989
```

## Advanced Usage

### Using External Media Stack Network

If your SABnzbd, Sonarr, etc. are on a shared Docker network:

1. Find the network name:

   ```bash
   docker network ls
   ```

2. Uncomment in `docker-compose.dev.yml`:

   ```yaml
   networks:
     default:
       name: your_media_network
       external: true
   ```

3. Update service URLs in `.env`:
   ```bash
   SABNZBD_URL=http://sabnzbd:8080
   SONARR_URL=http://sonarr:8989
   ```

### Multi-Terminal Development

Keep multiple terminals open:

1. **Terminal 1**: Backend

   ```bash
   docker exec -it autoarr-dev bash
   poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload
   ```

2. **Terminal 2**: Frontend

   ```bash
   docker exec -it autoarr-dev bash
   cd autoarr/ui && pnpm dev
   ```

3. **Terminal 3**: Tests/utilities

   ```bash
   docker exec -it autoarr-dev bash
   poetry run pytest -x --lf
   ```

4. **Terminal 4**: Logs
   ```bash
   docker logs -f autoarr-dev
   ```

### SSH Into Container

If you need persistent access:

```bash
docker run -it --volumes-from autoarr-dev autoarr_autoarr-dev /bin/bash
```

Or add an SSH service to `docker-compose.dev.yml`.

## Performance Tips

### Mac/Windows (Docker Desktop)

1. Use `:cached` mount option (already set)
2. Exclude large directories:

   ```yaml
   volumes:
     - ..:/app:cached
     # Add exclusions in .dockerignore
   ```

3. Create `.dockerignore`:
   ```
   node_modules
   .venv
   .pytest_cache
   __pycache__
   .git
   .idea
   .vscode
   ```

### Linux

Performance is better, but still:

- Use volumes for node_modules and venv
- Consider disabling SELinux if having issues
- Use `--storage-driver=overlay2`

## What's Different from Devcontainer

| Feature            | Devcontainer       | Dev Container Script         |
| ------------------ | ------------------ | ---------------------------- |
| IDE Integration    | VS Code native     | Manual shell access          |
| File Sync          | Native (better)    | Docker volumes               |
| Extensions         | VS Code extensions | Not applicable               |
| Port Forwarding    | Automatic          | Manual in docker-compose.yml |
| Post-create Script | Auto-runs          | Manual run via entrypoint    |

## Switching Between Devcontainer and Docker

You can use both:

- **Devcontainer**: For full VS Code IDE integration
- **Docker Container**: For standalone development or CI/CD testing

The setup is identical, just different access methods.

## Getting Help

See main project documentation:

- Architecture: `/app/docs/ARCHITECTURE.md`
- API Reference: `/app/docs/API_REFERENCE.md`
- Troubleshooting: `/app/docs/TROUBLESHOOTING.md`
