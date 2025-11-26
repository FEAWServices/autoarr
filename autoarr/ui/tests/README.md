# AutoArr Frontend E2E Tests with Playwright

This directory contains end-to-end (E2E) tests for the AutoArr React frontend using Playwright.

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm 8+
- Frontend dependencies installed (`pnpm install`)
- Playwright browsers installed (`pnpm exec playwright install`)

### Running Tests

```bash
# Run all tests
pnpm exec playwright test

# Run tests in UI mode (interactive, visual)
pnpm exec playwright test --ui

# Run tests with visible browser (headed)
pnpm exec playwright test --headed

# Run a specific test file
pnpm exec playwright test tests/chat-smoke.spec.ts

# Run tests matching a pattern
pnpm exec playwright test --grep "Chat"

# Debug mode (pause on failures)
pnpm exec playwright test --debug

# View test report
pnpm exec playwright show-report
```

## Test Files

### `chat-smoke.spec.ts` - Quick Smoke Tests

Quick sanity checks for the chat interface.

- Loads chat page
- Displays interface elements
- Allows text input

**Run alone:** `pnpm exec playwright test tests/chat-smoke.spec.ts`
**Duration:** ~30 seconds

### `chat.spec.ts` - Comprehensive Chat Tests

Full test suite for the chat interface with 60+ test cases covering:

- Message input and sending
- Message display and auto-scroll
- Content request flows
- Disambiguation handling
- Request status tracking
- Chat history management
- Mobile responsiveness (4 viewport sizes)
- Accessibility (WCAG 2.1 AA)
- Error handling and retry logic
- WebSocket simulations

**Duration:** Several minutes (mocked API)

### `dashboard.spec.ts` - Dashboard Tests

Tests for the configuration audit dashboard:

- Dashboard loading and initial state
- Service status cards display
- Audit button functionality
- Loading and error states
- System health overview
- Mobile responsiveness
- Accessibility compliance
- Recommendation cards

**Duration:** Several minutes (mocked API)

### `config-audit.spec.ts` - Configuration Audit UI

Tests for the detailed configuration audit interface:

- Recommendation list display
- Filtering by service, priority, category
- Sorting functionality
- Apply recommendation flow
- Confirmation dialogs
- Toast notifications
- Mobile responsiveness
- Accessibility features

### `branding.spec.ts` - Branding and UI Tests

Tests for AutoArr branding and UI consistency:

- Splash screen display
- Logo and styling
- Color scheme application
- Navigation and active states
- Hover effects

**Note:** May require investigation if timeout issues occur.

### `post-deployment.spec.ts` - Post-Deployment Checks

Quick checks after deployment:

- Settings page functionality
- Application navigation

### `no-inline-styles.spec.ts` - Code Quality

Validates that components follow Tailwind CSS guidelines:

- No inline style attributes
- No style tags in components

**Note:** Currently fails due to inline styles in:

- src/pages/Home.tsx
- src/pages/Chat.tsx
- src/components/Chat/TypingIndicator.tsx
- src/components/Chat/RequestStatus.tsx

## Test Coverage

### By Category

- **Smoke Tests:** 3 tests
- **Chat Tests:** 60+ tests
- **Dashboard Tests:** 25+ tests
- **Config Audit Tests:** 15+ tests
- **Branding Tests:** 5 tests
- **Post-Deployment Tests:** 5 tests
- **Code Quality Tests:** 2 tests

### By Type

- **Functional:** 85 tests
- **Responsive/Mobile:** 16 tests
- **Accessibility:** 15 tests
- **Error Handling:** 8 tests
- **Code Quality:** 2 tests

## Configuration

### Port Configuration

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8088/api/v1
- **Test Runner:** http://localhost:3000

### Environment Variables

```
VITE_API_URL=http://localhost:8088/api/v1
```

### Playwright Config (`playwright.config.ts`)

- Browser: Chromium
- Parallel execution: Enabled (unless CI)
- Web server auto-start: Yes
- Retries: 2 in CI, 0 locally
- Report: HTML format
- Trace: On first retry

## API Mocking

Tests use `page.route()` to mock API responses. This means:

- Backend doesn't need to be running for tests
- Responses are predictable and fast
- Full control over test scenarios (success, error, timeout)

Example mock:

```typescript
await page.route(`${API_BASE_URL}/request/content`, async (route) => {
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(mockContentRequestResponse),
  });
});
```

## Mobile Testing

Tests verify responsiveness at multiple viewports:

- Mobile Small: 320x568px
- Mobile Medium: 375x667px
- Tablet: 768x1024px
- Desktop: 1920x1080px

Touch target size validation:

- Minimum 44x44px on mobile (accessibility requirement)

## Accessibility Testing

Tests validate WCAG 2.1 AA compliance:

- Proper ARIA labels
- Keyboard navigation support
- Focus management
- Screen reader announcements
- Color contrast validation
- Semantic HTML structure

## Debugging Tips

### View what test is doing

```bash
pnpm exec playwright test --debug
```

### Pause on failure

```bash
pnpm exec playwright test --debug --headed
```

### Run single test in headed mode

```bash
pnpm exec playwright test tests/chat-smoke.spec.ts --headed --workers=1
```

### Increase timeouts for debugging

Edit `playwright.config.ts`:

```typescript
timeout: 60000, // 60 seconds instead of default
```

### Check test output

```bash
# View detailed output
pnpm exec playwright test --verbose

# View in UI
pnpm exec playwright show-report
```

## Known Issues

### 1. Inline Styles Code Quality Check

**Status:** Failing
**Reason:** Some components still use inline styles instead of Tailwind CSS
**Files Affected:**

- src/pages/Home.tsx
- src/pages/Chat.tsx
- src/components/Chat/TypingIndicator.tsx
- src/components/Chat/RequestStatus.tsx

**Fix:** Migrate to Tailwind CSS classes

### 2. Branding Tests Timeout

**Status:** Investigating
**Possible Causes:**

- UI elements not rendering on first load
- Splash screen animation timing
- Element selector issues

**Workaround:** Run other tests first while investigating

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Install Playwright dependencies
  run: pnpm exec playwright install-deps

- name: Install Playwright browsers
  run: pnpm exec playwright install

- name: Run E2E tests
  run: pnpm exec playwright test
  timeout-minutes: 30
```

### Environment Setup

```bash
# Install system dependencies once
pnpm exec playwright install-deps

# Install browsers once
pnpm exec playwright install

# Run tests (no install needed after setup)
pnpm exec playwright test
```

## Best Practices

### Writing New Tests

1. Use semantic HTML queries: `getByRole`, `getByLabel`, `getByText`
2. Avoid implementation details: `data-testid` only when semantic queries aren't possible
3. Mock external APIs consistently
4. Test user behavior, not internals
5. Include accessibility checks
6. Test mobile viewports

### Test Data

- Use `data-testid` for test selectors when semantic queries unavailable
- Keep mock data realistic
- Use consistent mock formats across tests
- Document mock data structure

### Assertions

- Use explicit waiters: `expect(...).toBeVisible({ timeout: 5000 })`
- Avoid arbitrary `waitForTimeout()`
- Assert on user-visible changes, not implementation

## Performance Tips

### Faster Test Runs

```bash
# Run in parallel with fewer workers
pnpm exec playwright test --workers=2

# Run subset of tests
pnpm exec playwright test tests/chat-smoke.spec.ts

# Run specific test
pnpm exec playwright test -g "should load chat page"
```

### Reuse Server

Playwright reuses the dev server between test runs (unless CI mode).
First run starts server (~30s), subsequent runs skip this.

## References

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Support

For issues:

1. Check test output carefully
2. Run single test with `--debug`
3. View HTML report: `pnpm exec playwright show-report`
4. Check logs in `test-results/` directory
5. Review test traces in `playwright-report/`

---

**Last Updated:** 2025-10-19
**Status:** Ready for use ✅
