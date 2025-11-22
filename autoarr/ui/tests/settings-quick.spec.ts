import { test, expect } from '@playwright/test';

test('should uncheck enabled checkbox and save settings without error', async ({ page }) => {
  // Navigate to settings page
  await page.goto('http://localhost:8088/settings');

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Find the first enabled checkbox (SABnzbd)
  const enabledCheckbox = page.locator('input[type="checkbox"]').first();

  // Uncheck it if it's checked
  if (await enabledCheckbox.isChecked()) {
    await enabledCheckbox.uncheck();
  }

  // Verify it's unchecked
  await expect(enabledCheckbox).not.toBeChecked();

  // Find and click the "Save Settings" button
  const saveButton = page.getByRole('button', { name: /save settings/i });

  // Click save
  await saveButton.click();

  // Wait a moment for the save to complete
  await page.waitForTimeout(2000);

  // Check that we didn't get an error state
  // The button should be re-enabled after save completes
  await expect(saveButton).toBeEnabled();

  // Optionally check for success indicator
  // This would depend on your UI implementation (toast, message, etc.)

  console.log('✅ Test passed: Checkbox unchecked and settings saved without error');
});
