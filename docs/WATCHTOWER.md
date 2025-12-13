# Auto-Update with Watchtower

This guide explains how to set up automatic container updates using [Watchtower](https://containrrr.dev/watchtower/) so your AutoArr installation stays current with the latest changes.

## How It Works

1. You merge a PR to `main`
2. CI runs and builds a new Docker image tagged `:staging`
3. Watchtower detects the new image and automatically pulls it
4. Your container restarts with the updated image

## Quick Start

### Option 1: Docker Compose (Recommended)

Create a `docker-compose.yml`:

```yaml
version: "3.8"

services:
  autoarr:
    image: ghcr.io/feawservices/autoarr:staging
    container_name: autoarr
    restart: unless-stopped
    ports:
      - "8088:8088"
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    environment:
      APP_ENV: production
      LOG_LEVEL: INFO
      DATABASE_URL: sqlite:////data/autoarr.db
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      # Poll interval in seconds (300 = 5 minutes)
      WATCHTOWER_POLL_INTERVAL: 300
      # Only update containers with the watchtower label
      WATCHTOWER_LABEL_ENABLE: "true"
      # Remove old images after updating
      WATCHTOWER_CLEANUP: "true"
```

Start the stack:

```bash
docker-compose up -d
```

### Option 2: Docker Run Commands

```bash
# Create network
docker network create autoarr-net

# Run AutoArr
docker run -d \
  --name autoarr \
  --network autoarr-net \
  --restart unless-stopped \
  -p 8088:8088 \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  -e APP_ENV=production \
  -e DATABASE_URL=sqlite:////data/autoarr.db \
  -l com.centurylinklabs.watchtower.enable=true \
  ghcr.io/feawservices/autoarr:staging

# Run Watchtower
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e WATCHTOWER_POLL_INTERVAL=300 \
  -e WATCHTOWER_LABEL_ENABLE=true \
  -e WATCHTOWER_CLEANUP=true \
  containrrr/watchtower
```

## Configuration Options

### Image Tags

| Tag       | Description                             | Use Case                             |
| --------- | --------------------------------------- | ------------------------------------ |
| `staging` | Updated on every merge to main          | Development, testing, early feedback |
| `latest`  | Same as staging (continuous deployment) | General use                          |
| `vX.Y.Z`  | Specific version (from releases)        | Production, stability                |

### Watchtower Settings

| Environment Variable       | Default | Description                              |
| -------------------------- | ------- | ---------------------------------------- |
| `WATCHTOWER_POLL_INTERVAL` | 86400   | Seconds between checks (300 = 5 min)     |
| `WATCHTOWER_LABEL_ENABLE`  | false   | Only update labeled containers           |
| `WATCHTOWER_CLEANUP`       | false   | Remove old images after update           |
| `WATCHTOWER_LOG_LEVEL`     | info    | Log verbosity (debug, info, warn, error) |
| `WATCHTOWER_NOTIFICATIONS` | -       | Notification type (slack, email, etc.)   |

### Polling Intervals

| Interval   | Seconds | Use Case                          |
| ---------- | ------- | --------------------------------- |
| 5 minutes  | 300     | Fast feedback during development  |
| 30 minutes | 1800    | Balanced for staging environments |
| 1 hour     | 3600    | Production-like stability         |
| 24 hours   | 86400   | Minimal API calls                 |

## Notifications (Optional)

### Slack

```yaml
watchtower:
  environment:
    WATCHTOWER_NOTIFICATIONS: slack
    WATCHTOWER_NOTIFICATION_SLACK_HOOK_URL: "https://hooks.slack.com/services/xxx/yyy/zzz"
    WATCHTOWER_NOTIFICATION_SLACK_IDENTIFIER: "watchtower"
```

### Email

```yaml
watchtower:
  environment:
    WATCHTOWER_NOTIFICATIONS: email
    WATCHTOWER_NOTIFICATION_EMAIL_FROM: "watchtower@example.com"
    WATCHTOWER_NOTIFICATION_EMAIL_TO: "admin@example.com"
    WATCHTOWER_NOTIFICATION_EMAIL_SERVER: "smtp.example.com"
    WATCHTOWER_NOTIFICATION_EMAIL_SERVER_PORT: 587
```

## Monitoring Updates

Check Watchtower logs:

```bash
docker logs watchtower
```

Check when AutoArr was last updated:

```bash
docker inspect autoarr --format '{{.Created}}'
```

## Troubleshooting

### Container Not Updating

1. Check Watchtower logs: `docker logs watchtower`
2. Verify label is set: `docker inspect autoarr | grep watchtower`
3. Ensure registry is accessible: `docker pull ghcr.io/feawservices/autoarr:staging`

### Private Registry Authentication

If the registry requires authentication, create a config file:

```json
{
  "auths": {
    "ghcr.io": {
      "auth": "<base64-encoded-credentials>"
    }
  }
}
```

Mount it in Watchtower:

```yaml
watchtower:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - ./config.json:/config.json
  command: --config-file=/config.json
```

## Security Considerations

- Watchtower requires access to Docker socket (`/var/run/docker.sock`)
- Consider using `WATCHTOWER_LABEL_ENABLE=true` to limit which containers can be updated
- Review container images before enabling auto-updates in production

## Further Reading

- [Watchtower Documentation](https://containrrr.dev/watchtower/)
- [AutoArr Docker Guide](QUICK-START.md)
