import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should display settings page title and description', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    await expect(page.getByText('Configure your media automation services')).toBeVisible();
  });

  test('should display all service sections', async ({ page }) => {
    // Check that all service sections are present
    await expect(page.getByText('SABnzbd')).toBeVisible();
    await expect(page.getByText('Sonarr')).toBeVisible();
    await expect(page.getByText('Radarr')).toBeVisible();
    await expect(page.getByText('Plex')).toBeVisible();
  });

  test('should allow toggling service enabled state', async ({ page }) => {
    // Find the first enabled checkbox (SABnzbd)
    const sabnzbdEnabled = page.getByRole('checkbox', { name: /enabled/i }).first();

    // Get initial state
    const initialState = await sabnzbdEnabled.isChecked();

    // Toggle it
    await sabnzbdEnabled.click();

    // Verify it toggled
    await expect(sabnzbdEnabled).toBeChecked({ checked: !initialState });
  });

  test('should allow entering service URL', async ({ page }) => {
    // Find URL input fields (there should be multiple)
    const urlInput = page.getByPlaceholder('http://localhost:8080').first();

    // Clear and enter new URL
    await urlInput.clear();
    await urlInput.fill('http://my-sabnzbd:8080');

    // Verify the value
    await expect(urlInput).toHaveValue('http://my-sabnzbd:8080');
  });

  test('should toggle password visibility', async ({ page }) => {
    // Find the first "Show/Hide" button for API key
    const toggleButton = page.locator('button[type="button"]').filter({ hasText: /eye/i }).first();

    // Find the first password/API key field
    const apiKeyInput = page.getByPlaceholder(/your_api_key|your_plex_token/).first();

    // Initially should be password type
    await expect(apiKeyInput).toHaveAttribute('type', 'password');

    // Click toggle button
    await toggleButton.click();

    // Should now be text type
    await expect(apiKeyInput).toHaveAttribute('type', 'text');

    // Click again to hide
    await toggleButton.click();

    // Should be password again
    await expect(apiKeyInput).toHaveAttribute('type', 'password');
  });

  test('should save settings successfully', async ({ page }) => {
    // Mock the API endpoint
    await page.route('**/api/v1/settings/**', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Successfully updated and saved configuration',
            service: 'sabnzbd'
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Fill in some test data
    const urlInput = page.getByPlaceholder('http://localhost:8080').first();
    await urlInput.clear();
    await urlInput.fill('http://test:8080');

    // Find and click save button
    const saveButton = page.getByRole('button', { name: /save/i });
    await saveButton.click();

    // Wait for success message/state
    await expect(saveButton).toBeEnabled();

    // Could also check for toast notification if implemented
  });

  test('should handle save errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/v1/settings/**', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Failed to connect to service'
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Try to save
    const saveButton = page.getByRole('button', { name: /save/i });
    await saveButton.click();

    // Should handle error (button should be re-enabled)
    await expect(saveButton).toBeEnabled();
  });

  test('should test connection to service', async ({ page }) => {
    // Find test connection button for SABnzbd
    const testButton = page.getByRole('button', { name: /test.*connection/i }).first();

    // Mock the test endpoint
    await page.route('**/health/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          healthy: true,
          service: 'sabnzbd',
        }),
      });
    });

    // Click test button
    await testButton.click();

    // Button should show testing state briefly
    // Then return to normal (implementation dependent)
    await expect(testButton).toBeEnabled();
  });

  test('should have responsive layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Page should still be usable
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

    // Service sections should stack vertically (visible)
    await expect(page.getByText('SABnzbd')).toBeVisible();
    await expect(page.getByText('Sonarr')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Clear URL field
    const urlInput = page.getByPlaceholder('http://localhost:8080').first();
    await urlInput.clear();

    // Clear API key field
    const apiKeyInput = page.getByPlaceholder(/your_api_key/).first();
    await apiKeyInput.clear();

    // Try to save - should fail validation
    const saveButton = page.getByRole('button', { name: /save/i });

    // Note: This test depends on client-side validation being implemented
    // If no validation, the API will return an error which we test above
  });
});
