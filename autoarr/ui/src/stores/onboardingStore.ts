/**
 * AutoArr Onboarding Store
 *
 * Zustand store for managing onboarding wizard state with API persistence.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

/**
 * Onboarding steps in order
 */
export const ONBOARDING_STEPS = [
  'welcome',
  'ai_setup',
  'service_selection',
  'service_config',
  'complete',
] as const;

export type OnboardingStep = (typeof ONBOARDING_STEPS)[number];

/**
 * Service configuration status for each service during onboarding
 */
export interface ServiceConfigStatus {
  id: string;
  name: string;
  selected: boolean;
  configured: boolean;
  error?: string;
}

/**
 * Onboarding state shape
 */
interface OnboardingState {
  // Core state
  completed: boolean;
  currentStep: OnboardingStep;
  skippedSteps: OnboardingStep[];
  aiConfigured: boolean;
  servicesConfigured: string[];
  bannerDismissed: boolean;
  needsOnboarding: boolean;

  // Local UI state (not persisted to API)
  isLoading: boolean;
  error: string | null;
  selectedServices: string[];
  currentServiceIndex: number;
  serviceConfigStatuses: ServiceConfigStatus[];

  // Waitlist
  waitlistEmail: string | null;
  isOnWaitlist: boolean;
}

/**
 * Onboarding actions
 */
interface OnboardingActions {
  // API sync
  fetchStatus: () => Promise<void>;

  // Navigation
  goToStep: (step: OnboardingStep) => Promise<void>;
  nextStep: () => Promise<void>;
  previousStep: () => void;

  // Step completion
  skipStep: (step: OnboardingStep) => Promise<void>;
  markAIConfigured: () => Promise<void>;
  addConfiguredService: (service: string) => Promise<void>;
  completeOnboarding: () => Promise<void>;
  skipOnboarding: () => Promise<void>;

  // Service selection
  selectService: (serviceId: string, selected: boolean) => void;
  setSelectedServices: (services: string[]) => void;
  nextService: () => void;
  previousService: () => void;
  updateServiceConfigStatus: (serviceId: string, configured: boolean, error?: string) => void;

  // Banner
  dismissBanner: () => Promise<void>;

  // Reset
  resetOnboarding: () => Promise<void>;

  // Waitlist
  joinWaitlist: (email: string) => Promise<boolean>;
  checkWaitlistStatus: (email: string) => Promise<boolean>;

  // Clear error
  clearError: () => void;
}

type OnboardingStore = OnboardingState & OnboardingActions;

/**
 * API base URL for onboarding endpoints
 */
const API_BASE = '/api/v1/onboarding';

/**
 * Get the index of a step
 */
function getStepIndex(step: OnboardingStep): number {
  return ONBOARDING_STEPS.indexOf(step);
}

/**
 * Create the onboarding store
 */
export const useOnboardingStore = create<OnboardingStore>()(
  persist(
    (set, get) => ({
      // Initial state
      completed: false,
      currentStep: 'welcome',
      skippedSteps: [],
      aiConfigured: false,
      servicesConfigured: [],
      bannerDismissed: false,
      needsOnboarding: true,

      isLoading: false,
      error: null,
      selectedServices: [],
      currentServiceIndex: 0,
      serviceConfigStatuses: [],
      waitlistEmail: null,
      isOnWaitlist: false,

      /**
       * Fetch onboarding status from API
       */
      fetchStatus: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/status`);
          if (!response.ok) {
            throw new Error('Failed to fetch onboarding status');
          }
          const data = await response.json();
          set({
            completed: data.completed,
            currentStep: data.current_step as OnboardingStep,
            skippedSteps: data.skipped_steps as OnboardingStep[],
            aiConfigured: data.ai_configured,
            servicesConfigured: data.services_configured,
            bannerDismissed: data.banner_dismissed,
            needsOnboarding: data.needs_onboarding,
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Navigate to a specific step
       */
      goToStep: async (step: OnboardingStep) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/step`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ step }),
          });
          if (!response.ok) {
            throw new Error('Failed to update step');
          }
          set({ currentStep: step, isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Move to next step
       */
      nextStep: async () => {
        const { currentStep, goToStep, selectedServices } = get();
        const currentIndex = getStepIndex(currentStep);

        if (currentIndex < ONBOARDING_STEPS.length - 1) {
          const nextStepValue = ONBOARDING_STEPS[currentIndex + 1];

          // If moving to service_config, ensure we have selected services
          if (nextStepValue === 'service_config' && selectedServices.length === 0) {
            // Skip service_config if no services selected
            await goToStep('complete');
          } else {
            await goToStep(nextStepValue);
          }
        }
      },

      /**
       * Move to previous step
       */
      previousStep: () => {
        const { currentStep } = get();
        const currentIndex = getStepIndex(currentStep);

        if (currentIndex > 0) {
          const prevStep = ONBOARDING_STEPS[currentIndex - 1];
          set({ currentStep: prevStep });
        }
      },

      /**
       * Skip a step
       */
      skipStep: async (step: OnboardingStep) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/skip-step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ step }),
          });
          if (!response.ok) {
            throw new Error('Failed to skip step');
          }
          const { skippedSteps } = get();
          const newSkipped = [...skippedSteps];
          if (!newSkipped.includes(step)) {
            newSkipped.push(step);
          }
          set({ skippedSteps: newSkipped, isLoading: false });

          // Auto advance
          await get().nextStep();
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Mark AI as configured
       */
      markAIConfigured: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/ai-configured`, {
            method: 'POST',
          });
          if (!response.ok) {
            throw new Error('Failed to mark AI as configured');
          }
          set({ aiConfigured: true, isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Add a configured service
       */
      addConfiguredService: async (service: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/add-service`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service }),
          });
          if (!response.ok) {
            throw new Error('Failed to add service');
          }
          const { servicesConfigured } = get();
          const newServices = [...servicesConfigured];
          if (!newServices.includes(service)) {
            newServices.push(service);
          }
          set({ servicesConfigured: newServices, isLoading: false });

          // Update config status
          get().updateServiceConfigStatus(service, true);
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
          get().updateServiceConfigStatus(
            service,
            false,
            error instanceof Error ? error.message : 'Unknown error'
          );
        }
      },

      /**
       * Complete onboarding
       */
      completeOnboarding: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/complete`, {
            method: 'POST',
          });
          if (!response.ok) {
            throw new Error('Failed to complete onboarding');
          }
          set({
            completed: true,
            currentStep: 'complete',
            needsOnboarding: false,
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Skip entire onboarding
       */
      skipOnboarding: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/skip`, {
            method: 'POST',
          });
          if (!response.ok) {
            throw new Error('Failed to skip onboarding');
          }
          set({
            completed: true,
            currentStep: 'complete',
            skippedSteps: ['welcome', 'ai_setup', 'service_selection', 'service_config'],
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Select/deselect a service
       */
      selectService: (serviceId: string, selected: boolean) => {
        const { selectedServices, serviceConfigStatuses } = get();
        let newServices: string[];

        if (selected) {
          newServices = [...selectedServices, serviceId];
        } else {
          newServices = selectedServices.filter((s) => s !== serviceId);
        }

        // Update config statuses
        const newStatuses = serviceConfigStatuses.map((s) =>
          s.id === serviceId ? { ...s, selected } : s
        );

        set({ selectedServices: newServices, serviceConfigStatuses: newStatuses });
      },

      /**
       * Set all selected services at once
       */
      setSelectedServices: (services: string[]) => {
        const { serviceConfigStatuses } = get();
        const newStatuses = serviceConfigStatuses.map((s) => ({
          ...s,
          selected: services.includes(s.id),
        }));
        set({
          selectedServices: services,
          serviceConfigStatuses: newStatuses,
          currentServiceIndex: 0,
        });
      },

      /**
       * Move to next service in config flow
       */
      nextService: () => {
        const { currentServiceIndex, selectedServices, nextStep } = get();
        if (currentServiceIndex < selectedServices.length - 1) {
          set({ currentServiceIndex: currentServiceIndex + 1 });
        } else {
          // All services configured, move to complete
          nextStep();
        }
      },

      /**
       * Move to previous service
       */
      previousService: () => {
        const { currentServiceIndex } = get();
        if (currentServiceIndex > 0) {
          set({ currentServiceIndex: currentServiceIndex - 1 });
        }
      },

      /**
       * Update service configuration status
       */
      updateServiceConfigStatus: (serviceId: string, configured: boolean, error?: string) => {
        const { serviceConfigStatuses } = get();
        const newStatuses = serviceConfigStatuses.map((s) =>
          s.id === serviceId ? { ...s, configured, error } : s
        );
        set({ serviceConfigStatuses: newStatuses });
      },

      /**
       * Dismiss the setup banner
       */
      dismissBanner: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/dismiss-banner`, {
            method: 'POST',
          });
          if (!response.ok) {
            throw new Error('Failed to dismiss banner');
          }
          set({ bannerDismissed: true, needsOnboarding: false, isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Reset onboarding to start fresh
       */
      resetOnboarding: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/reset`, {
            method: 'POST',
          });
          if (!response.ok) {
            throw new Error('Failed to reset onboarding');
          }
          set({
            completed: false,
            currentStep: 'welcome',
            skippedSteps: [],
            aiConfigured: false,
            servicesConfigured: [],
            bannerDismissed: false,
            needsOnboarding: true,
            selectedServices: [],
            currentServiceIndex: 0,
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      },

      /**
       * Join premium waitlist
       */
      joinWaitlist: async (email: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/waitlist`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, source: 'onboarding' }),
          });
          if (!response.ok) {
            throw new Error('Failed to join waitlist');
          }
          const data = await response.json();
          set({
            waitlistEmail: email,
            isOnWaitlist: true,
            isLoading: false,
          });
          return data.success;
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
          return false;
        }
      },

      /**
       * Check if email is on waitlist
       */
      checkWaitlistStatus: async (email: string) => {
        try {
          const response = await fetch(
            `${API_BASE}/waitlist/check?email=${encodeURIComponent(email)}`
          );
          if (!response.ok) {
            return false;
          }
          const data = await response.json();
          set({
            isOnWaitlist: data.is_on_waitlist,
            waitlistEmail: data.is_on_waitlist ? email : null,
          });
          return data.is_on_waitlist;
        } catch {
          return false;
        }
      },

      /**
       * Clear error state
       */
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'autoarr-onboarding',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist local UI state, API state is fetched fresh
        selectedServices: state.selectedServices,
        currentServiceIndex: state.currentServiceIndex,
        waitlistEmail: state.waitlistEmail,
        isOnWaitlist: state.isOnWaitlist,
      }),
    }
  )
);

/**
 * Hook to get current step progress (1-based for display)
 */
export function useStepProgress(): { current: number; total: number } {
  const currentStep = useOnboardingStore((state) => state.currentStep);
  return {
    current: getStepIndex(currentStep) + 1,
    total: ONBOARDING_STEPS.length,
  };
}

/**
 * Hook to check if a step was skipped
 */
export function useWasStepSkipped(step: OnboardingStep): boolean {
  const skippedSteps = useOnboardingStore((state) => state.skippedSteps);
  return skippedSteps.includes(step);
}

/**
 * Hook to get the current service being configured
 */
export function useCurrentServiceToConfig(): string | null {
  const { selectedServices, currentServiceIndex } = useOnboardingStore();
  return selectedServices[currentServiceIndex] || null;
}
