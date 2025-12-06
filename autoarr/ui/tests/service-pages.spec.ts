/**
 * Service Pages E2E Tests
 *
 * Tests the Downloads, Shows, Movies, and Media pages in both connected
 * and not-connected states. Uses Playwright route mocking to simulate
 * different service configurations.
 */

import { test, expect, Page } from '@playwright/test';

// Helper to mock health endpoint responses
async function mockHealthEndpoint(
  page: Page,
  service: string,
  healthy: boolean
) {
  await page.route(`**/health/${service}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ healthy, service }),
    });
  });
}

// Helper to mock all services as disconnected
async function mockAllServicesDisconnected(page: Page) {
  const services = ['sabnzbd', 'sonarr', 'radarr', 'plex'];
  for (const service of services) {
    await mockHealthEndpoint(page, service, false);
  }
}

// Helper to mock specific services as connected
async function mockServicesConnected(page: Page, connectedServices: string[]) {
  const services = ['sabnzbd', 'sonarr', 'radarr', 'plex'];
  for (const service of services) {
    await mockHealthEndpoint(page, service, connectedServices.includes(service));
  }
}

// ============================================================================
// Test Suite: Downloads Page (SABnzbd)
// ============================================================================

test.describe('Downloads Page - SABnzbd', () => {
  test('should show ServiceNotConnected when SABnzbd is not configured', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/downloads');

    // Should show the not connected screen
    await expect(page.getByTestId('downloads-not-connected')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Connect to SABnzbd')).toBeVisible();
    await expect(page.getByText('Configure SABnzbd')).toBeVisible();

    // Feature cards should be visible
    await expect(page.getByText('Real-time Progress')).toBeVisible();
    await expect(page.getByText('Smart Recovery')).toBeVisible();
    await expect(page.getByText('Queue Control')).toBeVisible();
  });

  test('should show downloads interface when SABnzbd is connected', async ({ page }) => {
    await mockServicesConnected(page, ['sabnzbd']);
    await page.goto('/downloads');

    // Should NOT show the not connected screen
    await expect(page.getByTestId('downloads-not-connected')).not.toBeVisible({ timeout: 10000 });

    // Should show the downloads page content
    await expect(page.getByRole('heading', { name: 'Downloads' })).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Shows Page (Sonarr)
// ============================================================================

test.describe('Shows Page - Sonarr', () => {
  test('should show ServiceNotConnected when Sonarr is not configured', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/shows');

    // Should show the not connected screen
    await expect(page.getByTestId('shows-not-connected')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Connect to Sonarr')).toBeVisible();
    await expect(page.getByText('Configure Sonarr')).toBeVisible();

    // Feature cards should be visible
    await expect(page.getByText('Series Tracking')).toBeVisible();
    await expect(page.getByText('Quality Profiles')).toBeVisible();
    await expect(page.getByText('Auto-Download')).toBeVisible();
  });

  test('should show TV shows interface when Sonarr is connected', async ({ page }) => {
    await mockServicesConnected(page, ['sonarr']);
    await page.goto('/shows');

    // Should NOT show the not connected screen
    await expect(page.getByTestId('shows-not-connected')).not.toBeVisible({ timeout: 10000 });

    // Should show the shows page content
    await expect(page.getByRole('heading', { name: 'TV Shows' })).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Movies Page (Radarr)
// ============================================================================

test.describe('Movies Page - Radarr', () => {
  test('should show ServiceNotConnected when Radarr is not configured', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/movies');

    // Should show the not connected screen
    await expect(page.getByTestId('movies-not-connected')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Connect to Radarr')).toBeVisible();
    await expect(page.getByText('Configure Radarr')).toBeVisible();

    // Feature cards should be visible
    await expect(page.getByText('Movie Discovery')).toBeVisible();
    await expect(page.getByText('Auto-Upgrade')).toBeVisible();
    await expect(page.getByText('Release Tracking')).toBeVisible();
  });

  test('should show movies interface when Radarr is connected', async ({ page }) => {
    await mockServicesConnected(page, ['radarr']);
    await page.goto('/movies');

    // Should NOT show the not connected screen
    await expect(page.getByTestId('movies-not-connected')).not.toBeVisible({ timeout: 10000 });

    // Should show the movies page content
    await expect(page.getByRole('heading', { name: 'Movies' })).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Media Page (Plex)
// ============================================================================

test.describe('Media Page - Plex', () => {
  test('should show ServiceNotConnected when Plex is not configured', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/media');

    // Should show the not connected screen
    await expect(page.getByTestId('media-not-connected')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Connect to Plex')).toBeVisible();
    await expect(page.getByText('Configure Plex')).toBeVisible();

    // Feature cards should be visible
    await expect(page.getByText('Library Browse')).toBeVisible();
    await expect(page.getByText('Auto Scan')).toBeVisible();
    await expect(page.getByText('Stream Anywhere')).toBeVisible();
  });

  test('should show media interface when Plex is connected', async ({ page }) => {
    await mockServicesConnected(page, ['plex']);
    await page.goto('/media');

    // Should NOT show the not connected screen
    await expect(page.getByTestId('media-not-connected')).not.toBeVisible({ timeout: 10000 });

    // Should show the media page content
    await expect(page.getByRole('heading', { name: 'Media Server' })).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Sidebar Navigation
// ============================================================================

test.describe('Sidebar - Conditional Navigation', () => {
  test('should hide service tabs when no services are connected', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/');

    // Wait for sidebar to load
    await expect(page.getByRole('navigation')).toBeVisible({ timeout: 10000 });

    // Base items should be visible
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Search' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Activity' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();

    // Service-specific tabs should NOT be visible
    await expect(page.getByRole('link', { name: 'Downloads' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'TV Shows' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Movies' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Media Server' })).not.toBeVisible();
  });

  test('should show only connected service tabs', async ({ page }) => {
    // Only SABnzbd and Sonarr connected
    await mockServicesConnected(page, ['sabnzbd', 'sonarr']);
    await page.goto('/');

    // Wait for sidebar to load
    await expect(page.getByRole('navigation')).toBeVisible({ timeout: 10000 });

    // Connected services should show
    await expect(page.getByRole('link', { name: 'Downloads' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'TV Shows' })).toBeVisible();

    // Disconnected services should not show
    await expect(page.getByRole('link', { name: 'Movies' })).not.toBeVisible();
    await expect(page.getByRole('link', { name: 'Media Server' })).not.toBeVisible();
  });

  test('should show all service tabs when all services are connected', async ({ page }) => {
    await mockServicesConnected(page, ['sabnzbd', 'sonarr', 'radarr', 'plex']);
    await page.goto('/');

    // Wait for sidebar to load
    await expect(page.getByRole('navigation')).toBeVisible({ timeout: 10000 });

    // All service tabs should be visible
    await expect(page.getByRole('link', { name: 'Downloads' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'TV Shows' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Movies' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Media Server' })).toBeVisible();
  });
});

// ============================================================================
// Test Suite: Service Status Indicators
// ============================================================================

test.describe('Sidebar - Service Status Indicators', () => {
  test('should show red status for disconnected services', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/');

    // Wait for status indicators
    await expect(page.getByTestId('sidebar-status-sabnzbd')).toBeVisible({ timeout: 10000 });

    // All should show offline status (red)
    const services = ['sabnzbd', 'sonarr', 'radarr', 'plex'];
    for (const service of services) {
      const indicator = page.getByTestId(`sidebar-status-${service}`);
      await expect(indicator).toBeVisible();
      // The text should have red color class
      await expect(indicator.locator('span')).toHaveClass(/text-red-500/);
    }
  });

  test('should show green status for connected services', async ({ page }) => {
    await mockServicesConnected(page, ['sabnzbd', 'sonarr', 'radarr', 'plex']);
    await page.goto('/');

    // Wait for status indicators
    await expect(page.getByTestId('sidebar-status-sabnzbd')).toBeVisible({ timeout: 10000 });

    // All should show connected status (green)
    const services = ['sabnzbd', 'sonarr', 'radarr', 'plex'];
    for (const service of services) {
      const indicator = page.getByTestId(`sidebar-status-${service}`);
      await expect(indicator).toBeVisible();
      // The text should have green color class
      await expect(indicator.locator('span')).toHaveClass(/text-green-500/);
    }
  });

  test('should show mixed status for partially connected services', async ({ page }) => {
    await mockServicesConnected(page, ['sabnzbd', 'radarr']);
    await page.goto('/');

    // Wait for status indicators
    await expect(page.getByTestId('sidebar-status-sabnzbd')).toBeVisible({ timeout: 10000 });

    // SABnzbd and Radarr should be green
    await expect(page.getByTestId('sidebar-status-sabnzbd').locator('span')).toHaveClass(/text-green-500/);
    await expect(page.getByTestId('sidebar-status-radarr').locator('span')).toHaveClass(/text-green-500/);

    // Sonarr and Plex should be red
    await expect(page.getByTestId('sidebar-status-sonarr').locator('span')).toHaveClass(/text-red-500/);
    await expect(page.getByTestId('sidebar-status-plex').locator('span')).toHaveClass(/text-red-500/);
  });
});

// ============================================================================
// Test Suite: Navigation from Not Connected State
// ============================================================================

test.describe('ServiceNotConnected - Navigation', () => {
  test('should navigate to settings when clicking configure button', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/downloads');

    // Wait for page to load
    await expect(page.getByTestId('downloads-not-connected')).toBeVisible({ timeout: 10000 });

    // Click the configure button
    await page.getByRole('link', { name: /Configure SABnzbd/i }).click();

    // Should navigate to settings
    await expect(page).toHaveURL(/\/settings/);
  });

  test('should have external link to documentation', async ({ page }) => {
    await mockAllServicesDisconnected(page);
    await page.goto('/shows');

    // Wait for page to load
    await expect(page.getByTestId('shows-not-connected')).toBeVisible({ timeout: 10000 });

    // Check documentation link
    const docsLink = page.getByRole('link', { name: /Sonarr documentation/i });
    await expect(docsLink).toBeVisible();
    await expect(docsLink).toHaveAttribute('href', 'https://wiki.servarr.com/sonarr');
    await expect(docsLink).toHaveAttribute('target', '_blank');
  });
});
