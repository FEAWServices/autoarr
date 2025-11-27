import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for testing against a running Docker container.
 * Does NOT start a web server - expects the app to be running at port 8001.
 *
 * Usage: pnpm exec playwright test --config=playwright-docker.config.ts
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  timeout: 60000,
  use: {
    baseURL: "http://host.docker.internal:8001",
    trace: "on",
    screenshot: "on",
    video: "on",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // NO webServer - expect container to be running
});
