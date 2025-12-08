/**
 * Chat Interface Smoke Tests
 * Quick verification that the chat interface is working
 *
 * Note: Chat is now the home page (/) instead of a separate /chat route.
 */

import { test, expect } from "@playwright/test";

test.describe("Home (Chat) - Smoke Tests", () => {
  test("should load home page successfully", async ({ page }) => {
    await page.goto("/");

    // Check that page loads
    const chatContainer = page.getByTestId("chat-container");
    await expect(chatContainer).toBeVisible({ timeout: 10000 });
  });

  test("should display chat interface elements", async ({ page }) => {
    await page.goto("/");

    // Verify key elements are present
    await expect(page.getByTestId("chat-container")).toBeVisible();
    await expect(page.getByTestId("messages-list")).toBeVisible();
    await expect(
      page.getByRole("textbox", { name: /message input/i }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /send/i })).toBeVisible();
  });

  test("should be able to type in input", async ({ page }) => {
    await page.goto("/");

    const input = page.getByRole("textbox", { name: /message input/i });
    await input.fill("Test message");
    await expect(input).toHaveValue("Test message");
  });
});
