import { test, expect } from '@playwright/test';

/**
 * E2E test for Chat - Send Message functionality
 *
 * Tests that:
 * 1. Chat page loads successfully
 * 2. User can type and send a message
 * 3. Assistant responds with content classification
 * 4. No critical console errors during the flow
 */
test.describe('Chat - Send Message', () => {
  test('should send a message and receive response', async ({ page }) => {
    // Increase timeout for slow proxy environment
    test.setTimeout(120000);

    // Collect console errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to chat page (home)
    await page.goto('/');

    // Wait for chat container to load
    const chatContainer = page.getByTestId('chat-container');
    await expect(chatContainer).toBeVisible({ timeout: 60000 });

    // Verify input field is present
    const input = page.getByRole('textbox', { name: /message input/i });
    await expect(input).toBeVisible({ timeout: 15000 });

    // Type a test message
    const testMessage = 'download inception';
    await input.fill(testMessage);
    await expect(input).toHaveValue(testMessage);

    // Click send button
    const sendButton = page.getByRole('button', { name: /send/i });
    await expect(sendButton).toBeEnabled();
    await sendButton.click();

    // Verify user message appears in the chat
    const messagesList = page.getByTestId('messages-list');
    await expect(messagesList.getByText(testMessage)).toBeVisible({ timeout: 10000 });

    // Wait for assistant response containing the response text
    // The assistant should respond with a message about finding "inception"
    const assistantResponse = messagesList.getByText(/I found.*inception.*movie/i);

    // Wait for assistant response with longer timeout due to API call
    await expect(assistantResponse).toBeVisible({ timeout: 60000 });

    // Verify the response mentions the movie
    const responseText = await assistantResponse.textContent();
    console.log(`Assistant response: ${responseText}`);

    // Should have found "inception" as a movie
    expect(responseText?.toLowerCase()).toContain('inception');

    // Check for error states
    const errorAlert = page.locator('[role="alert"]');
    const hasError = await errorAlert.isVisible().catch(() => false);

    if (hasError) {
      const errorText = await errorAlert.textContent();
      console.error(`Error detected: ${errorText}`);
    }
    expect(hasError).toBe(false);

    // Filter out known non-critical console errors
    const criticalErrors = consoleErrors.filter((err) => {
      if (err.includes('React DevTools')) return false;
      if (err.includes('WebSocket')) return false;
      if (err.includes('favicon')) return false;
      if (err.includes('Failed to load resource')) return false;
      return true;
    });

    if (criticalErrors.length > 0) {
      console.error('Console errors detected:', criticalErrors);
    }
    expect(criticalErrors).toHaveLength(0);
  });
});
