/**
 * Unit tests for AISetupStep model selection
 *
 * Regression tests to ensure model selection has visible visual feedback
 * Bug: Selected model had nearly invisible styling
 * Fix: Added stronger contrast with bg-primary/20, ring-2, shadow-md
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

// Mock the onboarding store
const mockStore = {
  previousStep: vi.fn(),
  nextStep: vi.fn(),
  skipStep: vi.fn(),
  markAIConfigured: vi.fn(),
  joinWaitlist: vi.fn(),
  isOnWaitlist: false,
  isLoading: false,
};

vi.mock('../../../stores/onboardingStore', () => ({
  useOnboardingStore: () => mockStore,
}));

// Import component after mocking
const { AISetupStep } = await import('../../pages/Onboarding/steps/AISetupStep');

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('AISetupStep Model Selection - Regression', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.isLoading = false;
    mockStore.isOnWaitlist = false;
  });

  describe('Model Selection Visual Feedback', () => {
    it('should render model selector with default Gemini selected', () => {
      renderWithRouter(<AISetupStep />);

      const modelSelector = screen.getByTestId('model-selector');
      expect(modelSelector).toBeInTheDocument();

      // Gemini should be the default selected option
      const geminiOption = screen.getByTestId('model-option-google');
      expect(geminiOption).toBeInTheDocument();
    });

    it('selected model should have visible selection classes', () => {
      renderWithRouter(<AISetupStep />);

      // Default selected model is Gemini
      const geminiOption = screen.getByTestId('model-option-google');

      // Check for the key selection styling classes
      // These are the classes we added to fix the visibility bug
      expect(geminiOption.className).toContain('border-primary');
      expect(geminiOption.className).toContain('bg-primary');
      expect(geminiOption.className).toContain('ring-2');
      expect(geminiOption.className).toContain('shadow-md');
    });

    it('unselected model should NOT have selection classes', () => {
      renderWithRouter(<AISetupStep />);

      // Claude is not the default, so it should not have selection styling
      const claudeOption = screen.getByTestId('model-option-anthropic');

      // Should NOT have the selection classes
      expect(claudeOption.className).not.toContain('ring-2');
      expect(claudeOption.className).not.toContain('shadow-md');
      // Should have the unselected border style
      expect(claudeOption.className).toContain('border-border');
    });

    it('clicking a model should update selection styling', () => {
      renderWithRouter(<AISetupStep />);

      const geminiOption = screen.getByTestId('model-option-google');
      const claudeOption = screen.getByTestId('model-option-anthropic');

      // Initially Gemini is selected
      expect(geminiOption.className).toContain('ring-2');
      expect(claudeOption.className).not.toContain('ring-2');

      // Click Claude to select it
      fireEvent.click(claudeOption);

      // Now Claude should have selection styling
      expect(claudeOption.className).toContain('border-primary');
      expect(claudeOption.className).toContain('bg-primary');
      expect(claudeOption.className).toContain('ring-2');
      expect(claudeOption.className).toContain('shadow-md');

      // Gemini should lose selection styling
      expect(geminiOption.className).not.toContain('ring-2');
      expect(geminiOption.className).not.toContain('shadow-md');
    });
  });

  describe('Radio Button Indicator Visual Feedback', () => {
    it('selected model radio indicator should have filled background', () => {
      renderWithRouter(<AISetupStep />);

      const geminiOption = screen.getByTestId('model-option-google');

      // Find the radio indicator - it's the first rounded-full div inside the button
      const radioIndicator = geminiOption.querySelector('div.rounded-full');
      expect(radioIndicator).toBeInTheDocument();

      // Should have bg-primary for filled appearance
      expect(radioIndicator?.className).toContain('bg-primary');
      expect(radioIndicator?.className).toContain('border-primary');
    });

    it('unselected model radio indicator should NOT be filled', () => {
      renderWithRouter(<AISetupStep />);

      const claudeOption = screen.getByTestId('model-option-anthropic');

      // Find the radio indicator
      const radioIndicator = claudeOption.querySelector('div.rounded-full');
      expect(radioIndicator).toBeInTheDocument();

      // Should NOT have bg-primary (not filled)
      expect(radioIndicator?.className).not.toContain('bg-primary');
      // Should have muted border
      expect(radioIndicator?.className).toContain('border-muted-foreground');
    });

    it('radio indicator should contain white dot when selected', () => {
      renderWithRouter(<AISetupStep />);

      const geminiOption = screen.getByTestId('model-option-google');

      // The inner white dot is the second rounded-full div
      const innerDots = geminiOption.querySelectorAll('div.rounded-full');

      // Should have at least 2 rounded-full elements (radio + inner dot)
      expect(innerDots.length).toBeGreaterThanOrEqual(2);

      // The inner dot should have bg-white
      const innerDot = innerDots[1];
      expect(innerDot?.className).toContain('bg-white');
    });
  });

  describe('Model Selection Functionality', () => {
    it('should have three model options', () => {
      renderWithRouter(<AISetupStep />);

      expect(screen.getByTestId('model-option-google')).toBeInTheDocument();
      expect(screen.getByTestId('model-option-meta-llama')).toBeInTheDocument();
      expect(screen.getByTestId('model-option-anthropic')).toBeInTheDocument();
    });

    it('clicking model should not trigger form submission', () => {
      renderWithRouter(<AISetupStep />);

      const claudeOption = screen.getByTestId('model-option-anthropic');

      // Should be a button element
      expect(claudeOption.tagName.toLowerCase()).toBe('button');

      // Should have type="button" to prevent form submission
      expect(claudeOption.getAttribute('type')).toBe('button');
    });
  });
});

describe('AISetupStep API Key Input', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have API key input field', () => {
    renderWithRouter(<AISetupStep />);

    const apiKeyInput = screen.getByTestId('openrouter-api-key-input');
    expect(apiKeyInput).toBeInTheDocument();
    expect(apiKeyInput).toHaveAttribute('type', 'password');
  });

  it('test connection button should be disabled without API key', () => {
    renderWithRouter(<AISetupStep />);

    const testButton = screen.getByTestId('test-connection-button');
    expect(testButton).toBeDisabled();
  });

  it('skip button should be present', () => {
    renderWithRouter(<AISetupStep />);

    const skipButton = screen.getByTestId('skip-ai-button');
    expect(skipButton).toBeInTheDocument();
  });
});
