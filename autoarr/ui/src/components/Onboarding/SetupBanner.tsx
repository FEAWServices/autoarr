/**
 * Setup Banner Component
 *
 * A persistent, dismissible banner that appears when the user has
 * skipped onboarding or hasn't completed setup. Encourages them
 * to finish configuration.
 */

import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, X, ArrowRight } from 'lucide-react';
import { useOnboardingStore } from '../../stores/onboardingStore';

export const SetupBanner = () => {
  const {
    completed,
    bannerDismissed,
    skippedSteps,
    aiConfigured,
    servicesConfigured,
    fetchStatus,
    dismissBanner,
  } = useOnboardingStore();

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Determine if banner should show (derived state, no useEffect)
  // Show banner if:
  // 1. Onboarding is complete (user didn't go through wizard) AND
  // 2. Banner not dismissed AND
  // 3. Setup is incomplete (AI not configured OR no services configured)
  const hasSkippedSetup =
    skippedSteps.length > 0 || !aiConfigured || servicesConfigured.length === 0;
  const isVisible = completed && !bannerDismissed && hasSkippedSetup;

  if (!isVisible) {
    return null;
  }

  const handleDismiss = async () => {
    await dismissBanner();
  };

  // Determine what's missing
  const missingItems: string[] = [];
  if (!aiConfigured) {
    missingItems.push('AI Assistant');
  }
  if (servicesConfigured.length === 0) {
    missingItems.push('media services');
  }

  return (
    <div
      className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b border-primary/20"
      data-testid="setup-banner"
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <div>
              <p className="text-sm text-foreground">
                <span className="font-medium">Complete your setup</span>
                {missingItems.length > 0 && (
                  <span className="text-muted-foreground">
                    {' '}
                    to unlock all features. Missing: {missingItems.join(', ')}.
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/onboarding"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
              data-testid="continue-setup-button"
            >
              Continue Setup
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <button
              onClick={handleDismiss}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              aria-label="Dismiss banner"
              data-testid="dismiss-banner-button"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
