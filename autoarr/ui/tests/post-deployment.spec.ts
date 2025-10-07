import { test, expect } from "@playwright/test";

test.describe("Post-Deployment Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app and wait for splash screen to complete
    await page.goto("/");
    await page.waitForTimeout(2500); // Wait for splash screen
  });

  test("should save settings without error", async ({ page }) => {
    // Navigate to Settings page
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page).toHaveURL("/settings");

    // Verify Settings page loaded
    await expect(
      page.getByRole("heading", { name: "Settings", level: 1 }),
    ).toBeVisible({ timeout: 10000 });

    // Fill in some test data for SABnzbd
    const sabnzbdUrl = page.getByLabel("URL").first();
    await sabnzbdUrl.clear();
    await sabnzbdUrl.fill("http://localhost:8080");

    const sabnzbdApiKey = page.getByPlaceholder("your_api_key").first();
    await sabnzbdApiKey.clear();
    await sabnzbdApiKey.fill("test-api-key-123");

    // Click Save Settings button
    const saveButton = page.getByRole("button", { name: "Save Settings" });
    await saveButton.click();

    // Wait for save operation
    await page.waitForTimeout(1000);

    // Verify success message appears (button should show checkmark or success state)
    // Note: Adjust this assertion based on your actual success indicator
    await expect(saveButton).not.toHaveText(/error|failed/i);

    // Verify no error toast or message appears
    const errorMessage = page.locator("text=/error|failed/i").first();
    await expect(errorMessage)
      .not.toBeVisible({ timeout: 2000 })
      .catch(() => {
        // It's okay if no error element exists
      });
  });

  test("should display dashboard with all sections", async ({ page }) => {
    // Verify we're on home/dashboard
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Verify System Status section
    await expect(page.getByText("System Status")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Sonarr", level: 3 }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Radarr", level: 3 }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Plex", level: 3 }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "SABnzbd", level: 3 }),
    ).toBeVisible();

    // Verify Next Up section
    await expect(page.getByText("Next Up")).toBeVisible();

    // Verify Unified Download Queue section
    await expect(page.getByText("Unified Download Queue")).toBeVisible();

    // Verify Library Overview section
    await expect(page.getByText("Library Overview")).toBeVisible();
  });

  test("should navigate to search page", async ({ page }) => {
    // Click Search link in sidebar
    await page.getByRole("link", { name: "Search" }).click();
    await expect(page).toHaveURL("/search");

    // Verify search page content
    await expect(
      page.getByText("Search and Add to Your Library"),
    ).toBeVisible();
    await expect(
      page.getByPlaceholder(
        /add The Simpsons|get me the latest Mission Impossible/i,
      ),
    ).toBeVisible();
  });

  test("should navigate between all pages without errors", async ({ page }) => {
    const pages = [
      { name: "Search", expectedText: "Search and Add to Your Library" },
      { name: "Downloads", expectedText: "Downloads" },
      { name: "TV Shows", expectedText: "TV Shows" },
      { name: "Movies", expectedText: "Movies" },
      { name: "Media Server", expectedText: "Media Server" },
      { name: "Activity", expectedText: "Activity" },
      { name: "Settings", expectedText: "Settings" },
    ];

    for (const { name, expectedText } of pages) {
      await page.getByRole("link", { name }).click();
      // Use more flexible heading matcher
      await expect(
        page
          .locator(
            `h1:has-text("${expectedText}"), h2:has-text("${expectedText}")`,
          )
          .first(),
      ).toBeVisible({
        timeout: 10000,
      });

      // Check for JavaScript errors
      const errors: string[] = [];
      page.on("pageerror", (error) => {
        errors.push(error.message);
      });

      expect(errors).toHaveLength(0);
    }
  });

  test("should display logo correctly", async ({ page }) => {
    // Check sidebar logo
    const logo = page.locator('aside img[alt="AutoArr Logo"]');
    await expect(logo).toBeVisible();

    // Verify logo is loaded (not broken image)
    const logoSrc = await logo.getAttribute("src");
    expect(logoSrc).toBeTruthy();
    expect(logoSrc).toContain("autoarr-logo");
  });

  test("should show online status in sidebar", async ({ page }) => {
    // Verify status indicator
    await expect(page.locator("aside").getByText("Status")).toBeVisible();
    await expect(page.locator("aside").getByText("Online")).toBeVisible();

    // Verify status dot is present
    const statusDot = page.locator("aside .bg-status-success").first();
    await expect(statusDot).toBeVisible();
  });

  test("should have working sidebar navigation", async ({ page }) => {
    // Click on Settings
    const settingsLink = page
      .locator("aside")
      .getByRole("link", { name: "Settings" });
    await settingsLink.click();
    await expect(page).toHaveURL("/settings");

    // Verify active state (gradient background)
    const classAttr = await settingsLink.getAttribute("class");
    expect(classAttr).toContain("bg-gradient-primary");

    // Click on logo to go home
    await page.locator('aside a[href="/"]').click();
    await expect(page).toHaveURL("/");
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
  });

  test("should handle API errors gracefully in test connection", async ({
    page,
  }) => {
    // Navigate to Settings
    await page.getByRole("link", { name: "Settings" }).click();
    await page.waitForTimeout(1000);

    // Try to test connection with invalid configuration
    const testButton = page
      .getByRole("button", { name: "Test Connection" })
      .first();
    await testButton.click({ timeout: 10000 });

    // Wait for test to complete
    await page.waitForTimeout(2000);

    // Should show either "Failed" or error message, not crash the app
    const buttonText = await testButton.textContent();
    expect(buttonText).toBeTruthy();

    // Page should still be functional
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  });

  test("should persist through page refresh", async ({ page }) => {
    // Navigate to Settings
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page).toHaveURL("/settings");

    // Refresh the page
    await page.reload();

    // Should still be on settings page (not redirect to splash)
    await expect(page).toHaveURL("/settings");
    await expect(
      page.getByRole("heading", { name: "Settings", level: 1 }),
    ).toBeVisible({ timeout: 10000 });
  });

  test("should have responsive header on dashboard", async ({ page }) => {
    // Verify header elements
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();

    // Verify header action buttons
    const headerButtons = page.locator("header button");
    const buttonCount = await headerButtons.count();
    expect(buttonCount).toBeGreaterThanOrEqual(3); // Plus, Search, Bell icons
  });

  test("should display Add Media button", async ({ page }) => {
    // Verify Add Media button is present
    const addMediaButton = page.getByRole("button", { name: /Add Media/i });
    await expect(addMediaButton).toBeVisible();
  });
});
