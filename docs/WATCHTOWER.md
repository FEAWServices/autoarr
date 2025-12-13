# Auto-Update with Watchtower

This guide explains how to set up automatic container updates using [Watchtower](https://containrrr.dev/watchtower/) so your AutoArr installation stays current with the latest changes.

## Fast Deployment Pipeline

AutoArr is configured for rapid deployment. When you merge a PR to main:

| Step                         | Duration     |
| ---------------------------- | ------------ |
| PR merged to main            | 0 min        |
| Docker build starts          | ~30 sec      |
| Docker build & push to GHCR  | ~3-5 min     |
| Watchtower detects new image | ~0-2 min     |
| Container restart            | ~30 sec      |
| **Total**                    | **~5-8 min** |

## How It Works

1. You merge a PR to `main`
2. Docker image is built and tagged `:staging` (CI already validated the PR)
3. Watchtower detects the new image and automatically pulls it
4. Your container restarts with the updated image

## Quick Start

### Option 1: Synology NAS (Recommended)

Use the pre-configured Synology docker-compose file:

```bash
# SSH into your Synology
ssh admin@your-synology-ip

# Create directory
mkdir -p /volume1/docker/autoarr/{data,logs}
cd /volume1/docker/autoarr

# Download the Synology compose file
curl -O https://raw.githubusercontent.com/FEAWServices/autoarr/main/docker/docker-compose.synology.yml

# Start the stack
docker-compose -f docker-compose.synology.yml up -d
```

See [Synology Deployment Guide](deployment/synology-deployment.md) for detailed instructions.

### Option 2: Generic Docker Compose

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
      # Poll every 2 minutes for fast updates
      WATCHTOWER_POLL_INTERVAL: 120
      # Only update containers with the watchtower label
      WATCHTOWER_LABEL_ENABLE: "true"
      # Remove old images after updating
      WATCHTOWER_CLEANUP: "true"
```

Start the stack:

```bash
docker-compose up -d
```

### Option 3: Docker Run Commands

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

# Run Watchtower (2-minute polling)
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e WATCHTOWER_POLL_INTERVAL=120 \
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
| `WATCHTOWER_POLL_INTERVAL` | 86400   | Seconds between checks (120 = 2 min)     |
| `WATCHTOWER_LABEL_ENABLE`  | false   | Only update labeled containers           |
| `WATCHTOWER_CLEANUP`       | false   | Remove old images after update           |
| `WATCHTOWER_LOG_LEVEL`     | info    | Log verbosity (debug, info, warn, error) |
| `WATCHTOWER_NOTIFICATIONS` | -       | Notification type (slack, email, etc.)   |

### Recommended Polling Intervals

| Interval   | Seconds | Use Case                         |
| ---------- | ------- | -------------------------------- |
| 2 minutes  | 120     | Fast feedback during development |
| 5 minutes  | 300     | Balanced for most users          |
| 30 minutes | 1800    | Lower resource usage             |
| 1 hour     | 3600    | Production-like stability        |

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

Watch for updates in real-time:

```bash
docker logs -f watchtower
```

## Troubleshooting

### Container Not Updating

1. Check Watchtower logs: `docker logs watchtower`
2. Verify label is set: `docker inspect autoarr | grep watchtower`
3. Ensure registry is accessible: `docker pull ghcr.io/feawservices/autoarr:staging`
4. Check if new image exists: `docker images | grep autoarr`

### Force Update Now

```bash
# Trigger immediate update check
docker exec watchtower /watchtower --run-once
```

### Verify Image is Public

The AutoArr image is public on GHCR. Verify you can pull without auth:

```bash
docker logout ghcr.io  # Remove any cached credentials
docker pull ghcr.io/feawservices/autoarr:staging
```

## Security Considerations

- Watchtower requires access to Docker socket (`/var/run/docker.sock`)
- Use `WATCHTOWER_LABEL_ENABLE=true` to limit which containers can be updated
- The AutoArr image is public - no secrets are included in the image
- Review container images before enabling auto-updates in production

## Further Reading

- [Watchtower Documentation](https://containrrr.dev/watchtower/)
- [AutoArr Synology Guide](deployment/synology-deployment.md)
- [AutoArr Docker Guide](QUICK-START.md)
