/**
 * Onboarding Wizard Container
 *
 * Main component that orchestrates the onboarding flow, displaying
 * the appropriate step component and handling navigation.
 */

import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useOnboardingStore, ONBOARDING_STEPS, type OnboardingStep } from '../../stores/onboardingStore';
import { ProgressIndicator } from '../../components/Onboarding/ProgressIndicator';
import { PullToRefresh } from '../../components/PullToRefresh';
import { WelcomeStep } from './steps/WelcomeStep';
import { AISetupStep } from './steps/AISetupStep';
import { ServiceSelectionStep } from './steps/ServiceSelectionStep';
import { ServiceConfigStep } from './steps/ServiceConfigStep';
import { CompleteStep } from './steps/CompleteStep';
import { servicePlugins } from '../../plugins/services';

/**
 * Map step names to components
 */
const stepComponents: Record<OnboardingStep, React.ComponentType> = {
  welcome: WelcomeStep,
  ai_setup: AISetupStep,
  service_selection: ServiceSelectionStep,
  service_config: ServiceConfigStep,
  complete: CompleteStep,
};

/**
 * Step labels for display
 */
const stepLabels: Record<OnboardingStep, string> = {
  welcome: 'Welcome',
  ai_setup: 'AI Setup',
  service_selection: 'Services',
  service_config: 'Configure',
  complete: 'Complete',
};

export const Onboarding = () => {
  const navigate = useNavigate();
  const {
    completed,
    currentStep,
    isInitializing,
    error,
    fetchStatus,
    clearError,
    goToStep,
  } = useOnboardingStore();

  // Initialize service config statuses when component mounts
  useEffect(() => {
    useOnboardingStore.setState({
      serviceConfigStatuses: servicePlugins.map((p) => ({
        id: p.id,
        name: p.name,
        selected: false,
        configured: false,
      })),
    });
  }, []);

  // Track if user completed onboarding during THIS session (not loaded from API)
  const [completedThisSession, setCompletedThisSession] = useState(false);

  // Track if we've already checked for AI auto-skip (to prevent loops)
  const [aiAutoSkipChecked, setAiAutoSkipChecked] = useState(false);

  // Fetch status on mount, and reset if already complete (to allow re-running wizard)
  useEffect(() => {
    const initOnboarding = async () => {
      await fetchStatus();
      // Check if onboarding is already complete - if so, reset to allow re-running
      const state = useOnboardingStore.getState();
      if (state.completed && state.currentStep === 'complete') {
        // Reset so user can re-run the wizard
        await useOnboardingStore.getState().resetOnboarding();
      }
    };
    initOnboarding();
  }, [fetchStatus]);

  // Auto-skip AI step if already configured
  useEffect(() => {
    const checkAIAndAutoSkip = async () => {
      // Only check once when reaching ai_setup step
      if (currentStep !== 'ai_setup' || aiAutoSkipChecked) {
        return;
      }

      setAiAutoSkipChecked(true);

      try {
        const response = await fetch('/api/v1/settings/llm');
        if (response.ok) {
          const data = await response.json();
          // If AI is already connected, auto-skip to service selection
          if (data.status === 'connected' && data.selected_model) {
            // Mark AI as configured in store
            await useOnboardingStore.getState().markAIConfigured();
            // Skip to next step
            await goToStep('service_selection');
          }
        }
      } catch (error) {
        console.error('Failed to check LLM status for auto-skip:', error);
      }
    };

    checkAIAndAutoSkip();
  }, [currentStep, aiAutoSkipChecked, goToStep]);

  // Handle step click from progress indicator
  const handleStepClick = useCallback((stepId: string) => {
    goToStep(stepId as OnboardingStep);
    // Reset the AI auto-skip check if navigating back to ai_setup
    // This allows the user to stay on the page if they manually navigate there
    if (stepId === 'ai_setup') {
      setAiAutoSkipChecked(true); // Keep it true so we don't auto-skip when user manually goes back
    }
  }, [goToStep]);

  // Redirect to home after user completes the wizard during this session
  useEffect(() => {
    if (completedThisSession && completed && currentStep === 'complete') {
      const timer = setTimeout(() => {
        navigate('/');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [completedThisSession, completed, currentStep, navigate]);

  // Listen for completion during this session
  useEffect(() => {
    const unsubscribe = useOnboardingStore.subscribe((state, prevState) => {
      // Detect when user completes onboarding (transition to complete)
      if (state.completed && state.currentStep === 'complete' &&
          (!prevState.completed || prevState.currentStep !== 'complete')) {
        setCompletedThisSession(true);
      }
    });
    return unsubscribe;
  }, []);

  // Handle pull-to-refresh - reload the page to refresh all state
  const handleRefresh = useCallback(async () => {
    // Reload the window to get fresh state
    window.location.reload();
  }, []);

  // Loading state - only show during initial fetch, not during navigation
  if (isInitializing) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--main-bg)' }}
      >
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Get current step component
  const StepComponent = stepComponents[currentStep];
  const currentStepIndex = ONBOARDING_STEPS.indexOf(currentStep);

  return (
    <div
      className="h-screen flex flex-col overflow-hidden"
      style={{ backgroundColor: 'var(--main-bg)' }}
      data-testid="onboarding-container"
    >
      {/* Header with progress */}
      <header className="flex-shrink-0 border-b border-border/50 bg-card/50 backdrop-blur-sm z-10">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <img src="/logo-192.png" alt="AutoArr Logo" className="w-10 h-10 object-contain" />
              <div>
                <h1 className="text-lg font-bold text-foreground">AutoArr</h1>
                <p className="text-xs text-muted-foreground">Setup Wizard</p>
              </div>
            </div>
            <div className="text-sm text-muted-foreground">
              Step {currentStepIndex + 1} of {ONBOARDING_STEPS.length}
            </div>
          </div>

          {/* Progress indicator */}
          <ProgressIndicator
            steps={ONBOARDING_STEPS.map((step) => ({
              id: step,
              label: stepLabels[step],
            }))}
            currentStep={currentStep}
            onStepClick={handleStepClick}
          />
        </div>
      </header>

      {/* Main content area - scrollable with pull-to-refresh on mobile */}
      <PullToRefresh
        onRefresh={handleRefresh}
        className="flex-1 min-h-0 pb-safe"
      >
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 pb-24">
          {/* Error display */}
          {error && (
            <div
              className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-500"
              role="alert"
            >
              <div className="flex items-center justify-between">
                <p>{error}</p>
                <button
                  onClick={clearError}
                  className="text-red-500/70 hover:text-red-500"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Current step component */}
          <StepComponent />
        </main>
      </PullToRefresh>
    </div>
  );
};

export default Onboarding;
