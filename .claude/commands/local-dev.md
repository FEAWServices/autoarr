# Local Development Environment

Start and verify the local development environment using Docker.

## Instructions

When the user runs `/local-dev`, perform these steps:

### 1. Check Current Container Status

First, check if containers are already running:

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker ps --filter "name=autoarr" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 2. Start or Restart the Environment

If the user wants to start fresh or containers aren't running:

```bash
# Build the dev image if needed (from repo root)
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f /app/docker/docker-compose.local-test.yml build

# Start the containers
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f /app/docker/docker-compose.local-test.yml up -d
```

If containers are already running and the user just wants to verify health:

```bash
# Check container logs for startup progress
DOCKER_HOST=unix:///var/run/docker.sock docker logs autoarr-local --tail 50
```

### 3. Wait for Health Check

Wait for the container to become healthy (up to 90 seconds):

```bash
# Poll health status
for i in {1..30}; do
  STATUS=$(DOCKER_HOST=unix:///var/run/docker.sock docker inspect --format='{{.State.Health.Status}}' autoarr-local 2>/dev/null || echo "not_found")
  echo "Health check $i/30: $STATUS"
  if [ "$STATUS" = "healthy" ]; then
    echo "Container is healthy!"
    break
  fi
  sleep 3
done
```

### 4. Run Post-Deployment Tests

Once healthy, run the verification tests:

```bash
# Test health endpoint
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -sf http://localhost:8088/health

# Test UI is accessible
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -sf http://localhost:5173 -o /dev/null && echo "UI accessible"

# Test API docs
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -sf http://localhost:8088/docs -o /dev/null && echo "API docs accessible"
```

### 5. Report Access URLs

After successful startup, report:

- **Application**: http://localhost:9080 (Vite dev server + API proxy)
- **Direct API**: http://localhost:9081 (optional, direct backend access)
- **Storybook**: http://localhost:6006 (component library)

### Common Commands

Provide these helpful commands to the user:

```bash
# View logs
DOCKER_HOST=unix:///var/run/docker.sock docker logs autoarr-local -f

# Restart the app
DOCKER_HOST=unix:///var/run/docker.sock docker restart autoarr-local

# Stop everything
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f /app/docker/docker-compose.local-test.yml down

# Rebuild and restart (after code changes)
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f /app/docker/docker-compose.local-test.yml up -d --build
```

## Arguments

- `start` - Start/restart the environment (default)
- `stop` - Stop all containers
- `logs` - Show container logs
- `status` - Show container status only
- `test` - Run health tests only (assumes already running)
