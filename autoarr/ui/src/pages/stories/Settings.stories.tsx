import type { Meta, StoryObj } from '@storybook/react-vite';
import { MemoryRouter } from 'react-router-dom';
import { within, expect } from 'storybook/test';
import { Settings } from '../Settings';

/**
 * # SettingsPage
 *
 * The main settings hub page that provides access to all configuration options.
 * Uses a responsive 2-column grid layout for service cards.
 *
 * ## Component Naming Reference
 *
 * Use these names when referring to UI elements in the DOM:
 *
 * | data-component | Description |
 * |----------------|-------------|
 * | `SettingsPage` | Main page container |
 * | `SettingsPageHeader` | Title "Settings" + description |
 * | `QuickSettingsLinks` | 2-column grid for Appearance/Config Audit links |
 * | `QuickSettingsLink-Appearance` | Link to Appearance settings |
 * | `QuickSettingsLink-ConfigAudit` | Link to Config Audit |
 * | `MediaServicesSection` | 2-column grid containing service cards |
 * | `ServiceCard` | Compact service config card (SABnzbd, Sonarr, etc.) |
 * | `ServiceCardHeader` | Service name + enabled toggle |
 * | `ServiceCardUrlField` | URL input wrapper |
 * | `ServiceCardUrlInput` | URL text input |
 * | `ServiceCardApiKeyField` | API key/token input wrapper |
 * | `ServiceCardApiKeyInput` | API key/token password input |
 * | `ServiceCardToggleVisibility` | Show/hide password button |
 * | `ServiceCardActions` | Test connection button area |
 * | `ServiceCardTestButton` | Test Connection button |
 * | `AIAndAppSection` | 2-column grid for AI and App settings |
 * | `OpenRouterCard` | OpenRouter LLM configuration card |
 * | `OpenRouterCardHeader` | OpenRouter name + enabled toggle |
 * | `ApplicationCard` | Log level and timezone card |
 * | `ApplicationCardHeader` | Application card header |
 * | `SaveButtonSection` | Save button area |
 * | `SaveButton` | Main save button |
 *
 * ## Test IDs
 *
 * | data-testid | Description |
 * |-------------|-------------|
 * | `settings-page` | Main page container |
 * | `service-card-sabnzbd` | SABnzbd service card |
 * | `service-card-sonarr` | Sonarr service card |
 * | `service-card-radarr` | Radarr service card |
 * | `service-card-plex` | Plex service card |
 * | `openrouter-card` | OpenRouter configuration card |
 * | `openrouter-enabled` | OpenRouter enabled checkbox |
 * | `openrouter-api-key` | OpenRouter API key input |
 * | `openrouter-model` | OpenRouter model input |
 * | `openrouter-test-button` | OpenRouter test connection button |
 *
 * ## Responsive Layout
 *
 * - **Desktop (md+)**: 2-column grid for all card sections
 * - **Mobile (<md)**: Single column, cards stack vertically
 *
 * ## Layout Structure
 * ```
 * SettingsPage
 * ├── SettingsPageHeader
 * ├── QuickSettingsLinks (grid cols-1 md:cols-2)
 * │   ├── QuickSettingsLink-Appearance
 * │   └── QuickSettingsLink-ConfigAudit
 * ├── MediaServicesSection (grid cols-1 md:cols-2)
 * │   ├── ServiceCard (sabnzbd)
 * │   ├── ServiceCard (sonarr)
 * │   ├── ServiceCard (radarr)
 * │   └── ServiceCard (plex)
 * ├── AIAndAppSection (grid cols-1 md:cols-2)
 * │   ├── OpenRouterCard
 * │   └── ApplicationCard
 * └── SaveButtonSection
 *     └── SaveButton
 * ```
 */
const meta = {
  title: 'Pages/SettingsPage',
  component: Settings,
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/settings']}>
        <div
          style={{
            minHeight: '100vh',
            background: 'hsl(222 47% 8%)',
          }}
        >
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
          'Main settings hub page with service configuration, API keys, and application settings. All elements have data-component attributes for easy identification.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Settings>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default view of the Settings page with all sections visible.
 * The page has 50px padding on all sides via `--page-padding` CSS variable.
 */
export const Default: Story = {};

/**
 * Settings page at mobile viewport (375px width).
 * Content adjusts to narrower width while maintaining padding.
 */
export const Mobile: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};

/**
 * Settings page at tablet viewport (768px width).
 */
export const Tablet: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'tablet',
    },
  },
};

/**
 * Test that service cards are displayed in a 2-column grid on desktop.
 * This verifies the responsive grid layout is working.
 */
export const ServiceCardGridTest: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    // Find the SABnzbd service card
    const sabnzbdCard = canvas.getByTestId('service-card-sabnzbd');

    // Verify the card exists and has the compact styling
    expect(sabnzbdCard).toBeInTheDocument();

    // Check the parent grid container has proper grid styles
    const gridContainer = sabnzbdCard.parentElement;
    const computedStyle = window.getComputedStyle(gridContainer!);
    expect(computedStyle.display).toBe('grid');
  },
};
