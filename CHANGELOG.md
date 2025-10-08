# Changelog

All notable changes to AutoArr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-01-08

### Added

#### Core Features

- **Configuration Intelligence**: Intelligent configuration auditing with LLM-powered recommendations

  - Automatic scanning of SABnzbd, Sonarr, Radarr, and Plex configurations
  - Comparison against community best practices database
  - AI-powered contextual analysis and prioritization
  - One-click application of recommended changes with rollback support
  - Configuration history tracking for safe rollbacks

- **Autonomous Download Recovery**: Automatic detection and recovery of failed downloads

  - Real-time monitoring of SABnzbd queue
  - Instant detection of failed downloads
  - Intelligent retry strategies (quality fallback, alternative releases)
  - Proactive wanted list management
  - Detailed activity logging and metrics

- **Natural Language Content Requests**: Chat-based interface for content requests
  - Plain English content requests (e.g., "Add the new Dune movie in 4K")
  - Automatic movie vs. TV show classification using LLM
  - Smart search with disambiguation
  - Real-time status updates via WebSocket
  - Request history and tracking

#### Architecture

- **MCP Integration**: Complete Model Context Protocol implementation

  - SABnzbd MCP server with queue management, history, and retry capabilities
  - Sonarr MCP server with series management and search
  - Radarr MCP server with movie management and search
  - Plex MCP server with library management and scanning
  - MCP orchestrator with connection pooling and circuit breakers
  - Automatic retry logic with exponential backoff
  - Health checking and failover

- **Event-Driven System**: Comprehensive event bus implementation

  - Asynchronous event publishing and subscription
  - Event correlation tracking across services
  - WebSocket integration for real-time UI updates
  - Event persistence for auditing
  - Support for multiple subscribers per event type

- **LLM Integration**: Flexible AI integration
  - Anthropic Claude API integration (default)
  - Token usage tracking and cost monitoring
  - Rate limiting and backoff
  - Rule-based fallback engine for reliability
  - Prompt engineering framework
  - Graceful degradation when LLM unavailable

#### API

- **REST API**: Complete RESTful API with OpenAPI documentation

  - Configuration management endpoints (audit, recommendations, apply)
  - Download management endpoints (queue, history, retry)
  - TV show management endpoints (Sonarr integration)
  - Movie management endpoints (Radarr integration)
  - Media library endpoints (Plex integration)
  - Health check endpoints with circuit breaker status
  - Settings management endpoints
  - MCP proxy endpoints for direct server access

- **WebSocket API**: Real-time updates
  - Room-based subscriptions
  - Event broadcasting
  - Heartbeat/ping mechanism
  - Automatic reconnection handling
  - Client management

#### User Interface

- **Modern React UI**: Mobile-first responsive design
  - Dashboard with system health overview
  - Configuration audit interface with recommendations
  - Download monitoring and management
  - Content request chat interface
  - Settings and MCP server configuration
  - Real-time updates via WebSocket
  - Dark mode support (future)
  - WCAG 2.1 AA accessible

#### Database

- **Flexible Database Support**: SQLite and PostgreSQL
  - SQLAlchemy 2.0 ORM with async support
  - Alembic database migrations
  - Configuration audit history
  - Download recovery tracking
  - Content request history
  - Event logging
  - Settings persistence
  - MCP server configuration storage

#### Infrastructure

- **Docker Deployment**: Production-ready containerization

  - Multi-stage Docker builds
  - Docker Compose configuration
  - Synology NAS support with custom docker-compose
  - Health checks
  - Volume management
  - Network configuration
  - Resource limits

- **Testing**: Comprehensive test suite
  - 85%+ code coverage
  - Unit tests for all components
  - Integration tests for services
  - E2E tests with Playwright
  - MCP server tests
  - API endpoint tests
  - Pytest configuration with fixtures

#### Documentation

- **Complete Documentation Suite**
  - Architecture Deep Dive with diagrams
  - Complete API Reference
  - MCP Server Development Guide
  - Troubleshooting Guide
  - FAQ
  - Quick Start Guide
  - Configuration Guide
  - Contributing Guide
  - Code of Conduct

### Changed

- N/A (initial release)

### Deprecated

- N/A (initial release)

### Removed

- N/A (initial release)

### Fixed

- N/A (initial release)

### Security

- **Authentication**: API key authentication
- **Input Validation**: Comprehensive validation using Pydantic
- **Rate Limiting**: Protection against abuse
- **Security Headers**: Standard security headers on all responses
- **API Key Encryption**: Secure storage of service API keys
- **CORS Configuration**: Configurable cross-origin resource sharing
- **SQL Injection Prevention**: Parameterized queries throughout
- **No Secrets in Code**: All sensitive data via environment variables

---

## Version History

### Version Numbering

AutoArr follows [Semantic Versioning](https://semver.org/):

- **Major version**: Incompatible API changes
- **Minor version**: New functionality (backwards compatible)
- **Patch version**: Backwards compatible bug fixes

### Release Schedule

- **Major releases**: When significant features warrant breaking changes
- **Minor releases**: Every 2-3 months with new features
- **Patch releases**: As needed for bug fixes and security updates

### Upgrade Guide

For upgrade instructions between versions, see [UPGRADE_GUIDE.md](docs/UPGRADE_GUIDE.md).

---

[Unreleased]: https://github.com/autoarr/autoarr/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/autoarr/autoarr/releases/tag/v1.0.0
