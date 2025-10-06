# AutoArr Packaging Strategy

## Overview

AutoArr supports **two deployment modes** aligned with the BUILD-PLAN.md roadmap:

| Version | Mode | Architecture | Use Case |
|---------|------|--------------|----------|
| **v1.0** | Single Container | Monolithic | Home users, simplicity |
| **v2.0** | Microservices | Distributed | SaaS, enterprise, scale |

## v1.0: Single Container (Current)

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              AutoArr Container                      │
│                                                     │
│  ┌──────────────┐      ┌──────────────┐           │
│  │   Frontend   │◄─────┤  FastAPI     │           │
│  │  (Static)    │      │  Backend     │           │
│  └──────────────┘      └──────┬───────┘           │
│                               │                    │
│  ┌────────────────────────────┴─────────────┐     │
│  │         MCP Servers (Embedded)           │     │
│  ├──────────┬──────────┬──────────┬─────────┤     │
│  │ SABnzbd  │  Sonarr  │  Radarr  │  Plex   │     │
│  └──────────┴──────────┴──────────┴─────────┘     │
│                                                     │
│  ┌─────────────────────────────────────────┐      │
│  │   SQLite Database (/data/autoarr.db)    │      │
│  └─────────────────────────────────────────┘      │
│                                                     │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │SABnzbd  │    │ Sonarr  │    │ Radarr  │  (External)
   │Container│    │Container│    │Container│
   └─────────┘    └─────────┘    └─────────┘
```

### What's Included in the Container

✅ **Application Layer**
- FastAPI backend (Python 3.11)
- React frontend (built static files)
- Uvicorn ASGI server (4 workers)

✅ **MCP Servers** (Embedded Libraries)
- SABnzbd MCP client & server
- Sonarr MCP client & server
- Radarr MCP client & server
- Plex MCP client & server

✅ **Database**
- SQLite (default) - stored in `/data` volume
- Optional: PostgreSQL (external)

✅ **Caching**
- In-memory cache (default)
- Optional: Redis (external)

✅ **Dependencies**
- All Python packages (Poetry)
- Runtime libraries

### What's NOT Included (External Dependencies)

❌ SABnzbd application (user provides URL + API key)
❌ Sonarr application (user provides URL + API key)
❌ Radarr application (user provides URL + API key)
❌ Plex Media Server (user provides URL + token)
❌ PostgreSQL (optional, for advanced users)
❌ Redis (optional, for advanced users)

### Image Size Target

- **Base Image**: `python:3.11-slim` (~150 MB)
- **Python Dependencies**: ~200 MB
- **Frontend Build**: ~10 MB (gzipped static files)
- **Application Code**: ~5 MB

**Total Target**: < 400 MB

### Build Process

The `Dockerfile` uses **multi-stage builds**:

1. **Stage 1**: Build React frontend
   - Node.js 18 Alpine
   - pnpm build → static files in `dist/`

2. **Stage 2**: Install Python dependencies
   - Python 3.11 + Poetry
   - Install packages to system Python

3. **Stage 3**: Create production image
   - Python 3.11 slim
   - Copy dependencies from Stage 2
   - Copy frontend from Stage 1
   - Copy application code

### Configuration

Users configure via **environment variables**:

```env
# Required
SABNZBD_URL=http://sabnzbd:8080
SABNZBD_API_KEY=abc123...

SONARR_URL=http://sonarr:8989
SONARR_API_KEY=def456...

RADARR_URL=http://radarr:7878
RADARR_API_KEY=ghi789...

PLEX_URL=http://plex:32400
PLEX_TOKEN=xyz123...

# Optional
DATABASE_URL=sqlite:////data/autoarr.db
REDIS_URL=memory://
ANTHROPIC_API_KEY=sk-ant-...
LOG_LEVEL=INFO
```

### Data Persistence

Single volume mount: `/data`

Contains:
- `autoarr.db` - SQLite database
- `logs/` - Application logs
- `cache/` - Downloaded best practices & embeddings

### Deployment Examples

**Docker CLI:**
```bash
docker run -d \
  --name autoarr \
  -p 8000:8000 \
  -v autoarr-data:/data \
  -e SABNZBD_URL=http://sabnzbd:8080 \
  -e SABNZBD_API_KEY=your_key \
  autoarr/autoarr:latest
```

**Docker Compose:**
```yaml
services:
  autoarr:
    image: autoarr/autoarr:latest
    ports:
      - "8000:8000"
    volumes:
      - autoarr-data:/data
    env_file: .env
```

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 1  # Stateful, single replica
  template:
    spec:
      containers:
      - name: autoarr
        image: autoarr/autoarr:latest
        volumeMounts:
        - name: data
          mountPath: /data
```

---

## v2.0: Microservices (Future)

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Load Balancer                      │
│              (Nginx / Traefik)                      │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│   Frontend   │   │  API Gateway │
│  (Static CDN)│   │  (FastAPI)   │
└──────────────┘   └──────┬───────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│MCP Service  │   │ Config Mgr  │   │  Monitor    │
│(SABnzbd)    │   │  Service    │   │  Service    │
└─────────────┘   └─────────────┘   └─────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
        ┌──────────────┐    ┌──────────────┐
        │  PostgreSQL  │    │    Redis     │
        │   Cluster    │    │   Cluster    │
        └──────────────┘    └──────────────┘
```

### Services Breakdown

Each service gets its own container:

1. **Frontend Service** (Nginx)
   - Serves static React app from CDN
   - ~50 MB image

2. **API Gateway** (FastAPI)
   - Routes requests to MCP services
   - Authentication & rate limiting
   - ~200 MB image

3. **MCP Service - SABnzbd** (Python)
   - Dedicated MCP server for SABnzbd
   - Horizontally scalable
   - ~150 MB image

4. **MCP Service - Sonarr** (Python)
   - Dedicated MCP server for Sonarr
   - ~150 MB image

5. **MCP Service - Radarr** (Python)
   - Dedicated MCP server for Radarr
   - ~150 MB image

6. **MCP Service - Plex** (Python)
   - Dedicated MCP server for Plex
   - ~150 MB image

7. **Configuration Manager** (Python)
   - Best practices & auditing
   - LLM integration
   - ~250 MB image

8. **Monitoring Service** (Python)
   - Download monitoring & recovery
   - WebSocket real-time updates
   - ~200 MB image

### Orchestration

**Docker Swarm:**
```yaml
version: '3.8'
services:
  api-gateway:
    image: autoarr/api-gateway:2.0
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-sabnzbd
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### Benefits of Microservices (v2.0)

✅ **Scalability**
- Scale each MCP service independently
- Handle high load (thousands of users)

✅ **Reliability**
- Service isolation (one failure doesn't take down others)
- Rolling updates with zero downtime

✅ **Development**
- Teams can work on services independently
- Faster CI/CD pipelines

✅ **Multi-tenancy**
- SaaS platform support
- User isolation

### Drawbacks vs Single Container

❌ **Complexity**
- Requires orchestration (K8s/Swarm)
- More configuration

❌ **Resource Usage**
- Higher memory overhead (~2GB minimum vs 512MB)
- More CPU for inter-service communication

❌ **Cost**
- Requires managed database & cache
- Higher hosting costs

---

## Recommendation

### For v1.0 (Home Users) ✅

**Use single container deployment:**
- Easy setup: One `docker run` command
- Low resources: 512 MB RAM, 0.5 CPU
- Simple updates: `docker pull && docker restart`
- Perfect for 1-10 users
- Self-hosted on Raspberry Pi, NAS, or home server

**Dockerfile location**: `./Dockerfile`
**Compose file**: `./docker-compose.prod.yml`

### For v2.0 (SaaS Platform) 🚀

**Use microservices deployment:**
- Kubernetes cluster (AWS EKS, GKE, or self-hosted)
- Managed PostgreSQL (AWS RDS, Cloud SQL)
- Managed Redis (ElastiCache, Cloud Memorystore)
- CDN for frontend (CloudFront, Cloudflare)
- Perfect for 100+ users

**Location**: `./k8s/` (to be created in Phase 5)

---

## Build Commands

### Single Container

**Build locally:**
```bash
docker build -t autoarr/autoarr:latest .
```

**Build with version tag:**
```bash
docker build -t autoarr/autoarr:v1.0.0 .
```

**Multi-platform build:**
```bash
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t autoarr/autoarr:latest \
  --push .
```

### CI/CD (GitHub Actions)

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: |
      autoarr/autoarr:latest
      autoarr/autoarr:${{ github.ref_name }}
```

---

## Distribution Channels

### Docker Hub
- Primary distribution
- `autoarr/autoarr:latest`
- `autoarr/autoarr:v1.0.0`

### GitHub Container Registry
- Backup/alternative
- `ghcr.io/autoarr/autoarr:latest`

### Platform-Specific

**Unraid:**
- Community Applications template
- One-click install

**Synology:**
- Community package

**Home Assistant:**
- Add-on repository

---

## Summary

**Yes, AutoArr will be packaged as a single container for v1.0!**

The architecture is designed to:
- ✅ Be simple for end users (one container)
- ✅ Work with existing *arr stacks
- ✅ Use minimal resources (< 1GB RAM)
- ✅ Support easy updates
- ✅ Scale to microservices in v2.0 when needed

The current `docker-compose.yml` is for **development only**. The production deployment uses a single `Dockerfile` that bundles everything together.
