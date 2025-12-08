import { test, expect } from '@playwright/test';

/**
 * E2E test for Settings page - Log Level change functionality
 *
 * Tests that:
 * 1. Settings page loads successfully
 * 2. Log level can be changed to Debug
 * 3. Save button works without errors
 * 4. No console errors during the flow
 */
test.describe('Settings - Log Level', () => {
  test('should change log level to Debug and save without errors', async ({ page }) => {
    // Collect console errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to settings page
    await page.goto('/settings');

    // Wait for page to load - look for the settings page header
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible({ timeout: 30000 });

    // Wait for the Application card to be visible (contains log level)
    const applicationCard = page.locator('[data-component="ApplicationCard"]');
    await expect(applicationCard).toBeVisible({ timeout: 15000 });

    // Find the Log Level select dropdown
    const logLevelSelect = applicationCard.locator('select').first();
    await expect(logLevelSelect).toBeVisible();

    // Get current value
    const currentValue = await logLevelSelect.inputValue();
    console.log(`Current log level: ${currentValue}`);

    // Change to DEBUG
    await logLevelSelect.selectOption('DEBUG');

    // Verify the selection changed
    await expect(logLevelSelect).toHaveValue('DEBUG');

    // Find and click the Save button
    const saveButton = page.locator('[data-component="SaveButton"]');
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();

    // Click save
    await saveButton.click();

    // Wait for save to complete - button should show "Saving..." then go back to "Save Settings"
    // or show success message
    await expect(saveButton).toContainText('Saving', { timeout: 5000 }).catch(() => {
      // Button might transition too fast to catch "Saving..."
    });

    // Wait for either success message or button to return to normal state
    // Success shows a green checkmark with "Settings saved successfully!"
    const successIndicator = page.getByText('Settings saved successfully');
    const saveCompleted = await Promise.race([
      successIndicator.waitFor({ state: 'visible', timeout: 60000 }).then(() => 'success'),
      saveButton.waitFor({ state: 'visible', timeout: 60000 }).then(async () => {
        // Check if button is back to normal (not showing "Saving...")
        const buttonText = await saveButton.textContent();
        if (buttonText?.includes('Save Settings')) {
          return 'completed';
        }
        return 'unknown';
      }),
    ]);

    console.log(`Save result: ${saveCompleted}`);

    // If we got success message, great! Otherwise check button state
    if (saveCompleted === 'success') {
      await expect(successIndicator).toBeVisible();
    } else {
      // Verify button is clickable again (not stuck on "Saving...")
      await expect(saveButton).not.toContainText('Saving');
    }

    // Check for any error states on the page
    const errorIndicator = page.getByText('Failed to save');
    const hasError = await errorIndicator.isVisible().catch(() => false);

    if (hasError) {
      const errorText = await page.locator('[data-component="SaveButtonSection"]').textContent();
      console.error(`Save error detected: ${errorText}`);
    }

    expect(hasError).toBe(false);

    // Filter out known non-critical console errors
    const criticalErrors = consoleErrors.filter((err) => {
      // Ignore React DevTools message
      if (err.includes('React DevTools')) return false;
      // Ignore WebSocket reconnection messages (not errors)
      if (err.includes('WebSocket')) return false;
      // Ignore favicon errors
      if (err.includes('favicon')) return false;
      return true;
    });

    // Assert no critical console errors
    if (criticalErrors.length > 0) {
      console.error('Console errors detected:', criticalErrors);
    }
    expect(criticalErrors).toHaveLength(0);
  });

  test('should persist log level after page reload', async ({ page }) => {
    // Increase test timeout for slow proxy environment
    test.setTimeout(120000);

    // First, set to DEBUG
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible({ timeout: 60000 });

    const applicationCard = page.locator('[data-component="ApplicationCard"]');
    await expect(applicationCard).toBeVisible({ timeout: 30000 });

    const logLevelSelect = applicationCard.locator('select').first();
    await logLevelSelect.selectOption('DEBUG');

    // Save
    const saveButton = page.locator('[data-component="SaveButton"]');
    await saveButton.click();

    // Wait for save to complete - longer timeout for slow proxy
    await page.waitForTimeout(5000);

    // Navigate away and back instead of reload (more reliable)
    await page.goto('/');
    await page.waitForTimeout(2000);
    await page.goto('/settings');

    // Wait for page to load again
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible({ timeout: 60000 });

    // Re-locate the application card after navigation
    const applicationCardAfterNav = page.locator('[data-component="ApplicationCard"]');
    await expect(applicationCardAfterNav).toBeVisible({ timeout: 30000 });

    // Verify log level persisted
    const logLevelSelectAfterReload = applicationCardAfterNav.locator('select').first();
    await expect(logLevelSelectAfterReload).toHaveValue('DEBUG');
  });
});
