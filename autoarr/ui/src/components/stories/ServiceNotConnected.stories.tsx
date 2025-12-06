import type { Meta, StoryObj } from '@storybook/react-vite';
import { MemoryRouter } from 'react-router-dom';
import { Download, Tv, Film, Server } from 'lucide-react';
import { ServiceNotConnected } from '../ServiceNotConnected';

/**
 * # ServiceNotConnected
 *
 * Displays an engaging prompt when a media automation service is not connected.
 * Used across all service-specific pages (Downloads, Shows, Movies, Media).
 *
 * ## Usage
 * This component should be shown when the health check for a service fails
 * or returns `healthy: false`. It provides:
 *
 * - Visual indicator with service-specific icon and color
 * - Description of what the service does
 * - Three feature highlights
 * - Connection status indicator
 * - CTA button to configure the service
 * - Link to service documentation
 *
 * ## Color Themes
 * | Service | Color |
 * |---------|-------|
 * | SABnzbd | yellow |
 * | Sonarr | blue |
 * | Radarr | orange |
 * | Plex | amber |
 *
 * ## Component Hierarchy
 * | data-component | Description |
 * |----------------|-------------|
 * | `ServiceNotConnected` | Root container |
 * | `ServiceIcon` | Icon with glow effect |
 * | `ServiceTitle` | "Connect to {Service}" heading |
 * | `ServiceDescription` | Main description text |
 * | `FeatureGrid` | 3-column feature grid |
 * | `FeatureCard` | Individual feature card |
 * | `StatusIndicator` | Connection status pill |
 * | `CTAButton` | Configure button |
 * | `HelpText` | Documentation link |
 */

const meta = {
  title: 'Pages/ServiceNotConnected',
  component: ServiceNotConnected,
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div style={{ height: '100vh', background: 'hsl(222 47% 11%)' }}>
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'Engaging prompt shown when a service is not connected. Guides users to configure the service.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    colorClass: {
      control: 'select',
      options: ['yellow', 'blue', 'orange', 'amber'],
      description: 'Color theme for the service',
    },
  },
} satisfies Meta<typeof ServiceNotConnected>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * SABnzbd not connected - Download management
 */
export const SABnzbd: Story = {
  args: {
    icon: Download,
    serviceName: 'SABnzbd',
    description:
      'Monitor your downloads in real-time with AutoArr. Track progress, manage queues, and get automatic failure recovery.',
    colorClass: 'yellow',
    features: [
      { emoji: '📊', title: 'Real-time Progress', description: 'Live speed and ETA' },
      { emoji: '🔄', title: 'Smart Recovery', description: 'Auto-retry failures' },
      { emoji: '📋', title: 'Queue Control', description: 'Pause, resume, prioritize' },
    ],
    docsUrl: 'https://sabnzbd.org/wiki/configuration',
    testId: 'downloads-not-connected',
  },
};

/**
 * Sonarr not connected - TV show management
 */
export const Sonarr: Story = {
  args: {
    icon: Tv,
    serviceName: 'Sonarr',
    description:
      'Manage your TV show collection with AutoArr. Track series, monitor new episodes, and automate your downloads.',
    colorClass: 'blue',
    features: [
      { emoji: '📺', title: 'Series Tracking', description: 'Never miss an episode' },
      { emoji: '🎯', title: 'Quality Profiles', description: 'Get the best releases' },
      { emoji: '🔔', title: 'Auto-Download', description: 'Episodes on release' },
    ],
    docsUrl: 'https://wiki.servarr.com/sonarr',
    testId: 'shows-not-connected',
  },
};

/**
 * Radarr not connected - Movie management
 */
export const Radarr: Story = {
  args: {
    icon: Film,
    serviceName: 'Radarr',
    description:
      'Build your movie collection with AutoArr. Discover films, track releases, and automatically download in your preferred quality.',
    colorClass: 'orange',
    features: [
      { emoji: '🎬', title: 'Movie Discovery', description: 'Find new films' },
      { emoji: '⬆️', title: 'Auto-Upgrade', description: 'Better quality when available' },
      { emoji: '📅', title: 'Release Tracking', description: 'Get movies on release' },
    ],
    docsUrl: 'https://wiki.servarr.com/radarr',
    testId: 'movies-not-connected',
  },
};

/**
 * Plex not connected - Media server
 */
export const Plex: Story = {
  args: {
    icon: Server,
    serviceName: 'Plex',
    description:
      'Stream your media anywhere with Plex integration. Browse libraries, trigger scans, and keep your collection organized.',
    colorClass: 'amber',
    features: [
      { emoji: '🎥', title: 'Library Browse', description: 'View all your media' },
      { emoji: '🔄', title: 'Auto Scan', description: 'Detect new content' },
      { emoji: '📱', title: 'Stream Anywhere', description: 'Watch on any device' },
    ],
    docsUrl: 'https://support.plex.tv/',
    testId: 'media-not-connected',
  },
};
