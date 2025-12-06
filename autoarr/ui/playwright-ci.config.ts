import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for CI environment.
 *
 * Runs tests against a Docker container that's already running.
 * The container is started by the CI workflow before tests run.
 *
 * Key differences from other configs:
 * - No webServer (container is started by CI)
 * - Connects to container via TEST_BASE_URL (default: http://localhost:8088)
 * - Parallel execution with retries for stability
 * - Comprehensive artifact collection (screenshots, videos, traces)
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: true,
  retries: 2,
  workers: 4,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: "test-results/playwright-results.json" }],
    ["junit", { outputFile: "test-results/junit.xml" }],
  ],
  timeout: 30000,
  expect: {
    timeout: 10000,
  },

  use: {
    // Container runs on localhost:8088 in CI
    baseURL: process.env.TEST_BASE_URL || "http://localhost:8088",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    // Longer timeouts for CI environment
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    // Firefox and WebKit can be enabled later once chromium is stable
    // {
    //   name: "firefox",
    //   use: { ...devices["Desktop Firefox"] },
    // },
    // {
    //   name: "webkit",
    //   use: { ...devices["Desktop Safari"] },
    // },
  ],

  // NO webServer - the container is started by the CI workflow
});
