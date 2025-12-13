/**
 * Service Config Step
 *
 * Guides users through configuring each selected service one by one.
 * Shows step-by-step instructions and tests connections.
 */

import { useState } from 'react';
import {
  ArrowRight,
  ArrowLeft,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Loader2,
  Key,
  Globe,
  SkipForward,
} from 'lucide-react';
import { useOnboardingStore, useCurrentServiceToConfig } from '../../../stores/onboardingStore';
import { getServicePlugin, getColorClasses, getDefaultUrl } from '../../../plugins/services';

export const ServiceConfigStep = () => {
  const {
    selectedServices,
    currentServiceIndex,
    nextService,
    previousService,
    previousStep,
    addConfiguredService,
    servicesConfigured,
    isLoading,
  } = useOnboardingStore();

  const currentServiceId = useCurrentServiceToConfig();
  const plugin = currentServiceId ? getServicePlugin(currentServiceId) : null;

  // Initialize state with default values based on current plugin
  const [url, setUrl] = useState(() => (plugin ? getDefaultUrl(plugin) : ''));
  const [apiKey, setApiKey] = useState('');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testError, setTestError] = useState<string | null>(null);

  // If no services selected, this step shouldn't be shown
  if (!plugin || selectedServices.length === 0) {
    return null;
  }

  const colors = getColorClasses(plugin);
  const Icon = plugin.icon;
  const isAlreadyConfigured = servicesConfigured.includes(plugin.id);
  const isLastService = currentServiceIndex === selectedServices.length - 1;

  const handleTestConnection = async () => {
    if (!url.trim() || !apiKey.trim()) {
      setTestError('Please enter both URL and API key');
      return;
    }

    setTestStatus('testing');
    setTestError(null);

    try {
      const result = await plugin.testConnection(url, apiKey);

      if (result.success) {
        // Save the settings
        await fetch(`/api/v1/settings/${plugin.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            enabled: true,
            url,
            api_key_or_token: apiKey,
            timeout: 30,
          }),
        });

        setTestStatus('success');
        await addConfiguredService(plugin.id);
      } else {
        setTestStatus('error');
        // Show the detailed error message from the API
        const errorDetails = result.details?.error ? ` (${result.details.error})` : '';
        setTestError(result.message || `Connection test failed.${errorDetails}`);
      }
    } catch (error) {
      setTestStatus('error');
      setTestError(error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleContinue = () => {
    if (testStatus === 'success' || isAlreadyConfigured) {
      nextService();
    }
  };

  const handleSkipService = () => {
    nextService();
  };

  const handleBack = () => {
    if (currentServiceIndex === 0) {
      previousStep();
    } else {
      previousService();
    }
  };

  return (
    <div key={currentServiceId} className="max-w-2xl mx-auto" data-testid="service-config-step">
      {/* Progress header */}
      <div className="mb-6 p-4 rounded-xl bg-card border border-border">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Configuring service {currentServiceIndex + 1} of {selectedServices.length}
          </span>
          <div className="flex gap-2">
            {selectedServices.map((id, index) => {
              const isComplete = servicesConfigured.includes(id);
              const isCurrent = index === currentServiceIndex;
              return (
                <div
                  key={id}
                  className={`
                    w-2 h-2 rounded-full
                    ${isComplete ? 'bg-green-500' : isCurrent ? 'bg-primary' : 'bg-muted'}
                  `}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Service header */}
      <div className="text-center mb-8">
        <div
          className={`w-20 h-20 mx-auto mb-4 rounded-2xl ${colors.bg} flex items-center justify-center p-3`}
        >
          <img
            src={plugin.logo}
            alt={`${plugin.name} logo`}
            className="w-full h-full object-contain"
            onError={(e) => {
              // Fallback to icon if logo fails to load
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
          <Icon className={`w-10 h-10 ${colors.text} hidden`} />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">Configure {plugin.name}</h2>
        <p className="text-muted-foreground">{plugin.description}</p>
      </div>

      {/* Already configured notice */}
      {isAlreadyConfigured && (
        <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-500 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-medium">{plugin.name} is already connected!</p>
            <p className="text-sm opacity-80">You can continue or reconfigure if needed.</p>
          </div>
        </div>
      )}

      {/* Configuration form */}
      <div className="bg-card rounded-xl border border-border p-6 mb-6">
        {/* API Key instructions */}
        <div className="mb-6">
          <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
            <Key className={`w-5 h-5 ${colors.text}`} />
            Where to find your API key
          </h3>
          <p className="text-sm text-muted-foreground mb-3">{plugin.apiKeyLocation}</p>
          <ol className="space-y-2">
            {plugin.apiKeySteps.map((step, index) => (
              <li key={index} className="flex gap-3 text-sm">
                <span
                  className={`w-5 h-5 rounded-full ${colors.bg} ${colors.text} flex items-center justify-center flex-shrink-0 text-xs font-medium`}
                >
                  {index + 1}
                </span>
                <span className="text-muted-foreground">{step}</span>
              </li>
            ))}
          </ol>
          <a
            href={plugin.docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center gap-1 mt-3 text-sm ${colors.text} hover:underline`}
          >
            View documentation
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        {/* Form fields */}
        <div className="space-y-4">
          <div>
            <label htmlFor="service-url" className="block text-sm font-medium text-foreground mb-2">
              Service URL
            </label>
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id="service-url"
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={getDefaultUrl(plugin)}
                className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                data-testid="service-url-input"
              />
            </div>
          </div>

          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-foreground mb-2">
              API Key
            </label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                data-testid="api-key-input"
              />
            </div>
          </div>
        </div>

        {/* Test connection button */}
        <div className="mt-6 pt-6 border-t border-border">
          <button
            onClick={handleTestConnection}
            disabled={!url.trim() || !apiKey.trim() || testStatus === 'testing'}
            className={`
              w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors
              ${
                testStatus === 'success'
                  ? 'bg-green-500 text-white'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            data-testid="test-connection-button"
          >
            {testStatus === 'testing' && (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Testing Connection...
              </>
            )}
            {testStatus === 'success' && (
              <>
                <CheckCircle className="w-4 h-4" />
                Connected!
              </>
            )}
            {testStatus !== 'testing' && testStatus !== 'success' && <>Test Connection</>}
          </button>

          {testStatus === 'error' && testError && (
            <div className="mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-500 text-sm flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              {testError}
            </div>
          )}
        </div>
      </div>

      {/* Navigation - sticky on mobile */}
      <div className="flex flex-col sm:flex-row justify-between gap-3 pt-4 mt-4 border-t border-border/50">
        <button
          onClick={handleBack}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors disabled:opacity-50 order-2 sm:order-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <div className="flex flex-col sm:flex-row gap-3 order-1 sm:order-2">
          {!isAlreadyConfigured && testStatus !== 'success' && (
            <button
              onClick={handleSkipService}
              disabled={isLoading}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors disabled:opacity-50"
              data-testid="skip-service-button"
            >
              <SkipForward className="w-4 h-4" />
              Skip {plugin.name}
            </button>
          )}
          <button
            onClick={handleContinue}
            disabled={isLoading || (testStatus !== 'success' && !isAlreadyConfigured)}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="continue-button"
          >
            {isLastService ? 'Finish Setup' : 'Next Service'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
