/**
 * Progress Indicator Component
 *
 * Displays a visual progress bar showing the current step in the onboarding flow.
 */

import { Check } from 'lucide-react';

interface Step {
  id: string;
  label: string;
}

interface ProgressIndicatorProps {
  steps: Step[];
  currentStep: string;
}

export const ProgressIndicator = ({ steps, currentStep }: ProgressIndicatorProps) => {
  const currentIndex = steps.findIndex((s) => s.id === currentStep);

  return (
    <div className="flex items-center gap-2">
      {steps.map((step, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;

        return (
          <div key={step.id} className="flex items-center">
            {/* Step indicator */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  transition-all duration-300
                  ${
                    isCompleted
                      ? 'bg-primary text-primary-foreground'
                      : isCurrent
                        ? 'bg-primary/20 text-primary border-2 border-primary'
                        : 'bg-muted text-muted-foreground'
                  }
                `}
                data-testid={`step-indicator-${step.id}`}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>
              <span
                className={`
                  text-xs mt-1 hidden sm:block
                  ${isCurrent ? 'text-primary font-medium' : 'text-muted-foreground'}
                `}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line (not after last step) */}
            {index < steps.length - 1 && (
              <div
                className={`
                  h-0.5 w-8 sm:w-12 mx-1 transition-all duration-300
                  ${isCompleted ? 'bg-primary' : 'bg-muted'}
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};
