import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Save,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
  Palette,
  ChevronRight,
  ClipboardCheck,
} from 'lucide-react';

interface ServiceConfig {
  url: string;
  apiKey: string;
  enabled: boolean;
}

interface SettingsData {
  sabnzbd: ServiceConfig;
  sonarr: ServiceConfig;
  radarr: ServiceConfig;
  plex: ServiceConfig & { token: string };
  anthropic: {
    apiKey: string;
    enabled: boolean;
  };
  brave: {
    apiKey: string;
    enabled: boolean;
  };
  app: {
    logLevel: string;
    timezone: string;
  };
}

// ServiceSection component - must be defined outside Settings to avoid re-creation on each render
const ServiceSection = ({
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
    className="bg-gray-800 rounded-lg space-y-6"
    data-testid={`service-card-${service}`}
    data-component="ServiceCard"
    style={{
      margin: 'var(--service-card-margin, 10px)',
      padding: 'var(--service-card-padding, 10px)',
    }}
  >
    <div className="flex items-center justify-between pb-2" data-component="ServiceCardHeader">
      <h3 className="text-lg font-semibold text-white py-1">{title}</h3>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={config.enabled}
          onChange={(e) => onChange({ enabled: e.target.checked })}
          className="w-4 h-4 rounded border-gray-600 text-indigo-600 focus:ring-indigo-500"
        />
        <span className="text-sm text-gray-400">Enabled</span>
      </label>
    </div>

    <div data-component="ServiceCardUrlField">
      <label className="block text-sm font-medium text-gray-300 mb-3 py-1">URL</label>
      <input
        type="text"
        value={config.url ?? ''}
        onChange={(e) => onChange({ url: e.target.value })}
        placeholder="http://localhost:8080"
        className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        data-component="ServiceCardUrlInput"
      />
    </div>

    <div data-component="ServiceCardApiKeyField">
      <label className="block text-sm font-medium text-gray-300 mb-3 py-1">
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
          className="w-full px-4 py-3 pr-20 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          data-component="ServiceCardApiKeyInput"
        />
        <button
          type="button"
          onClick={() => toggleShowKey(service)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-white"
          data-component="ServiceCardToggleVisibility"
        >
          {showKeys[service] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
    </div>

    <div className="space-y-2" data-component="ServiceCardActions">
      <button
        onClick={() => testConnection(service)}
        disabled={!config.enabled || testResults[service] === 'testing'}
        className="bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        data-component="ServiceCardTestButton"
        style={{ padding: 'var(--service-card-test-button-padding, 10px)' }}
      >
        {testResults[service] === 'testing' ? (
          'Testing...'
        ) : testResults[service] === 'success' ? (
          <span className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4" /> Connected
          </span>
        ) : testResults[service] === 'error' ? (
          <span className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" /> Failed
          </span>
        ) : (
          'Test Connection'
        )}
      </button>

      {testResults[service] === 'error' && testErrors[service] && (
        <div className="flex items-start gap-2 p-3 bg-red-900/20 border border-red-800 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-400 mb-1">Connection Failed</p>
            <p className="text-xs text-red-300 font-mono">{testErrors[service]}</p>
          </div>
        </div>
      )}
    </div>
  </div>
);

export const Settings = () => {
  const [settings, setSettings] = useState<SettingsData>({
    sabnzbd: { url: 'http://localhost:8080', apiKey: '', enabled: true },
    sonarr: { url: 'http://localhost:8989', apiKey: '', enabled: true },
    radarr: { url: 'http://localhost:7878', apiKey: '', enabled: true },
    plex: {
      url: 'http://localhost:32400',
      apiKey: '',
      token: '',
      enabled: true,
    },
    anthropic: { apiKey: '', enabled: false },
    brave: { apiKey: '', enabled: false },
    app: { logLevel: 'INFO', timezone: 'America/New_York' },
  });

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [testResults, setTestResults] = useState<
    Record<string, 'idle' | 'testing' | 'success' | 'error'>
  >({});
  const [testErrors, setTestErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Load settings from backend
    const loadSettings = async () => {
      try {
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
            anthropic: {
              apiKey: data.anthropic?.apiKey ?? prev.anthropic.apiKey,
              enabled: data.anthropic?.enabled ?? prev.anthropic.enabled,
            },
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
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    };

    loadSettings();
  }, []);

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      // Save each service individually
      const services: Array<'sabnzbd' | 'sonarr' | 'radarr' | 'plex'> = [
        'sabnzbd',
        'sonarr',
        'radarr',
        'plex',
      ];

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

        const response = await fetch(`/api/v1/settings/${service}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to save ${service}`);
        }
      });

      await Promise.all(savePromises);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const testConnection = async (service: string) => {
    setTestResults({ ...testResults, [service]: 'testing' });
    setTestErrors({ ...testErrors, [service]: '' });

    try {
      const response = await fetch(`/health/${service}`);

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
        <div className="space-y-3" data-component="QuickSettingsLinks">
          <Link
            to="/settings/appearance"
            className="flex items-center justify-between p-4 bg-[var(--modal-bg-color)] rounded-lg border border-[var(--aa-border)] hover:border-[var(--accent-color)] transition-colors group"
            data-component="QuickSettingsLink-Appearance"
            style={{ margin: 'var(--quick-settings-link-margin, 10px)' }}
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-[var(--accent-color)]/10">
                <Palette className="w-6 h-6 text-[var(--accent-color)]" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-[var(--text)]">Appearance</h3>
                <p className="text-sm text-[var(--text-muted)]">
                  Customize themes, colors, and visual preferences
                </p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-[var(--text-muted)] group-hover:text-[var(--accent-color)] transition-colors" />
          </Link>

          <Link
            to="/settings/config-audit"
            className="flex items-center justify-between p-4 bg-[var(--modal-bg-color)] rounded-lg border border-[var(--aa-border)] hover:border-[var(--accent-color)] transition-colors group"
            data-component="QuickSettingsLink-ConfigAudit"
            style={{ margin: 'var(--quick-settings-link-margin, 10px)' }}
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-green-500/10">
                <ClipboardCheck className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-[var(--text)]">Configuration Audit</h3>
                <p className="text-sm text-[var(--text-muted)]">
                  Analyze and optimize your service configurations
                </p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-[var(--text-muted)] group-hover:text-[var(--accent-color)] transition-colors" />
          </Link>
        </div>

        {/* Media Services */}
        <div data-component="MediaServicesSection">
          <h2 className="text-xl font-semibold text-white mb-4">Media Services</h2>
          <div className="space-y-4">
            <ServiceSection
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
            <ServiceSection
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
            <ServiceSection
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
            <ServiceSection
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

        {/* AI & Search */}
        <div data-component="AISearchSection">
          <h2 className="text-xl font-semibold text-white mb-4">AI & Search</h2>
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-8 space-y-6" data-component="AnthropicCard">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Anthropic Claude</h3>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.anthropic.enabled}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        anthropic: {
                          ...settings.anthropic,
                          enabled: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 rounded border-gray-600 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-400">Enabled</span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">API Key</label>
                <input
                  type={showKeys['anthropic'] ? 'text' : 'password'}
                  value={settings.anthropic.apiKey ?? ''}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      anthropic: {
                        ...settings.anthropic,
                        apiKey: e.target.value,
                      },
                    })
                  }
                  placeholder="sk-ant-..."
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Application Settings */}
        <div data-component="ApplicationSection">
          <h2 className="text-xl font-semibold text-white mb-4">Application</h2>
          <div className="bg-gray-800 rounded-lg p-8 space-y-6" data-component="ApplicationCard">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Log Level</label>
              <select
                value={settings.app.logLevel ?? 'INFO'}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    app: { ...settings.app, logLevel: e.target.value },
                  })
                }
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="DEBUG">Debug</option>
                <option value="INFO">Info</option>
                <option value="WARNING">Warning</option>
                <option value="ERROR">Error</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Timezone</label>
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
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center gap-4" data-component="SaveButtonSection">
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            data-component="SaveButton"
          >
            <Save className="w-5 h-5" />
            {saveStatus === 'saving' ? 'Saving...' : 'Save Settings'}
          </button>

          {saveStatus === 'success' && (
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="w-5 h-5" />
              <span>Settings saved successfully!</span>
            </div>
          )}

          {saveStatus === 'error' && (
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span>Failed to save settings</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
