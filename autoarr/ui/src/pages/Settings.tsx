import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Save,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
  Palette,
  ChevronRight,
  ClipboardCheck,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useOnboardingStore } from '../stores/onboardingStore';

interface ServiceConfig {
  url: string;
  apiKey: string;
  enabled: boolean;
}

interface LLMConfig {
  apiKey: string;
  enabled: boolean;
  model: string;
  availableModels: Array<{ id: string; name: string; provider: string }>;
}

interface SettingsData {
  sabnzbd: ServiceConfig;
  sonarr: ServiceConfig;
  radarr: ServiceConfig;
  plex: ServiceConfig & { token: string };
  openrouter: LLMConfig;
  brave: {
    apiKey: string;
    enabled: boolean;
  };
  app: {
    logLevel: string;
    timezone: string;
  };
}

// ServiceCard component - compact card for service configuration
const ServiceCard = ({
  title,
  service,
  config,
  onChange,
  showToken = false,
  showKeys,
  testResults,
  testErrors,
  toggleShowKey,
  testConnection,
}: {
  title: string;
  service: string;
  config: ServiceConfig & { token?: string };
  onChange: (updates: Partial<ServiceConfig> | { token: string }) => void;
  showToken?: boolean;
  showKeys: Record<string, boolean>;
  testResults: Record<string, 'idle' | 'testing' | 'success' | 'error'>;
  testErrors: Record<string, string>;
  toggleShowKey: (key: string) => void;
  testConnection: (service: string) => void;
}) => (
  <div
    className="bg-gray-800 rounded-lg p-4 space-y-3 h-full"
    data-testid={`service-card-${service}`}
    data-component="ServiceCard"
  >
    <div className="flex items-center justify-between" data-component="ServiceCardHeader">
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <label className="flex items-center gap-1.5">
        <input
          type="checkbox"
          checked={config.enabled}
          onChange={(e) => onChange({ enabled: e.target.checked })}
          className="w-4 h-4 rounded border-gray-600 text-indigo-600 focus:ring-indigo-500"
        />
        <span className="text-xs text-gray-400">Enabled</span>
      </label>
    </div>

    <div data-component="ServiceCardUrlField">
      <label className="block text-xs font-medium text-gray-300 mb-1">URL</label>
      <input
        type="text"
        value={config.url ?? ''}
        onChange={(e) => onChange({ url: e.target.value })}
        placeholder="http://localhost:8080"
        className="w-full px-2.5 py-1.5 text-sm bg-gray-900 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        data-component="ServiceCardUrlInput"
      />
    </div>

    <div data-component="ServiceCardApiKeyField">
      <label className="block text-xs font-medium text-gray-300 mb-1">
        {showToken ? 'Token' : 'API Key'}
      </label>
      <div className="relative">
        <input
          type={showKeys[service] ? 'text' : 'password'}
          value={showToken ? (config.token ?? '') : (config.apiKey ?? '')}
          onChange={(e) =>
            onChange(showToken ? { token: e.target.value } : { apiKey: e.target.value })
          }
          placeholder={showToken ? 'your_plex_token' : 'your_api_key'}
          className="w-full px-2.5 py-1.5 pr-9 text-sm bg-gray-900 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          data-component="ServiceCardApiKeyInput"
        />
        <button
          type="button"
          onClick={() => toggleShowKey(service)}
          className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-white"
          data-component="ServiceCardToggleVisibility"
        >
          {showKeys[service] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>

    <div className="space-y-2 pt-1" data-component="ServiceCardActions">
      <button
        onClick={() => testConnection(service)}
        disabled={!config.enabled || testResults[service] === 'testing'}
        className="w-full bg-gray-700 hover:bg-gray-600 text-white rounded-md text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors px-3 py-2"
        data-component="ServiceCardTestButton"
      >
        {testResults[service] === 'testing' ? (
          'Testing...'
        ) : testResults[service] === 'success' ? (
          <span className="flex items-center justify-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5" /> Connected
          </span>
        ) : testResults[service] === 'error' ? (
          <span className="flex items-center justify-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" /> Failed
          </span>
        ) : (
          'Test Connection'
        )}
      </button>

      {testResults[service] === 'error' && testErrors[service] && (
        <div className="flex items-start gap-1.5 p-2 bg-red-900/20 border border-red-800 rounded-md">
          <AlertCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-red-400">Connection Failed</p>
            <p className="text-xs text-red-300 font-mono truncate">{testErrors[service]}</p>
          </div>
        </div>
      )}
    </div>
  </div>
);

export const Settings = () => {
  const navigate = useNavigate();
  const { resetOnboarding } = useOnboardingStore();
  const [settings, setSettings] = useState<SettingsData>({
    sabnzbd: { url: 'http://localhost:8080', apiKey: '', enabled: false },
    sonarr: { url: 'http://localhost:8989', apiKey: '', enabled: false },
    radarr: { url: 'http://localhost:7878', apiKey: '', enabled: false },
    plex: {
      url: 'http://localhost:32400',
      apiKey: '',
      token: '',
      enabled: false,
    },
    openrouter: { apiKey: '', enabled: false, model: '', availableModels: [] },
    brave: { apiKey: '', enabled: false },
    app: { logLevel: 'INFO', timezone: 'America/New_York' },
  });

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [saveError, setSaveError] = useState<string>('');
  const [reconnectingServices, setReconnectingServices] = useState<string[]>([]);
  const [testResults, setTestResults] = useState<
    Record<string, 'idle' | 'testing' | 'success' | 'error'>
  >({});
  const [testErrors, setTestErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Load settings from backend
    const loadSettings = async () => {
      try {
        // Load service settings
        const response = await fetch('/api/v1/settings');
        if (response.ok) {
          const data = await response.json();
          // Deep merge API data with existing state to preserve fields not in API response
          // and ensure all input values are defined (never undefined)
          setSettings((prev) => ({
            sabnzbd: {
              url: data.sabnzbd?.url ?? prev.sabnzbd.url,
              apiKey: data.sabnzbd?.apiKey ?? prev.sabnzbd.apiKey,
              enabled: data.sabnzbd?.enabled ?? prev.sabnzbd.enabled,
            },
            sonarr: {
              url: data.sonarr?.url ?? prev.sonarr.url,
              apiKey: data.sonarr?.apiKey ?? prev.sonarr.apiKey,
              enabled: data.sonarr?.enabled ?? prev.sonarr.enabled,
            },
            radarr: {
              url: data.radarr?.url ?? prev.radarr.url,
              apiKey: data.radarr?.apiKey ?? prev.radarr.apiKey,
              enabled: data.radarr?.enabled ?? prev.radarr.enabled,
            },
            plex: {
              url: data.plex?.url ?? prev.plex.url,
              apiKey: data.plex?.apiKey ?? prev.plex.apiKey,
              token: data.plex?.token ?? prev.plex.token,
              enabled: data.plex?.enabled ?? prev.plex.enabled,
            },
            openrouter: prev.openrouter, // Will be updated by LLM settings fetch
            brave: {
              apiKey: data.brave?.apiKey ?? prev.brave.apiKey,
              enabled: data.brave?.enabled ?? prev.brave.enabled,
            },
            app: {
              logLevel: data.app?.logLevel ?? prev.app.logLevel,
              timezone: data.app?.timezone ?? prev.app.timezone,
            },
          }));
        }

        // Load LLM settings separately
        const llmResponse = await fetch('/api/v1/settings/llm');
        if (llmResponse.ok) {
          const llmData = await llmResponse.json();
          setSettings((prev) => ({
            ...prev,
            openrouter: {
              apiKey: llmData.api_key ?? '',
              enabled: llmData.enabled ?? false,
              model: llmData.default_model ?? '',
              availableModels: prev.openrouter.availableModels,
            },
          }));
        }
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    };

    loadSettings();
  }, []);

  const handleSave = async () => {
    setSaveStatus('saving');
    setSaveError('');

    // Validate: enabled services must have an API key
    const services: Array<'sabnzbd' | 'sonarr' | 'radarr' | 'plex'> = [
      'sabnzbd',
      'sonarr',
      'radarr',
      'plex',
    ];
    const servicesWithoutApiKey: string[] = [];

    for (const service of services) {
      const config = settings[service];
      const apiKeyOrToken =
        service === 'plex' ? (config as ServiceConfig & { token: string }).token : config.apiKey;
      if (config.enabled && !apiKeyOrToken?.trim()) {
        servicesWithoutApiKey.push(service.charAt(0).toUpperCase() + service.slice(1));
      }
    }

    if (servicesWithoutApiKey.length > 0) {
      setSaveStatus('error');
      setSaveError(
        `API key required for enabled services: ${servicesWithoutApiKey.join(', ')}. ` +
          `Please add an API key or disable the service.`
      );
      return;
    }

    const failedServices: string[] = [];
    const errorMessages: string[] = [];
    const servicesReconnecting: string[] = [];

    try {
      // Save each service individually

      const savePromises = services.map(async (service) => {
        const serviceConfig = settings[service];

        // Transform the data to match backend expectations
        const payload = {
          enabled: serviceConfig.enabled,
          url: serviceConfig.url,
          // Backend expects 'api_key_or_token' field
          api_key_or_token:
            service === 'plex'
              ? (serviceConfig as ServiceConfig & { token: string }).token
              : serviceConfig.apiKey,
          timeout: 30.0, // Default timeout
        };

        try {
          const response = await fetch(`/api/v1/settings/${service}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorDetail = errorData.detail || `HTTP ${response.status}`;
            failedServices.push(service);
            errorMessages.push(`${service}: ${errorDetail}`);
          } else {
            // Check if the service is reconnecting in background
            const data = await response.json();
            if (data.reconnecting) {
              servicesReconnecting.push(service);
            }
          }
        } catch (networkError) {
          failedServices.push(service);
          errorMessages.push(
            `${service}: Network error - ${
              networkError instanceof Error ? networkError.message : 'Cannot reach server'
            }`
          );
        }
      });

      await Promise.all(savePromises);

      // Save LLM settings
      if (settings.openrouter.apiKey || settings.openrouter.enabled) {
        try {
          const llmPayload = {
            api_key: settings.openrouter.apiKey,
            enabled: settings.openrouter.enabled,
            default_model: settings.openrouter.model || 'anthropic/claude-3.5-sonnet',
          };
          const llmResponse = await fetch('/api/v1/settings/llm', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(llmPayload),
          });

          if (!llmResponse.ok) {
            const errorData = await llmResponse.json().catch(() => ({}));
            failedServices.push('openrouter');
            errorMessages.push(`LLM: ${errorData.detail || `HTTP ${llmResponse.status}`}`);
          }
        } catch (networkError) {
          failedServices.push('openrouter');
          errorMessages.push(
            `LLM: Network error - ${
              networkError instanceof Error ? networkError.message : 'Cannot reach server'
            }`
          );
        }
      }

      if (failedServices.length > 0) {
        setSaveStatus('error');
        setSaveError(`Failed to save: ${failedServices.join(', ')}. ${errorMessages.join('; ')}`);
        setTimeout(() => setSaveStatus('idle'), 8000);
      } else {
        setSaveStatus('success');
        // Track which services are reconnecting
        if (servicesReconnecting.length > 0) {
          setReconnectingServices(servicesReconnecting);
          // Clear reconnecting status after 10 seconds (background reconnect should be done)
          setTimeout(() => setReconnectingServices([]), 10000);
        }
        setTimeout(() => setSaveStatus('idle'), 3000);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus('error');
      setSaveError(
        error instanceof Error ? error.message : 'An unexpected error occurred while saving'
      );
      setTimeout(() => setSaveStatus('idle'), 8000);
    }
  };

  const testConnection = async (service: string) => {
    setTestResults({ ...testResults, [service]: 'testing' });
    setTestErrors({ ...testErrors, [service]: '' });

    try {
      // Use different endpoint for LLM testing
      const endpoint = service === 'llm' ? '/api/v1/settings/test/llm' : `/health/${service}`;
      const options: RequestInit =
        service === 'llm'
          ? {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                api_key: settings.openrouter.apiKey,
                model: settings.openrouter.model || 'anthropic/claude-3.5-sonnet',
              }),
            }
          : {};

      const response = await fetch(endpoint, options);

      if (response.ok) {
        await response.json();
        setTestResults({ ...testResults, [service]: 'success' });
        setTestErrors({ ...testErrors, [service]: '' });
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const errorMessage =
          errorData.detail ||
          errorData.message ||
          `HTTP ${response.status}: ${response.statusText}`;
        setTestResults({ ...testResults, [service]: 'error' });
        setTestErrors({ ...testErrors, [service]: errorMessage });
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Network error - cannot reach backend';
      setTestResults({ ...testResults, [service]: 'error' });
      setTestErrors({ ...testErrors, [service]: errorMessage });
    }
  };

  const toggleShowKey = (key: string) => {
    setShowKeys({ ...showKeys, [key]: !showKeys[key] });
  };

  const handleRunSetupWizard = async () => {
    await resetOnboarding();
    navigate('/onboarding');
  };

  return (
    <div
      className="max-w-4xl mx-auto"
      style={{ padding: 'var(--page-padding)' }}
      data-testid="settings-page"
      data-component="SettingsPage"
    >
      <div className="mb-8" data-component="SettingsPageHeader">
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-gray-400">Configure your media automation services</p>
      </div>

      <div className="space-y-8">
        {/* Quick Settings Links */}
        <div
          className="grid grid-cols-1 md:grid-cols-3 gap-3"
          data-component="QuickSettingsLinks"
        >
          <Link
            to="/settings/appearance"
            className="flex items-center justify-between p-3 bg-[var(--modal-bg-color)] rounded-lg border border-[var(--aa-border)] hover:border-[var(--accent-color)] transition-colors group"
            data-component="QuickSettingsLink-Appearance"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--accent-color)]/10">
                <Palette className="w-5 h-5 text-[var(--accent-color)]" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text)]">Appearance</h3>
                <p className="text-xs text-[var(--text-muted)]">Themes & colors</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--accent-color)] transition-colors" />
          </Link>

          <Link
            to="/settings/config-audit"
            className="flex items-center justify-between p-3 bg-[var(--modal-bg-color)] rounded-lg border border-[var(--aa-border)] hover:border-[var(--accent-color)] transition-colors group"
            data-component="QuickSettingsLink-ConfigAudit"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <ClipboardCheck className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text)]">Config Audit</h3>
                <p className="text-xs text-[var(--text-muted)]">Analyze & optimize</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--accent-color)] transition-colors" />
          </Link>

          <button
            onClick={handleRunSetupWizard}
            className="flex items-center justify-between p-3 bg-[var(--modal-bg-color)] rounded-lg border border-[var(--aa-border)] hover:border-primary transition-colors group text-left"
            data-testid="run-setup-wizard-button"
            data-component="QuickSettingsLink-SetupWizard"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Sparkles className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text)]">Setup Wizard</h3>
                <p className="text-xs text-[var(--text-muted)]">Re-run guided setup</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-primary transition-colors" />
          </button>
        </div>

        {/* Media Services */}
        <div data-component="MediaServicesSection">
          <h2 className="text-xl font-semibold text-white mb-4">Media Services</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ServiceCard
              title="SABnzbd"
              service="sabnzbd"
              config={settings.sabnzbd}
              onChange={(updates) =>
                setSettings({
                  ...settings,
                  sabnzbd: { ...settings.sabnzbd, ...updates },
                })
              }
              showKeys={showKeys}
              testResults={testResults}
              testErrors={testErrors}
              toggleShowKey={toggleShowKey}
              testConnection={testConnection}
            />
            <ServiceCard
              title="Sonarr"
              service="sonarr"
              config={settings.sonarr}
              onChange={(updates) =>
                setSettings({
                  ...settings,
                  sonarr: { ...settings.sonarr, ...updates },
                })
              }
              showKeys={showKeys}
              testResults={testResults}
              testErrors={testErrors}
              toggleShowKey={toggleShowKey}
              testConnection={testConnection}
            />
            <ServiceCard
              title="Radarr"
              service="radarr"
              config={settings.radarr}
              onChange={(updates) =>
                setSettings({
                  ...settings,
                  radarr: { ...settings.radarr, ...updates },
                })
              }
              showKeys={showKeys}
              testResults={testResults}
              testErrors={testErrors}
              toggleShowKey={toggleShowKey}
              testConnection={testConnection}
            />
            <ServiceCard
              title="Plex"
              service="plex"
              config={settings.plex}
              onChange={(updates) =>
                setSettings({
                  ...settings,
                  plex: { ...settings.plex, ...updates },
                })
              }
              showToken
              showKeys={showKeys}
              testResults={testResults}
              testErrors={testErrors}
              toggleShowKey={toggleShowKey}
              testConnection={testConnection}
            />
          </div>
        </div>

        {/* AI & Application Settings - Side by Side */}
        <div data-component="AIAndAppSection">
          <h2 className="text-xl font-semibold text-white mb-4">Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* OpenRouter Card */}
            <div
              className="bg-gray-800 rounded-lg p-4 space-y-3 h-full"
              data-testid="openrouter-card"
              data-component="OpenRouterCard"
            >
              <div className="flex items-center justify-between" data-component="OpenRouterCardHeader">
                <h3 className="text-base font-semibold text-white">OpenRouter</h3>
                <label className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={settings.openrouter.enabled}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        openrouter: {
                          ...settings.openrouter,
                          enabled: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 rounded border-gray-600 text-indigo-600 focus:ring-indigo-500"
                    data-testid="openrouter-enabled"
                  />
                  <span className="text-xs text-gray-400">Enabled</span>
                </label>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">API Key</label>
                <div className="relative">
                  <input
                    type={showKeys['openrouter'] ? 'text' : 'password'}
                    value={settings.openrouter.apiKey ?? ''}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        openrouter: {
                          ...settings.openrouter,
                          apiKey: e.target.value,
                        },
                      })
                    }
                    placeholder="sk-or-..."
                    className="w-full px-2.5 py-1.5 pr-9 text-sm bg-gray-900 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="openrouter-api-key"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey('openrouter')}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-white"
                  >
                    {showKeys['openrouter'] ? (
                      <EyeOff className="w-3.5 h-3.5" />
                    ) : (
                      <Eye className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  <a
                    href="https://openrouter.ai/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:text-indigo-300"
                  >
                    Get API key →
                  </a>
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Model</label>
                <input
                  type="text"
                  value={settings.openrouter.model ?? ''}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      openrouter: {
                        ...settings.openrouter,
                        model: e.target.value,
                      },
                    })
                  }
                  placeholder="anthropic/claude-3.5-sonnet"
                  className="w-full px-2.5 py-1.5 text-sm bg-gray-900 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  data-testid="openrouter-model"
                />
                <p className="text-xs text-gray-500 mt-1">
                  <a
                    href="https://openrouter.ai/models"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:text-indigo-300"
                  >
                    Browse models →
                  </a>
                </p>
              </div>

              <div className="space-y-2 pt-1">
                <button
                  onClick={() => testConnection('llm')}
                  disabled={!settings.openrouter.enabled || testResults['llm'] === 'testing'}
                  className="w-full bg-gray-700 hover:bg-gray-600 text-white rounded-md text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors px-3 py-2"
                  data-testid="openrouter-test-button"
                >
                  {testResults['llm'] === 'testing' ? (
                    'Testing...'
                  ) : testResults['llm'] === 'success' ? (
                    <span className="flex items-center justify-center gap-1.5">
                      <CheckCircle className="w-3.5 h-3.5" /> Connected
                    </span>
                  ) : testResults['llm'] === 'error' ? (
                    <span className="flex items-center justify-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5" /> Failed
                    </span>
                  ) : (
                    'Test Connection'
                  )}
                </button>

                {testResults['llm'] === 'error' && testErrors['llm'] && (
                  <div className="flex items-start gap-1.5 p-2 bg-red-900/20 border border-red-800 rounded-md">
                    <AlertCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-red-400">Connection Failed</p>
                      <p className="text-xs text-red-300 font-mono truncate">{testErrors['llm']}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Application Card */}
            <div
              className="bg-gray-800 rounded-lg p-4 space-y-3 h-full"
              data-component="ApplicationCard"
            >
              <div className="flex items-center justify-between" data-component="ApplicationCardHeader">
                <h3 className="text-base font-semibold text-white">Application</h3>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Log Level</label>
                <select
                  value={settings.app.logLevel ?? 'INFO'}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      app: { ...settings.app, logLevel: e.target.value },
                    })
                  }
                  className="w-full px-2.5 py-1.5 text-sm bg-gray-900 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="DEBUG">Debug</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Timezone</label>
                <input
                  type="text"
                  value={settings.app.timezone ?? ''}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      app: { ...settings.app, timezone: e.target.value },
                    })
                  }
                  placeholder="America/New_York"
                  className="w-full px-2.5 py-1.5 text-sm bg-gray-900 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center gap-4" data-component="SaveButtonSection">
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            data-component="SaveButton"
          >
            <Save className="w-5 h-5" />
            {saveStatus === 'saving' ? 'Saving...' : 'Save Settings'}
          </button>

          {saveStatus === 'success' && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle className="w-5 h-5" />
                <span>Settings saved successfully!</span>
              </div>
              {reconnectingServices.length > 0 && (
                <div className="flex items-center gap-2 text-blue-400">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="text-sm">
                    Reconnecting to {reconnectingServices.join(', ')} in background...
                  </span>
                </div>
              )}
            </div>
          )}

          {saveStatus === 'idle' && reconnectingServices.length > 0 && (
            <div className="flex items-center gap-2 text-blue-400">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span className="text-sm">Reconnecting to {reconnectingServices.join(', ')}...</span>
            </div>
          )}

          {saveStatus === 'error' && (
            <div className="flex items-start gap-2 text-red-400 max-w-xl">
              <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
              <div className="flex flex-col">
                <span className="font-medium">Failed to save settings</span>
                {saveError && <span className="text-sm text-red-300 mt-1">{saveError}</span>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
