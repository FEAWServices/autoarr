import { test, expect } from "@playwright/test";

test("should uncheck enabled checkbox and save settings without error", async ({
  page,
}) => {
  // Navigate to settings page
  await page.goto("http://localhost:8088/settings");

  // Wait for page to load and settings heading to appear
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();

  // Wait for settings form to render - check for SABnzbd section
  await expect(page.getByText("SABnzbd")).toBeVisible();

  // Find the first enabled checkbox by label association
  const enabledCheckbox = page
    .getByRole("checkbox", { name: /enabled/i })
    .first();

  // Wait for checkbox to be visible
  await expect(enabledCheckbox).toBeVisible();

  // Uncheck it if it's checked
  if (await enabledCheckbox.isChecked()) {
    await enabledCheckbox.uncheck();
  }

  // Verify it's unchecked
  await expect(enabledCheckbox).not.toBeChecked();

  // Find and click the "Save Settings" button
  const saveButton = page.getByRole("button", { name: /save settings/i });

  // Click save
  await saveButton.click();

  // Wait a moment for the save to complete
  await page.waitForTimeout(2000);

  // Check that we didn't get an error state
  // The button should be re-enabled after save completes
  await expect(saveButton).toBeEnabled();

  // Optionally check for success indicator
  // This would depend on your UI implementation (toast, message, etc.)

  console.log(
    "✅ Test passed: Checkbox unchecked and settings saved without error",
  );
});
