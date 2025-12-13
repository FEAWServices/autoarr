# Changelog

All notable changes to AutoArr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.1](https://github.com/FEAWServices/autoarr/compare/v0.8.0...v0.8.1) (2025-12-13)


### Features

* Add comprehensive release management and security scanning ([a564278](https://github.com/FEAWServices/autoarr/commit/a5642785502b8a5a6005736771c0e969e4e1bc46))
* Add full tool providers and optimization for Sonarr, Radarr, Plex ([76bbd70](https://github.com/FEAWServices/autoarr/commit/76bbd70b61c446bc259c3d6ded69c6c02138e578))
* Add local test harness matching CI pipeline (DRY principle) ([3822a63](https://github.com/FEAWServices/autoarr/commit/3822a638fd339f646340a3b98f955a5147c00b62))
* Add OpenRouter LLM provider, onboarding flow, and service pages ([1a240b8](https://github.com/FEAWServices/autoarr/commit/1a240b89d7e0aaf136a2ef0581648ee236e16a3b))
* Add pull-to-refresh, fix onboarding connection, enhance documentation ([56a608a](https://github.com/FEAWServices/autoarr/commit/56a608aa6ded3ce3b839f2b668b7333811900d0e))
* Add VS Code Dev Container with Poetry and Claude CLI ([6832460](https://github.com/FEAWServices/autoarr/commit/683246001384794963e72bf5fde275912e6b1ba9))
* **api:** Add Activity API router for activity log access ([37254a3](https://github.com/FEAWServices/autoarr/commit/37254a3d58b51de124245e3ae8510d5d3185e750))
* **api:** Non-blocking service reconnect and settings validation tests ([dab2155](https://github.com/FEAWServices/autoarr/commit/dab21550a51ddf33f5a6ca0e0c9003ffcf6a8b79))
* **ci:** Add E2E test results to GitHub Actions job summary ([01be34c](https://github.com/FEAWServices/autoarr/commit/01be34c2982c4cbc0ce5015f6b1336b8a020de8e))
* **ci:** Add GitHub Action to auto-rebase dependabot PRs ([079f9fb](https://github.com/FEAWServices/autoarr/commit/079f9fbe4cec65303080d5f748abe949cc321c78))
* **ci:** Add GitHub Action to auto-rebase dependabot PRs ([#128](https://github.com/FEAWServices/autoarr/issues/128)) ([5cf4c7f](https://github.com/FEAWServices/autoarr/commit/5cf4c7fdddfabbb44b1847b22d8cdfa3fefe594e))
* **ci:** Re-enable E2E tests with Docker container in CI ([d527d7e](https://github.com/FEAWServices/autoarr/commit/d527d7e90f3a324a2cbb64f4470302232901e941))
* Complete Phase 1 - Foundation with Web Admin Interface ([12a0e5c](https://github.com/FEAWServices/autoarr/commit/12a0e5cc157dabe2ca75b8537ce2171d7e9b0436))
* **docs:** Add clear-devcontainer-memory command documentation ([2f444f6](https://github.com/FEAWServices/autoarr/commit/2f444f641857dc88c824fe701f656f6dc6b0e354))
* **health:** Add application warmup for faster restart recovery ([00ead45](https://github.com/FEAWServices/autoarr/commit/00ead4572aae55169726272272bf7e5a1e14bbfc))
* **infra:** Add landing page infrastructure with Pulumi IaC ([207f654](https://github.com/FEAWServices/autoarr/commit/207f6542cd640ff8db4764f74fd400f73ca0edd9))
* **landing:** Add user guide and service logos ([67ff1aa](https://github.com/FEAWServices/autoarr/commit/67ff1aafd12ffd33d60b1695e07d3e4c251bfbfa))
* **release:** Prepare v0.8.0 beta release ([1f0794e](https://github.com/FEAWServices/autoarr/commit/1f0794ef696edb97039eccab77cc305c8f48f7ec))
* **ui:** Add Activity page and switch to GitHub-hosted runners ([2ab4d03](https://github.com/FEAWServices/autoarr/commit/2ab4d033f5ae94fe0fef575053fda5f704c2ca00))
* **ui:** Add AutoArr logo branding and teal color theme ([8153d5a](https://github.com/FEAWServices/autoarr/commit/8153d5a2329c35f7e96f0e95fed43b9021f92b19))
* **ui:** Add consistent page padding and component naming system ([7a9332d](https://github.com/FEAWServices/autoarr/commit/7a9332deb31d56fec8a0cfa47881756dc9bcb97c))
* **ui:** Add CSS design tokens for service cards, quick links, and fix Storybook router ([3bd8d68](https://github.com/FEAWServices/autoarr/commit/3bd8d685ed82c51650487fdbc95c5645c92e7d1c))
* **ui:** Add dynamic service status to Sidebar and Welcome page ([1b83c44](https://github.com/FEAWServices/autoarr/commit/1b83c44f3df79d90624ea2bb4fcd9a04801d7da5))
* **ui:** Add global H3 and label padding with CSS design tokens ([52af873](https://github.com/FEAWServices/autoarr/commit/52af873246180a5d6b378ace629d352e732d0f31))
* **ui:** Add pull-to-refresh and solid mobile sidebar background ([3acee3b](https://github.com/FEAWServices/autoarr/commit/3acee3b103949da39d7ff641a9b00969d7770033))


### Bug Fixes

* **api:** Fix CORS_ORIGINS parsing from .env file ([398f5b6](https://github.com/FEAWServices/autoarr/commit/398f5b65d6fc708fc057282b351768931c0ed300))
* **ci:** Fix Python formatting and remove stale xfail marker ([cfecab3](https://github.com/FEAWServices/autoarr/commit/cfecab3b05fd10583bf1c2c961be1b8421c7de82))
* **ci:** Resolve Prettier version conflict between pre-commit and CI ([f0cc7e1](https://github.com/FEAWServices/autoarr/commit/f0cc7e1d76e2f5cd57e7ce3f1eb6c9f116be73ec))
* Container improvements and onboarding fixes ([#168](https://github.com/FEAWServices/autoarr/issues/168)) ([9f83392](https://github.com/FEAWServices/autoarr/commit/9f83392c7863b2fee4a65c263773f304aa1ce152))
* Format CSS files for prettier 3.7.1 and exclude CSS from pre-commit ([576d03c](https://github.com/FEAWServices/autoarr/commit/576d03c978305fc85db7f34ac604a50752504eb4))
* **onboarding:** Add missing useState import ([fc577eb](https://github.com/FEAWServices/autoarr/commit/fc577eb37f22459da734a6cb4dfd3967e05b82ae))
* **onboarding:** Allow re-running wizard when already complete ([849e0ec](https://github.com/FEAWServices/autoarr/commit/849e0ecf8d7c4fbbcd2080576a067b2150d5efc7))
* **onboarding:** Prevent double-click required on Get Started button ([d2e2ed0](https://github.com/FEAWServices/autoarr/commit/d2e2ed0e48153775b0f5566029b5ccfd72a61279))
* **onboarding:** Use isInitializing in OnboardingRedirect component ([7a40d91](https://github.com/FEAWServices/autoarr/commit/7a40d919d9858b545795347ab012bb66c23a4e78))
* SABnzbd tool provider reads API key from database ([07c5a41](https://github.com/FEAWServices/autoarr/commit/07c5a41ccb6ec209ea1c2fa730f7fdda0a6ae47b))
* **security:** Address GitHub Advanced Security findings ([#145](https://github.com/FEAWServices/autoarr/issues/145)) ([5b16497](https://github.com/FEAWServices/autoarr/commit/5b164974b36ae2c1138080ee5852a33f8ea0fb53))
* **settings:** Reorder routes to fix /llm 404 error and improve model button UI ([1ebd2f2](https://github.com/FEAWServices/autoarr/commit/1ebd2f21d7ac17bdfd1b669eef83cf1a7bd83166))
* **settings:** Show masked API keys and preserve them on save ([46fec66](https://github.com/FEAWServices/autoarr/commit/46fec66ca2c69916ad968a240e25291f21f76f95))


### Code Refactoring

* **docker:** Unify devcontainer and test container architecture ([0a8de8c](https://github.com/FEAWServices/autoarr/commit/0a8de8c222f43c2e851a5ec731c7721d5c3e7552))
* **ui:** Clean up CSS following Tailwind best practices ([e053c67](https://github.com/FEAWServices/autoarr/commit/e053c6794960f8d78efbe78b776e4303761e7207))
* **ui:** Make Chat the default home page with compact UI refinements ([a34b515](https://github.com/FEAWServices/autoarr/commit/a34b515258b70c90d0fd713963cd4c54cc0629fb))


### Documentation

* Add comprehensive testing guide ([bccc9cc](https://github.com/FEAWServices/autoarr/commit/bccc9cc7f2cb40d548bde30a6ff4cca5422c105d))
* Reorganize markdown documentation structure ([d2deae1](https://github.com/FEAWServices/autoarr/commit/d2deae1716c0d0001d6c0be61e9a1d6db3c96d8f))
* restructure README with comprehensive vision and organized documentation ([d015db2](https://github.com/FEAWServices/autoarr/commit/d015db28a311a84400eff1f42f8f67e7312cb600))
* Update BUILD_PLAN_REMAINING.md with completed Activity tasks ([e8925c2](https://github.com/FEAWServices/autoarr/commit/e8925c288d6bb7cc3d759e436c053c10332f246f))
* Update README to format init.py section correctly ([10783d0](https://github.com/FEAWServices/autoarr/commit/10783d0b3738a994982db1a944bc237dc8dd51bc))
* Update SECURITY.md with container security verification ([202223a](https://github.com/FEAWServices/autoarr/commit/202223a7496719dccb4348bcda8bcadec3d125cc))

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
