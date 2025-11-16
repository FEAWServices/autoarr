# Test Documentation

This directory contains test specifications and implementation guides for TDD (Test-Driven Development).

## Files

### Implementation Guides

- **`SPRINT_5_6_TEST_STRATEGY.md`**: Complete test strategy for Event Bus, Activity Log, Monitoring, and Recovery services
- **`SPRINT_7_8_IMPLEMENTATION_GUIDE.md`** _(untracked)_: TDD guide for Request Handler and WebSocket Manager

### Test Specifications

- **`SPRINT_7_8_TEST_SPECIFICATIONS.md`** _(untracked)_: Detailed test specifications for Sprint 7/8 features

## Untracked TDD Files

The following files are intentionally left untracked as they are TDD preparation documents:

```
autoarr/tests/unit/services/test_request_handler.py
autoarr/tests/unit/services/test_websocket_manager.py
docs/testing/SPRINT_7_8_IMPLEMENTATION_GUIDE.md
docs/testing/SPRINT_7_8_TEST_SPECIFICATIONS.md
```

**Why untracked?**

- Sprint 7 (Request Handler) is already implemented with tests in `autoarr/tests/unit/api/services/`
- `websocket_manager` backend service is not yet implemented (frontend WebSocket client exists)
- These files serve as reference material and alternative test scenarios
- They can be used when implementing `websocket_manager` or enhancing existing tests

## Usage

When implementing new backend services:

1. Review relevant test specifications in this directory
2. Follow TDD methodology: Write tests first, then implementation
3. Aim for 85%+ test coverage
4. Include unit, integration, and E2E tests as appropriate
