/**
 * License Management Component
 *
 * Displays license status and allows activation/validation of AutoArr licenses
 */

import React, { useState, useEffect } from 'react';
import {
  Key,
  Check,
  X,
  AlertCircle,
  Loader,
  Shield,
  Zap,
  TrendingUp,
  ExternalLink,
} from 'lucide-react';

interface LicenseFeatures {
  autonomous_recovery: boolean;
  enhanced_monitoring: boolean;
  custom_model: boolean;
  priority_support: boolean;
  advanced_analytics: boolean;
  multi_instance: boolean;
  max_concurrent_downloads: number | null;
  max_monitored_items: number | null;
}

interface License {
  license_key: string;
  tier: 'free' | 'personal' | 'professional' | 'enterprise';
  customer_id: string;
  customer_email: string;
  issued_at: string;
  expires_at: string | null;
  features: LicenseFeatures;
  grace_period_days: number;
}

interface LicenseValidationResult {
  valid: boolean;
  error?: string;
  license?: License;
  validation_type: 'offline' | 'online' | 'grace_period';
  warnings?: string[];
  days_until_expiry?: number;
  validated_at: string;
}

interface LicenseManagementProps {
  onLicenseChange?: (license: License | null) => void;
}

const TIER_INFO = {
  free: {
    name: 'Free',
    color: 'gray',
    icon: Shield,
    description: 'Basic features with local LLM',
  },
  personal: {
    name: 'Personal',
    color: 'blue',
    icon: Key,
    description: 'Enhanced features for home use',
  },
  professional: {
    name: 'Professional',
    color: 'purple',
    icon: Zap,
    description: 'Advanced automation for power users',
  },
  enterprise: {
    name: 'Enterprise',
    color: 'orange',
    icon: TrendingUp,
    description: 'Full capabilities for organizations',
  },
};

export const LicenseManagement: React.FC<LicenseManagementProps> = ({ onLicenseChange }) => {
  const [licenseKey, setLicenseKey] = useState('');
  const [currentLicense, setCurrentLicense] = useState<License | null>(null);
  const [validationResult, setValidationResult] = useState<LicenseValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load existing license on mount
  useEffect(() => {
    loadExistingLicense();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadExistingLicense = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/license/current');
      if (response.ok) {
        const data = await response.json();
        if (data.license) {
          setCurrentLicense(data.license);
          setValidationResult(data.validation);
          setLicenseKey(data.license.license_key);
          onLicenseChange?.(data.license);
        }
      }
    } catch (error) {
      console.error('Failed to load license:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!licenseKey.trim()) {
      return;
    }

    setValidating(true);
    setValidationResult(null);

    try {
      const response = await fetch('/api/license/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: licenseKey }),
      });

      const result = await response.json();

      if (result.valid) {
        setCurrentLicense(result.license);
        setValidationResult(result);
        onLicenseChange?.(result.license);
      } else {
        setValidationResult(result);
        setCurrentLicense(null);
        onLicenseChange?.(null);
      }
    } catch (error) {
      setValidationResult({
        valid: false,
        error: error instanceof Error ? error.message : 'Validation failed',
        validation_type: 'offline',
        validated_at: new Date().toISOString(),
      });
    } finally {
      setValidating(false);
    }
  };

  const handleDeactivate = async () => {
    if (!window.confirm('Are you sure you want to deactivate this license?')) {
      return;
    }

    try {
      await fetch('/api/license/deactivate', { method: 'POST' });
      setCurrentLicense(null);
      setValidationResult(null);
      setLicenseKey('');
      onLicenseChange?.(null);
    } catch (error) {
      console.error('Failed to deactivate license:', error);
      alert('Failed to deactivate license');
    }
  };

  const getTierColor = (tier: string) => {
    const colors = {
      free: 'text-gray-600 bg-gray-100 border-gray-300',
      personal: 'text-blue-600 bg-blue-100 border-blue-300',
      professional: 'text-purple-600 bg-purple-100 border-purple-300',
      enterprise: 'text-orange-600 bg-orange-100 border-orange-300',
    };
    return colors[tier as keyof typeof colors] || colors.free;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current License Status */}
      {currentLicense ? (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              {React.createElement(TIER_INFO[currentLicense.tier].icon, {
                className: 'w-8 h-8 text-gray-700',
              })}
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  AutoArr {TIER_INFO[currentLicense.tier].name}
                </h3>
                <p className="text-sm text-gray-600">
                  {TIER_INFO[currentLicense.tier].description}
                </p>
              </div>
            </div>

            <div
              className={`px-3 py-1 rounded-full text-sm font-medium border ${getTierColor(
                currentLicense.tier
              )}`}
            >
              {TIER_INFO[currentLicense.tier].name}
            </div>
          </div>

          {/* License Details */}
          <div className="space-y-3 mb-4">
            <div className="flex items-center text-sm">
              <span className="text-gray-600 w-32">License Key:</span>
              <span className="text-gray-900 font-mono text-xs">
                {currentLicense.license_key.substring(0, 15)}...
                {currentLicense.license_key.substring(currentLicense.license_key.length - 5)}
              </span>
            </div>

            {currentLicense.expires_at ? (
              <div className="flex items-center text-sm">
                <span className="text-gray-600 w-32">Expires:</span>
                <span className="text-gray-900">
                  {new Date(currentLicense.expires_at).toLocaleDateString()}
                  {validationResult?.days_until_expiry !== undefined &&
                    validationResult.days_until_expiry <= 30 && (
                      <span className="ml-2 text-orange-600 font-medium">
                        ({validationResult.days_until_expiry} days remaining)
                      </span>
                    )}
                </span>
              </div>
            ) : (
              <div className="flex items-center text-sm">
                <span className="text-gray-600 w-32">Expires:</span>
                <span className="text-green-600 font-medium">Never (Lifetime)</span>
              </div>
            )}

            <div className="flex items-center text-sm">
              <span className="text-gray-600 w-32">Validation:</span>
              <span className="text-gray-900 capitalize">
                {validationResult?.validation_type || 'Unknown'}
              </span>
            </div>
          </div>

          {/* Warnings */}
          {validationResult?.warnings && validationResult.warnings.length > 0 && (
            <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-md">
              {validationResult.warnings.map((warning, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
                  <span className="text-orange-800">{warning}</span>
                </div>
              ))}
            </div>
          )}

          {/* Features */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Enabled Features:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.entries(currentLicense.features).map(([feature, enabled]) => {
                if (typeof enabled !== 'boolean') return null;

                const featureName = feature
                  .split('_')
                  .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                  .join(' ');

                return (
                  <div
                    key={feature}
                    className={`flex items-center gap-2 text-sm ${
                      enabled ? 'text-green-700' : 'text-gray-400'
                    }`}
                  >
                    {enabled ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                    <span>{featureName}</span>
                  </div>
                );
              })}

              {currentLicense.features.max_concurrent_downloads && (
                <div className="flex items-center gap-2 text-sm text-green-700">
                  <Check className="w-4 h-4" />
                  <span>
                    {currentLicense.features.max_concurrent_downloads === -1
                      ? 'Unlimited Downloads'
                      : `${currentLicense.features.max_concurrent_downloads} Concurrent Downloads`}
                  </span>
                </div>
              )}

              {currentLicense.features.max_monitored_items && (
                <div className="flex items-center gap-2 text-sm text-green-700">
                  <Check className="w-4 h-4" />
                  <span>
                    {currentLicense.features.max_monitored_items === -1
                      ? 'Unlimited Monitored Items'
                      : `${currentLicense.features.max_monitored_items} Monitored Items`}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleDeactivate}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
            >
              Deactivate License
            </button>

            {currentLicense.tier !== 'enterprise' && (
              <a
                href="https://autoarr.app/upgrade"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <TrendingUp className="w-4 h-4" />
                Upgrade License
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>
      ) : (
        /* License Activation Form */
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3 mb-4">
            <Key className="w-8 h-8 text-gray-700" />
            <div>
              <h3 className="text-xl font-bold text-gray-900">Activate License</h3>
              <p className="text-sm text-gray-600">
                Enter your license key to unlock premium features
              </p>
            </div>
          </div>

          {/* License Key Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">License Key</label>
            <input
              type="text"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
              placeholder="AUTOARR-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              disabled={validating}
            />
            <p className="mt-1 text-xs text-gray-500">
              Don't have a license?{' '}
              <a
                href="https://autoarr.app/pricing"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                View pricing options
              </a>
            </p>
          </div>

          {/* Validation Result */}
          {validationResult && !validationResult.valid && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <X className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-800">License validation failed</p>
                  <p className="text-sm text-red-700 mt-1">{validationResult.error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Activate Button */}
          <button
            onClick={handleValidate}
            disabled={validating || !licenseKey.trim()}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {validating ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Validating License...
              </>
            ) : (
              <>
                <Key className="w-4 h-4" />
                Activate License
              </>
            )}
          </button>
        </div>
      )}

      {/* Tier Comparison */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Available License Tiers</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(TIER_INFO).map(([tier, info]) => (
            <div
              key={tier}
              className={`p-4 rounded-lg border-2 ${
                currentLicense?.tier === tier ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                {React.createElement(info.icon, {
                  className: `w-6 h-6 text-${info.color}-600`,
                })}
                <h4 className="font-bold text-gray-900">{info.name}</h4>
              </div>
              <p className="text-sm text-gray-600 mb-3">{info.description}</p>

              {currentLicense?.tier === tier && (
                <div className="flex items-center gap-1 text-sm text-blue-600 font-medium">
                  <Check className="w-4 h-4" />
                  <span>Current Tier</span>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <a
            href="https://autoarr.app/pricing"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline text-sm font-medium inline-flex items-center gap-1"
          >
            Compare features and pricing
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};
