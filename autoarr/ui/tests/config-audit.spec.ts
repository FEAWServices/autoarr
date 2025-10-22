/**
 * Configuration Audit UI - Playwright E2E Tests
 *
 * Following TDD principles, these tests define the expected behavior
 * of the Configuration Audit UI before implementation.
 *
 * Test Coverage:
 * - Recommendation list display
 * - Filtering by service, priority, category
 * - Sorting functionality
 * - Apply recommendation flow
 * - Confirmation dialog
 * - Toast notifications
 * - Mobile responsiveness
 * - Accessibility (WCAG 2.1 AA)
 */

import { test, expect, type Page } from "@playwright/test";
import { injectAxe, checkA11y } from "axe-playwright";

// Mock API responses
const mockRecommendations = {
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
      impact: "Improved download speed by 30-40%",
      source: "Official Documentation",
      applied: false,
      applied_at: null,
    },
    {
      id: 2,
      service: "sonarr",
      category: "security",
      priority: "high",
      title: "Enable SSL/TLS",
      description: "API communication should use HTTPS",
      current_value: "false",
      recommended_value: "true",
      impact: "Protects credentials and download information",
      source: "Security Best Practices",
      applied: false,
      applied_at: null,
    },
    {
      id: 3,
      service: "radarr",
      category: "best_practices",
      priority: "medium",
      title: "Configure recycling bin",
      description: "Set up recycling bin to prevent accidental deletions",
      current_value: "null",
      recommended_value: "/data/recycling",
      impact: "Allows recovery of accidentally deleted files",
      source: "Community Recommendation",
      applied: false,
      applied_at: null,
    },
    {
      id: 4,
      service: "plex",
      category: "performance",
      priority: "low",
      title: "Enable hardware acceleration",
      description: "Use GPU for video transcoding",
      current_value: "false",
      recommended_value: "true",
      impact: "Reduces CPU usage during transcoding",
      source: "Official Documentation",
      applied: false,
      applied_at: null,
    },
  ],
  total: 4,
  page: 1,
  page_size: 10,
};

const mockApplySuccess = {
  results: [
    {
      recommendation_id: 1,
      success: true,
      message: "Setting applied successfully",
      service: "sabnzbd",
      applied_at: "2025-10-08T12:00:00Z",
      dry_run: false,
    },
  ],
  total_requested: 1,
  total_successful: 1,
  total_failed: 0,
  dry_run: false,
};

const mockApplyError = {
  results: [
    {
      recommendation_id: 2,
      success: false,
      message: "Failed to connect to service",
      service: "sonarr",
      applied_at: null,
      dry_run: false,
    },
  ],
  total_requested: 1,
  total_successful: 0,
  total_failed: 1,
  dry_run: false,
};

/**
 * Setup function to mock API routes
 */
async function setupMockAPI(page: Page) {
  // Mock GET /api/v1/config/recommendations
  await page.route("**/api/v1/config/recommendations*", async (route) => {
    const url = new URL(route.request().url());
    const service = url.searchParams.get("service");
    const priority = url.searchParams.get("priority");
    const category = url.searchParams.get("category");

    let filteredRecommendations = [...mockRecommendations.recommendations];

    if (service) {
      filteredRecommendations = filteredRecommendations.filter(
        (r) => r.service === service,
      );
    }
    if (priority) {
      filteredRecommendations = filteredRecommendations.filter(
        (r) => r.priority === priority,
      );
    }
    if (category) {
      filteredRecommendations = filteredRecommendations.filter(
        (r) => r.category === category,
      );
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...mockRecommendations,
        recommendations: filteredRecommendations,
        total: filteredRecommendations.length,
      }),
    });
  });

  // Mock POST /api/v1/config/apply (success case by default)
  await page.route("**/api/v1/config/apply", async (route) => {
    const requestBody = route.request().postDataJSON();
    const recommendationId = requestBody.recommendation_ids[0];

    // Simulate error for recommendation ID 2
    if (recommendationId === 2) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockApplyError),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockApplySuccess),
      });
    }
  });
}

test.describe("Configuration Audit UI", () => {
  test.beforeEach(async ({ page }) => {
    await setupMockAPI(page);
  });

  test.describe("Recommendation List Display", () => {
    test("should display all recommendations with correct information", async ({
      page,
    }) => {
      await page.goto("/config-audit");

      // Wait for recommendations to load
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Check that all 4 recommendations are displayed
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBe(4);

      // Verify first recommendation card content
      const firstCard = page
        .locator('[data-testid="recommendation-card"]')
        .first();
      await expect(firstCard).toContainText("sabnzbd");
      await expect(firstCard).toContainText("Increase article cache");
      await expect(firstCard).toContainText("100M");
      await expect(firstCard).toContainText("500M");
      await expect(firstCard).toContainText(
        "Improved download speed by 30-40%",
      );
    });

    test("should display priority badges with correct colors", async ({
      page,
    }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // High priority should have red/danger styling
      const highPriority = page
        .locator('[data-testid="priority-badge"]')
        .filter({ hasText: "HIGH" })
        .first();
      await expect(highPriority).toBeVisible();
      await expect(highPriority).toHaveClass(/high|red|danger/i);

      // Medium priority should have yellow/warning styling
      const mediumPriority = page
        .locator('[data-testid="priority-badge"]')
        .filter({ hasText: "MEDIUM" });
      await expect(mediumPriority).toBeVisible();
      await expect(mediumPriority).toHaveClass(/medium|yellow|warning/i);

      // Low priority should have blue/info styling
      const lowPriority = page
        .locator('[data-testid="priority-badge"]')
        .filter({ hasText: "LOW" });
      await expect(lowPriority).toBeVisible();
      await expect(lowPriority).toHaveClass(/low|blue|info/i);
    });

    test("should display service icons", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Check for service icons/names
      await expect(
        page.locator('[data-testid="service-icon"]').first(),
      ).toBeVisible();
    });

    test("should show loading state while fetching recommendations", async ({
      page,
    }) => {
      // Delay the API response
      await page.route("**/api/v1/config/recommendations*", async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockRecommendations),
        });
      });

      await page.goto("/config-audit");

      // Should show loading indicator
      await expect(
        page.locator('[data-testid="loading-spinner"]'),
      ).toBeVisible();

      // Loading should disappear after data loads
      await page.waitForSelector('[data-testid="recommendation-card"]');
      await expect(
        page.locator('[data-testid="loading-spinner"]'),
      ).not.toBeVisible();
    });

    test("should handle empty recommendations gracefully", async ({ page }) => {
      await page.route("**/api/v1/config/recommendations*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            recommendations: [],
            total: 0,
            page: 1,
            page_size: 10,
          }),
        });
      });

      await page.goto("/config-audit");

      // Should show empty state message
      await expect(page.getByText(/no recommendations found/i)).toBeVisible();
    });

    test("should handle API error gracefully", async ({ page }) => {
      await page.route("**/api/v1/config/recommendations*", async (route) => {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Internal server error" }),
        });
      });

      await page.goto("/config-audit");

      // Should show error message
      await expect(
        page.getByText(/failed to load recommendations/i),
      ).toBeVisible();
    });
  });

  test.describe("Filtering", () => {
    test("should filter by service", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Open service filter
      await page.click('[data-testid="filter-service"]');

      // Select SABnzbd
      await page.click('[data-value="sabnzbd"]');

      // Should only show SABnzbd recommendations
      await page.waitForTimeout(500); // Wait for filter to apply
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBe(1);

      const card = page.locator('[data-testid="recommendation-card"]').first();
      await expect(card).toContainText("sabnzbd");
    });

    test("should filter by priority", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Open priority filter
      await page.click('[data-testid="filter-priority"]');

      // Select HIGH
      await page.click('[data-value="high"]');

      // Should only show high priority recommendations
      await page.waitForTimeout(500);
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBe(2); // SABnzbd and Sonarr

      // All visible cards should have HIGH priority
      for (const card of cards) {
        await expect(
          card.locator('[data-testid="priority-badge"]'),
        ).toContainText("HIGH");
      }
    });

    test("should filter by category", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Open category filter
      await page.click('[data-testid="filter-category"]');

      // Select performance
      await page.click('[data-value="performance"]');

      // Should only show performance recommendations
      await page.waitForTimeout(500);
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBe(2); // SABnzbd and Plex
    });

    test("should combine multiple filters", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Filter by service: SABnzbd
      await page.click('[data-testid="filter-service"]');
      await page.click('[data-value="sabnzbd"]');
      await page.waitForTimeout(300);

      // Filter by priority: HIGH
      await page.click('[data-testid="filter-priority"]');
      await page.click('[data-value="high"]');
      await page.waitForTimeout(300);

      // Should show only SABnzbd high priority recommendations
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBe(1);
    });

    test("should allow clearing filters", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Apply a filter
      await page.click('[data-testid="filter-service"]');
      await page.click('[data-value="sabnzbd"]');
      await page.waitForTimeout(300);

      // Clear filters
      await page.click('[data-testid="clear-filters"]');
      await page.waitForTimeout(300);

      // Should show all recommendations again
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBe(4);
    });
  });

  test.describe("Sorting", () => {
    test("should sort by priority by default", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // First cards should be HIGH priority
      const firstBadge = page.locator('[data-testid="priority-badge"]').first();
      await expect(firstBadge).toContainText("HIGH");
    });

    test("should sort by service name", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Select service sort
      await page.click('[data-testid="sort-select"]');
      await page.click('[data-value="service"]');

      await page.waitForTimeout(300);

      // First card should be Plex (alphabetically)
      const cards = page.locator('[data-testid="recommendation-card"]');
      await expect(cards.first()).toContainText("plex");
    });

    test("should sort by category", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Select category sort
      await page.click('[data-testid="sort-select"]');
      await page.click('[data-value="category"]');

      await page.waitForTimeout(300);

      // First card should be best_practices (alphabetically)
      const cards = page.locator('[data-testid="recommendation-card"]');
      await expect(cards.first()).toContainText("radarr"); // radarr has best_practices category
    });
  });

  test.describe("Apply Recommendation Flow", () => {
    test("should show confirmation dialog when clicking Apply", async ({
      page,
    }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Click Apply button on first recommendation
      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      // Confirmation dialog should appear
      await expect(
        page.getByRole("dialog", { name: /confirm/i }),
      ).toBeVisible();
    });

    test("should display change details in confirmation dialog", async ({
      page,
    }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Click Apply on first recommendation
      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      // Dialog should show what will change
      const dialog = page.getByRole("dialog");
      await expect(dialog).toContainText("sabnzbd");
      await expect(dialog).toContainText("Increase article cache");
      await expect(dialog).toContainText("100M"); // Current value
      await expect(dialog).toContainText("500M"); // New value
    });

    test("should show impact warning for HIGH priority changes", async ({
      page,
    }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Click Apply on high priority recommendation
      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      // Should show warning for high priority
      const dialog = page.getByRole("dialog");
      await expect(
        dialog.getByText(/high priority|warning|important/i),
      ).toBeVisible();
    });

    test("should offer dry-run option", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      // Should have dry-run checkbox
      await expect(
        page.getByRole("checkbox", { name: /dry run|preview|test/i }),
      ).toBeVisible();
    });

    test("should close dialog when clicking Cancel", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();

      // Click Cancel
      await page.getByRole("button", { name: /cancel/i }).click();

      // Dialog should close
      await expect(dialog).not.toBeVisible();
    });

    test("should show loading state while applying", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      // Click Confirm
      await page.getByRole("button", { name: /apply|confirm/i }).click();

      // Should show loading indicator
      await expect(page.locator('[data-testid="apply-loading"]')).toBeVisible();
    });

    test("should show success toast on successful apply", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      await page.getByRole("button", { name: /apply|confirm/i }).click();

      // Wait for success toast
      await expect(page.getByText(/setting applied successfully/i)).toBeVisible(
        { timeout: 5000 },
      );
    });

    test("should show error toast on failed apply", async ({ page }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Click Apply on second recommendation (ID 2, configured to fail)
      await page
        .locator('[data-testid="recommendation-card"]')
        .nth(1)
        .locator('[data-testid="apply-button"]')
        .click();

      await page.getByRole("button", { name: /apply|confirm/i }).click();

      // Wait for error toast
      await expect(page.getByText(/failed to connect to service/i)).toBeVisible(
        { timeout: 5000 },
      );
    });

    test("should disable Apply button after successful application", async ({
      page,
    }) => {
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      const firstCard = page
        .locator('[data-testid="recommendation-card"]')
        .first();
      const applyButton = firstCard.locator('[data-testid="apply-button"]');

      await applyButton.click();
      await page.getByRole("button", { name: /apply|confirm/i }).click();

      // Wait for success
      await expect(page.getByText(/setting applied successfully/i)).toBeVisible(
        { timeout: 5000 },
      );

      // Apply button should be disabled or show "Applied"
      await expect(applyButton).toBeDisabled();
    });
  });

  test.describe("Mobile Responsive Design", () => {
    test("should display properly on mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Cards should stack vertically
      const cards = await page
        .locator('[data-testid="recommendation-card"]')
        .all();
      expect(cards.length).toBeGreaterThan(0);

      // Check that cards are visible
      for (const card of cards) {
        await expect(card).toBeVisible();
      }
    });

    test("should make filter controls accessible on mobile", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Filters should be visible and clickable
      await expect(
        page.locator('[data-testid="filter-service"]'),
      ).toBeVisible();
      await expect(
        page.locator('[data-testid="filter-priority"]'),
      ).toBeVisible();
      await expect(
        page.locator('[data-testid="filter-category"]'),
      ).toBeVisible();
    });

    test("should display dialog full-screen on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();

      // Dialog should be readable on mobile
      const dialogBox = await dialog.boundingBox();
      expect(dialogBox?.width).toBeLessThanOrEqual(375);
    });

    test("should have touch-friendly button sizes on mobile", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("/config-audit");

      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Apply buttons should be at least 44x44px (iOS guidelines)
      const applyButton = page.locator('[data-testid="apply-button"]').first();
      const buttonBox = await applyButton.boundingBox();

      expect(buttonBox?.height).toBeGreaterThanOrEqual(44);
      expect(buttonBox?.width).toBeGreaterThanOrEqual(44);
    });
  });

  test.describe("Accessibility (WCAG 2.1 AA)", () => {
    test("should have no accessibility violations on main page", async ({
      page,
    }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      await injectAxe(page);
      await checkA11y(page, undefined, {
        detailedReport: true,
        detailedReportOptions: { html: true },
      });
    });

    test("should have proper heading hierarchy", async ({ page }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Should have h1 for page title
      const h1 = page.locator("h1");
      await expect(h1).toBeVisible();
      await expect(h1).toContainText(/configuration|audit|recommendations/i);
    });

    test("should have accessible filter controls", async ({ page }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Filter controls should have labels
      const serviceFilter = page.locator('[data-testid="filter-service"]');
      const label = await serviceFilter.getAttribute("aria-label");
      expect(label).toBeTruthy();
    });

    test("should announce recommendations to screen readers", async ({
      page,
    }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Recommendations container should have aria-live region
      const container = page.locator(
        '[data-testid="recommendations-container"]',
      );
      const ariaLive = await container.getAttribute("aria-live");
      expect(ariaLive).toBe("polite");
    });

    test("should support keyboard navigation", async ({ page }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Tab through interactive elements
      await page.keyboard.press("Tab");
      await page.keyboard.press("Tab");

      // Filter should be focused
      const focused = await page.evaluate(
        () => document.activeElement?.getAttribute("data-testid"),
      );
      expect(focused).toBeTruthy();
    });

    test("should have accessible Apply buttons", async ({ page }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      const applyButton = page.locator('[data-testid="apply-button"]').first();

      // Button should have accessible name
      const accessibleName = await applyButton.getAttribute("aria-label");
      expect(accessibleName).toBeTruthy();
    });

    test("should have sufficient color contrast for priority badges", async ({
      page,
    }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      await injectAxe(page);

      // Check color contrast specifically for badges
      await checkA11y(
        page,
        '[data-testid="priority-badge"]',
        {
          detailedReport: true,
        },
        true,
        "v2",
      );
    });

    test("should announce toast messages to screen readers", async ({
      page,
    }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      await page.getByRole("button", { name: /apply|confirm/i }).click();

      // Toast should have role="status" or role="alert"
      const toast = page.getByText(/setting applied successfully/i);
      await expect(toast).toBeVisible({ timeout: 5000 });

      // Check for aria-live region
      const toastContainer = toast.locator("..");
      const ariaLive = await toastContainer.getAttribute("aria-live");
      expect(ariaLive).toBeTruthy();
    });

    test("should have accessible confirmation dialog", async ({ page }) => {
      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      await page
        .locator('[data-testid="recommendation-card"]')
        .first()
        .locator('[data-testid="apply-button"]')
        .click();

      const dialog = page.getByRole("dialog");

      // Dialog should have aria-labelledby or aria-label
      const ariaLabel = await dialog.getAttribute("aria-label");
      const ariaLabelledBy = await dialog.getAttribute("aria-labelledby");
      expect(ariaLabel || ariaLabelledBy).toBeTruthy();

      // Dialog should trap focus
      await page.keyboard.press("Tab");
      const focusedElement = await page.evaluate(
        () => document.activeElement?.tagName,
      );
      expect(focusedElement).toBe("BUTTON"); // Should focus first button in dialog
    });
  });

  test.describe("Pagination", () => {
    test("should show pagination controls when there are many recommendations", async ({
      page,
    }) => {
      // Mock many recommendations
      await page.route("**/api/v1/config/recommendations*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            recommendations: mockRecommendations.recommendations.slice(0, 3),
            total: 25,
            page: 1,
            page_size: 10,
          }),
        });
      });

      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Pagination controls should be visible
      await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
    });

    test("should navigate to next page", async ({ page }) => {
      await page.route("**/api/v1/config/recommendations*", async (route) => {
        const url = new URL(route.request().url());
        const pageNum = url.searchParams.get("page") || "1";

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            recommendations: mockRecommendations.recommendations.slice(0, 2),
            total: 25,
            page: parseInt(pageNum),
            page_size: 10,
          }),
        });
      });

      await page.goto("/config-audit");
      await page.waitForSelector('[data-testid="recommendation-card"]');

      // Click next page
      await page.click('[data-testid="next-page"]');

      // Should request page 2
      await page.waitForTimeout(500);
      // Page indicator should show page 2
      await expect(page.getByText(/page 2/i)).toBeVisible();
    });
  });
});
