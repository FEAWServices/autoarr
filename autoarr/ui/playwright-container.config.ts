import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for running tests INSIDE the Docker container.
 * Tests against localhost:5173 (Vite dev server with HMR for live updates).
 *
 * Usage (from inside container):
 *   cd /app/autoarr/ui
 *   pnpm exec playwright test --config=playwright-container.config.ts
 *
 * Or via docker exec:
 *   docker exec autoarr-local sh -c "cd /app/autoarr/ui && pnpm exec playwright test --config=playwright-container.config.ts"
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false, // Run sequentially for stability
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  timeout: 30000,

  use: {
    // Use Vite dev server (port 5173) for live HMR updates
    // Falls back to backend (port 8088) if Vite isn't running
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // NO webServer - the app is already running in this container
});
