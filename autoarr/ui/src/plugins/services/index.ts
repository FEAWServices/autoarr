/**
 * Service Plugin Registry
 *
 * Defines the plugin interface for media automation services and
 * provides a registry of all available service plugins.
 */

import { Download, Tv, Film, Server, type LucideIcon } from 'lucide-react';

/**
 * Service category for grouping
 */
export type ServiceCategory = 'download' | 'media' | 'streaming';

/**
 * Service plugin interface
 *
 * Each service plugin provides metadata and configuration helpers
 * for integrating with a specific media automation service.
 */
export interface ServicePlugin {
  /** Unique identifier (e.g., 'sabnzbd') */
  id: string;

  /** Display name (e.g., 'SABnzbd') */
  name: string;

  /** Short description */
  description: string;

  /** Lucide icon component */
  icon: LucideIcon;

  /** Brand/accent color (Tailwind color name) */
  color: string;

  /** Service category */
  category: ServiceCategory;

  /** Common default port */
  defaultPort: number;

  /** Default URL path (optional) */
  defaultPath?: string;

  /** Where to find the API key in the service UI */
  apiKeyLocation: string;

  /** Step-by-step instructions for getting API key */
  apiKeySteps: string[];

  /** Documentation URL */
  docsUrl: string;

  /** Whether this is a required service or optional */
  optional: boolean;

  /**
   * Test connection to the service
   * @param url - Service URL
   * @param apiKey - API key or token
   * @returns Promise resolving to result with success flag and optional error message
   */
  testConnection: (url: string, apiKey: string) => Promise<{ success: boolean; message?: string; details?: Record<string, unknown> }>;
}

/**
 * SABnzbd Plugin
 */
export const sabnzbdPlugin: ServicePlugin = {
  id: 'sabnzbd',
  name: 'SABnzbd',
  description: 'Usenet download client for automated NZB downloading',
  icon: Download,
  color: 'amber',
  category: 'download',
  defaultPort: 8080,
  defaultPath: '/sabnzbd',
  apiKeyLocation: 'Config > General > SABnzbd Web Server > API Key',
  apiKeySteps: [
    'Open SABnzbd web interface',
    'Click the gear icon (Settings)',
    'Go to General',
    'Scroll down to "SABnzbd Web Server" section',
    'Copy the API Key (or generate a new one)',
  ],
  docsUrl: 'https://sabnzbd.org/wiki/configuration/general',
  optional: false,
  testConnection: async (url: string, apiKey: string): Promise<{ success: boolean; message?: string; details?: Record<string, unknown> }> => {
    try {
      const response = await fetch(
        `/api/v1/settings/test/sabnzbd`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, api_key_or_token: apiKey, timeout: 10 }),
        }
      );
      const data = await response.json();
      return {
        success: data.success === true,
        message: data.message,
        details: data.details,
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Network error',
      };
    }
  },
};

/**
 * Sonarr Plugin
 */
export const sonarrPlugin: ServicePlugin = {
  id: 'sonarr',
  name: 'Sonarr',
  description: 'TV show management and automatic episode downloading',
  icon: Tv,
  color: 'blue',
  category: 'media',
  defaultPort: 8989,
  apiKeyLocation: 'Settings > General > Security > API Key',
  apiKeySteps: [
    'Open Sonarr web interface',
    'Go to Settings',
    'Click on General',
    'Find the "Security" section',
    'Copy the API Key displayed there',
  ],
  docsUrl: 'https://wiki.servarr.com/sonarr',
  optional: false,
  testConnection: async (url: string, apiKey: string): Promise<{ success: boolean; message?: string; details?: Record<string, unknown> }> => {
    try {
      const response = await fetch(
        `/api/v1/settings/test/sonarr`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, api_key_or_token: apiKey, timeout: 10 }),
        }
      );
      const data = await response.json();
      return {
        success: data.success === true,
        message: data.message,
        details: data.details,
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Network error',
      };
    }
  },
};

/**
 * Radarr Plugin
 */
export const radarrPlugin: ServicePlugin = {
  id: 'radarr',
  name: 'Radarr',
  description: 'Movie collection manager and automatic downloading',
  icon: Film,
  color: 'orange',
  category: 'media',
  defaultPort: 7878,
  apiKeyLocation: 'Settings > General > Security > API Key',
  apiKeySteps: [
    'Open Radarr web interface',
    'Go to Settings',
    'Click on General',
    'Find the "Security" section',
    'Copy the API Key displayed there',
  ],
  docsUrl: 'https://wiki.servarr.com/radarr',
  optional: false,
  testConnection: async (url: string, apiKey: string): Promise<{ success: boolean; message?: string; details?: Record<string, unknown> }> => {
    try {
      const response = await fetch(
        `/api/v1/settings/test/radarr`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, api_key_or_token: apiKey, timeout: 10 }),
        }
      );
      const data = await response.json();
      return {
        success: data.success === true,
        message: data.message,
        details: data.details,
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Network error',
      };
    }
  },
};

/**
 * Plex Plugin
 */
export const plexPlugin: ServicePlugin = {
  id: 'plex',
  name: 'Plex',
  description: 'Media server for streaming your library anywhere',
  icon: Server,
  color: 'amber',
  category: 'streaming',
  defaultPort: 32400,
  defaultPath: '/web',
  apiKeyLocation: 'Plex Account > Authorized Devices > X-Plex-Token',
  apiKeySteps: [
    'Sign in to Plex',
    'Open any media item in the web player',
    'Click the three dots menu (...)',
    'Select "Get Info"',
    'Click "View XML"',
    'In the URL, find "X-Plex-Token=XXXX" and copy the token',
    'Alternatively, visit plex.tv/claim for a one-time token',
  ],
  docsUrl: 'https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/',
  optional: true,
  testConnection: async (url: string, apiKey: string): Promise<{ success: boolean; message?: string; details?: Record<string, unknown> }> => {
    try {
      const response = await fetch(
        `/api/v1/settings/test/plex`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, api_key_or_token: apiKey, timeout: 10 }),
        }
      );
      const data = await response.json();
      return {
        success: data.success === true,
        message: data.message,
        details: data.details,
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Network error',
      };
    }
  },
};

/**
 * Registry of all available service plugins
 */
export const servicePlugins: ServicePlugin[] = [
  sabnzbdPlugin,
  sonarrPlugin,
  radarrPlugin,
  plexPlugin,
];

/**
 * Get a service plugin by ID
 */
export function getServicePlugin(id: string): ServicePlugin | undefined {
  return servicePlugins.find((p) => p.id === id);
}

/**
 * Get plugins by category
 */
export function getPluginsByCategory(category: ServiceCategory): ServicePlugin[] {
  return servicePlugins.filter((p) => p.category === category);
}

/**
 * Get required plugins only
 */
export function getRequiredPlugins(): ServicePlugin[] {
  return servicePlugins.filter((p) => !p.optional);
}

/**
 * Get optional plugins only
 */
export function getOptionalPlugins(): ServicePlugin[] {
  return servicePlugins.filter((p) => p.optional);
}

/**
 * Get default URL for a service plugin
 */
export function getDefaultUrl(plugin: ServicePlugin): string {
  const path = plugin.defaultPath || '';
  return `http://localhost:${plugin.defaultPort}${path}`;
}

/**
 * Plugin color to Tailwind classes mapping
 */
export const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
  amber: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-500',
    border: 'border-amber-500/30',
  },
  blue: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-500',
    border: 'border-blue-500/30',
  },
  orange: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-500',
    border: 'border-orange-500/30',
  },
  green: {
    bg: 'bg-green-500/10',
    text: 'text-green-500',
    border: 'border-green-500/30',
  },
  purple: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-500',
    border: 'border-purple-500/30',
  },
};

/**
 * Get color classes for a service plugin
 */
export function getColorClasses(plugin: ServicePlugin): { bg: string; text: string; border: string } {
  return colorClasses[plugin.color] || colorClasses.blue;
}
