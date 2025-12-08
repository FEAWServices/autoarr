# Changelog

All notable changes to AutoArr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2025-12-08

### Important

This is a **beta release**. AutoArr is feature-complete for configuration auditing and chat-based content requests, but some autonomous features are still being refined.

### Added

- **Configuration Intelligence**: AI-powered configuration auditing with recommendations
- **Chat Assistant**: Natural language interface for content requests with LLM tool calling
- **MCP Server Integrations**: Full integration with SABnzbd, Sonarr, Radarr, and Plex
- **Dashboard**: Service health monitoring and status overview
- **Settings Management**: Service connection configuration and testing
- **Activity Logging**: Backend service for tracking system activities
- **Monitoring Service**: Download queue monitoring (backend implemented)
- **Recovery Service**: Intelligent retry strategies (backend implemented)
- **Event Bus**: Pub/sub event system with correlation tracking

### Changed

- Version numbering aligned with actual feature completeness (was 1.1.0, now 0.8.0)
- Honest feature status in documentation

### Security

- Enterprise-grade container security (SBOM, cosign signing, SLSA provenance)
- Blocking Trivy scans for HIGH/CRITICAL vulnerabilities
- Docker Hub publishing alongside GHCR
- Non-root container user
- Comprehensive security policy

### Documentation

- Added BUILD_PLAN_REMAINING.md documenting path to v1.0
- Updated SECURITY.md with container security verification
- Added links to Sonarr/Radarr wikis

## [0.7.0] - 2025-11-27

### Features

- Add local test harness matching CI pipeline (DRY principle)
- Add VS Code Dev Container with Poetry and Claude CLI
- Add GitHub Action to auto-rebase dependabot PRs
- Complete Phase 1 - Foundation with Web Admin Interface

### Documentation

- Add comprehensive testing guide
- Restructure README with comprehensive vision and organized documentation

## [0.6.0] - 2025-10-19

### Added

#### Sprint 4 & 6: Dashboard UI and Activity Feed

- Dashboard with health scores and service status cards
- ConfigAudit UI with priority-based recommendation cards
- Activity feed for real-time system activity display
- Mobile-first responsive design (WCAG 2.1 AA compliant)
- Comprehensive Playwright E2E test suite

#### Sprint 5-6: Backend Services

- Event Bus service with pub/sub pattern and correlation tracking
- Activity Log service for system activity tracking and filtering
- Monitoring Service for SABnzbd queue monitoring
- Recovery Service with intelligent retry strategies
- 153 tests with ~95% code coverage

#### Sprint 7: Content Request Handler

- Request Handler service with NLP and content classification
- Content Integration service for Radarr/Sonarr
- Enhanced LLM agent for intelligent classification
- TMDB search integration
- POST/GET /api/requests API endpoints
- 639 new tests

#### Sprint 8: Chat UI & Request Tracking

- Chat interface for conversational content requests
- Real-time request status tracking
- WebSocket integration for live updates
- 1,436 lines of Playwright E2E tests

#### Sprint 9-10: Testing, CI/CD & Documentation

- Comprehensive CI/CD pipeline (Python CI, Frontend CI, Docker Deploy)
- Git Flow branching strategy with documentation
- Self-hosted runner configuration
- Host deployment tools and guides
- Security scanning (Bandit, Safety, Trivy)

### Changed

- Upgraded to self-hosted runner (Alienware)
- Enhanced pre-commit hooks

### Fixed

- Dockerfile Python version (3.14 -> 3.11)
- Frontend CI pnpm installation order

### Security

- Non-root Docker user
- .dockerignore for secrets
- Comprehensive security scanning

## [Unreleased]

### Planned for v1.0.0

- Activity API router (expose existing ActivityLogService)
- Activity UI page
- Monitoring service auto-start on application startup
- WebSocket real-time updates for activity feed
- Test coverage improvement (25% -> 85%)

[0.8.0]: https://github.com/FEAWServices/autoarr/releases/tag/v0.8.0
[0.7.0]: https://github.com/FEAWServices/autoarr/releases/tag/v0.7.0
[0.6.0]: https://github.com/FEAWServices/autoarr/releases/tag/v0.6.0
