# AutoArr Build Plan - Remaining Work

**Version**: v0.8.0 (Current) → v1.0.0 (Target)
**Last Updated**: 2025-12-08

This document tracks what remains to be completed for the v1.0.0 stable release.

---

## Current Status: v0.8.0

AutoArr v0.8.0 is a **beta release** with the following working:

### Fully Functional

- Configuration auditing with AI-powered recommendations
- MCP server integrations (SABnzbd, Sonarr, Radarr, Plex)
- Chat assistant with LLM tool calling
- Settings management with service testing
- Dashboard with service health monitoring
- Docker containerization with multi-platform support

### Implemented but Needs Polish

- Monitoring service (implemented, needs startup integration)
- Recovery service (implemented, needs real-world testing)
- Event bus (implemented, needs production validation)
- Activity logging (implemented, API and UI complete)

---

## Remaining for v1.0.0

### High Priority

#### Activity Feed (Backend + Frontend) - ✅ COMPLETE

- [x] Create `/api/v1/activity` router to expose existing ActivityLogService
- [x] Create Activity.tsx page with paginated feed
- [x] Add activity filtering (by service, type, severity, search)
- [x] Add export to JSON functionality
- [x] Add cleanup with configurable retention
- [ ] Add real-time activity updates via WebSocket (deferred)

#### Test Coverage

- [ ] Increase backend test coverage from 25% to 85%
- [ ] Add integration tests for chat flow
- [ ] Add integration tests for monitoring/recovery services
- [ ] Add load tests for API endpoints

#### Documentation

- [ ] Update docs/deployment/readiness.md (currently outdated)
- [ ] Add API versioning documentation
- [ ] Create user guide for common workflows
- [ ] Add troubleshooting section for chat issues

### Medium Priority

#### Monitoring Auto-Start

- [ ] Wire MonitoringService.start_monitoring() to application lifespan
- [ ] Add configuration for monitoring intervals
- [ ] Add health check for monitoring service status

#### Recovery Integration

- [ ] Connect RecoveryService to Sonarr/Radarr search APIs
- [ ] Add intelligent quality fallback strategies
- [ ] Add user notification on recovery actions

#### WebSocket Real-Time Updates

- [ ] Wire WebSocket manager to event bus
- [ ] Add download progress indicators
- [ ] Add toast notifications for recovery events

### Low Priority (v1.1+)

#### Multi-User Support

- [ ] Add JWT authentication
- [ ] Add user management API
- [ ] Add per-user settings

#### Advanced Features

- [ ] Custom notification channels (Discord, Telegram)
- [ ] Plugin system for extensibility
- [ ] Advanced analytics dashboard
- [ ] Local LLM fallback (Ollama)

---

## Related Documentation

- [Architecture](./ARCHITECTURE.md) - System design
- [API Reference](./API_REFERENCE.md) - Endpoint documentation
- [Contributing](./CONTRIBUTING.md) - How to contribute
- [Deployment](./deployment/overview.md) - Deployment guide

---

## Links

- **Sonarr Wiki**: https://wiki.servarr.com/sonarr
- **Radarr Wiki**: https://wiki.servarr.com/radarr
- **SABnzbd Wiki**: https://sabnzbd.org/wiki/
- **Plex Support**: https://support.plex.tv/
