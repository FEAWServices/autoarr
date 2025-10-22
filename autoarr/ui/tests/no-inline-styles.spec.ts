import { test, expect } from "@playwright/test";
import { glob } from "glob";
import { readFileSync } from "fs";
import { join } from "path";

test.describe("No Inline Styles Policy", () => {
  test("should not have inline style attributes in TSX/JSX files", async () => {
    // Find all TSX/JSX files
    const files = await glob("src/**/*.{tsx,jsx}", { cwd: process.cwd() });

    const filesWithInlineStyles: string[] = [];
    const inlineStylePattern = /style={{|style=\{/g;

    for (const file of files) {
      const content = readFileSync(join(process.cwd(), file), "utf-8");

      if (inlineStylePattern.test(content)) {
        filesWithInlineStyles.push(file);
      }
    }

    if (filesWithInlineStyles.length > 0) {
      const errorMessage = `Found inline styles in the following files:\n${filesWithInlineStyles
        .map((f) => `  - ${f}`)
        .join(
          "\n",
        )}\n\nPlease use Tailwind CSS classes or CSS modules instead of inline styles.`;

      expect(filesWithInlineStyles, errorMessage).toHaveLength(0);
    }
  });

  test("should not have style tags in TSX/JSX files", async () => {
    const files = await glob("src/**/*.{tsx,jsx}", { cwd: process.cwd() });

    const filesWithStyleTags: string[] = [];
    const styleTagPattern = /<style[^>]*>/gi;

    for (const file of files) {
      const content = readFileSync(join(process.cwd(), file), "utf-8");

      if (styleTagPattern.test(content)) {
        filesWithStyleTags.push(file);
      }
    }

    if (filesWithStyleTags.length > 0) {
      const errorMessage = `Found <style> tags in the following files:\n${filesWithStyleTags
        .map((f) => `  - ${f}`)
        .join("\n")}\n\nPlease use external CSS files instead of <style> tags.`;

      expect(filesWithStyleTags, errorMessage).toHaveLength(0);
    }
  });
});
