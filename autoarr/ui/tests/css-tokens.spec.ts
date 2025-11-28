/**
 * CSS Design Tokens E2E Tests
 *
 * Tests that verify CSS variables and design tokens are applied correctly.
 */

import { test, expect } from '@playwright/test';

test.describe('CSS Design Tokens', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    // Wait for the page to load
    await page.waitForSelector('[data-testid="settings-page"]');
  });

  test('service cards have correct margin from --service-card-margin', async ({ page }) => {
    // Find the SABnzbd service card
    const sabnzbdCard = page.locator('[data-testid="service-card-sabnzbd"]');
    await expect(sabnzbdCard).toBeVisible();

    // Get computed margin
    const margin = await sabnzbdCard.evaluate((el) => {
      return window.getComputedStyle(el).margin;
    });

    // Assert margin is 10px (from --service-card-margin CSS variable)
    expect(margin).toBe('10px');
  });

  test('service cards have correct padding from --service-card-padding', async ({ page }) => {
    // Find the SABnzbd service card
    const sabnzbdCard = page.locator('[data-testid="service-card-sabnzbd"]');
    await expect(sabnzbdCard).toBeVisible();

    // Get computed padding
    const padding = await sabnzbdCard.evaluate((el) => {
      return window.getComputedStyle(el).padding;
    });

    // Assert padding is 10px (from --service-card-padding CSS variable)
    expect(padding).toBe('10px');
  });

  test('quick settings links have correct margin from --quick-settings-link-margin', async ({
    page,
  }) => {
    // Find a quick settings link
    const quickLink = page.locator('[data-component="QuickSettingsLink-Appearance"]');
    await expect(quickLink).toBeVisible();

    // Get computed margin
    const margin = await quickLink.evaluate((el) => {
      return window.getComputedStyle(el).margin;
    });

    // Assert margin is 10px (from --quick-settings-link-margin CSS variable)
    expect(margin).toBe('10px');
  });

  test('service card test button has correct padding from --service-card-test-button-padding', async ({
    page,
  }) => {
    // Find the test button
    const testButton = page.locator('[data-component="ServiceCardTestButton"]').first();
    await expect(testButton).toBeVisible();

    // Get computed padding
    const padding = await testButton.evaluate((el) => {
      return window.getComputedStyle(el).padding;
    });

    // Assert padding is 10px (from --service-card-test-button-padding CSS variable)
    expect(padding).toBe('10px');
  });

  test('h3 elements have vertical padding from --h3-padding-y', async ({ page }) => {
    // Find an h3 element in the page
    const h3 = page.locator('h3').first();
    await expect(h3).toBeVisible();

    // Get computed padding
    const paddingTop = await h3.evaluate((el) => {
      return window.getComputedStyle(el).paddingTop;
    });
    const paddingBottom = await h3.evaluate((el) => {
      return window.getComputedStyle(el).paddingBottom;
    });

    // Assert padding is 8px (from --h3-padding-y CSS variable)
    expect(paddingTop).toBe('8px');
    expect(paddingBottom).toBe('8px');
  });

  test('label elements have vertical padding from --label-padding-y', async ({ page }) => {
    // Find a label element in a service card
    const label = page.locator('[data-testid="service-card-sabnzbd"] label').first();
    await expect(label).toBeVisible();

    // Get computed padding
    const paddingTop = await label.evaluate((el) => {
      return window.getComputedStyle(el).paddingTop;
    });
    const paddingBottom = await label.evaluate((el) => {
      return window.getComputedStyle(el).paddingBottom;
    });

    // Assert padding is 4px (from --label-padding-y CSS variable)
    expect(paddingTop).toBe('4px');
    expect(paddingBottom).toBe('4px');
  });

  test('page container has correct padding from --page-padding', async ({ page }) => {
    // Find the settings page container
    const settingsPage = page.locator('[data-testid="settings-page"]');
    await expect(settingsPage).toBeVisible();

    // Get computed padding
    const padding = await settingsPage.evaluate((el) => {
      return window.getComputedStyle(el).padding;
    });

    // Assert padding is 50px (from --page-padding CSS variable)
    expect(padding).toBe('50px');
  });
});
