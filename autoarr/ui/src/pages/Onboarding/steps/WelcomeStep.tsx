/**
 * Welcome Step
 *
 * First step of the onboarding wizard. Introduces AutoArr, explains
 * its value proposition, and provides options to continue or skip.
 */

import { Bot, Shield, Zap, ArrowRight, SkipForward } from 'lucide-react';
import { useOnboardingStore } from '../../../stores/onboardingStore';

export const WelcomeStep = () => {
  const { nextStep, skipOnboarding, isLoading } = useOnboardingStore();

  return (
    <div className="max-w-2xl mx-auto text-center" data-testid="welcome-step">
      {/* Hero section */}
      <div className="mb-12">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg shadow-primary/25">
          <Bot className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-foreground mb-4">
          Welcome to AutoArr
        </h1>
        <p className="text-lg text-muted-foreground leading-relaxed">
          Your intelligent media automation assistant. AutoArr orchestrates your
          media stack with AI-powered insights and automatic management.
        </p>
      </div>

      {/* Value propositions */}
      <div className="grid gap-4 mb-12">
        <div className="flex items-start gap-4 p-4 rounded-xl bg-card border border-border text-left">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-1">AI-Powered Intelligence</h3>
            <p className="text-sm text-muted-foreground">
              Natural language requests, smart configuration auditing, and intelligent
              recommendations powered by your choice of AI models.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-4 p-4 rounded-xl bg-card border border-border text-left">
          <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
            <Zap className="w-5 h-5 text-green-500" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-1">Automatic Recovery</h3>
            <p className="text-sm text-muted-foreground">
              Failed downloads are automatically detected and retried with intelligent
              strategies. Less manual intervention, more successful downloads.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-4 p-4 rounded-xl bg-card border border-border text-left">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-1">Privacy First</h3>
            <p className="text-sm text-muted-foreground">
              Your data stays on your server. AutoArr is self-hosted and open source
              (GPL-3.0). No data collection, no phone home.
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={() => nextStep()}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          data-testid="get-started-button"
        >
          Get Started
          <ArrowRight className="w-4 h-4" />
        </button>
        <button
          onClick={() => skipOnboarding()}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors disabled:opacity-50"
          data-testid="skip-button"
        >
          <SkipForward className="w-4 h-4" />
          Skip Setup
        </button>
      </div>

      <p className="text-xs text-muted-foreground mt-6">
        You can always run the setup wizard again from Settings
      </p>
    </div>
  );
};
