# AutoArr Documentation

**License:** GPL-3.0-or-later
**Status:** v1.0 feature-complete

## Overview

AutoArr is a 100% free and open source intelligent orchestration layer for media automation stacks. This directory contains user-facing documentation.

## Quick Links

- [Quick Start Guide](../QUICK_START.md)
- [API Reference](../API_REFERENCE.md)
- [Architecture](../ARCHITECTURE.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
- [Contributing](../CONTRIBUTING.md)

## Documentation Index

### Getting Started

- [Quick Start](../QUICK_START.md) - Installation and setup
- [Configuration](../CONFIGURATION.md) - Environment variables and settings
- [Docker Setup](../DOCKER_SETUP.md) - Docker deployment

### User Guides

- [API Reference](../API_REFERENCE.md) - Complete API documentation
- [MCP Server Guide](../MCP_SERVER_GUIDE.md) - MCP server development
- [Troubleshooting](../TROUBLESHOOTING.md) - Common issues and solutions

### Architecture

- [Architecture Overview](../ARCHITECTURE.md) - System design
- [Architecture Deep Dive](../ARCHITECTURE_DEEP_DIVE.md) - Detailed technical docs
- [Build Plan](../BUILD-PLAN.md) - 20-week development plan

### Development

- [Contributing](../CONTRIBUTING.md) - How to contribute
- [Development Guide](../DEVELOPMENT.md) - Local development setup
- [Testing](../TESTING.md) - Testing strategy
- [Code Examples](../CODE-EXAMPLES.md) - Example code

### Deployment

- [Deployment Guide](../DEPLOYMENT.md) - Production deployment
- [Synology Setup](../SYNOLOGY_SETUP.md) - Synology NAS deployment
- [Docker Compose](../../docker/) - Docker compose files

## Feature Documentation

### Configuration Intelligence

- Configuration auditing
- Intelligent recommendations
- Quality profile analysis

### Download Recovery

- Automatic failure detection
- Intelligent retry strategies
- SABnzbd integration

### Natural Language Interface

- Chat-based content requests
- Movie/TV classification
- Web search integration (TMDB, Brave)

### Monitoring

- Real-time activity feed
- WebSocket live updates
- System health monitoring

## API Documentation

See [API_REFERENCE.md](../API_REFERENCE.md) for complete API documentation.

**Base URL:** `http://localhost:8000`

**Key Endpoints:**

- `/api/v1/config/audit` - Configuration auditing
- `/api/v1/monitoring/queue` - Queue monitoring
- `/api/v1/recovery/failures` - Download failures
- `/api/v1/requests` - Content requests
- `/api/v1/activity` - Activity feed
- `/ws` - WebSocket connection

## Technology Stack

**Backend:**

- Python 3.11+ with FastAPI
- SQLite/PostgreSQL
- MCP (Model Context Protocol)
- Claude 3.5 Sonnet

**Frontend:**

- React 18 + TypeScript
- Tailwind CSS
- Zustand state management
- React Query

## Support

- **Documentation:** This directory
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Community:** Discord (coming soon)

## License

AutoArr is licensed under GPL-3.0-or-later. See `/app/autoarr/LICENSE` for details.

---

_Last Updated: 2025-01-12_
_Version: 1.0.0_
