/**
 * Onboarding Wizard Container
 *
 * Main component that orchestrates the onboarding flow, displaying
 * the appropriate step component and handling navigation.
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useOnboardingStore, ONBOARDING_STEPS, type OnboardingStep } from '../../stores/onboardingStore';
import { ProgressIndicator } from '../../components/Onboarding/ProgressIndicator';
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

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Redirect to home if onboarding is already complete
  useEffect(() => {
    if (completed && currentStep === 'complete') {
      const timer = setTimeout(() => {
        navigate('/');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [completed, currentStep, navigate]);

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
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <span className="text-primary text-xl font-bold">A</span>
              </div>
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
          />
        </div>
      </header>

      {/* Main content area - scrollable */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8 pb-16">
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
        </div>
      </main>
    </div>
  );
};

export default Onboarding;
