/**
 * Service Connection Card Component
 *
 * Displays status and controls for a service connection (SABnzbd, Sonarr, Radarr, Plex)
 */

import React, { useState } from 'react';
import { Check, X, AlertCircle, Settings, Trash2, RefreshCw } from 'lucide-react';

export interface ServiceConnection {
  id: string;
  type: 'sabnzbd' | 'sonarr' | 'radarr' | 'plex';
  name: string;
  url: string;
  apiKey: string;
  status: 'connected' | 'disconnected' | 'error';
  lastCheck?: Date;
  errorMessage?: string;
  version?: string;
}

interface ServiceConnectionCardProps {
  connection: ServiceConnection;
  onEdit: (connection: ServiceConnection) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => Promise<void>;
}

const SERVICE_ICONS: Record<string, string> = {
  sabnzbd: '📦',
  sonarr: '📺',
  radarr: '🎬',
  plex: '▶️',
};

const SERVICE_NAMES: Record<string, string> = {
  sabnzbd: 'SABnzbd',
  sonarr: 'Sonarr',
  radarr: 'Radarr',
  plex: 'Plex',
};

export const ServiceConnectionCard: React.FC<ServiceConnectionCardProps> = ({
  connection,
  onEdit,
  onDelete,
  onTest,
}) => {
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    try {
      await onTest(connection.id);
    } finally {
      setTesting(false);
    }
  };

  const getStatusColor = () => {
    switch (connection.status) {
      case 'connected':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'disconnected':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    switch (connection.status) {
      case 'connected':
        return <Check className="w-4 h-4" />;
      case 'error':
        return <X className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-3xl">{SERVICE_ICONS[connection.type]}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {SERVICE_NAMES[connection.type]}
            </h3>
            <p className="text-sm text-gray-600">{connection.name}</p>
          </div>
        </div>

        {/* Status Badge */}
        <div
          className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor()}`}
        >
          {getStatusIcon()}
          <span className="capitalize">{connection.status}</span>
        </div>
      </div>

      {/* Connection Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm">
          <span className="text-gray-600 w-20">URL:</span>
          <span className="text-gray-900 font-mono text-xs truncate">
            {connection.url}
          </span>
        </div>

        {connection.version && (
          <div className="flex items-center text-sm">
            <span className="text-gray-600 w-20">Version:</span>
            <span className="text-gray-900">{connection.version}</span>
          </div>
        )}

        {connection.lastCheck && (
          <div className="flex items-center text-sm">
            <span className="text-gray-600 w-20">Checked:</span>
            <span className="text-gray-900">
              {new Date(connection.lastCheck).toLocaleString()}
            </span>
          </div>
        )}

        {connection.errorMessage && (
          <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{connection.errorMessage}</p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleTest}
          disabled={testing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
          {testing ? 'Testing...' : 'Test Connection'}
        </button>

        <button
          onClick={() => onEdit(connection)}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          title="Edit Connection"
        >
          <Settings className="w-4 h-4" />
        </button>

        <button
          onClick={() => {
            if (window.confirm(`Delete ${SERVICE_NAMES[connection.type]} connection?`)) {
              onDelete(connection.id);
            }
          }}
          className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          title="Delete Connection"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
