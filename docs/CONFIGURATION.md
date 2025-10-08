# AutoArr Configuration Guide

Complete guide to configuring AutoArr for optimal performance.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Service Configuration](#service-configuration)
- [Feature Settings](#feature-settings)
- [Advanced Configuration](#advanced-configuration)
- [Configuration Files](#configuration-files)

## Environment Variables

### Required Settings

```bash
# SABnzbd Configuration
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=your_sabnzbd_api_key

# Sonarr Configuration
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_sonarr_api_key

# Radarr Configuration
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_radarr_api_key
```

### Optional Settings

```bash
# Plex Configuration (Optional)
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_plex_token

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-xxx  # For Claude API
```

### System Configuration

```bash
# Database
DATABASE_URL=sqlite:///./autoarr.db  # Default
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/autoarr

# API Configuration
AUTOARR_HOST=0.0.0.0
AUTOARR_PORT=8000
AUTOARR_RELOAD=false  # Enable in development

# Security
AUTOARR_SECRET_KEY=your-secret-key-here  # For JWT tokens
```

## Service Configuration

### SABnzbd

| Setting               | Description                   | Default | Recommended      |
| --------------------- | ----------------------------- | ------- | ---------------- |
| `direct_unpack`       | Extract while downloading     | false   | true             |
| `par2_multicore`      | Use multiple cores for repair | true    | true             |
| `unwanted_extensions` | Extensions to delete          | []      | [".nfo", ".txt"] |
| `quota_size`          | Download quota                | 0       | Leave at 0       |

### Sonarr

| Setting                      | Description       | Default | Recommended                                  |
| ---------------------------- | ----------------- | ------- | -------------------------------------------- |
| `rename_episodes`            | Auto-rename files | false   | true                                         |
| `replace_illegal_characters` | Clean filenames   | false   | true                                         |
| `standard_episode_format`    | Naming format     | Default | `{Series Title} - S{season:00}E{episode:00}` |

### Radarr

| Setting                      | Description       | Default | Recommended                      |
| ---------------------------- | ----------------- | ------- | -------------------------------- |
| `rename_movies`              | Auto-rename files | false   | true                             |
| `replace_illegal_characters` | Clean filenames   | false   | true                             |
| `standard_movie_format`      | Naming format     | Default | `{Movie Title} ({Release Year})` |

## Feature Settings

### Auto Configuration Audit

```bash
# Enable automatic configuration auditing
ENABLE_AUTO_AUDIT=true
AUDIT_INTERVAL=86400  # Run every 24 hours (in seconds)
```

### Download Monitoring

```bash
# Enable automatic download monitoring
ENABLE_DOWNLOAD_MONITORING=true
MONITOR_INTERVAL=120  # Check every 2 minutes (in seconds)
```

### Auto-Retry

```bash
# Enable automatic retry of failed downloads
ENABLE_AUTO_RETRY=true
MAX_RETRY_ATTEMPTS=3
```

## Advanced Configuration

### Circuit Breaker

```bash
# Circuit breaker settings for fault tolerance
CIRCUIT_BREAKER_THRESHOLD=5  # Open after 5 failures
CIRCUIT_BREAKER_TIMEOUT=60.0  # Stay open for 60 seconds
```

### Connection Pool

```bash
# MCP connection pool settings
CONNECTION_POOL_SIZE=10
MAX_CONCURRENT_REQUESTS=10
```

### Caching

```bash
# Redis cache settings
REDIS_URL=redis://localhost:6379
CACHE_TTL=300  # Cache for 5 minutes
```

## Configuration Files

### Using .env File

Create a `.env` file in the project root:

```bash
# Copy from template
cp .env.example .env

# Edit with your values
nano .env
```

### Using Docker Environment

```yaml
# docker-compose.yml
version: "3.8"
services:
  autoarr:
    image: autoarr/autoarr:latest
    environment:
      - SABNZBD_URL=http://sabnzbd:8080
      - SABNZBD_API_KEY=${SABNZBD_API_KEY}
      - SONARR_URL=http://sonarr:8989
      - SONARR_API_KEY=${SONARR_API_KEY}
```

### Using Environment File

```yaml
services:
  autoarr:
    env_file:
      - .env
```

---

For troubleshooting configuration issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
