# AutoArr Docker Deployment Guide

This guide explains how to deploy both the free (GPL-3.0) and premium (proprietary) versions of AutoArr using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Free Version Deployment](#free-version-deployment)
- [Premium Version Deployment](#premium-version-deployment)
- [Volume Management](#volume-management)
- [Upgrading](#upgrading)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Free Version:**

- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended for Ollama)
- 20GB disk space (more if using large Ollama models)
- CPU: 2+ cores recommended

**Premium Version:**

- Docker 20.10+ and Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 50GB disk space (for ML models and data)
- CPU: 4+ cores recommended
- Optional: NVIDIA GPU with nvidia-docker for accelerated inference

### Docker Installation

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## Free Version Deployment

The free version uses Ollama for local LLM inference and includes all core features without proprietary enhancements.

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/autoarr.git
cd autoarr
```

### Step 2: Configure Environment

```bash
# Copy the free version example environment file
cp .env.free.example .env

# Edit the environment file with your service credentials
nano .env
```

Required configuration:

- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `SABNZBD_API_KEY`: From SABnzbd Config → General
- `SONARR_API_KEY`: From Sonarr Settings → General
- `RADARR_API_KEY`: From Radarr Settings → General

### Step 3: Build and Start

```bash
# Build the image
docker-compose -f docker-compose.free.yml build

# Start services
docker-compose -f docker-compose.free.yml up -d

# Check logs
docker-compose -f docker-compose.free.yml logs -f autoarr-free
```

### Step 4: Download Ollama Model

The first time you start, you need to download the Ollama model:

```bash
# Enter the Ollama container
docker exec -it autoarr-ollama ollama pull llama3.1:8b

# Or for a larger model (requires more RAM)
docker exec -it autoarr-ollama ollama pull llama3.1:70b
```

### Step 5: Access AutoArr

- Web UI: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

---

## Premium Version Deployment

The premium version includes custom-trained ML models, enhanced monitoring, and autonomous recovery features.

### Step 1: Obtain License

1. Purchase a license at https://autoarr.app/pricing
2. You will receive a license key in the format: `AUTOARR-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`

### Step 2: Prepare ML Model

**Option A: Download Pre-trained Model**

```bash
# Create models directory
mkdir -p models/trained

# Download the official AutoArr recovery model
# (Replace with actual download URL)
wget https://models.autoarr.app/autoarr-recovery-model-v1.tar.gz
tar -xzf autoarr-recovery-model-v1.tar.gz -C models/trained/
```

**Option B: Train Your Own Model**

See [ML_TRAINING.md](./docs/ML_TRAINING.md) for instructions on training a custom model.

### Step 3: Configure Environment

```bash
# Copy the premium version example environment file
cp .env.premium.example .env

# Edit the environment file
nano .env
```

Required configuration:

- `LICENSE_KEY`: Your premium license key
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `MODEL_DIR`: Path to directory containing trained model
- Service API keys (SABnzbd, Sonarr, Radarr)
- Database credentials (PostgreSQL)

### Step 4: Build and Start

```bash
# Build the image
docker-compose -f docker-compose.premium.yml build

# Start services
docker-compose -f docker-compose.premium.yml up -d

# Check logs
docker-compose -f docker-compose.premium.yml logs -f autoarr-premium
```

### Step 5: Verify License

```bash
# Check license status
curl http://localhost:8000/api/settings/license/current

# Expected response:
# {
#   "license": {
#     "tier": "professional",
#     "expires_at": "2026-01-01T00:00:00Z",
#     ...
#   },
#   "validation": {
#     "valid": true,
#     "validation_type": "online"
#   }
# }
```

### Step 6: Access AutoArr

- Web UI: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/api/premium/monitoring/health

---

## Volume Management

### Free Version Volumes

```bash
# List volumes
docker volume ls | grep autoarr-free

# Backup data
docker run --rm -v autoarr-free-data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/autoarr-free-data-$(date +%Y%m%d).tar.gz /data

# Restore data
docker run --rm -v autoarr-free-data:/data -v $(pwd)/backup:/backup alpine tar xzf /backup/autoarr-free-data-YYYYMMDD.tar.gz -C /

# Remove all volumes (DESTRUCTIVE)
docker-compose -f docker-compose.free.yml down -v
```

### Premium Version Volumes

```bash
# List volumes
docker volume ls | grep autoarr-premium

# Backup database
docker exec autoarr-postgres pg_dump -U autoarr autoarr > backup/autoarr-db-$(date +%Y%m%d).sql

# Restore database
cat backup/autoarr-db-YYYYMMDD.sql | docker exec -i autoarr-postgres psql -U autoarr autoarr

# Backup all data
docker run --rm -v autoarr-premium-data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/autoarr-premium-data-$(date +%Y%m%d).tar.gz /data

# Remove all volumes (DESTRUCTIVE)
docker-compose -f docker-compose.premium.yml down -v
```

---

## Upgrading

### Free Version

```bash
# Pull latest images
docker-compose -f docker-compose.free.yml pull

# Rebuild (if using custom build)
docker-compose -f docker-compose.free.yml build

# Stop old containers
docker-compose -f docker-compose.free.yml down

# Start new containers
docker-compose -f docker-compose.free.yml up -d

# Check logs
docker-compose -f docker-compose.free.yml logs -f
```

### Premium Version

```bash
# Backup before upgrading!
docker exec autoarr-postgres pg_dump -U autoarr autoarr > backup/pre-upgrade-$(date +%Y%m%d).sql

# Pull latest images
docker-compose -f docker-compose.premium.yml pull

# Rebuild (if using custom build)
docker-compose -f docker-compose.premium.yml build

# Stop old containers
docker-compose -f docker-compose.premium.yml down

# Start new containers
docker-compose -f docker-compose.premium.yml up -d

# Check logs
docker-compose -f docker-compose.premium.yml logs -f

# Verify license still valid
curl http://localhost:8000/api/settings/license/current
```

---

## Troubleshooting

### Free Version Issues

**Ollama not responding:**

```bash
# Check Ollama logs
docker-compose -f docker-compose.free.yml logs ollama

# Restart Ollama
docker-compose -f docker-compose.free.yml restart ollama

# Verify model is downloaded
docker exec -it autoarr-ollama ollama list
```

**Out of memory:**

```bash
# Check resource usage
docker stats

# Increase Docker memory limits in Docker Desktop
# Or use a smaller Ollama model (e.g., llama3.1:8b instead of 70b)
```

### Premium Version Issues

**License validation failed:**

```bash
# Check license status
docker-compose -f docker-compose.premium.yml logs autoarr-premium | grep -i license

# Verify environment variable is set
docker exec autoarr-premium printenv LICENSE_KEY

# Test network connectivity to license server
docker exec autoarr-premium curl -I https://license.autoarr.app
```

**ML model not loading:**

```bash
# Check model path
docker exec autoarr-premium ls -la /app/models/trained/

# Verify model files
docker exec autoarr-premium ls -la /app/models/trained/autoarr-recovery-model/

# Check logs for model loading errors
docker-compose -f docker-compose.premium.yml logs autoarr-premium | grep -i model
```

**PostgreSQL connection failed:**

```bash
# Check PostgreSQL health
docker-compose -f docker-compose.premium.yml ps postgres

# Test connection
docker exec autoarr-postgres psql -U autoarr -c "SELECT version();"

# View PostgreSQL logs
docker-compose -f docker-compose.premium.yml logs postgres
```

### Common Issues (Both Versions)

**Port already in use:**

```bash
# Change the port in .env file
AUTOARR_PORT=8001

# Or find and kill the process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Permission denied errors:**

```bash
# Fix ownership of data directories
sudo chown -R 1001:1001 data/ logs/ cache/

# Or recreate volumes
docker-compose down -v
docker-compose up -d
```

**Service connections failing:**

```bash
# Verify services are accessible from container
docker exec autoarr-premium curl http://sabnzbd:8080

# Check network connectivity
docker network inspect autoarr-premium-network

# Verify API keys are correct in .env
```

---

## Advanced Configuration

### Using External PostgreSQL (Premium)

```yaml
# docker-compose.premium.yml
environment:
  - DATABASE_URL=postgresql://user:password@external-postgres:5432/autoarr
```

### Using vLLM for High-Throughput Inference (Premium)

Uncomment the vLLM service in `docker-compose.premium.yml` and set:

```bash
MODEL_TYPE=vllm
VLLM_URL=http://vllm:8080
```

### GPU Acceleration (Premium)

1. Install nvidia-docker:

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. Verify GPU access:

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

3. Enable GPU in compose file (uncomment vLLM service runtime)

---

## Monitoring

### Health Checks

```bash
# Free version
curl http://localhost:8000/health

# Premium version with detailed metrics
curl http://localhost:8000/api/premium/monitoring/health
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.premium.yml logs

# Follow specific service
docker-compose -f docker-compose.premium.yml logs -f autoarr-premium

# Filter by time
docker-compose -f docker-compose.premium.yml logs --since 1h

# Save logs to file
docker-compose -f docker-compose.premium.yml logs > autoarr-logs-$(date +%Y%m%d).log
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Disk usage
docker system df
```

---

## Support

- **Free Version**: GitHub Issues at https://github.com/your-org/autoarr/issues
- **Premium Version**: Priority support at support@autoarr.app
- **Documentation**: https://docs.autoarr.app
- **Community**: Discord at https://discord.gg/autoarr
