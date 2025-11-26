import { describe, it, expect, beforeEach } from "vitest";
import { useThemeStore } from "../../stores/themeStore";

describe("themeStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useThemeStore.setState({ isDarkMode: false });
  });

  it("should have initial state", () => {
    const { isDarkMode } = useThemeStore.getState();
    expect(isDarkMode).toBe(false);
  });

  it("should toggle dark mode", () => {
    const { toggleDarkMode } = useThemeStore.getState();

    // Initially light mode (from beforeEach reset)
    expect(useThemeStore.getState().isDarkMode).toBe(false);

    // Toggle to dark
    toggleDarkMode();
    expect(useThemeStore.getState().isDarkMode).toBe(true);

    // Toggle back to light
    toggleDarkMode();
    expect(useThemeStore.getState().isDarkMode).toBe(false);
  });

  it("should set dark mode directly", () => {
    const { setDarkMode } = useThemeStore.getState();

    setDarkMode(true);
    expect(useThemeStore.getState().isDarkMode).toBe(true);

    setDarkMode(false);
    expect(useThemeStore.getState().isDarkMode).toBe(false);
  });
});
