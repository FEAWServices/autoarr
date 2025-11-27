/**
 * Service Connection Form Component
 *
 * Form for adding/editing service connections with auto-discovery
 */

import React, { useState, useEffect } from 'react';
import { Search, Loader, Check, AlertCircle, X } from 'lucide-react';
import type { ServiceConnection } from './ServiceConnectionCard';

interface ServiceConnectionFormProps {
  connection?: ServiceConnection;
  onSave: (connection: Partial<ServiceConnection>) => Promise<void>;
  onCancel: () => void;
}

interface DiscoveredService {
  type: ServiceConnection['type'];
  url: string;
  name: string;
}

export const ServiceConnectionForm: React.FC<ServiceConnectionFormProps> = ({
  connection,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    type: connection?.type || ('sabnzbd' as ServiceConnection['type']),
    name: connection?.name || '',
    url: connection?.url || '',
    apiKey: connection?.apiKey || '',
  });

  const [discovering, setDiscovering] = useState(false);
  const [discoveredServices, setDiscoveredServices] = useState<DiscoveredService[]>([]);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    version?: string;
  } | null>(null);
  const [saving, setSaving] = useState(false);

  // Auto-discovery on mount
  useEffect(() => {
    if (!connection) {
      handleDiscover();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDiscover = async () => {
    setDiscovering(true);
    setDiscoveredServices([]);

    try {
      const response = await fetch('/api/services/discover');
      const services = await response.json();
      setDiscoveredServices(services);
    } catch (error) {
      console.error('Discovery failed:', error);
    } finally {
      setDiscovering(false);
    }
  };

  const handleSelectDiscovered = (service: DiscoveredService) => {
    setFormData({
      ...formData,
      type: service.type,
      url: service.url,
      name: service.name,
    });
    setTestResult(null);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch('/api/services/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: formData.type,
          url: formData.url,
          apiKey: formData.apiKey,
        }),
      });

      const result = await response.json();

      if (result.success) {
        setTestResult({
          success: true,
          message: 'Connection successful!',
          version: result.version,
        });
      } else {
        setTestResult({
          success: false,
          message: result.error || 'Connection failed',
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Connection failed',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      await onSave(formData);
    } catch (error) {
      console.error('Save failed:', error);
      alert('Failed to save connection');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          {connection ? 'Edit' : 'Add'} Service Connection
        </h2>
        <button onClick={onCancel} className="text-gray-500 hover:text-gray-700" title="Close">
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Auto-Discovery Section */}
      {!connection && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-blue-900">Auto-Discovery</h3>
            <button
              onClick={handleDiscover}
              disabled={discovering}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {discovering ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Scan Network
                </>
              )}
            </button>
          </div>

          {discoveredServices.length > 0 ? (
            <div className="space-y-2">
              <p className="text-sm text-blue-800 mb-2">
                Found {discoveredServices.length} service(s):
              </p>
              {discoveredServices.map((service, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectDiscovered(service)}
                  className="w-full text-left p-3 bg-white border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{service.name}</p>
                      <p className="text-sm text-gray-600 font-mono">{service.url}</p>
                    </div>
                    <span className="text-sm text-blue-600 capitalize">{service.type}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : discovering ? (
            <p className="text-sm text-blue-700">Scanning network for services...</p>
          ) : (
            <p className="text-sm text-blue-700">
              No services found. Enter details manually below.
            </p>
          )}
        </div>
      )}

      {/* Connection Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Service Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Service Type</label>
          <select
            value={formData.type}
            onChange={(e) =>
              setFormData({
                ...formData,
                type: e.target.value as ServiceConnection['type'],
              })
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={!!connection}
          >
            <option value="sabnzbd">SABnzbd - Download Client</option>
            <option value="sonarr">Sonarr - TV Shows</option>
            <option value="radarr">Radarr - Movies</option>
            <option value="plex">Plex - Media Server (Optional)</option>
          </select>
        </div>

        {/* Connection Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Connection Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="My SABnzbd Server"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        {/* URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">URL</label>
          <input
            type="url"
            value={formData.url}
            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
            placeholder="http://192.168.1.100:8080"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
            required
          />
          <p className="mt-1 text-xs text-gray-500">Include http:// or https:// and port number</p>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
          <input
            type="password"
            value={formData.apiKey}
            onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
            placeholder="••••••••••••••••••••••••••••••••"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Found in {formData.type === 'sabnzbd' ? 'Config → General' : 'Settings → General'}
          </p>
        </div>

        {/* Test Connection Button */}
        <button
          type="button"
          onClick={handleTest}
          disabled={testing || !formData.url || !formData.apiKey}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {testing ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Testing Connection...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Test Connection
            </>
          )}
        </button>

        {/* Test Result */}
        {testResult && (
          <div
            className={`p-4 rounded-lg border ${
              testResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex items-start gap-2">
              {testResult.success ? (
                <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p
                  className={`font-medium ${
                    testResult.success ? 'text-green-800' : 'text-red-800'
                  }`}
                >
                  {testResult.message}
                </p>
                {testResult.version && (
                  <p className="text-sm text-green-700 mt-1">Version: {testResult.version}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving || !testResult?.success}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'Saving...' : connection ? 'Update Connection' : 'Add Connection'}
          </button>
        </div>
      </form>
    </div>
  );
};
