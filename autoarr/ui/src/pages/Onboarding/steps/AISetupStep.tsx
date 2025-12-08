/**
 * AI Setup Step
 *
 * Guides users through setting up an AI provider (OpenRouter).
 * Includes step-by-step instructions and a premium waitlist teaser.
 */

import { useState, useEffect } from 'react';
import {
  Bot,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Key,
  Globe,
  Cpu,
} from 'lucide-react';
import { useOnboardingStore } from '../../../stores/onboardingStore';

/**
 * Feature flag for premium teaser (would come from config in production)
 */
const SHOW_PREMIUM_TEASER = true;

/**
 * Recommended models with pricing info
 */
const recommendedModels = [
  {
    id: 'google/gemini-2.0-flash-exp:free',
    name: 'Gemini 2.0 Flash (Free)',
    description: 'Fast and capable, completely free to use',
    free: true,
  },
  {
    id: 'meta-llama/llama-3.2-3b-instruct:free',
    name: 'Llama 3.2 3B (Free)',
    description: 'Lightweight and responsive, free tier',
    free: true,
  },
  {
    id: 'anthropic/claude-3.5-sonnet',
    name: 'Claude 3.5 Sonnet',
    description: 'Best quality reasoning (~$3/M tokens)',
    free: false,
  },
];

export const AISetupStep = () => {
  const {
    previousStep,
    nextStep,
    skipStep,
    markAIConfigured,
    joinWaitlist,
    isOnWaitlist,
    isLoading,
  } = useOnboardingStore();

  const [apiKey, setApiKey] = useState('');
  const [selectedModel, setSelectedModel] = useState('google/gemini-2.0-flash-exp:free');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testError, setTestError] = useState<string | null>(null);
  const [waitlistEmail, setWaitlistEmail] = useState('');
  const [waitlistSubmitting, setWaitlistSubmitting] = useState(false);
  const [waitlistSuccess, setWaitlistSuccess] = useState(false);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);

  // Fetch existing LLM settings on mount
  useEffect(() => {
    const fetchExistingSettings = async () => {
      try {
        const response = await fetch('/api/v1/settings/llm');
        if (response.ok) {
          const data = await response.json();
          // If already configured, pre-fill and mark as success
          if (data.status === 'connected' && data.selected_model) {
            setSelectedModel(data.selected_model);
            setTestStatus('success');
            // Mark as configured in onboarding store
            await markAIConfigured();
          } else if (data.selected_model) {
            // Has model but not connected
            setSelectedModel(data.selected_model);
          }
          // Note: API key is masked, so we can't pre-fill it
          // But we show a placeholder if configured
          if (data.api_key_masked && data.api_key_masked !== '(not set)') {
            setApiKey(''); // Keep empty but show success state
          }
        }
      } catch (error) {
        console.error('Failed to fetch LLM settings:', error);
      } finally {
        setIsLoadingSettings(false);
      }
    };

    fetchExistingSettings();
  }, [markAIConfigured]);

  const handleTestConnection = async () => {
    if (!apiKey.trim()) {
      setTestError('Please enter an API key');
      return;
    }

    setTestStatus('testing');
    setTestError(null);

    try {
      // Save settings first (this will also test the connection)
      const response = await fetch('/api/v1/settings/llm', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: true,
          api_key: apiKey,
          selected_model: selectedModel,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to save settings');
      }

      // Now fetch the LLM status to verify connection
      const statusResponse = await fetch('/api/v1/settings/llm');
      const statusData = await statusResponse.json();

      if (statusData.status === 'connected') {
        setTestStatus('success');
        await markAIConfigured();
      } else {
        setTestStatus('error');
        setTestError('API key saved but connection failed. Please verify your key.');
      }
    } catch (error) {
      setTestStatus('error');
      setTestError(error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleContinue = async () => {
    if (testStatus === 'success') {
      await nextStep();
    }
  };

  const handleSkip = async () => {
    await skipStep('ai_setup');
  };

  const handleWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!waitlistEmail.trim()) return;

    setWaitlistSubmitting(true);
    const success = await joinWaitlist(waitlistEmail);
    setWaitlistSubmitting(false);
    if (success) {
      setWaitlistSuccess(true);
    }
  };

  // Show loading state while fetching settings
  if (isLoadingSettings) {
    return (
      <div className="max-w-2xl mx-auto" data-testid="ai-setup-step">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto" data-testid="ai-setup-step">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary/10 flex items-center justify-center">
          <Bot className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">Connect Your AI</h2>
        <p className="text-muted-foreground">
          AutoArr uses AI to power intelligent features. Choose from 200+ models via OpenRouter.
        </p>
      </div>

      {/* Already Connected Notice */}
      {testStatus === 'success' && (
        <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-500 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-medium">AI is already connected!</p>
            <p className="text-sm opacity-80">
              Using {selectedModel.split('/').pop()}. You can continue or reconfigure below.
            </p>
          </div>
        </div>
      )}

      {/* OpenRouter Setup Instructions */}
      <div className="bg-card rounded-xl border border-border p-6 mb-6">
        <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-primary" />
          Quick Setup Guide
        </h3>

        <ol className="space-y-4 text-sm">
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center flex-shrink-0 text-xs font-medium">
              1
            </span>
            <div>
              <p className="text-foreground font-medium">Create an OpenRouter account</p>
              <a
                href="https://openrouter.ai/auth?tab=signup"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center gap-1"
              >
                Sign up at openrouter.ai
                <ExternalLink className="w-3 h-3" />
              </a>
              <span className="text-muted-foreground ml-2">(free)</span>
            </div>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center flex-shrink-0 text-xs font-medium">
              2
            </span>
            <div>
              <p className="text-foreground font-medium">Generate an API key</p>
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center gap-1"
              >
                Go to API Keys dashboard
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center flex-shrink-0 text-xs font-medium">
              3
            </span>
            <div className="flex-1">
              <p className="text-foreground font-medium mb-2">Paste your API key below</p>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-or-v1-..."
                  className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  data-testid="openrouter-api-key-input"
                />
              </div>
            </div>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center flex-shrink-0 text-xs font-medium">
              4
            </span>
            <div className="flex-1">
              <p className="text-foreground font-medium mb-2">Choose a model</p>
              <div className="space-y-2" data-testid="model-selector">
                {recommendedModels.map((model) => (
                  <button
                    key={model.id}
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setSelectedModel(model.id);
                    }}
                    className={`
                      w-full flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all text-left
                      ${
                        selectedModel === model.id
                          ? 'border-primary bg-primary/10 shadow-sm shadow-primary/20'
                          : 'border-border/50 hover:border-primary/50 hover:bg-muted/30'
                      }
                    `}
                    data-testid={`model-option-${model.id.split('/')[0]}`}
                  >
                    <div
                      className={`
                        w-4 h-4 rounded-full border-2 flex items-center justify-center
                        ${selectedModel === model.id ? 'border-primary' : 'border-muted-foreground'}
                      `}
                    >
                      {selectedModel === model.id && (
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-foreground">{model.name}</span>
                        {model.free && (
                          <span className="px-1.5 py-0.5 rounded text-xs bg-green-500/10 text-green-500">
                            Free
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{model.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </li>
        </ol>

        {/* Test connection button */}
        <div className="mt-6 pt-6 border-t border-border">
          <button
            onClick={handleTestConnection}
            disabled={!apiKey.trim() || testStatus === 'testing'}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="test-connection-button"
          >
            {testStatus === 'testing' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Testing Connection...
              </>
            ) : testStatus === 'success' ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Connected Successfully!
              </>
            ) : (
              <>
                <Cpu className="w-4 h-4" />
                Test Connection
              </>
            )}
          </button>

          {testStatus === 'error' && testError && (
            <div className="mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-500 text-sm flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              {testError}
            </div>
          )}
        </div>
      </div>

      {/* Premium Waitlist Teaser */}
      {SHOW_PREMIUM_TEASER && (
        <div className="bg-gradient-to-br from-primary/5 to-primary/10 rounded-xl border border-primary/20 p-6 mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-primary/20 text-primary">
              Coming Soon
            </span>
          </div>
          <h3 className="font-semibold text-foreground mb-2">AutoArr Premium</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Get access to a specialized AI model trained specifically on the *arr suite of tools for
            even better recommendations and automation.
          </p>

          {isOnWaitlist || waitlistSuccess ? (
            <div className="flex items-center gap-2 text-green-500">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">You're on the list!</span>
            </div>
          ) : (
            <form onSubmit={handleWaitlistSubmit} className="flex gap-2">
              <input
                type="email"
                value={waitlistEmail}
                onChange={(e) => setWaitlistEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 px-4 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                data-testid="waitlist-email-input"
              />
              <button
                type="submit"
                disabled={waitlistSubmitting || !waitlistEmail.trim()}
                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                data-testid="join-waitlist-button"
              >
                {waitlistSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Join Waitlist'
                )}
              </button>
            </form>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={previousStep}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <div className="flex gap-3">
          <button
            onClick={handleSkip}
            disabled={isLoading}
            className="px-6 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors disabled:opacity-50"
            data-testid="skip-ai-button"
          >
            Skip for now
          </button>
          <button
            onClick={handleContinue}
            disabled={isLoading || testStatus !== 'success'}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="continue-button"
          >
            Continue
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {testStatus !== 'success' && (
        <p className="text-xs text-muted-foreground text-center mt-4">
          AI features require a working connection. You can skip and configure later in Settings.
        </p>
      )}
    </div>
  );
};
