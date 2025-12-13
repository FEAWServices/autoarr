# Playwright E2E Testing Skill

## Overview

This skill covers Playwright end-to-end testing for AutoArr's React frontend,
including best practices for running tests in Docker containers.

## Critical: Running E2E Tests

**IMPORTANT**: Playwright tests MUST be run inside the Docker container, NOT from
the devcontainer. Running from devcontainer causes network/memory issues.

```bash
# Start the local test container
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d

# Run all E2E tests inside container
./scripts/run-e2e-tests.sh

# Run specific test file
./scripts/run-e2e-tests.sh tests/home.spec.ts

# Run tests matching pattern
./scripts/run-e2e-tests.sh "dashboard"

# Manual execution
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test --config=playwright-container.config.ts"
```

## Test Structure

```
autoarr/ui/tests/
├── home.spec.ts           # Dashboard/home page tests
├── chat.spec.ts           # Chat interface tests
├── activity.spec.ts       # Activity feed tests
├── settings.spec.ts       # Settings page tests
├── config-audit.spec.ts   # Configuration audit tests
├── onboarding.spec.ts     # Onboarding flow tests
└── fixtures/
    ├── test-data.ts       # Shared test data
    └── page-objects/      # Page object models
        ├── HomePage.ts
        ├── ChatPage.ts
        └── SettingsPage.ts
```

## Configuration Files

### Container Config (for running inside Docker)

```typescript
// playwright-container.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:8088", // Same container as app
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  // No webServer - app already running in container
});
```

### CI Config (for GitHub Actions)

```typescript
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["html"], ["github"]],
  use: {
    baseURL: "http://localhost:8088",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "Mobile Chrome",
      use: { ...devices["Pixel 5"] },
    },
  ],
  webServer: {
    command: "pnpm run dev",
    url: "http://localhost:8088",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

## Writing E2E Tests

### Basic Test Structure

```typescript
// autoarr/ui/tests/home.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Home Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display dashboard with health scores", async ({ page }) => {
    // Wait for dashboard to load
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Check health score cards are displayed
    await expect(page.getByTestId("sabnzbd-health")).toBeVisible();
    await expect(page.getByTestId("sonarr-health")).toBeVisible();
    await expect(page.getByTestId("radarr-health")).toBeVisible();
  });

  test("should show recent activity", async ({ page }) => {
    // Activity feed should be present
    const activityFeed = page.getByTestId("activity-feed");
    await expect(activityFeed).toBeVisible();

    // Should have at least one activity item
    const activityItems = activityFeed.getByRole("listitem");
    await expect(activityItems.first()).toBeVisible();
  });

  test("should navigate to audit page", async ({ page }) => {
    await page.getByRole("link", { name: "Config Audit" }).click();

    await expect(page).toHaveURL(/\/audit/);
    await expect(
      page.getByRole("heading", { name: "Configuration Audit" }),
    ).toBeVisible();
  });
});
```

### Page Object Model

```typescript
// autoarr/ui/tests/fixtures/page-objects/ChatPage.ts
import { Page, Locator, expect } from "@playwright/test";

export class ChatPage {
  readonly page: Page;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly messageList: Locator;

  constructor(page: Page) {
    this.page = page;
    this.messageInput = page.getByPlaceholder("Ask for a movie or TV show...");
    this.sendButton = page.getByRole("button", { name: "Send" });
    this.messageList = page.getByTestId("message-list");
  }

  async goto() {
    await this.page.goto("/chat");
  }

  async sendMessage(text: string) {
    await this.messageInput.fill(text);
    await this.sendButton.click();
  }

  async waitForResponse() {
    // Wait for assistant response (not user message)
    await expect(
      this.messageList.locator('[data-role="assistant"]').last(),
    ).toBeVisible({ timeout: 30000 });
  }

  async getLastResponse(): Promise<string> {
    return (
      (await this.messageList
        .locator('[data-role="assistant"]')
        .last()
        .textContent()) ?? ""
    );
  }
}

// Usage in test
// autoarr/ui/tests/chat.spec.ts
import { test, expect } from "@playwright/test";
import { ChatPage } from "./fixtures/page-objects/ChatPage";

test.describe("Chat", () => {
  test("should handle content request", async ({ page }) => {
    const chatPage = new ChatPage(page);
    await chatPage.goto();

    await chatPage.sendMessage("Add the movie Dune 2021");
    await chatPage.waitForResponse();

    const response = await chatPage.getLastResponse();
    expect(response).toContain("Dune");
  });
});
```

### Testing Forms

```typescript
// autoarr/ui/tests/settings.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Settings", () => {
  test("should test SABnzbd connection", async ({ page }) => {
    await page.goto("/settings");

    // Fill in SABnzbd settings
    await page
      .getByLabel("SABnzbd URL")
      .fill("http://192.168.0.80:8090/sabnzbd/");
    await page.getByLabel("API Key").fill("test-api-key");

    // Click test connection
    await page.getByRole("button", { name: "Test Connection" }).click();

    // Wait for result
    await expect(
      page.getByText(/Connection successful|Connection failed/),
    ).toBeVisible({
      timeout: 15000,
    });
  });

  test("should save settings", async ({ page }) => {
    await page.goto("/settings");

    // Update a setting
    await page.getByLabel("Retry Attempts").fill("5");

    // Save
    await page.getByRole("button", { name: "Save" }).click();

    // Verify save succeeded
    await expect(page.getByText("Settings saved")).toBeVisible();

    // Reload and verify persisted
    await page.reload();
    await expect(page.getByLabel("Retry Attempts")).toHaveValue("5");
  });
});
```

### Testing Real-Time Updates (WebSocket)

```typescript
// autoarr/ui/tests/activity.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Activity Feed", () => {
  test("should receive real-time updates", async ({ page }) => {
    await page.goto("/activity");

    // Get initial activity count
    const initialItems = await page.getByTestId("activity-item").count();

    // Trigger an action that generates activity (via API)
    await page.request.post("/api/v1/audit/start");

    // Wait for new activity item to appear
    await expect(page.getByTestId("activity-item")).toHaveCount(
      initialItems + 1,
      {
        timeout: 10000,
      },
    );

    // Verify latest activity
    const latestActivity = page.getByTestId("activity-item").first();
    await expect(latestActivity).toContainText("Audit");
  });
});
```

### Mobile Testing

```typescript
// autoarr/ui/tests/mobile.spec.ts
import { test, expect, devices } from "@playwright/test";

test.use({ ...devices["iPhone 13"] });

test.describe("Mobile", () => {
  test("should show mobile navigation", async ({ page }) => {
    await page.goto("/");

    // Mobile menu should be collapsed
    await expect(page.getByRole("navigation")).not.toBeVisible();

    // Open mobile menu
    await page.getByRole("button", { name: "Menu" }).click();

    // Navigation should now be visible
    await expect(page.getByRole("navigation")).toBeVisible();
    await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
  });

  test("should have accessible touch targets", async ({ page }) => {
    await page.goto("/");

    // All buttons should be at least 44x44 pixels (WCAG)
    const buttons = page.getByRole("button");
    const count = await buttons.count();

    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const box = await button.boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThanOrEqual(44);
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }
  });
});
```

### Visual Regression Testing

```typescript
// autoarr/ui/tests/visual.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Visual Regression", () => {
  test("dashboard should match snapshot", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Take screenshot and compare
    await expect(page).toHaveScreenshot("dashboard.png", {
      maxDiffPixels: 100,
    });
  });

  test("config audit results should match snapshot", async ({ page }) => {
    await page.goto("/audit");
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveScreenshot("audit-results.png", {
      maxDiffPixels: 100,
    });
  });
});
```

## API Mocking

```typescript
// autoarr/ui/tests/mocked.spec.ts
import { test, expect } from "@playwright/test";

test.describe("With Mocked API", () => {
  test("should display mocked audit results", async ({ page }) => {
    // Mock the audit API
    await page.route("/api/v1/audit/results", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          health_score: 75,
          recommendations: [
            {
              id: "1",
              service: "sabnzbd",
              setting: "article_cache_limit",
              current_value: "100",
              recommended_value: "500",
              priority: "high",
              explanation: "Increase cache for better performance",
            },
          ],
        }),
      });
    });

    await page.goto("/audit");

    // Verify mocked data is displayed
    await expect(page.getByText("75%")).toBeVisible();
    await expect(page.getByText("article_cache_limit")).toBeVisible();
  });
});
```

## Debugging Tests

```bash
# Run with headed browser
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test --headed"

# Run with Playwright Inspector
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && PWDEBUG=1 pnpm exec playwright test"

# Generate trace for failed tests
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test --trace on"

# View test report
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright show-report"
```

## Checklist

Before merging E2E test changes:

- [ ] Tests run inside Docker container
- [ ] Using `playwright-container.config.ts` for local tests
- [ ] Page objects used for reusable interactions
- [ ] Proper waiting strategies (no arbitrary sleeps)
- [ ] Accessibility tested (WCAG compliance)
- [ ] Mobile viewport tested
- [ ] Tests are independent (no test order dependencies)
- [ ] API mocks used where appropriate
- [ ] Meaningful test descriptions
- [ ] Screenshots captured for failures
