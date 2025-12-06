import { test, expect } from '@playwright/test';

test.describe('Onboarding Wizard', () => {
  test.beforeEach(async ({ page }) => {
    // Reset onboarding state before each test
    await page.request.post('/api/v1/onboarding/reset');
    await page.goto('/onboarding');
  });

  test('should load without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        const isExpectedError =
          text.includes('React DevTools') ||
          text.includes('WebSocket') ||
          text.includes('ws://') ||
          text.includes('404') ||
          text.includes('Failed to fetch') ||
          text.includes('NetworkError') ||
          text.includes('net::ERR');

        if (!isExpectedError) {
          consoleErrors.push(text);
        }
      }
    });

    await page.goto('/onboarding', { waitUntil: 'networkidle' });
    await expect(page.getByTestId('welcome-step')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);
    expect(consoleErrors).toEqual([]);
  });

  test('should display welcome step with value proposition', async ({ page }) => {
    await expect(page.getByTestId('welcome-step')).toBeVisible();
    await expect(page.getByRole('heading', { name: /welcome to autoarr/i })).toBeVisible();
    await expect(page.getByText(/intelligent orchestration/i)).toBeVisible();

    // Feature cards should be visible
    await expect(page.getByText(/AI-Powered/i)).toBeVisible();
    await expect(page.getByText(/Automatic Recovery/i)).toBeVisible();
    await expect(page.getByText(/Privacy First/i)).toBeVisible();
  });

  test('should have get started and skip buttons on welcome step', async ({ page }) => {
    await expect(page.getByTestId('welcome-step')).toBeVisible();
    await expect(page.getByTestId('get-started-button')).toBeVisible();
    await expect(page.getByTestId('skip-setup-button')).toBeVisible();
  });

  test('should navigate to AI setup step when clicking get started', async ({ page }) => {
    await expect(page.getByTestId('welcome-step')).toBeVisible();
    await page.getByTestId('get-started-button').click();
    await expect(page.getByTestId('ai-setup-step')).toBeVisible();
    await expect(page.getByRole('heading', { name: /set up ai assistant/i })).toBeVisible();
  });

  test('should display OpenRouter setup instructions', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await expect(page.getByTestId('ai-setup-step')).toBeVisible();

    // Should show step-by-step instructions
    await expect(page.getByText(/create.*openrouter.*account/i)).toBeVisible();
    await expect(page.getByText(/generate.*api key/i)).toBeVisible();

    // Should have input field for API key
    await expect(page.getByTestId('openrouter-api-key-input')).toBeVisible();
  });

  test('should show model selection options', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await expect(page.getByTestId('ai-setup-step')).toBeVisible();

    // Should have model selector
    await expect(page.getByTestId('model-selector')).toBeVisible();
  });

  test('should allow skipping AI setup', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await expect(page.getByTestId('ai-setup-step')).toBeVisible();

    // Click skip button
    await page.getByTestId('skip-ai-button').click();

    // Should show warning about reduced functionality
    await expect(page.getByTestId('skip-ai-confirmation')).toBeVisible();
    await expect(page.getByText(/reduced functionality/i)).toBeVisible();
  });

  test('should navigate to service selection from AI setup', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await expect(page.getByTestId('ai-setup-step')).toBeVisible();

    // Skip AI setup to proceed
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();

    // Should be on service selection
    await expect(page.getByTestId('service-selection-step')).toBeVisible();
    await expect(page.getByRole('heading', { name: /select.*services/i })).toBeVisible();
  });

  test('should display all service options in service selection', async ({ page }) => {
    // Navigate to service selection step
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();

    await expect(page.getByTestId('service-selection-step')).toBeVisible();

    // All services should be visible
    await expect(page.getByTestId('service-card-sabnzbd')).toBeVisible();
    await expect(page.getByTestId('service-card-sonarr')).toBeVisible();
    await expect(page.getByTestId('service-card-radarr')).toBeVisible();
    await expect(page.getByTestId('service-card-plex')).toBeVisible();
  });

  test('should toggle service selection', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();

    await expect(page.getByTestId('service-selection-step')).toBeVisible();

    // Click on SABnzbd card to select it
    const sabnzbdCard = page.getByTestId('service-card-sabnzbd');
    await sabnzbdCard.click();

    // Should be selected (has checkmark or selected state)
    await expect(sabnzbdCard).toHaveAttribute('data-selected', 'true');

    // Click again to deselect
    await sabnzbdCard.click();
    await expect(sabnzbdCard).toHaveAttribute('data-selected', 'false');
  });

  test('should navigate to service config when services selected', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();

    await expect(page.getByTestId('service-selection-step')).toBeVisible();

    // Select SABnzbd
    await page.getByTestId('service-card-sabnzbd').click();

    // Click continue
    await page.getByTestId('continue-button').click();

    // Should be on service config step
    await expect(page.getByTestId('service-config-step')).toBeVisible();
    await expect(page.getByRole('heading', { name: /configure sabnzbd/i })).toBeVisible();
  });

  test('should show service config form fields', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();
    await page.getByTestId('service-card-sabnzbd').click();
    await page.getByTestId('continue-button').click();

    await expect(page.getByTestId('service-config-step')).toBeVisible();

    // Should have URL and API key inputs
    await expect(page.getByTestId('service-url-input')).toBeVisible();
    await expect(page.getByTestId('api-key-input')).toBeVisible();
    await expect(page.getByTestId('test-connection-button')).toBeVisible();
  });

  test('should allow skipping service configuration', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();
    await page.getByTestId('service-card-sabnzbd').click();
    await page.getByTestId('continue-button').click();

    await expect(page.getByTestId('service-config-step')).toBeVisible();

    // Skip button should be visible
    await expect(page.getByTestId('skip-service-button')).toBeVisible();
  });

  test('should show complete step after all services configured', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();

    // Skip service selection - click continue without selecting any
    await page.getByTestId('continue-button').click();

    // Should be on complete step
    await expect(page.getByTestId('complete-step')).toBeVisible();
    await expect(page.getByRole('heading', { name: /you're all set/i })).toBeVisible();
  });

  test('should show setup summary on complete step', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();
    await page.getByTestId('continue-button').click();

    await expect(page.getByTestId('complete-step')).toBeVisible();

    // Should show summary
    await expect(page.getByText(/setup summary/i)).toBeVisible();
    await expect(page.getByText(/ai assistant/i)).toBeVisible();
  });

  test('should navigate to dashboard from complete step', async ({ page }) => {
    await page.getByTestId('get-started-button').click();
    await page.getByTestId('skip-ai-button').click();
    await page.getByTestId('confirm-skip-button').click();
    await page.getByTestId('continue-button').click();

    await expect(page.getByTestId('complete-step')).toBeVisible();

    // Click go to dashboard
    await page.getByTestId('go-to-dashboard').click();

    // Should be on home page
    await expect(page).toHaveURL('/');
  });

  test('should complete full skip flow', async ({ page }) => {
    await expect(page.getByTestId('welcome-step')).toBeVisible();

    // Skip entire setup from welcome
    await page.getByTestId('skip-setup-button').click();

    // Should go to complete step
    await expect(page.getByTestId('complete-step')).toBeVisible();
  });

  test('should show progress indicator throughout wizard', async ({ page }) => {
    await expect(page.getByTestId('progress-indicator')).toBeVisible();

    // Should show current step highlighted
    await expect(page.getByTestId('step-welcome')).toHaveAttribute('data-active', 'true');

    // Navigate to next step
    await page.getByTestId('get-started-button').click();
    await expect(page.getByTestId('step-ai')).toHaveAttribute('data-active', 'true');
  });
});

test.describe('Onboarding API', () => {
  test('should fetch onboarding status', async ({ request }) => {
    const response = await request.get('/api/v1/onboarding/status');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('completed');
    expect(data).toHaveProperty('current_step');
    expect(data).toHaveProperty('ai_configured');
    expect(data).toHaveProperty('services_configured');
  });

  test('should reset onboarding state', async ({ request }) => {
    // First complete onboarding
    await request.post('/api/v1/onboarding/complete');

    // Then reset
    const resetResponse = await request.post('/api/v1/onboarding/reset');
    expect(resetResponse.ok()).toBeTruthy();

    // Verify reset
    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.completed).toBe(false);
    expect(data.current_step).toBe('welcome');
  });

  test('should update current step', async ({ request }) => {
    const response = await request.put('/api/v1/onboarding/step', {
      data: { step: 'ai_setup' },
    });
    expect(response.ok()).toBeTruthy();

    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.current_step).toBe('ai_setup');
  });

  test('should mark AI as configured', async ({ request }) => {
    const response = await request.put('/api/v1/onboarding/ai-configured', {
      data: { configured: true },
    });
    expect(response.ok()).toBeTruthy();

    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.ai_configured).toBe(true);
  });

  test('should add service to configured list', async ({ request }) => {
    const response = await request.post('/api/v1/onboarding/add-service', {
      data: { service_id: 'sabnzbd' },
    });
    expect(response.ok()).toBeTruthy();

    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.services_configured).toContain('sabnzbd');
  });

  test('should mark onboarding complete', async ({ request }) => {
    const response = await request.post('/api/v1/onboarding/complete');
    expect(response.ok()).toBeTruthy();

    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.completed).toBe(true);
    expect(data.completed_at).not.toBeNull();
  });

  test('should skip onboarding', async ({ request }) => {
    const response = await request.post('/api/v1/onboarding/skip');
    expect(response.ok()).toBeTruthy();

    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.completed).toBe(true);
  });

  test('should dismiss banner', async ({ request }) => {
    await request.post('/api/v1/onboarding/skip'); // Skip to complete onboarding

    const response = await request.put('/api/v1/onboarding/dismiss-banner', {
      data: { dismissed: true },
    });
    expect(response.ok()).toBeTruthy();

    const statusResponse = await request.get('/api/v1/onboarding/status');
    const data = await statusResponse.json();
    expect(data.banner_dismissed).toBe(true);
  });
});

test.describe('Premium Waitlist', () => {
  test('should submit waitlist signup', async ({ request }) => {
    const response = await request.post('/api/v1/onboarding/waitlist', {
      data: { email: 'test@example.com' },
    });
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.message).toContain('waitlist');
  });

  test('should reject invalid email', async ({ request }) => {
    const response = await request.post('/api/v1/onboarding/waitlist', {
      data: { email: 'invalid-email' },
    });
    expect(response.ok()).toBeFalsy();
    expect(response.status()).toBe(422);
  });
});

test.describe('Setup Banner', () => {
  test('should show setup banner when onboarding skipped', async ({ page }) => {
    // Skip onboarding
    await page.request.post('/api/v1/onboarding/skip');

    // Go to home page
    await page.goto('/');

    // Banner should be visible
    await expect(page.getByTestId('setup-banner')).toBeVisible();
    await expect(page.getByText(/complete your setup/i)).toBeVisible();
  });

  test('should have continue setup button in banner', async ({ page }) => {
    await page.request.post('/api/v1/onboarding/skip');
    await page.goto('/');

    await expect(page.getByTestId('continue-setup-button')).toBeVisible();
  });

  test('should navigate to onboarding when clicking continue setup', async ({ page }) => {
    await page.request.post('/api/v1/onboarding/skip');
    await page.goto('/');

    await page.getByTestId('continue-setup-button').click();
    await expect(page).toHaveURL('/onboarding');
  });

  test('should dismiss banner when clicking dismiss', async ({ page }) => {
    await page.request.post('/api/v1/onboarding/skip');
    await page.goto('/');

    await expect(page.getByTestId('setup-banner')).toBeVisible();

    await page.getByTestId('dismiss-banner-button').click();

    // Banner should be hidden
    await expect(page.getByTestId('setup-banner')).not.toBeVisible();
  });

  test('should not show banner when onboarding fully complete', async ({ page }) => {
    // Complete full onboarding with AI configured
    await page.request.post('/api/v1/onboarding/reset');
    await page.request.put('/api/v1/onboarding/ai-configured', {
      data: { configured: true },
    });
    await page.request.post('/api/v1/onboarding/add-service', {
      data: { service_id: 'sabnzbd' },
    });
    await page.request.post('/api/v1/onboarding/complete');

    await page.goto('/');

    // Banner should not be visible
    await expect(page.getByTestId('setup-banner')).not.toBeVisible();
  });
});

test.describe('Settings - Setup Wizard Button', () => {
  test('should have run setup wizard button', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByTestId('run-setup-wizard-button')).toBeVisible();
  });

  test('should navigate to onboarding when clicking setup wizard button', async ({ page }) => {
    await page.goto('/settings');
    await page.getByTestId('run-setup-wizard-button').click();

    // Should navigate to onboarding
    await expect(page).toHaveURL('/onboarding');
    await expect(page.getByTestId('welcome-step')).toBeVisible();
  });
});

test.describe('Onboarding Redirect Behavior', () => {
  test('should redirect to onboarding when not completed', async ({ page }) => {
    // Reset onboarding to ensure it's not completed
    await page.request.post('/api/v1/onboarding/reset');

    // Visit home page
    await page.goto('/');

    // Should be redirected to onboarding
    await expect(page).toHaveURL('/onboarding');
    await expect(page.getByTestId('onboarding-container')).toBeVisible();
  });

  test('should allow re-running wizard when already complete', async ({ page }) => {
    // Complete onboarding first
    await page.request.post('/api/v1/onboarding/complete');

    // Verify it's complete
    const statusResponse = await page.request.get('/api/v1/onboarding/status');
    const status = await statusResponse.json();
    expect(status.completed).toBe(true);

    // Navigate directly to onboarding
    await page.goto('/onboarding');

    // Should reset and show welcome step (not redirect away)
    await expect(page.getByTestId('onboarding-container')).toBeVisible();
    // Wait for reset to complete and welcome step to appear
    await expect(page.getByTestId('welcome-step')).toBeVisible({ timeout: 5000 });
  });

  test('should not auto-redirect from home when onboarding complete', async ({ page }) => {
    // Complete onboarding
    await page.request.post('/api/v1/onboarding/complete');

    // Visit home page
    await page.goto('/');

    // Should stay on home, not redirect to onboarding
    await expect(page).toHaveURL('/');
  });
});

test.describe('LLM Settings API - Route Ordering', () => {
  test('should access /api/v1/settings/llm without 404', async ({ request }) => {
    const response = await request.get('/api/v1/settings/llm');
    // Should not return 404 (which would indicate route was matched by /{service})
    expect(response.status()).not.toBe(404);
    // Should return 200 or 503 (if DB not configured)
    expect([200, 503]).toContain(response.status());
  });

  test('should access /api/v1/settings/llm/models without 404', async ({ request }) => {
    const response = await request.get('/api/v1/settings/llm/models');
    expect(response.status()).not.toBe(404);
    expect([200, 503]).toContain(response.status());
  });

  test('should get proper error for invalid service', async ({ request }) => {
    const response = await request.get('/api/v1/settings/invalid-service');
    // Should return 404 with "Service not found" message
    expect(response.status()).toBe(404);
    const data = await response.json();
    expect(data.detail).toContain('not found');
  });
});
