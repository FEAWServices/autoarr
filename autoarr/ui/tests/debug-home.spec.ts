/**
 * Debug Home Page Test
 *
 * When running inside Docker container: uses localhost:8088 (via playwright-container.config.ts)
 * When running from host: uses TEST_BASE_URL env var or host.docker.internal:8001
 *
 * Usage inside container: pnpm exec playwright test tests/debug-home.spec.ts --config=playwright-container.config.ts
 * Usage from host: TEST_BASE_URL=http://localhost:8001 pnpm exec playwright test tests/debug-home.spec.ts
 */

import { test, expect } from "@playwright/test";

test.describe("Debug Home Page", () => {
  test("capture page content after load", async ({ page }) => {
    // Collect all console messages
    const consoleMessages: string[] = [];
    page.on("console", (msg) => {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    });

    // Collect page errors
    const pageErrors: string[] = [];
    page.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    // Navigate to the page
    console.log("Navigating to home page...");
    await page.goto("/");

    // Wait for network to settle
    await page.waitForLoadState("networkidle");

    // Wait additional time for splash screen (2 seconds) + React render
    console.log("Waiting for splash screen to complete...");
    await page.waitForTimeout(4000);

    // Take a screenshot
    await page.screenshot({
      path: "test-results/debug-home-screenshot.png",
      fullPage: true,
    });
    console.log("Screenshot saved to test-results/debug-home-screenshot.png");

    // Get page content
    const bodyHTML = await page.locator("body").innerHTML();
    console.log("\n=== PAGE BODY HTML ===");
    console.log(bodyHTML.substring(0, 2000)); // First 2000 chars
    console.log("=== END PAGE BODY ===\n");

    // Get root element content
    const rootHTML = await page.locator("#root").innerHTML();
    console.log("\n=== ROOT ELEMENT HTML ===");
    console.log(rootHTML.substring(0, 2000));
    console.log("=== END ROOT ===\n");

    // Print console messages
    console.log("\n=== CONSOLE MESSAGES ===");
    consoleMessages.forEach((msg) => console.log(msg));
    console.log("=== END CONSOLE ===\n");

    // Print page errors
    console.log("\n=== PAGE ERRORS ===");
    pageErrors.forEach((err) => console.log(err));
    console.log("=== END ERRORS ===\n");

    // Check if there's any visible text
    const visibleText = await page.locator("body").textContent();
    console.log("\n=== VISIBLE TEXT ===");
    console.log(visibleText?.substring(0, 500));
    console.log("=== END TEXT ===\n");

    // Report findings
    expect(pageErrors.length, "Page should not have JavaScript errors").toBe(0);
    expect(rootHTML.length, "Root element should have content").toBeGreaterThan(
      10,
    );
  });
});
