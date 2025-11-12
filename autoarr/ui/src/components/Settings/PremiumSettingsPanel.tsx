/**
 * Premium Settings Panel Component
 *
 * Configuration panel for premium features (autonomous recovery, enhanced monitoring)
 */

import React, { useState, useEffect } from "react";
import {
  Loader,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle,
  Zap,
  Activity,
  TrendingUp,
  Lock,
} from "lucide-react";

interface RecoveryConfig {
  enabled: boolean;
  max_retry_attempts: number;
  retry_strategies: string[];
  quality_cascade_enabled: boolean;
  quality_cascade_order: string[];
  alternative_search_enabled: boolean;
  indexer_failover_enabled: boolean;
  predictive_failure_detection: boolean;
}

interface MonitoringConfig {
  enabled: boolean;
  health_check_interval: number;
  pattern_detection_enabled: boolean;
  predictive_analysis_enabled: boolean;
  notification_threshold: string;
  detailed_metrics_enabled: boolean;
}

interface AnalyticsConfig {
  enabled: boolean;
  retention_days: number;
  success_rate_tracking: boolean;
  performance_metrics: boolean;
  trend_analysis: boolean;
}

interface PremiumConfig {
  recovery: RecoveryConfig;
  monitoring: MonitoringConfig;
  analytics: AnalyticsConfig;
}

interface PremiumSettingsPanelProps {
  licenseValid: boolean;
  licenseTier: "free" | "personal" | "professional" | "enterprise";
}

const QUALITY_PROFILES = ["4K/2160p", "1080p", "720p", "480p"];

const RETRY_STRATEGIES = [
  { value: "immediate", label: "Immediate Retry", tier: "personal" },
  {
    value: "exponential_backoff",
    label: "Exponential Backoff",
    tier: "personal",
  },
  { value: "quality_cascade", label: "Quality Cascade", tier: "professional" },
  {
    value: "alternative_release",
    label: "Alternative Release",
    tier: "professional",
  },
  {
    value: "alternative_indexer",
    label: "Alternative Indexer",
    tier: "professional",
  },
  { value: "repack_search", label: "Repack Search", tier: "professional" },
  { value: "manual_fallback", label: "Manual Fallback", tier: "enterprise" },
];

export const PremiumSettingsPanel: React.FC<PremiumSettingsPanelProps> = ({
  licenseValid,
  licenseTier,
}) => {
  const [config, setConfig] = useState<PremiumConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  useEffect(() => {
    loadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/premium/config");
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        // Set default config
        setConfig(getDefaultConfig());
      }
    } catch (error) {
      console.error("Failed to load config:", error);
      setConfig(getDefaultConfig());
    } finally {
      setLoading(false);
    }
  };

  const getDefaultConfig = (): PremiumConfig => ({
    recovery: {
      enabled: false,
      max_retry_attempts: 3,
      retry_strategies: ["immediate", "exponential_backoff"],
      quality_cascade_enabled: false,
      quality_cascade_order: ["1080p", "720p"],
      alternative_search_enabled: false,
      indexer_failover_enabled: false,
      predictive_failure_detection: false,
    },
    monitoring: {
      enabled: false,
      health_check_interval: 300,
      pattern_detection_enabled: false,
      predictive_analysis_enabled: false,
      notification_threshold: "high",
      detailed_metrics_enabled: false,
    },
    analytics: {
      enabled: false,
      retention_days: 30,
      success_rate_tracking: false,
      performance_metrics: false,
      trend_analysis: false,
    },
  });

  const handleSave = async () => {
    if (!config) return;

    setSaving(true);
    setSaveResult(null);

    try {
      const response = await fetch("/api/premium/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        setSaveResult({
          success: true,
          message: "Premium settings saved successfully",
        });
      } else {
        const error = await response.json();
        setSaveResult({
          success: false,
          message: error.detail || "Failed to save settings",
        });
      }
    } catch (error) {
      setSaveResult({
        success: false,
        message:
          error instanceof Error ? error.message : "Failed to save settings",
      });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveResult(null), 5000);
    }
  };

  const handleReset = () => {
    if (window.confirm("Reset all premium settings to defaults?")) {
      setConfig(getDefaultConfig());
    }
  };

  const isFeatureAvailable = (requiredTier: string): boolean => {
    const tierOrder = ["free", "personal", "professional", "enterprise"];
    return (
      licenseValid &&
      tierOrder.indexOf(licenseTier) >= tierOrder.indexOf(requiredTier)
    );
  };

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!licenseValid) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-start gap-4">
          <Lock className="w-12 h-12 text-gray-400 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              Premium License Required
            </h3>
            <p className="text-gray-600 mb-4">
              These settings require a valid premium license. Activate a license
              to unlock autonomous recovery, enhanced monitoring, and advanced
              analytics.
            </p>
            <a
              href="https://autoarr.app/pricing"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Pricing
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Save Result */}
      {saveResult && (
        <div
          className={`p-4 rounded-lg border ${
            saveResult.success
              ? "bg-green-50 border-green-200"
              : "bg-red-50 border-red-200"
          }`}
        >
          <div className="flex items-start gap-2">
            {saveResult.success ? (
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            )}
            <p
              className={`text-sm ${
                saveResult.success ? "text-green-800" : "text-red-800"
              }`}
            >
              {saveResult.message}
            </p>
          </div>
        </div>
      )}

      {/* Autonomous Recovery Settings */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Zap className="w-6 h-6 text-blue-600" />
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">
              Autonomous Recovery
            </h3>
            <p className="text-sm text-gray-600">
              Automatic download failure detection and intelligent retry
              strategies
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.recovery.enabled}
              onChange={(e) =>
                setConfig({
                  ...config,
                  recovery: { ...config.recovery, enabled: e.target.checked },
                })
              }
              disabled={!isFeatureAvailable("personal")}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
          </label>
        </div>

        {config.recovery.enabled && (
          <div className="space-y-4">
            {/* Max Retry Attempts */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Retry Attempts
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={config.recovery.max_retry_attempts}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    recovery: {
                      ...config.recovery,
                      max_retry_attempts: parseInt(e.target.value),
                    },
                  })
                }
                className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Number of times to retry failed downloads (1-10)
              </p>
            </div>

            {/* Retry Strategies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enabled Strategies
              </label>
              <div className="space-y-2">
                {RETRY_STRATEGIES.map((strategy) => (
                  <label
                    key={strategy.value}
                    className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                      !isFeatureAvailable(strategy.tier)
                        ? "opacity-50 cursor-not-allowed"
                        : ""
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={config.recovery.retry_strategies.includes(
                        strategy.value,
                      )}
                      onChange={(e) => {
                        const strategies = e.target.checked
                          ? [
                              ...config.recovery.retry_strategies,
                              strategy.value,
                            ]
                          : config.recovery.retry_strategies.filter(
                              (s) => s !== strategy.value,
                            );
                        setConfig({
                          ...config,
                          recovery: {
                            ...config.recovery,
                            retry_strategies: strategies,
                          },
                        });
                      }}
                      disabled={!isFeatureAvailable(strategy.tier)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900">
                          {strategy.label}
                        </span>
                        {!isFeatureAvailable(strategy.tier) && (
                          <span className="text-xs px-2 py-0.5 bg-gray-200 text-gray-600 rounded">
                            {strategy.tier}+
                          </span>
                        )}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Quality Cascade */}
            {isFeatureAvailable("professional") && (
              <div>
                <label className="flex items-center gap-2 mb-2">
                  <input
                    type="checkbox"
                    checked={config.recovery.quality_cascade_enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        recovery: {
                          ...config.recovery,
                          quality_cascade_enabled: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Quality Cascade Order
                  </span>
                </label>

                {config.recovery.quality_cascade_enabled && (
                  <div className="flex flex-wrap gap-2">
                    {QUALITY_PROFILES.map((profile) => (
                      <label
                        key={profile}
                        className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-gray-50"
                      >
                        <input
                          type="checkbox"
                          checked={config.recovery.quality_cascade_order.includes(
                            profile,
                          )}
                          onChange={(e) => {
                            const order = e.target.checked
                              ? [
                                  ...config.recovery.quality_cascade_order,
                                  profile,
                                ]
                              : config.recovery.quality_cascade_order.filter(
                                  (p) => p !== profile,
                                );
                            setConfig({
                              ...config,
                              recovery: {
                                ...config.recovery,
                                quality_cascade_order: order,
                              },
                            });
                          }}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-900">{profile}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Advanced Options */}
            {isFeatureAvailable("professional") && (
              <div className="pt-4 border-t border-gray-200 space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.recovery.predictive_failure_detection}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        recovery: {
                          ...config.recovery,
                          predictive_failure_detection: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Predictive Failure Detection (ML-powered)
                  </span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.recovery.indexer_failover_enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        recovery: {
                          ...config.recovery,
                          indexer_failover_enabled: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Automatic Indexer Failover
                  </span>
                </label>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Enhanced Monitoring Settings */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Activity className="w-6 h-6 text-purple-600" />
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">
              Enhanced Monitoring
            </h3>
            <p className="text-sm text-gray-600">
              Real-time health monitoring with pattern detection and alerts
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.monitoring.enabled}
              onChange={(e) =>
                setConfig({
                  ...config,
                  monitoring: {
                    ...config.monitoring,
                    enabled: e.target.checked,
                  },
                })
              }
              disabled={!isFeatureAvailable("personal")}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
          </label>
        </div>

        {config.monitoring.enabled && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Health Check Interval (seconds)
              </label>
              <input
                type="number"
                min="60"
                max="3600"
                step="60"
                value={config.monitoring.health_check_interval}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    monitoring: {
                      ...config.monitoring,
                      health_check_interval: parseInt(e.target.value),
                    },
                  })
                }
                className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {isFeatureAvailable("professional") && (
              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.monitoring.pattern_detection_enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        monitoring: {
                          ...config.monitoring,
                          pattern_detection_enabled: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Pattern Detection
                  </span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.monitoring.predictive_analysis_enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        monitoring: {
                          ...config.monitoring,
                          predictive_analysis_enabled: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Predictive Analysis (ML-powered)
                  </span>
                </label>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Analytics Settings */}
      {isFeatureAvailable("professional") && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-6 h-6 text-orange-600" />
            <div className="flex-1">
              <h3 className="text-lg font-bold text-gray-900">
                Advanced Analytics
              </h3>
              <p className="text-sm text-gray-600">
                Track success rates, performance metrics, and trends
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.analytics.enabled}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    analytics: {
                      ...config.analytics,
                      enabled: e.target.checked,
                    },
                  })
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {config.analytics.enabled && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Retention (days)
                </label>
                <input
                  type="number"
                  min="7"
                  max="365"
                  value={config.analytics.retention_days}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      analytics: {
                        ...config.analytics,
                        retention_days: parseInt(e.target.value),
                      },
                    })
                  }
                  className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.analytics.success_rate_tracking}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        analytics: {
                          ...config.analytics,
                          success_rate_tracking: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Success Rate Tracking
                  </span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.analytics.performance_metrics}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        analytics: {
                          ...config.analytics,
                          performance_metrics: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Performance Metrics
                  </span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.analytics.trend_analysis}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        analytics: {
                          ...config.analytics,
                          trend_analysis: e.target.checked,
                        },
                      })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Trend Analysis</span>
                </label>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Reset to Defaults
        </button>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
};
