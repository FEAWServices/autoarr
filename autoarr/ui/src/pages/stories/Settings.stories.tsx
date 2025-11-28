import type { Meta, StoryObj } from '@storybook/react-vite';
import { MemoryRouter } from 'react-router-dom';
import { within, expect } from 'storybook/test';
import { Settings } from '../Settings';

/**
 * # SettingsPage
 *
 * The main settings hub page that provides access to all configuration options.
 *
 * ## Component Naming Reference
 *
 * Use these names when referring to UI elements in the DOM:
 *
 * | data-component | Description |
 * |----------------|-------------|
 * | `SettingsPage` | Main page container |
 * | `SettingsPageHeader` | Title "Settings" + description |
 * | `QuickSettingsLinks` | Container for Appearance/Config Audit links |
 * | `QuickSettingsLink-Appearance` | Link to Appearance settings |
 * | `QuickSettingsLink-ConfigAudit` | Link to Config Audit |
 * | `MediaServicesSection` | Section containing all media service cards |
 * | `ServiceCard` | Individual service config card (SABnzbd, Sonarr, etc.) |
 * | `ServiceCardHeader` | Service name + enabled toggle |
 * | `ServiceCardUrlField` | URL input wrapper |
 * | `ServiceCardUrlInput` | URL text input |
 * | `ServiceCardApiKeyField` | API key/token input wrapper |
 * | `ServiceCardApiKeyInput` | API key/token password input |
 * | `ServiceCardToggleVisibility` | Show/hide password button |
 * | `ServiceCardActions` | Test connection button area |
 * | `ServiceCardTestButton` | Test Connection button |
 * | `AISearchSection` | Section for AI configuration |
 * | `AnthropicCard` | Anthropic Claude configuration card |
 * | `ApplicationSection` | Section for app settings |
 * | `ApplicationCard` | Log level and timezone card |
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
 *
 * ## CSS Variables (Design Tokens)
 *
 * ### Layout Tokens
 * | Token | Value | Description |
 * |-------|-------|-------------|
 * | `--page-padding` | 50px | Page container padding (all sides) |
 * | `--modal-bg-color` | varies by theme | Card background |
 * | `--aa-border` | varies by theme | Card border |
 * | `--accent-color` | varies by theme | Hover/active accent |
 * | `--text` | varies by theme | Primary text |
 * | `--text-muted` | varies by theme | Secondary text |
 *
 * ### Typography Spacing Tokens
 * | Token | Value | Description |
 * |-------|-------|-------------|
 * | `--h3-padding-y` | 8px | Vertical padding on H3 headings |
 * | `--h3-margin-bottom` | 16px | Bottom margin on H3 headings |
 * | `--label-padding-y` | 4px | Vertical padding on labels |
 * | `--label-margin-bottom` | 8px | Bottom margin on labels |
 * | `--section-heading-mb` | 24px | Bottom margin on H2 section titles |
 *
 * ## Layout Structure
 * ```
 * SettingsPage
 * ├── SettingsPageHeader
 * ├── QuickSettingsLinks
 * │   ├── QuickSettingsLink-Appearance
 * │   └── QuickSettingsLink-ConfigAudit
 * ├── MediaServicesSection
 * │   ├── ServiceCard (sabnzbd)
 * │   │   ├── ServiceCardHeader
 * │   │   ├── ServiceCardUrlField / ServiceCardUrlInput
 * │   │   ├── ServiceCardApiKeyField / ServiceCardApiKeyInput / ServiceCardToggleVisibility
 * │   │   └── ServiceCardActions / ServiceCardTestButton
 * │   ├── ServiceCard (sonarr)
 * │   ├── ServiceCard (radarr)
 * │   └── ServiceCard (plex)
 * ├── AISearchSection
 * │   └── AnthropicCard
 * ├── ApplicationSection
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
 * Test that service cards have the correct margin applied via CSS.
 * This verifies that the `--service-card-margin` CSS variable is working.
 */
export const ServiceCardMarginTest: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    // Find the SABnzbd service card
    const sabnzbdCard = canvas.getByTestId('service-card-sabnzbd');

    // Get computed styles
    const computedStyle = window.getComputedStyle(sabnzbdCard);

    // Assert margin is 10px (from --service-card-margin CSS variable)
    expect(computedStyle.margin).toBe('10px');
  },
};
