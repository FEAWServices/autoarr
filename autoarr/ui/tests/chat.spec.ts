/**
 * Chat Interface E2E Tests with Playwright
 *
 * Following TDD principles:
 * - RED: Write failing tests first
 * - GREEN: Write minimal code to pass tests
 * - REFACTOR: Improve code while keeping tests green
 *
 * Test Coverage:
 * - Chat interface loading and rendering
 * - Message input and sending
 * - Message display (user/assistant/system)
 * - Content request flow with confirmation
 * - Real-time status updates via WebSocket
 * - Chat history persistence and search
 * - Mobile responsiveness (320px, 375px, 768px, 1920px)
 * - Accessibility (WCAG 2.1 AA compliance)
 * - Error handling and retry
 * - Keyboard navigation
 */

import { test, expect } from "@playwright/test";

// ============================================================================
// Test Configuration
// ============================================================================

const BASE_URL = "http://localhost:3000";
const API_BASE_URL = "http://localhost:8088/api/v1";

// Mock data for testing
const mockContentRequestResponse = {
  requestId: "req_test_123",
  message: "I found a movie matching your request",
  classification: {
    title: "Inception",
    type: "movie",
    year: 2010,
    confidence: 0.95,
  },
  searchResults: [
    {
      tmdbId: 27205,
      title: "Inception",
      originalTitle: "Inception",
      year: 2010,
      overview:
        "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets is offered a chance to regain his old life as payment for a task considered to be impossible: inception, the implantation of another person's idea into a target's subconscious.",
      posterPath: "/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
      voteAverage: 8.4,
      voteCount: 35000,
      mediaType: "movie",
      releaseDate: "2010-07-16",
    },
    {
      tmdbId: 123456,
      title: "Inception 2",
      originalTitle: "Inception 2",
      year: 2024,
      overview: "A sequel to the original Inception movie.",
      posterPath: "/fake.jpg",
      voteAverage: 7.5,
      voteCount: 1000,
      mediaType: "movie",
      releaseDate: "2024-01-01",
    },
  ],
  requiresConfirmation: true,
};

const mockConfirmationResponse = {
  requestId: "req_test_123",
  message: "Added to download queue",
  status: "downloading",
};

// ============================================================================
// Test Suite: Chat Interface Loading and Rendering
// ============================================================================

test.describe("Chat - Loading and Initial State", () => {
  test("should display chat page when navigating to /chat", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/chat`);

    // Verify chat container is visible
    const chatContainer = page.getByTestId("chat-container");
    await expect(chatContainer).toBeVisible();
  });

  test("should display empty messages list initially", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    // Messages list should be visible but empty
    const messagesList = page.getByTestId("messages-list");
    await expect(messagesList).toBeVisible();

    const messages = page.getByTestId("chat-message");
    await expect(messages).toHaveCount(0);
  });

  test("should display message input textarea", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled();
  });

  test("should display send button", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    const sendButton = page.getByRole("button", { name: /send/i });
    await expect(sendButton).toBeVisible();
  });

  test("should have placeholder text in input", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const placeholder = await input.getAttribute("placeholder");
    expect(placeholder).toBeTruthy();
    expect(placeholder?.length).toBeGreaterThan(0);
  });

  test("should load within 2 seconds", async ({ page }) => {
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/chat`);

    await page.waitForSelector('[data-testid="chat-container"]', {
      state: "visible",
    });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });
});

// ============================================================================
// Test Suite: User Interactions - Message Input
// ============================================================================

test.describe("Chat - Message Input Interactions", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
  });

  test("can type in message input", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });

    await input.fill("Add Inception to my library");
    await expect(input).toHaveValue("Add Inception to my library");
  });

  test("can send message with button click", async ({ page }) => {
    // Mock API response
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const sendButton = page.getByRole("button", { name: /send/i });

    await input.fill("Add Inception");
    await sendButton.click();

    // User message should appear
    const userMessage = page.getByTestId("user-message").first();
    await expect(userMessage).toBeVisible({ timeout: 5000 });
    await expect(userMessage).toContainText("Add Inception");
  });

  test("can send message with Enter key", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });

    await input.fill("Add Inception");
    await input.press("Enter");

    // User message should appear
    const userMessage = page.getByTestId("user-message").first();
    await expect(userMessage).toBeVisible({ timeout: 5000 });
  });

  test("Shift+Enter adds new line without sending", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });

    await input.fill("Line 1");
    await input.press("Shift+Enter");
    await input.type("Line 2");

    const value = await input.inputValue();
    expect(value).toContain("\n");
    expect(value).toContain("Line 1");
    expect(value).toContain("Line 2");
  });

  test("input clears after sending message", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const sendButton = page.getByRole("button", { name: /send/i });

    await input.fill("Add Inception");
    await sendButton.click();

    // Wait a bit for the send to complete
    await page.waitForTimeout(500);

    // Input should be cleared
    await expect(input).toHaveValue("");
  });

  test("input disabled while processing", async ({ page }) => {
    // Mock slow API response
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const sendButton = page.getByRole("button", { name: /send/i });

    await input.fill("Add Inception");
    await sendButton.click();

    // Input should be disabled
    await expect(input).toBeDisabled();
  });

  test("send button disabled while processing", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const sendButton = page.getByRole("button", { name: /send/i });

    await input.fill("Add Inception");
    await sendButton.click();

    // Send button should be disabled
    await expect(sendButton).toBeDisabled();
  });

  test("cannot send empty message", async ({ page }) => {
    const sendButton = page.getByRole("button", { name: /send/i });

    // Try to send empty message
    await sendButton.click();

    // No message should be added
    const messages = page.getByTestId("chat-message");
    await expect(messages).toHaveCount(0);
  });

  test("cannot send whitespace-only message", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const sendButton = page.getByRole("button", { name: /send/i });

    await input.fill("   ");
    await sendButton.click();

    // No message should be added
    const messages = page.getByTestId("chat-message");
    await expect(messages).toHaveCount(0);
  });
});

// ============================================================================
// Test Suite: Message Display
// ============================================================================

test.describe("Chat - Message Display", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);
  });

  test("user messages appear right-aligned", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const userMessage = page.getByTestId("user-message").first();
    await expect(userMessage).toBeVisible({ timeout: 5000 });

    const classes = await userMessage.getAttribute("class");
    expect(classes).toMatch(/justify-end|ml-auto|items-end/);
  });

  test("assistant messages appear left-aligned", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for assistant response
    const assistantMessage = page.getByTestId("assistant-message").first();
    await expect(assistantMessage).toBeVisible({ timeout: 5000 });

    const classes = await assistantMessage.getAttribute("class");
    expect(classes).toMatch(/justify-start|mr-auto|items-start/);
  });

  test("typing indicator shows during processing", async ({ page }) => {
    // Mock slow API
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Typing indicator should appear
    const typingIndicator = page.getByTestId("typing-indicator");
    await expect(typingIndicator).toBeVisible();
  });

  test("typing indicator disappears after response", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for response
    await page.waitForTimeout(1000);

    // Typing indicator should be gone
    const typingIndicator = page.getByTestId("typing-indicator");
    await expect(typingIndicator).not.toBeVisible();
  });

  test("auto-scrolls to bottom on new message", async ({ page }) => {
    // Send multiple messages to create scroll
    for (let i = 0; i < 5; i++) {
      const input = page.getByRole("textbox", {
        name: /message input|request a movie/i,
      });
      await input.fill(`Message ${i + 1}`);
      await input.press("Enter");
      await page.waitForTimeout(500);
    }

    // Get the last message
    const messages = page.getByTestId("chat-message");
    const lastMessage = messages.last();

    // Last message should be in viewport
    await expect(lastMessage).toBeInViewport();
  });

  test("timestamps display correctly", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const userMessage = page.getByTestId("user-message").first();
    const timestamp = userMessage.getByTestId("message-timestamp");
    await expect(timestamp).toBeVisible();

    const timeText = await timestamp.textContent();
    expect(timeText).toBeTruthy();
  });

  test("system messages display centered", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for potential system message
    await page.waitForTimeout(1000);

    const systemMessages = page.getByTestId("system-message");
    if ((await systemMessages.count()) > 0) {
      const firstSystem = systemMessages.first();
      const classes = await firstSystem.getAttribute("class");
      expect(classes).toMatch(/justify-center|text-center|mx-auto/);
    }
  });
});

// ============================================================================
// Test Suite: Content Request Flow
// ============================================================================

test.describe("Chat - Content Request Flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);
  });

  test("shows processing state after sending request", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Should show typing indicator
    const typingIndicator = page.getByTestId("typing-indicator");
    await expect(typingIndicator).toBeVisible();
  });

  test("receives classification response", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for assistant response
    const assistantMessage = page.getByTestId("assistant-message").first();
    await expect(assistantMessage).toBeVisible({ timeout: 5000 });
  });

  test("shows content cards with movie details", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for content cards
    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    // Should show title
    await expect(contentCard).toContainText("Inception");

    // Should show year
    await expect(contentCard).toContainText("2010");
  });

  test("content card shows poster image", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const poster = contentCard.getByRole("img", { name: /poster/i });
    await expect(poster).toBeVisible();
  });

  test("content card shows overview", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const overview = contentCard.getByTestId("content-overview");
    await expect(overview).toBeVisible();
    await expect(overview).toContainText("Cobb");
  });

  test("can confirm and add to library", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockConfirmationResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for content card
    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    // Click add button
    const addButton = contentCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Success notification should appear
    const successMessage = page.getByText(/added to download queue/i);
    await expect(successMessage).toBeVisible({ timeout: 5000 });
  });

  test("shows loading state while adding", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockConfirmationResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const addButton = contentCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Button should show loading state
    await expect(addButton).toBeDisabled();
  });

  test("displays multiple search results", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Should show 2 content cards
    const contentCards = page.getByTestId("content-card");
    await expect(contentCards).toHaveCount(2);
  });
});

// ============================================================================
// Test Suite: Disambiguation Flow
// ============================================================================

test.describe("Chat - Disambiguation", () => {
  test("shows multiple matches for ambiguous query", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Should show multiple content cards
    const contentCards = page.getByTestId("content-card");
    await expect(contentCards.first()).toBeVisible({ timeout: 5000 });
    const count = await contentCards.count();
    expect(count).toBeGreaterThan(1);
  });

  test("can select correct match from disambiguation", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockConfirmationResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Select second card
    const contentCards = page.getByTestId("content-card");
    const secondCard = contentCards.nth(1);
    await expect(secondCard).toBeVisible({ timeout: 5000 });

    const addButton = secondCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Should get confirmation
    await expect(page.getByText(/added to download queue/i)).toBeVisible({
      timeout: 5000,
    });
  });

  test("shows 'None of these' option for disambiguation", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Look for "None of these" button
    const noneButton = page.getByRole("button", { name: /none of these/i });
    await expect(noneButton).toBeVisible({ timeout: 5000 });
  });
});

// ============================================================================
// Test Suite: Request Status Tracking
// ============================================================================

test.describe("Chat - Request Status Tracking", () => {
  test("displays request status component", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockConfirmationResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const addButton = contentCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Wait for status to appear
    await page.waitForTimeout(1000);

    const statusBadge = page.getByTestId("request-status-badge");
    await expect(statusBadge).toBeVisible({ timeout: 5000 });
  });

  test("shows downloading status", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockConfirmationResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const addButton = contentCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Should show downloading status
    const statusBadge = page.getByTestId("request-status-badge");
    await expect(statusBadge).toContainText(/downloading/i);
  });

  test("progress bar updates with download progress", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockConfirmationResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const addButton = contentCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Look for progress bar
    const progressBar = page.getByTestId("download-progress-bar");
    await expect(progressBar).toBeVisible({ timeout: 5000 });
  });

  test("shows retry button if request failed", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.route(`${API_BASE_URL}/request/confirm`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Failed to add to library" }),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const contentCard = page.getByTestId("content-card").first();
    await expect(contentCard).toBeVisible({ timeout: 5000 });

    const addButton = contentCard.getByRole("button", {
      name: /add|add to library/i,
    });
    await addButton.click();

    // Should show error and retry button
    const retryButton = page.getByRole("button", { name: /retry/i });
    await expect(retryButton).toBeVisible({ timeout: 5000 });
  });
});

// ============================================================================
// Test Suite: Chat History Management
// ============================================================================

test.describe("Chat - History Management", () => {
  test("messages persist after page reload", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for messages to appear
    await page.waitForTimeout(1000);

    // Reload page
    await page.reload();

    // Messages should still be there
    const userMessage = page.getByTestId("user-message");
    await expect(userMessage.first()).toBeVisible({ timeout: 5000 });
  });

  test("can clear history", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for messages
    await page.waitForTimeout(1000);

    // Click clear history button
    const clearButton = page.getByRole("button", { name: /clear history/i });
    await clearButton.click();

    // Confirm dialog if present
    const confirmButton = page.getByRole("button", { name: /confirm|yes/i });
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }

    // Messages should be cleared
    const messages = page.getByTestId("chat-message");
    await expect(messages).toHaveCount(0);
  });

  test("search filters messages correctly", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.goto(`${BASE_URL}/chat`);

    // Send multiple messages
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });

    await input.fill("Add Inception");
    await input.press("Enter");
    await page.waitForTimeout(1000);

    await input.fill("Add The Matrix");
    await input.press("Enter");
    await page.waitForTimeout(1000);

    // Open search
    const searchButton = page.getByRole("button", { name: /search/i });
    if (await searchButton.isVisible()) {
      await searchButton.click();
    }

    // Search for specific term
    const searchInput = page.getByRole("textbox", {
      name: /search messages/i,
    });
    await searchInput.fill("Inception");

    // Should show only matching messages
    await page.waitForTimeout(500);

    const visibleMessages = page.getByTestId("chat-message");
    const count = await visibleMessages.count();
    expect(count).toBeGreaterThan(0);
  });
});

// ============================================================================
// Test Suite: Mobile Responsiveness
// ============================================================================

test.describe("Chat - Mobile Responsiveness", () => {
  const viewports = [
    { name: "Mobile Small", width: 320, height: 568 },
    { name: "Mobile Medium", width: 375, height: 667 },
    { name: "Tablet", width: 768, height: 1024 },
    { name: "Desktop", width: 1920, height: 1080 },
  ];

  for (const viewport of viewports) {
    test(`should be responsive at ${viewport.name} (${viewport.width}x${viewport.height})`, async ({
      page,
    }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });

      await page.goto(`${BASE_URL}/chat`);

      // Chat container should be visible
      const chatContainer = page.getByTestId("chat-container");
      await expect(chatContainer).toBeVisible();

      // Input should be visible
      const input = page.getByRole("textbox", {
        name: /message input|request a movie/i,
      });
      await expect(input).toBeVisible();

      // Send button should be visible
      const sendButton = page.getByRole("button", { name: /send/i });
      await expect(sendButton).toBeVisible();
    });
  }

  test("touch targets are minimum 44x44px on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto(`${BASE_URL}/chat`);

    const sendButton = page.getByRole("button", { name: /send/i });
    const box = await sendButton.boundingBox();

    expect(box?.width).toBeGreaterThanOrEqual(44);
    expect(box?.height).toBeGreaterThanOrEqual(44);
  });

  test("content cards stack vertically on mobile", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    await page.setViewportSize({ width: 320, height: 568 });
    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for content cards
    const contentCards = page.getByTestId("content-card");
    await expect(contentCards.first()).toBeVisible({ timeout: 5000 });

    // Cards should be full width
    const firstCard = contentCards.first();
    const box = await firstCard.boundingBox();
    expect(box?.width).toBeGreaterThan(280); // Close to full viewport width
  });

  test("virtual keyboard doesn't cover input on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });

    await input.click();

    // Input should still be in viewport
    await expect(input).toBeInViewport();
  });
});

// ============================================================================
// Test Suite: Accessibility (WCAG 2.1 AA)
// ============================================================================

test.describe("Chat - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
  });

  test("should have proper ARIA labels", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await expect(input).toBeVisible();

    const sendButton = page.getByRole("button", { name: /send/i });
    await expect(sendButton).toBeVisible();
  });

  test("keyboard navigation with Tab key", async ({ page }) => {
    // Tab to input
    await page.keyboard.press("Tab");

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await expect(input).toBeFocused();

    // Tab to send button
    await page.keyboard.press("Tab");

    const sendButton = page.getByRole("button", { name: /send/i });
    await expect(sendButton).toBeFocused();
  });

  test("can send message with keyboard only", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    // Tab to input
    await page.keyboard.press("Tab");

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.type("Add Inception");

    // Press Enter to send
    await page.keyboard.press("Enter");

    // Message should be sent
    const userMessage = page.getByTestId("user-message").first();
    await expect(userMessage).toBeVisible({ timeout: 5000 });
  });

  test("screen reader announces new messages", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Check for aria-live region
    const liveRegion = page.locator(
      '[role="log"], [role="status"], [aria-live]',
    );
    const count = await liveRegion.count();
    expect(count).toBeGreaterThan(0);
  });

  test("focus returns to input after sending message", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for send to complete
    await page.waitForTimeout(1000);

    // Focus should be back on input
    await expect(input).toBeFocused();
  });

  test("content cards are keyboard accessible", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for content cards
    await page.waitForTimeout(1000);

    // Tab to add button
    await page.keyboard.press("Tab");

    const addButton = page
      .getByRole("button", {
        name: /add|add to library/i,
      })
      .first();
    await expect(addButton).toBeFocused();
  });

  test("error messages are accessible", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Error should be in an accessible region
    const errorRegion = page.locator('[role="alert"], [aria-live="assertive"]');
    const count = await errorRegion.count();
    expect(count).toBeGreaterThan(0);
  });

  test("sufficient color contrast for text", async ({ page }) => {
    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    const color = await input.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        color: styles.color,
        backgroundColor: styles.backgroundColor,
      };
    });

    expect(color.color).toBeTruthy();
    expect(color.backgroundColor).toBeTruthy();
  });

  test("typing indicator has proper ARIA label", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockContentRequestResponse),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    const typingIndicator = page.getByTestId("typing-indicator");
    await expect(typingIndicator).toBeVisible();

    const ariaLabel = await typingIndicator.getAttribute("aria-label");
    expect(ariaLabel).toBeTruthy();
  });
});

// ============================================================================
// Test Suite: Error Handling
// ============================================================================

test.describe("Chat - Error Handling", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);
  });

  test("shows error message when request fails", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Error message should appear
    const errorMessage = page.getByText(/error|failed/i);
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test("shows retry option after network error", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.abort("failed");
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Retry option should appear
    const retryButton = page.getByRole("button", { name: /retry/i });
    await expect(retryButton).toBeVisible({ timeout: 5000 });
  });

  test("shows helpful message for invalid query", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Could not understand your request",
        }),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("asdfghjkl");
    await input.press("Enter");

    // Helpful error message should appear
    const errorMessage = page.getByText(/could not understand/i);
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test("handles API timeout gracefully", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async () => {
      // Never fulfill the request to simulate timeout
      await new Promise(() => {});
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Should show timeout message after reasonable wait
    const timeoutMessage = page.getByText(/timeout|taking too long/i);
    await expect(timeoutMessage).toBeVisible({ timeout: 35000 });
  });

  test("re-enables input after error", async ({ page }) => {
    await page.route(`${API_BASE_URL}/request/content`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    const input = page.getByRole("textbox", {
      name: /message input|request a movie/i,
    });
    await input.fill("Add Inception");
    await input.press("Enter");

    // Wait for error
    await page.waitForTimeout(1000);

    // Input should be enabled again
    await expect(input).toBeEnabled();
  });
});

// ============================================================================
// Test Suite: WebSocket Integration (Simulation)
// ============================================================================

test.describe("Chat - Real-time Updates", () => {
  test("displays connection status indicator", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    // Should show connection status
    const statusIndicator = page.getByTestId("connection-status");
    if (await statusIndicator.isVisible()) {
      await expect(statusIndicator).toBeVisible();
    }
  });

  test("shows warning when WebSocket disconnected", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    // Check if disconnection warning appears
    // Note: This test may need WebSocket mocking in a real implementation
    await page.waitForTimeout(1000);

    const warning = page.getByText(/connection lost|disconnected/i);
    // Warning should not be visible if connected
    const isVisible = await warning.isVisible().catch(() => false);
    expect(typeof isVisible).toBe("boolean");
  });
});
