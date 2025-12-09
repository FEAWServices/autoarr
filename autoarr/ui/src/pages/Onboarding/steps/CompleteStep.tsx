/**
 * Complete Step
 *
 * Final step showing a summary of what was configured and providing
 * quick actions to get started with AutoArr.
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  PartyPopper,
  MessageSquare,
  ClipboardCheck,
  Settings,
  ArrowRight,
  Bot,
} from 'lucide-react';
import { useOnboardingStore } from '../../../stores/onboardingStore';
import { getColorClasses, servicePlugins } from '../../../plugins/services';

export const CompleteStep = () => {
  const navigate = useNavigate();
  const { aiConfigured, servicesConfigured, skippedSteps, completeOnboarding, completed } =
    useOnboardingStore();

  // Mark onboarding as complete when we reach this step
  useEffect(() => {
    if (!completed) {
      completeOnboarding();
    }
  }, [completed, completeOnboarding]);

  const hasAI = aiConfigured && !skippedSteps.includes('ai_setup');
  const configuredCount = servicesConfigured.length;
  const skippedCount = skippedSteps.length;
  const hasSkippedItems = skippedCount > 0 || !hasAI || configuredCount < servicePlugins.length;

  return (
    <div className="max-w-2xl mx-auto text-center" data-testid="complete-step">
      {/* Celebration */}
      <div className="mb-8">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/25 animate-bounce">
          <PartyPopper className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-foreground mb-4">You're All Set!</h1>
        <p className="text-lg text-muted-foreground">
          AutoArr is ready to help you manage your media stack.
        </p>
      </div>

      {/* Configuration summary */}
      <div className="bg-card rounded-xl border border-border p-6 mb-8 text-left">
        <h2 className="font-semibold text-foreground mb-4">Setup Summary</h2>

        <div className="space-y-4">
          {/* AI Status */}
          <div className="flex items-center justify-between py-2 border-b border-border">
            <div className="flex items-center gap-3">
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center ${hasAI ? 'bg-green-500/10' : 'bg-muted'}`}
              >
                <Bot className={`w-4 h-4 ${hasAI ? 'text-green-500' : 'text-muted-foreground'}`} />
              </div>
              <span className="text-foreground">AI Assistant</span>
            </div>
            {hasAI ? (
              <span className="flex items-center gap-1 text-green-500 text-sm">
                <CheckCircle className="w-4 h-4" />
                Connected
              </span>
            ) : (
              <span className="text-muted-foreground text-sm">Not configured</span>
            )}
          </div>

          {/* Services */}
          {servicePlugins.map((plugin) => {
            const isConfigured = servicesConfigured.includes(plugin.id);
            const colors = getColorClasses(plugin);
            const Icon = plugin.icon;

            return (
              <div
                key={plugin.id}
                className="flex items-center justify-between py-2 border-b border-border last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center ${isConfigured ? colors.bg : 'bg-muted'}`}
                  >
                    <Icon
                      className={`w-4 h-4 ${isConfigured ? colors.text : 'text-muted-foreground'}`}
                    />
                  </div>
                  <span className="text-foreground">{plugin.name}</span>
                </div>
                {isConfigured ? (
                  <span className="flex items-center gap-1 text-green-500 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Connected
                  </span>
                ) : (
                  <span className="text-muted-foreground text-sm">Not configured</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid gap-4 sm:grid-cols-2 mb-8">
        {hasAI && (
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-4 p-4 rounded-xl bg-primary/10 border border-primary/30 text-left hover:bg-primary/20 transition-colors group"
            data-testid="chat-action"
          >
            <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center group-hover:bg-primary/30 transition-colors">
              <MessageSquare className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground mb-1">Start Chatting</h3>
              <p className="text-sm text-muted-foreground">Ask AI to find and download content</p>
            </div>
            <ArrowRight className="w-5 h-5 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        )}

        <button
          onClick={() => navigate('/settings/config-audit')}
          className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border text-left hover:border-primary/30 transition-colors group"
          data-testid="audit-action"
        >
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
            <ClipboardCheck className="w-6 h-6 text-blue-500" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-foreground mb-1">Configuration Audit</h3>
            <p className="text-sm text-muted-foreground">Check your settings for best practices</p>
          </div>
          <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </button>

        {hasSkippedItems && (
          <button
            onClick={() => navigate('/settings')}
            className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border text-left hover:border-primary/30 transition-colors group"
            data-testid="settings-action"
          >
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
              <Settings className="w-6 h-6 text-amber-500" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground mb-1">Complete Setup</h3>
              <p className="text-sm text-muted-foreground">Configure remaining services</p>
            </div>
            <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        )}
      </div>

      {/* Go to dashboard */}
      <button
        onClick={() => navigate('/')}
        className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
        data-testid="go-to-dashboard"
      >
        Go to Dashboard
        <ArrowRight className="w-4 h-4" />
      </button>

      <p className="text-xs text-muted-foreground mt-6">
        You can re-run the setup wizard anytime from Settings
      </p>
    </div>
  );
};
