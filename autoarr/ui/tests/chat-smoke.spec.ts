/**
 * Chat Interface Smoke Tests
 * Quick verification that the chat interface is working
 */

import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:3003";

test.describe("Chat - Smoke Tests", () => {
  test("should load chat page successfully", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    // Check that page loads
    const chatContainer = page.getByTestId("chat-container");
    await expect(chatContainer).toBeVisible({ timeout: 10000 });
  });

  test("should display chat interface elements", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    // Verify key elements are present
    await expect(page.getByTestId("chat-container")).toBeVisible();
    await expect(page.getByTestId("messages-list")).toBeVisible();
    await expect(
      page.getByRole("textbox", { name: /message input/i }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /send/i })).toBeVisible();
  });

  test("should be able to type in input", async ({ page }) => {
    await page.goto(`${BASE_URL}/chat`);

    const input = page.getByRole("textbox", { name: /message input/i });
    await input.fill("Test message");
    await expect(input).toHaveValue("Test message");
  });
});
