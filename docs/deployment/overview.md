# AutoArr Deployment Guide

## Overview

AutoArr can be deployed in two modes:

1. **Single Container** (recommended for v1.0) - All AutoArr components in one container
2. **Development Stack** (for contributors) - Full docker-compose with all dependencies

## Single Container Deployment (Production)

### Prerequisites

- Docker installed and running
- Existing SABnzbd, Sonarr, Radarr, and Plex instances (or other \*arr apps)
- API keys from your applications

### Quick Start

1. **Create environment file**

   ```bash
   curl -o .env https://raw.githubusercontent.com/autoarr/autoarr/main/.env.example
   ```

2. **Edit .env with your settings**

   ```bash
   nano .env
   ```

   Required settings:

   ```env
   SABNZBD_URL=http://your-sabnzbd:8080
   SABNZBD_API_KEY=your_sabnzbd_api_key

   SONARR_URL=http://your-sonarr:8989
   SONARR_API_KEY=your_sonarr_api_key

   RADARR_URL=http://your-radarr:7878
   RADARR_API_KEY=your_radarr_api_key

   PLEX_URL=http://your-plex:32400
   PLEX_TOKEN=your_plex_token
   ```

3. **Run AutoArr**

   ```bash
   docker run -d \
     --name autoarr \
     -p 8088:8088 \
     -v autoarr-data:/data \
     --env-file .env \
     autoarr/autoarr:latest
   ```

4. **Access AutoArr**
   - Web UI: http://localhost:8088
   - API Docs: http://localhost:8088/docs

### Using Docker Compose (Recommended)

1. **Download production compose file**

   ```bash
   curl -o docker-compose.yml https://raw.githubusercontent.com/autoarr/autoarr/main/docker-compose.prod.yml
   ```

2. **Create .env file** (see step 2 above)

3. **Start AutoArr**

   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f autoarr
   ```

### Configuration

#### Database

By default, AutoArr uses **SQLite** stored in `/data/autoarr.db`. This is perfect for most users.

For advanced users who want PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@postgres-host:5432/autoarr
```

#### Caching

By default, AutoArr uses **in-memory caching**. For better performance with PostgreSQL:

```env
REDIS_URL=redis://redis-host:6379/0
```

#### LLM Features (Optional)

To enable AI-powered configuration recommendations:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

#### Web Search (Optional)

To enable best practices search:

```env
BRAVE_API_KEY=your_brave_api_key
```

### Network Configuration

#### Connecting to Existing \*arr Stack

If your \*arr apps are on a custom Docker network:

```yaml
# In docker-compose.prod.yml, uncomment:
networks:
  - media-stack

# At bottom, uncomment:
networks:
  media-stack:
    external: true
    name: your-network-name  # e.g., "arr-stack", "media-network"
```

Then use container names in URLs:

```env
SABNZBD_URL=http://sabnzbd:8080
SONARR_URL=http://sonarr:8989
RADARR_URL=http://radarr:7878
PLEX_URL=http://plex:32400
```

#### Using Host Networking

If your \*arr apps run on the host machine:

```env
SABNZBD_URL=http://host.docker.internal:8080
SONARR_URL=http://host.docker.internal:8989
RADARR_URL=http://host.docker.internal:7878
PLEX_URL=http://host.docker.internal:32400
```

Or use your machine's IP:

```env
SABNZBD_URL=http://192.168.1.100:8080
```

### Data Persistence

The `/data` volume contains:

- `autoarr.db` - SQLite database
- `logs/` - Application logs
- `cache/` - Downloaded best practices

**Backup your data:**

```bash
docker run --rm \
  -v autoarr-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/autoarr-backup-$(date +%Y%m%d).tar.gz /data
```

**Restore from backup:**

```bash
docker run --rm \
  -v autoarr-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/autoarr-backup-YYYYMMDD.tar.gz -C /
```

### Updates

#### Pull latest image

```bash
docker pull autoarr/autoarr:latest
docker-compose down
docker-compose up -d
```

#### Update to specific version

```bash
docker pull autoarr/autoarr:v1.2.0
# Update image in docker-compose.yml
docker-compose up -d
```

### Security

#### Environment Variables Best Practices

Never commit `.env` to version control:

```bash
echo ".env" >> .gitignore
```

#### Use Docker Secrets (Docker Swarm/Compose v3.1+)

```yaml
services:
  autoarr:
    secrets:
      - sabnzbd_api_key
      - sonarr_api_key

secrets:
  sabnzbd_api_key:
    file: ./secrets/sabnzbd_api_key.txt
```

#### Reverse Proxy (Optional)

Use Nginx or Traefik for HTTPS:

**Nginx example:**

```nginx
server {
    listen 443 ssl;
    server_name autoarr.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Traefik labels:**

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.autoarr.rule=Host(`autoarr.yourdomain.com`)"
  - "traefik.http.routers.autoarr.entrypoints=websecure"
  - "traefik.http.routers.autoarr.tls.certresolver=letsencrypt"
```

## Kubernetes Deployment

For production Kubernetes deployment, see [KUBERNETES.md](KUBERNETES.md).

Basic deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autoarr
spec:
  replicas: 2
  selector:
    matchLabels:
      app: autoarr
  template:
    metadata:
      labels:
        app: autoarr
    spec:
      containers:
        - name: autoarr
          image: autoarr/autoarr:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: autoarr-config
            - secretRef:
                name: autoarr-secrets
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: autoarr-data
```

## Resource Requirements

### Minimum Requirements

- **CPU**: 0.5 cores
- **RAM**: 512 MB
- **Disk**: 100 MB (+ space for database growth)

### Recommended Requirements

- **CPU**: 1-2 cores
- **RAM**: 1-2 GB
- **Disk**: 1 GB

### Resource Limits (Docker)

```yaml
services:
  autoarr:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
```

## Monitoring

### Health Checks

AutoArr exposes a health endpoint:

```bash
curl http://localhost:8088/health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "sabnzbd": "reachable",
    "sonarr": "reachable",
    "radarr": "reachable",
    "plex": "reachable"
  }
}
```

### Logging

View logs:

```bash
docker logs -f autoarr
```

Configure log level:

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

Logs are also written to `/data/logs/`:

- `autoarr.log` - Application logs
- `access.log` - HTTP access logs
- `error.log` - Error logs

### Metrics (Future)

AutoArr will expose Prometheus metrics at `/metrics` in v1.1+

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs autoarr

# Check if port is in use
netstat -tuln | grep 8000

# Verify environment variables
docker exec autoarr env | grep -E "SABNZBD|SONARR|RADARR|PLEX"
```

### Can't connect to \*arr applications

```bash
# Test connectivity from container
docker exec autoarr curl -v http://sabnzbd:8080/api?mode=version&apikey=YOUR_KEY

# Check network
docker network inspect bridge
docker network ls
```

### Database errors

```bash
# Check database file
docker exec autoarr ls -lh /data/autoarr.db

# Reset database (WARNING: Deletes all data)
docker exec autoarr rm /data/autoarr.db
docker restart autoarr
```

### Performance issues

```bash
# Check resource usage
docker stats autoarr

# Increase memory limit
docker update --memory 2G autoarr

# Enable Redis caching
# Add to .env:
REDIS_URL=redis://redis:6379/0
```

## Uninstall

```bash
# Stop and remove container
docker-compose down

# Remove data volume (WARNING: Deletes all data)
docker volume rm autoarr-data

# Remove image
docker rmi autoarr/autoarr:latest
```

## Support

- **Documentation**: https://docs.autoarr.io
- **GitHub Issues**: https://github.com/autoarr/autoarr/issues
- **Discord**: https://discord.gg/autoarr
- **Discussions**: https://github.com/autoarr/autoarr/discussions
