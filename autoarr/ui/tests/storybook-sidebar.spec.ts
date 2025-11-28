/**
 * Test that Storybook Sidebar stories load without router errors
 */
import { test, expect } from '@playwright/test';

// Quick test with short timeout - we just want to check for the router error
test.setTimeout(60000);

test.describe('Storybook Sidebar Stories', () => {
  test('SettingsExpanded story loads without router error', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Navigate (don't wait for load - we just need to check for errors)
    const response = await page.goto(
      'http://autoarr-storybook:6006/iframe.html?viewMode=story&id=layout-sidebar--settings-expanded',
      { waitUntil: 'commit', timeout: 30000 }
    );

    console.log('Response status:', response?.status());

    // Wait just enough for React to error
    await page.waitForTimeout(5000);

    // Get page content
    const pageContent = await page.content();

    // Check for the router error
    const hasRouterError = pageContent.includes(
      'You cannot render a <Router> inside another <Router>'
    );

    // Get error message if any
    const errorMessage = await page
      .locator('#error-message')
      .textContent()
      .catch(() => '');
    const errorStack = await page
      .locator('#error-stack')
      .textContent()
      .catch(() => '');

    console.log('Has router error in content:', hasRouterError);
    console.log('Console errors:', errors);
    console.log('Error message element:', errorMessage);
    console.log('Error stack (first 300 chars):', errorStack?.substring(0, 300));

    // Fail fast if router error detected
    expect(hasRouterError, 'Found nested Router error').toBe(false);
    expect(errorMessage).not.toContain('Router');
    expect(errors.join('\n')).not.toContain('Router');
  });
});
