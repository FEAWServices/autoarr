# Changelog

All notable changes to AutoArr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-19

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

- Dockerfile Python version (3.14 → 3.11)
- Frontend CI pnpm installation order

### Security

- Non-root Docker user
- .dockerignore for secrets
- Comprehensive security scanning

## [Unreleased]

### Planned for v1.1.0

- WebSocket Manager backend service
- Additional integrations (Prowlarr, Bazarr)
- Performance optimizations

[1.0.0]: https://github.com/FEAWServices/autoarr/releases/tag/v1.0.0
