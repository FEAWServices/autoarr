import { test, expect } from '@playwright/test';

test.describe('Theme Settings', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to start with default theme
    await page.goto('/settings/appearance');
    await page.evaluate(() => localStorage.removeItem('autoarr-theme-v2'));
    await page.reload();
  });

  test('should display theme settings section', async ({ page }) => {
    await expect(page.getByText('Appearance')).toBeVisible();
    await expect(page.getByText('Theme')).toBeVisible();
  });

  test('should display theme grid with built-in themes', async ({ page }) => {
    // Check for built-in themes
    await expect(page.getByText('AutoArr Dark')).toBeVisible();
    await expect(page.getByText('AutoArr Light')).toBeVisible();
    await expect(page.getByText('Dracula')).toBeVisible();
    await expect(page.getByText('Nord')).toBeVisible();
    await expect(page.getByText('Plex')).toBeVisible();
  });

  test('should switch themes when clicking theme card', async ({ page }) => {
    // Initially should be AutoArr Dark (default)
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'autoarr-dark');

    // Click Dracula theme
    await page.getByText('Dracula').click();

    // Theme should change
    await expect(html).toHaveAttribute('data-theme', 'dracula');

    // CSS variables should be applied
    const bgColor = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--main-bg-color')
    );
    expect(bgColor.trim()).toContain('#282a36'); // Dracula background
  });

  test('should display accent color picker', async ({ page }) => {
    await expect(page.getByText('Accent Color')).toBeVisible();
    // Should have hue slider
    await expect(page.locator('input[type="range"]')).toBeVisible();
  });

  test('should change accent color with hue slider', async ({ page }) => {
    const slider = page.locator('input[type="range"]').first();
    await slider.fill('180'); // Cyan hue

    // Custom accent should be applied
    const hasCustomAccent = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return style.getPropertyValue('--accent-hue');
    });
    expect(hasCustomAccent.trim()).toBe('180');
  });

  test('should have import/export button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /import.*export/i })).toBeVisible();
  });

  test('should open import/export modal', async ({ page }) => {
    // Click import/export button
    await page.getByRole('button', { name: /import.*export/i }).click();

    // Modal should appear
    await expect(page.getByText('Import / Export Themes')).toBeVisible();
    await expect(page.getByText('Import Theme')).toBeVisible();
    await expect(page.getByText('Export Current Theme')).toBeVisible();
  });

  test('should export current theme as JSON', async ({ page }) => {
    // Open modal
    await page.getByRole('button', { name: /import.*export/i }).click();

    // Click copy JSON button
    const copyButton = page.getByRole('button', { name: /copy json/i });
    await copyButton.click();

    // Button should change to "Copied!"
    await expect(page.getByText('Copied!')).toBeVisible();
  });

  test('should persist theme selection on page reload', async ({ page }) => {
    // Switch to Dracula theme
    await page.getByText('Dracula').click();

    // Reload page
    await page.reload();

    // Theme should still be Dracula
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'dracula');
  });

  test('should switch between light and dark modes', async ({ page }) => {
    const html = page.locator('html');

    // Initially dark mode (AutoArr Dark)
    await expect(html).toHaveClass(/dark/);

    // Switch to AutoArr Light
    await page.getByText('AutoArr Light').click();

    // Should be light mode
    await expect(html).not.toHaveClass(/dark/);
    await expect(html).toHaveAttribute('data-theme', 'autoarr-light');
  });

  test('should have reset button for accent color', async ({ page }) => {
    // First set a custom accent
    const slider = page.locator('input[type="range"]').first();
    await slider.fill('180');

    // Reset button should be visible
    const resetButton = page.getByRole('button', { name: /reset/i });
    await expect(resetButton).toBeVisible();

    // Click reset
    await resetButton.click();

    // Custom accent should be removed
    const accentHue = await page.evaluate(() => {
      return localStorage.getItem('autoarr-theme-v2');
    });
    const parsed = JSON.parse(accentHue || '{}');
    expect(parsed.state?.accentHue).toBeNull();
  });
});
