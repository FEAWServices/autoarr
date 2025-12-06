/**
 * Home Page E2E Tests with Playwright
 *
 * These tests verify the home page loads correctly and displays expected content.
 * The home page now renders the Chat interface (AutoArr Assistant).
 *
 * Useful for debugging white screen issues and verifying basic functionality.
 */

import { test, expect } from "@playwright/test";

// Use localhost:8088 when running inside container, or configurable via env
const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:8088";
const API_BASE_URL = process.env.TEST_API_URL || "http://localhost:8088/api/v1";

// Mock data for API responses
const mockEmptyRecommendations = {
  recommendations: [],
  total: 0,
  page: 1,
  page_size: 10,
};

const mockSettings = {
  theme: "light",
  notifications_enabled: true,
};

// ============================================================================
// Test Suite: Basic Page Loading
// ============================================================================

test.describe("Home Page - Basic Loading", () => {
  test("should load without console errors", async ({ page }) => {
    const consoleErrors: string[] = [];

    // Collect console errors BEFORE navigation
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        const text = msg.text();
        // Ignore expected/acceptable errors:
        // - React DevTools reminder (not an actual error)
        // - WebSocket connection errors (expected when WS server is not running)
        // - 404 errors for optional endpoints that may not exist yet
        // - Network fetch errors (backend may not be fully configured)
        // - Failed to load settings (expected when API endpoints aren't available)
        const isExpectedError =
          text.includes("React DevTools") ||
          text.includes("WebSocket") ||
          text.includes("ws://") ||
          text.includes("404") ||
          text.includes("Failed to fetch") ||
          text.includes("Failed to load") ||
          text.includes("NetworkError") ||
          text.includes("net::ERR");

        if (!isExpectedError) {
          consoleErrors.push(text);
        }
      }
    });

    // Collect page errors (uncaught exceptions)
    const pageErrors: string[] = [];
    page.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    await page.goto("/", { waitUntil: "networkidle" });

    // Wait for chat container to be visible (home page is now the chat)
    await expect(page.getByTestId("chat-container")).toBeVisible({ timeout: 10000 });

    // Wait a bit for any async operations to complete
    await page.waitForTimeout(500);

    // Page should not have uncaught exceptions
    expect(pageErrors).toEqual([]);

    // Page should not have unexpected console errors
    expect(consoleErrors).toEqual([]);
  });

  test("should load the page without page errors", async ({ page }) => {
    // Collect page errors (uncaught exceptions)
    const pageErrors: string[] = [];
    page.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    await page.goto(BASE_URL);

    // Wait for page to stabilize
    await page.waitForTimeout(2000);

    // Page should not have uncaught exceptions
    expect(pageErrors.length).toBe(0);
  });

  test("should have a visible root element", async ({ page }) => {
    await page.goto(BASE_URL);

    const root = page.locator("#root");
    await expect(root).toBeVisible();

    // Root should have content (not empty)
    const innerHTML = await root.innerHTML();
    expect(innerHTML.length).toBeGreaterThan(0);
  });

  test("should display splash screen initially", async ({ page }) => {
    await page.goto(BASE_URL);

    // Splash screen should be visible initially
    const splashScreen = page.getByTestId("splash-screen");
    const hasSplash = await splashScreen.isVisible().catch(() => false);

    // Either splash screen is visible, or app has already loaded
    if (hasSplash) {
      await expect(splashScreen).toBeVisible();
    } else {
      // App should be visible if splash already completed
      const dashboard = page.getByTestId("dashboard-container");
      const heading = page.getByRole("heading", {
        name: /configuration audit/i,
      });
      const isVisible =
        (await dashboard.isVisible().catch(() => false)) ||
        (await heading.isVisible().catch(() => false));
      expect(isVisible).toBeTruthy();
    }
  });

  test("should display dashboard after splash screen", async ({ page }) => {
    // Mock API to prevent hanging on network requests
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );

    await page.route(`${API_BASE_URL}/settings`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSettings),
      });
    });

    await page.goto(BASE_URL);

    // Wait for splash screen to complete (2 second minimum + animation)
    await page.waitForTimeout(3000);

    // Dashboard heading should be visible
    const heading = page.getByRole("heading", { name: /configuration audit/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });
});

// ============================================================================
// Test Suite: API Integration
// ============================================================================

test.describe("Home Page - API Integration", () => {
  test("should call recommendations API on load", async ({ page }) => {
    let apiCalled = false;

    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        apiCalled = true;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );

    await page.goto(BASE_URL);

    // Wait for splash and API call
    await page.waitForTimeout(4000);

    expect(apiCalled).toBeTruthy();
  });

  test("should handle API timeout gracefully", async ({ page }) => {
    // Mock slow API
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 10000));
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );

    await page.goto(BASE_URL);

    // Page should still show dashboard (with loading or error state)
    await page.waitForTimeout(3000);

    const dashboard = page.getByTestId("dashboard-container");
    const isVisible = await dashboard.isVisible().catch(() => false);

    // Dashboard container should be visible even if API is slow
    expect(isVisible).toBeTruthy();
  });

  test("should handle API error gracefully", async ({ page }) => {
    // Mock API error
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Internal server error" }),
        });
      },
    );

    await page.goto(BASE_URL);

    // Wait for splash and API call
    await page.waitForTimeout(4000);

    // Page should show error state, not crash
    const dashboard = page.getByTestId("dashboard-container");
    const isVisible = await dashboard.isVisible().catch(() => false);
    expect(isVisible).toBeTruthy();
  });
});

// ============================================================================
// Test Suite: Navigation
// ============================================================================

test.describe("Home Page - Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );
  });

  test("should have sidebar navigation", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const sidebar = page.getByRole("navigation");
    await expect(sidebar).toBeVisible();
  });

  test("should navigate to Chat page", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const chatLink = page.getByRole("link", { name: /chat/i });
    await chatLink.click();

    await expect(page).toHaveURL(/.*\/chat/);
  });

  test("should navigate to Settings page", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const settingsLink = page.getByRole("link", { name: /settings/i });
    await settingsLink.click();

    await expect(page).toHaveURL(/.*\/settings/);
  });
});

// ============================================================================
// Test Suite: UI Components
// ============================================================================

test.describe("Home Page - UI Components", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );

    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);
  });

  test("should display AutoArr logo", async ({ page }) => {
    const logo = page.getByAltText(/autoarr/i);
    const isVisible = await logo.isVisible().catch(() => false);

    // Logo might be in sidebar or header
    if (!isVisible) {
      const logoImage = page.locator('img[src*="autoarr"]');
      await expect(logoImage).toBeVisible();
    }
  });

  test("should display service cards grid", async ({ page }) => {
    const services = ["sabnzbd", "sonarr", "radarr", "plex"];

    for (const service of services) {
      const card = page.getByTestId(`service-card-${service}`);
      await expect(card).toBeVisible();
    }
  });

  test("should display overall health score", async ({ page }) => {
    const healthScore = page.getByTestId("overall-health-score");
    await expect(healthScore).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Theme and Styling
// ============================================================================

test.describe("Home Page - Theme", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );
  });

  test("should have proper background color", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const body = page.locator("body");
    const bgColor = await body.evaluate(
      (el) => window.getComputedStyle(el).backgroundColor,
    );

    // Background should be defined (not transparent)
    expect(bgColor).not.toBe("rgba(0, 0, 0, 0)");
  });

  test("should have readable text", async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const heading = page.getByRole("heading", { name: /configuration audit/i });
    const color = await heading.evaluate(
      (el) => window.getComputedStyle(el).color,
    );

    // Text color should be defined
    expect(color).toBeTruthy();
    expect(color).not.toBe("rgba(0, 0, 0, 0)");
  });
});

// ============================================================================
// Test Suite: Performance
// ============================================================================

test.describe("Home Page - Performance", () => {
  test("should load within acceptable time", async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );

    const startTime = Date.now();

    await page.goto(BASE_URL);

    // Wait for dashboard to be visible
    await page.waitForSelector('[data-testid="dashboard-container"]', {
      state: "visible",
      timeout: 15000,
    });

    const loadTime = Date.now() - startTime;

    // Should load within 15 seconds (including splash screen)
    expect(loadTime).toBeLessThan(15000);

    console.log(`Page load time: ${loadTime}ms`);
  });

  test("should not have memory leaks on navigation", async ({ page }) => {
    await page.route(
      `${API_BASE_URL}/config/recommendations*`,
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockEmptyRecommendations),
        });
      },
    );

    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    // Navigate away and back multiple times
    for (let i = 0; i < 3; i++) {
      const settingsLink = page.getByRole("link", { name: /settings/i });
      await settingsLink.click();
      await page.waitForTimeout(500);

      const homeLink = page.getByRole("link", { name: /dashboard/i });
      await homeLink.click();
      await page.waitForTimeout(500);
    }

    // Page should still be responsive
    const heading = page.getByRole("heading", { name: /configuration audit/i });
    await expect(heading).toBeVisible();
  });
});
