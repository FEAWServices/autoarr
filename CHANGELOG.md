# Changelog

All notable changes to AutoArr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/FEAWServices/autoarr/compare/v1.0.0...v1.1.0) (2025-11-27)


### Features

* Add local test harness matching CI pipeline (DRY principle) ([7a7d4e2](https://github.com/FEAWServices/autoarr/commit/7a7d4e2875a4fd5903b5c6b99141209b412f7277))
* Add VS Code Dev Container with Poetry and Claude CLI ([9896afe](https://github.com/FEAWServices/autoarr/commit/9896afe023eff486a96892ffff825eb5f21b79ca))
* **ci:** Add GitHub Action to auto-rebase dependabot PRs ([#128](https://github.com/FEAWServices/autoarr/issues/128)) ([0a882ff](https://github.com/FEAWServices/autoarr/commit/0a882ffb78a44642901ef22177158787403a7858))
* Complete Phase 1 - Foundation with Web Admin Interface ([c3b6161](https://github.com/FEAWServices/autoarr/commit/c3b61617d06769aa74c7d4a5d230ebf925e4af1a))


### Documentation

* Add comprehensive testing guide ([2aa3733](https://github.com/FEAWServices/autoarr/commit/2aa37337bd633cbb627d974943711b0d94067e0e))
* restructure README with comprehensive vision and organized documentation ([68f4abe](https://github.com/FEAWServices/autoarr/commit/68f4abeffe929ed0292a321808c5557b978de83e))
* Update README to format init.py section correctly ([2f5c06f](https://github.com/FEAWServices/autoarr/commit/2f5c06f7a5f2d36ca851c0117212962e7ce6575c))

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
