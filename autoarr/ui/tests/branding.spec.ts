import { test, expect } from "@playwright/test";

// Helper function to skip splash screen for faster tests
async function goToPageAfterSplash(page) {
  await page.goto("/");
  await page.waitForTimeout(2500); // Wait for splash to complete
}

test.describe("AutoArr Branding", () => {
  test("should display splash screen with new branding", async ({ page }) => {
    // Navigate to the app
    await page.goto("/");

    // Check splash screen is visible
    const splashScreen = page
      .locator("div")
      .filter({ hasText: "AutoArr" })
      .first();
    await expect(splashScreen).toBeVisible();

    // Check for the tagline
    await expect(page.getByText("Intelligent Media, Automated.")).toBeVisible();

    // Check for "Loading..." text
    await expect(page.getByText("Loading...")).toBeVisible();

    // Verify background color (dark blue/purple gradient)
    const background = page.locator("div.fixed.inset-0").first();
    await expect(background).toHaveClass(/bg-gradient-hero/);

    // Check logo SVG is present
    const logo = page.locator("svg").first();
    await expect(logo).toBeVisible();
  });

  test("should display home page with new logo and branding after splash", async ({
    page,
  }) => {
    // Use helper to skip splash (already tested above)
    await goToPageAfterSplash(page);

    // Check that we're on the home page
    await expect(page).toHaveURL("/");

    // Verify sidebar is visible with new branding
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeVisible();
    await expect(sidebar).toHaveClass(/bg-background-secondary/);

    // Check logo is visible in sidebar
    const sidebarLogo = sidebar.locator("svg").first();
    await expect(sidebarLogo).toBeVisible();

    // Check AutoArr title in sidebar
    await expect(
      sidebar.getByRole("heading", { name: "AutoArr" }),
    ).toBeVisible();

    // Check version number
    await expect(sidebar.getByText("v1.0.0")).toBeVisible();

    // Verify navigation items with new styling
    await expect(page.getByRole("link", { name: "Downloads" })).toBeVisible();
    await expect(page.getByRole("link", { name: "TV Shows" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Movies" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Media Server" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "Activity" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Settings" })).toBeVisible();

    // Check status indicator
    await expect(sidebar.getByText("Online")).toBeVisible();
    const statusDot = sidebar.locator(".bg-status-success");
    await expect(statusDot).toBeVisible();

    // Verify home page content (ConfigAudit Dashboard)
    await expect(page.getByRole("heading", { name: "Configuration Audit" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "System Health Overview" })).toBeVisible();
  });

  test("should have correct color scheme applied", async ({ page }) => {
    await goToPageAfterSplash(page);

    // Check main background color
    const main = page.locator("main");
    await expect(main).toHaveClass(/bg-background-primary/);

    // Check text colors
    const heading = page.getByRole("heading", { name: "Configuration Audit" });
    await expect(heading).toHaveClass(/text-gray-900/);
  });

  test("should show logo hover effect", async ({ page }) => {
    await goToPageAfterSplash(page);

    // Get the logo link
    const logoLink = page.locator("aside").getByRole("link").first();

    // Hover over logo
    await logoLink.hover();

    // The hover effect changes the background, verify it's interactive
    await expect(logoLink).toHaveClass(/hover:bg-background-tertiary/);
  });
});
