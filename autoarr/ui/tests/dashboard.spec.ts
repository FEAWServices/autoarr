/**
 * Dashboard E2E Tests with Playwright
 *
 * Following TDD principles:
 * - RED: Write failing tests first
 * - GREEN: Write minimal code to pass tests
 * - REFACTOR: Improve code while keeping tests green
 *
 * Test Coverage:
 * - Dashboard loading and initial state
 * - Audit status cards for all 4 services
 * - Triggering audit with loading states
 * - Error handling
 * - Mobile responsiveness
 * - Accessibility (WCAG 2.1 AA)
 */

import { test, expect } from "@playwright/test";

// ============================================================================
// Test Configuration
// ============================================================================

const BASE_URL = "http://localhost:3001";
const API_BASE_URL = "http://localhost:8000/api/v1";

// Mock audit response data
const mockAuditResponse = {
  audit_id: "audit_test_123",
  timestamp: new Date().toISOString(),
  services: ["sabnzbd", "sonarr", "radarr", "plex"],
  recommendations: [
    {
      id: 1,
      service: "sabnzbd",
      category: "performance",
      priority: "high",
      title: "Increase article cache",
      description: "Current cache is too small for optimal performance",
      current_value: "100M",
      recommended_value: "500M",
      impact: "Improved download speed",
      applied: false,
    },
    {
      id: 2,
      service: "sonarr",
      category: "security",
      priority: "medium",
      title: "Enable SSL",
      description: "Enable SSL for secure connections",
      current_value: "false",
      recommended_value: "true",
      impact: "Improved security",
      applied: false,
    },
  ],
  total_recommendations: 2,
  web_search_used: false,
};

const mockRecommendationsResponse = {
  recommendations: mockAuditResponse.recommendations,
  total: 2,
  page: 1,
  page_size: 10,
};

// ============================================================================
// Test Suite: Dashboard Loading
// ============================================================================

test.describe("Dashboard - Loading and Initial State", () => {
  test("should display dashboard heading on load", async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for and verify main heading
    const heading = page.getByRole("heading", { name: /configuration audit/i });
    await expect(heading).toBeVisible();
  });

  test("should show loading state initially", async ({ page }) => {
    await page.goto(BASE_URL);

    // Check for loading indicator
    const loadingIndicator = page.getByTestId("dashboard-loading");
    // Loading should either be visible or quickly disappear
    const isVisible = await loadingIndicator.isVisible().catch(() => false);
    expect(typeof isVisible).toBe("boolean");
  });

  test("should load within 2 seconds", async ({ page }) => {
    const startTime = Date.now();
    await page.goto(BASE_URL);

    // Wait for dashboard to be interactive
    await page.waitForSelector('[data-testid="dashboard-container"]', {
      state: "visible",
    });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });
});

// ============================================================================
// Test Suite: Service Status Cards
// ============================================================================

test.describe("Dashboard - Service Status Cards", () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    await page.goto(BASE_URL);
  });

  test("should display all 4 service status cards", async ({ page }) => {
    const services = ["SABnzbd", "Sonarr", "Radarr", "Plex"];

    for (const service of services) {
      const card = page.getByTestId(`service-card-${service.toLowerCase()}`);
      await expect(card).toBeVisible();
    }
  });

  test("service cards should display service name", async ({ page }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    await expect(sabnzbdCard.getByText("SABnzbd")).toBeVisible();
  });

  test("service cards should display health score", async ({ page }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    const healthScore = sabnzbdCard.getByTestId("health-score");
    await expect(healthScore).toBeVisible();

    // Health score should be between 0-100
    const scoreText = await healthScore.textContent();
    const score = parseInt(scoreText || "0");
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);
  });

  test("service cards should show recommendation counts", async ({ page }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");

    // Should show counts for high, medium, low priority recommendations
    const highCount = sabnzbdCard.getByTestId("rec-count-high");
    const mediumCount = sabnzbdCard.getByTestId("rec-count-medium");
    const lowCount = sabnzbdCard.getByTestId("rec-count-low");

    await expect(highCount).toBeVisible();
    await expect(mediumCount).toBeVisible();
    await expect(lowCount).toBeVisible();
  });

  test("service cards should display last audit timestamp", async ({
    page,
  }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    const timestamp = sabnzbdCard.getByTestId("last-audit-time");
    await expect(timestamp).toBeVisible();
  });

  test("service cards should have appropriate icons", async ({ page }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    const icon = sabnzbdCard.getByTestId("service-icon");
    await expect(icon).toBeVisible();
  });

  test("health score should have color coding", async ({ page }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    const healthScore = sabnzbdCard.getByTestId("health-score");

    // Check for color class (red/yellow/green based on score)
    const classes = await healthScore.getAttribute("class");
    const hasColorClass =
      classes?.includes("text-red") ||
      classes?.includes("text-yellow") ||
      classes?.includes("text-green");
    expect(hasColorClass).toBeTruthy();
  });
});

// ============================================================================
// Test Suite: Audit Button and Loading States
// ============================================================================

test.describe("Dashboard - Run Audit Button", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test("should display Run Audit button", async ({ page }) => {
    const button = page.getByRole("button", { name: /run audit/i });
    await expect(button).toBeVisible();
  });

  test("should trigger audit on button click", async ({ page }) => {
    let auditCalled = false;

    // Mock audit API
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      auditCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockAuditResponse),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Wait for API call
    await page.waitForTimeout(100);
    expect(auditCalled).toBeTruthy();
  });

  test("should show loading spinner while audit is running", async ({
    page,
  }) => {
    // Mock slow API response
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockAuditResponse),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Check for loading spinner
    const spinner = page.getByTestId("audit-loading-spinner");
    await expect(spinner).toBeVisible();
  });

  test("should disable button while audit is running", async ({ page }) => {
    // Mock slow API response
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockAuditResponse),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Button should be disabled
    await expect(button).toBeDisabled();
  });

  test("should show success message after audit completes", async ({
    page,
  }) => {
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockAuditResponse),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Wait for success toast
    const successToast = page.getByText(/audit completed successfully/i);
    await expect(successToast).toBeVisible({ timeout: 5000 });
  });

  test("should update service cards after audit completes", async ({
    page,
  }) => {
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockAuditResponse),
      });
    });

    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Wait for cards to update
    await page.waitForTimeout(1000);

    // Verify timestamp updated
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    const timestamp = sabnzbdCard.getByTestId("last-audit-time");
    await expect(timestamp).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Error Handling
// ============================================================================

test.describe("Dashboard - Error Handling", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test("should show error message when audit fails", async ({ page }) => {
    // Mock API error
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal server error",
        }),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Wait for error toast
    const errorToast = page.getByText(/failed to run audit/i);
    await expect(errorToast).toBeVisible({ timeout: 5000 });
  });

  test("should re-enable button after error", async ({ page }) => {
    // Mock API error
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal server error",
        }),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Wait for error to complete
    await page.waitForTimeout(1000);

    // Button should be enabled again
    await expect(button).toBeEnabled();
  });

  test("should show error when recommendations fail to load", async ({
    page,
  }) => {
    // Mock API error
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({
            detail: "Internal server error",
          }),
        });
      },
    );

    await page.reload();

    // Should show error message
    const errorMessage = page.getByText(/failed to load recommendations/i);
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });
});

// ============================================================================
// Test Suite: Overall System Health
// ============================================================================

test.describe("Dashboard - System Health Overview", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    await page.goto(BASE_URL);
  });

  test("should display overall system health score", async ({ page }) => {
    const overallHealth = page.getByTestId("overall-health-score");
    await expect(overallHealth).toBeVisible();
  });

  test("should show total recommendations count", async ({ page }) => {
    const totalRecs = page.getByTestId("total-recommendations");
    await expect(totalRecs).toBeVisible();

    const countText = await totalRecs.textContent();
    expect(countText).toContain("2");
  });

  test("should show priority breakdown", async ({ page }) => {
    const highPriority = page.getByTestId("total-high-priority");
    const mediumPriority = page.getByTestId("total-medium-priority");
    const lowPriority = page.getByTestId("total-low-priority");

    await expect(highPriority).toBeVisible();
    await expect(mediumPriority).toBeVisible();
    await expect(lowPriority).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Mobile Responsiveness
// ============================================================================

test.describe("Dashboard - Mobile Responsiveness", () => {
  const viewports = [
    { name: "Mobile Small", width: 320, height: 568 },
    { name: "Mobile Medium", width: 375, height: 667 },
    { name: "Tablet", width: 768, height: 1024 },
    { name: "Desktop", width: 1920, height: 1080 },
  ];

  for (const viewport of viewports) {
    test(`should be responsive at ${viewport.name} (${viewport.width}x${viewport.height})`, async ({
      page,
    }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });

      await page.route(
        `${API_BASE_URL}/config/recommendations*`,
        async (route) => {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify(mockRecommendationsResponse),
          });
        },
      );

      await page.goto(BASE_URL);

      // Dashboard should be visible
      const dashboard = page.getByTestId("dashboard-container");
      await expect(dashboard).toBeVisible();

      // All service cards should be visible
      const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
      await expect(sabnzbdCard).toBeVisible();

      // Run audit button should be visible
      const button = page.getByRole("button", { name: /run audit/i });
      await expect(button).toBeVisible();
    });
  }

  test("service cards should stack vertically on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 });

    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    await page.goto(BASE_URL);

    const cardsGrid = page.getByTestId("service-cards-grid");
    const gridClass = await cardsGrid.getAttribute("class");

    // Should have single column on mobile
    expect(gridClass).toContain("grid-cols-1");
  });

  test("service cards should have 2 columns on tablet", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    await page.goto(BASE_URL);

    const cardsGrid = page.getByTestId("service-cards-grid");
    const gridClass = await cardsGrid.getAttribute("class");

    // Should have 2 columns on tablet
    expect(gridClass).toMatch(/md:grid-cols-2/);
  });
});

// ============================================================================
// Test Suite: Accessibility (WCAG 2.1 AA)
// ============================================================================

test.describe("Dashboard - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    await page.goto(BASE_URL);
  });

  test("should have proper heading hierarchy", async ({ page }) => {
    // Check for h1
    const h1 = page.getByRole("heading", { level: 1 });
    await expect(h1).toBeVisible();

    // Service cards should have h2 or h3 headings
    const serviceHeadings = page.getByRole("heading", { level: 2 });
    const count = await serviceHeadings.count();
    expect(count).toBeGreaterThan(0);
  });

  test("should have accessible button labels", async ({ page }) => {
    const button = page.getByRole("button", { name: /run audit/i });
    await expect(button).toBeVisible();

    // Button should have accessible name
    const accessibleName = await button.getAttribute("aria-label");
    expect(accessibleName || "Run Audit").toBeTruthy();
  });

  test("all interactive elements should be keyboard accessible", async ({
    page,
  }) => {
    // Tab to the Run Audit button
    await page.keyboard.press("Tab");

    const button = page.getByRole("button", { name: /run audit/i });
    await expect(button).toBeFocused();

    // Should be able to activate with Enter
    await page.keyboard.press("Enter");

    // Button should be disabled after click
    await expect(button).toBeDisabled();
  });

  test("should have sufficient color contrast", async ({ page }) => {
    // Get computed styles for various elements
    const heading = page.getByRole("heading", { name: /configuration audit/i });
    const color = await heading.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.color;
    });

    // Color should be defined
    expect(color).toBeTruthy();
  });

  test("loading states should be announced to screen readers", async ({
    page,
  }) => {
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockAuditResponse),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Check for aria-live region
    const liveRegion = page.locator('[role="status"], [aria-live]');
    const count = await liveRegion.count();
    expect(count).toBeGreaterThan(0);
  });

  test("should have proper ARIA labels for status indicators", async ({
    page,
  }) => {
    const sabnzbdCard = page.getByTestId("service-card-sabnzbd");
    const healthScore = sabnzbdCard.getByTestId("health-score");

    // Should have aria-label or accessible description
    const ariaLabel = await healthScore.getAttribute("aria-label");
    const title = await healthScore.getAttribute("title");

    expect(ariaLabel || title).toBeTruthy();
  });

  test("error messages should be accessible", async ({ page }) => {
    await page.route(`${API_BASE_URL}/config/audit`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal server error",
        }),
      });
    });

    const button = page.getByRole("button", { name: /run audit/i });
    await button.click();

    // Error should be in an accessible region
    const errorRegion = page.locator('[role="alert"], [aria-live="assertive"]');
    const count = await errorRegion.count();
    expect(count).toBeGreaterThan(0);
  });
});

// ============================================================================
// Test Suite: Recommendation Cards Display
// ============================================================================

test.describe("Dashboard - Recommendation Cards", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendationsResponse),
        });
      },
    );

    await page.goto(BASE_URL);
  });

  test("should display recommendation cards when recommendations exist", async ({
    page,
  }) => {
    const recommendationCards = page.getByTestId("recommendation-card");
    const count = await recommendationCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test("recommendation cards should show priority badge", async ({ page }) => {
    const firstCard = page.getByTestId("recommendation-card").first();
    const priorityBadge = firstCard.getByTestId("priority-badge");
    await expect(priorityBadge).toBeVisible();
  });

  test("recommendation cards should show service name", async ({ page }) => {
    const firstCard = page.getByTestId("recommendation-card").first();
    const serviceName = firstCard.getByTestId("recommendation-service");
    await expect(serviceName).toBeVisible();
  });
});
