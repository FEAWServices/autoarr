import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for running tests INSIDE the Docker container.
 * Tests against localhost:8088 (the app running in the same container).
 *
 * Usage (from inside container):
 *   cd /app/autoarr/ui
 *   pnpm exec playwright test --config=playwright-container.config.ts
 *
 * Or via docker exec:
 *   docker exec autoarr-local sh -c "cd /app/autoarr/ui && pnpm exec playwright test --config=playwright-container.config.ts"
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false, // Run sequentially for stability
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  timeout: 30000,

  use: {
    baseURL: "http://localhost:8088",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // NO webServer - the app is already running in this container
});
