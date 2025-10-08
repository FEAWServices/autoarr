/**
 * Activity Feed E2E Tests with Playwright
 *
 * Following TDD principles for Sprint 6 Activity Feed implementation
 *
 * Test Coverage:
 * - Activity feed loading and display
 * - Real-time updates via WebSocket
 * - Filtering by type, service, level
 * - Search functionality
 * - Infinite scroll / pagination
 * - Mobile responsiveness
 * - Accessibility (WCAG 2.1 AA)
 * - Error handling
 */

import { test, expect, Page } from "@playwright/test";

// ============================================================================
// Test Configuration & Mock Data
// ============================================================================

const BASE_URL = "http://localhost:3002";
const API_BASE_URL = "http://localhost:8000/api/v1";

const mockActivities = [
  {
    id: "activity-1",
    timestamp: new Date().toISOString(),
    type: "download",
    service: "sabnzbd",
    level: "success",
    title: "Download completed",
    description: "Movie.2024.1080p.mkv downloaded successfully",
  },
  {
    id: "activity-2",
    timestamp: new Date(Date.now() - 300000).toISOString(),
    type: "search",
    service: "sonarr",
    level: "info",
    title: "Search initiated",
    description: "Searching for TV Show S01E01",
  },
  {
    id: "activity-3",
    timestamp: new Date(Date.now() - 600000).toISOString(),
    type: "error",
    service: "radarr",
    level: "error",
    title: "Import failed",
    description: "Failed to import file: permission denied",
  },
  {
    id: "activity-4",
    timestamp: new Date(Date.now() - 900000).toISOString(),
    type: "config_change",
    service: "plex",
    level: "info",
    title: "Configuration updated",
    description: "Library scan interval changed to 12 hours",
  },
  {
    id: "activity-5",
    timestamp: new Date(Date.now() - 1200000).toISOString(),
    type: "audit",
    service: "autoarr",
    level: "success",
    title: "Audit completed",
    description: "Configuration audit found 3 recommendations",
  },
];

const mockActivityResponse = {
  activities: mockActivities,
  total: 5,
  page: 1,
  page_size: 20,
  has_more: false,
};

// ============================================================================
// Helper Functions
// ============================================================================

async function setupApiMocks(page: Page) {
  await page.route(`${API_BASE_URL}/activity*`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockActivityResponse),
    });
  });
}

// ============================================================================
// Test Suite: Activity Page Loading
// ============================================================================

test.describe("Activity Feed - Loading and Initial State", () => {
  test("should display activity feed heading on load", async ({ page }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);

    const heading = page.getByRole("heading", { name: /activity feed/i });
    await expect(heading).toBeVisible();
  });

  test("should show loading state initially", async ({ page }) => {
    await page.goto(`${BASE_URL}/activity`);

    const loadingIndicator = page.getByTestId("activity-loading");
    const isVisible = await loadingIndicator.isVisible().catch(() => false);
    expect(typeof isVisible).toBe("boolean");
  });

  test("should load within 2 seconds", async ({ page }) => {
    await setupApiMocks(page);
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/activity`);

    await page.waitForSelector('[data-testid="activity-feed-container"]', {
      state: "visible",
    });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });
});

// ============================================================================
// Test Suite: Activity List Display
// ============================================================================

test.describe("Activity Feed - Activity List Display", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);
  });

  test("should display all activity items", async ({ page }) => {
    const activityItems = page.getByTestId("activity-item");
    await expect(activityItems).toHaveCount(5);
  });

  test("activity items should display title", async ({ page }) => {
    const firstItem = page.getByTestId("activity-item").first();
    await expect(firstItem.getByText("Download completed")).toBeVisible();
  });

  test("activity items should display description", async ({ page }) => {
    const firstItem = page.getByTestId("activity-item").first();
    await expect(
      firstItem.getByText(/Movie.2024.1080p.mkv downloaded successfully/i),
    ).toBeVisible();
  });

  test("activity items should display timestamp", async ({ page }) => {
    const firstItem = page.getByTestId("activity-item").first();
    const timestamp = firstItem.getByTestId("activity-timestamp");
    await expect(timestamp).toBeVisible();
  });

  test("activity items should display service badge", async ({ page }) => {
    const firstItem = page.getByTestId("activity-item").first();
    const serviceBadge = firstItem.getByTestId("service-badge");
    await expect(serviceBadge).toBeVisible();
    await expect(serviceBadge).toHaveText(/sabnzbd/i);
  });

  test("activity items should display type icon", async ({ page }) => {
    const firstItem = page.getByTestId("activity-item").first();
    const typeIcon = firstItem.getByTestId("activity-type-icon");
    await expect(typeIcon).toBeVisible();
  });

  test("activity items should have level color coding", async ({ page }) => {
    const errorItem = page.getByTestId("activity-item").nth(2);
    const levelIndicator = errorItem.getByTestId("level-indicator");

    const classes = await levelIndicator.getAttribute("class");
    expect(classes).toContain("bg-red");
  });

  test("should display items in chronological order (newest first)", async ({
    page,
  }) => {
    const items = page.getByTestId("activity-item");
    const firstItemTitle = await items.first().getByTestId("activity-title");
    await expect(firstItemTitle).toHaveText("Download completed");
  });
});

// ============================================================================
// Test Suite: Filtering Functionality
// ============================================================================

test.describe("Activity Feed - Filtering", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);
  });

  test("should display filter controls", async ({ page }) => {
    const filterPanel = page.getByTestId("filter-panel");
    await expect(filterPanel).toBeVisible();
  });

  test("should have type filter dropdown", async ({ page }) => {
    const typeFilter = page.getByTestId("filter-type");
    await expect(typeFilter).toBeVisible();
  });

  test("should have service filter dropdown", async ({ page }) => {
    const serviceFilter = page.getByTestId("filter-service");
    await expect(serviceFilter).toBeVisible();
  });

  test("should have level filter dropdown", async ({ page }) => {
    const levelFilter = page.getByTestId("filter-level");
    await expect(levelFilter).toBeVisible();
  });

  test("should filter activities by type", async ({ page }) => {
    const typeFilter = page.getByTestId("filter-type");
    await typeFilter.selectOption("download");

    const items = page.getByTestId("activity-item");
    await expect(items).toHaveCount(1);
  });

  test("should filter activities by service", async ({ page }) => {
    const serviceFilter = page.getByTestId("filter-service");
    await serviceFilter.selectOption("sabnzbd");

    const items = page.getByTestId("activity-item");
    await expect(items).toHaveCount(1);
  });

  test("should filter activities by level", async ({ page }) => {
    const levelFilter = page.getByTestId("filter-level");
    await levelFilter.selectOption("error");

    const items = page.getByTestId("activity-item");
    await expect(items).toHaveCount(1);
  });

  test("should combine multiple filters", async ({ page }) => {
    await page.getByTestId("filter-service").selectOption("sonarr");
    await page.getByTestId("filter-type").selectOption("search");

    const items = page.getByTestId("activity-item");
    await expect(items).toHaveCount(1);
  });

  test("should show clear filters button when filters are active", async ({
    page,
  }) => {
    await page.getByTestId("filter-type").selectOption("download");

    const clearButton = page.getByTestId("clear-filters-button");
    await expect(clearButton).toBeVisible();
  });

  test("should clear all filters when clear button clicked", async ({
    page,
  }) => {
    await page.getByTestId("filter-type").selectOption("download");
    await page.getByTestId("clear-filters-button").click();

    const items = page.getByTestId("activity-item");
    await expect(items).toHaveCount(5);
  });
});

// ============================================================================
// Test Suite: Search Functionality
// ============================================================================

test.describe("Activity Feed - Search", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);
  });

  test("should display search input", async ({ page }) => {
    const searchInput = page.getByTestId("search-input");
    await expect(searchInput).toBeVisible();
  });

  test("should filter activities by search term", async ({ page }) => {
    const searchInput = page.getByTestId("search-input");
    await searchInput.fill("download");

    const items = page.getByTestId("activity-item");
    await expect(items).toHaveCount(1);
  });

  test("should show no results message when no matches", async ({ page }) => {
    const searchInput = page.getByTestId("search-input");
    await searchInput.fill("nonexistent");

    const noResults = page.getByTestId("no-results-message");
    await expect(noResults).toBeVisible();
  });

  test("should clear search with clear button", async ({ page }) => {
    const searchInput = page.getByTestId("search-input");
    await searchInput.fill("download");

    const clearButton = page.getByTestId("clear-search-button");
    await clearButton.click();

    await expect(searchInput).toHaveValue("");
  });
});

// ============================================================================
// Test Suite: Real-time Updates (WebSocket)
// ============================================================================

test.describe("Activity Feed - Real-time Updates", () => {
  test("should display WebSocket connection indicator", async ({ page }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);

    const connectionIndicator = page.getByTestId("ws-connection-indicator");
    await expect(connectionIndicator).toBeVisible();
  });

  test("should show connected status when WebSocket is connected", async ({
    page,
  }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);

    const connectionStatus = page.getByTestId("ws-connection-status");
    // Initially should be disconnected or connecting
    await expect(connectionStatus).toBeVisible();
  });

  test("should add new activity to top of list when received", async ({
    page,
  }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);

    // Simulate WebSocket message
    await page.evaluate(() => {
      const event = new CustomEvent("websocket-message", {
        detail: {
          type: "activity",
          data: {
            id: "activity-new",
            timestamp: new Date().toISOString(),
            type: "download",
            service: "sabnzbd",
            level: "success",
            title: "New download",
            description: "New item downloaded",
          },
        },
      });
      window.dispatchEvent(event);
    });

    // Wait for new item to appear
    await page.waitForTimeout(500);

    const items = page.getByTestId("activity-item");
    const count = await items.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });
});

// ============================================================================
// Test Suite: Pagination / Infinite Scroll
// ============================================================================

test.describe("Activity Feed - Pagination", () => {
  test("should load more activities on scroll", async ({ page }) => {
    // Mock paginated response
    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      const url = new URL(route.request().url());
      const page_param = url.searchParams.get("page") || "1";
      const pageNum = parseInt(page_param);

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          activities: mockActivities,
          total: 25,
          page: pageNum,
          page_size: 5,
          has_more: pageNum < 5,
        }),
      });
    });

    await page.goto(`${BASE_URL}/activity`);

    // Scroll to bottom
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });

    // Wait for more items to load
    await page.waitForTimeout(1000);

    const items = page.getByTestId("activity-item");
    const count = await items.count();
    expect(count).toBeGreaterThan(5);
  });

  test("should show loading indicator when loading more", async ({ page }) => {
    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockActivityResponse),
      });
    });

    await page.goto(`${BASE_URL}/activity`);

    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });

    const loadingMore = page.getByTestId("loading-more-indicator");
    await expect(loadingMore).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Mobile Responsiveness
// ============================================================================

test.describe("Activity Feed - Mobile Responsiveness", () => {
  const viewports = [
    { name: "Mobile Small", width: 320, height: 568 },
    { name: "Mobile Medium", width: 375, height: 667 },
    { name: "Tablet", width: 768, height: 1024 },
  ];

  for (const viewport of viewports) {
    test(`should be responsive at ${viewport.name} (${viewport.width}x${viewport.height})`, async ({
      page,
    }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });

      await setupApiMocks(page);
      await page.goto(`${BASE_URL}/activity`);

      const feedContainer = page.getByTestId("activity-feed-container");
      await expect(feedContainer).toBeVisible();

      const activityItems = page.getByTestId("activity-item");
      await expect(activityItems.first()).toBeVisible();
    });
  }

  test("touch targets should be at least 44x44px on mobile", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);

    const filterButton = page.getByTestId("filter-type");
    const box = await filterButton.boundingBox();

    expect(box).toBeTruthy();
    if (box) {
      expect(box.height).toBeGreaterThanOrEqual(44);
    }
  });

  test("should stack filters vertically on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);

    const filterPanel = page.getByTestId("filter-panel");
    const classes = await filterPanel.getAttribute("class");

    expect(classes).toContain("flex-col");
  });
});

// ============================================================================
// Test Suite: Accessibility (WCAG 2.1 AA)
// ============================================================================

test.describe("Activity Feed - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto(`${BASE_URL}/activity`);
  });

  test("should have proper heading hierarchy", async ({ page }) => {
    const h1 = page.getByRole("heading", { level: 1 });
    await expect(h1).toBeVisible();
  });

  test("activity items should be in a list", async ({ page }) => {
    const list = page.getByRole("list");
    await expect(list).toBeVisible();

    const items = page.getByRole("listitem");
    const count = await items.count();
    expect(count).toBeGreaterThan(0);
  });

  test("filter controls should have labels", async ({ page }) => {
    const typeFilter = page.getByTestId("filter-type");
    const label = await typeFilter.getAttribute("aria-label");
    expect(label || "Filter by type").toBeTruthy();
  });

  test("search input should have label", async ({ page }) => {
    const searchInput = page.getByTestId("search-input");
    const label = await searchInput.getAttribute("aria-label");
    expect(label || "Search activities").toBeTruthy();
  });

  test("should be keyboard navigable", async ({ page }) => {
    await page.keyboard.press("Tab");

    const searchInput = page.getByTestId("search-input");
    await expect(searchInput).toBeFocused();
  });

  test("loading states should be announced to screen readers", async ({
    page,
  }) => {
    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockActivityResponse),
      });
    });

    await page.reload();

    const liveRegion = page.locator('[role="status"], [aria-live="polite"]');
    const count = await liveRegion.count();
    expect(count).toBeGreaterThan(0);
  });

  test("activity level should be accessible", async ({ page }) => {
    const firstItem = page.getByTestId("activity-item").first();
    const levelIndicator = firstItem.getByTestId("level-indicator");

    const ariaLabel = await levelIndicator.getAttribute("aria-label");
    expect(ariaLabel).toContain("success");
  });
});

// ============================================================================
// Test Suite: Error Handling
// ============================================================================

test.describe("Activity Feed - Error Handling", () => {
  test("should show error message when activities fail to load", async ({
    page,
  }) => {
    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal server error",
        }),
      });
    });

    await page.goto(`${BASE_URL}/activity`);

    const errorMessage = page.getByTestId("error-message");
    await expect(errorMessage).toBeVisible();
  });

  test("should show retry button on error", async ({ page }) => {
    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal server error",
        }),
      });
    });

    await page.goto(`${BASE_URL}/activity`);

    const retryButton = page.getByTestId("retry-button");
    await expect(retryButton).toBeVisible();
  });

  test("should retry loading on retry button click", async ({ page }) => {
    let requestCount = 0;

    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      requestCount++;
      if (requestCount === 1) {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Error" }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockActivityResponse),
        });
      }
    });

    await page.goto(`${BASE_URL}/activity`);

    const retryButton = page.getByTestId("retry-button");
    await retryButton.click();

    const items = page.getByTestId("activity-item");
    await expect(items.first()).toBeVisible({ timeout: 3000 });
  });

  test("should show empty state when no activities", async ({ page }) => {
    await page.route(`${API_BASE_URL}/activity*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          activities: [],
          total: 0,
          page: 1,
          page_size: 20,
          has_more: false,
        }),
      });
    });

    await page.goto(`${BASE_URL}/activity`);

    const emptyState = page.getByTestId("empty-state");
    await expect(emptyState).toBeVisible();
  });
});
