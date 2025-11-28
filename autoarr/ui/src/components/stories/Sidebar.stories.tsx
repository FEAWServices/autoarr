import type { Meta, StoryObj } from '@storybook/react-vite';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../Sidebar';

/**
 * # Sidebar Navigation
 *
 * The main navigation sidebar following the *arr family design pattern.
 *
 * ## CSS Variables (Design Tokens)
 * These can be adjusted in `src/theme/variables.css`:
 *
 * | Token | Current Value | Description |
 * |-------|---------------|-------------|
 * | `--sidebar-width` | 256px (w-64) | Total sidebar width |
 * | `--sidebar-background` | hsl(222 47% 11%) | Background color |
 * | `--sidebar-accent` | hsl(222 47% 18%) | Hover/active background |
 * | `--sidebar-border` | hsl(222 47% 18%) | Border color |
 * | `--accent-color` | hsl(280 100% 70%) | Active indicator color |
 *
 * ## Spacing Reference
 * | Element | Class | Pixels |
 * |---------|-------|--------|
 * | Nav item padding | py-3 px-6 | 12px 24px |
 * | Child item padding | py-2.5 px-6 pl-10 | 10px 24px 40px |
 * | Logo area | px-5 py-4 | 20px 16px |
 * | Left border indicator | border-l-[3px] | 3px |
 * | Icon size | w-[18px] h-[18px] | 18px |
 * | Icon margin | mr-2 | 8px |
 *
 * ## Typography Spacing Tokens (Global)
 * | Token | Value | Description |
 * |-------|-------|-------------|
 * | `--h3-padding-y` | 8px | Vertical padding on H3 headings |
 * | `--label-padding-y` | 4px | Vertical padding on labels |
 * | `--section-heading-mb` | 24px | Bottom margin on H2 section titles |
 */
// Helper to create the sidebar wrapper with router
const createSidebarDecorator = (initialPath: string) => (Story: React.ComponentType) => (
  <MemoryRouter initialEntries={[initialPath]}>
    <div style={{ height: '100vh', display: 'flex' }}>
      <Story />
      <div style={{ flex: 1, padding: '20px', background: 'hsl(222 47% 8%)' }}>
        <p style={{ color: '#888' }}>Main content area</p>
      </div>
    </div>
  </MemoryRouter>
);

const meta = {
  title: 'Layout/Sidebar',
  component: Sidebar,
  // No decorators at meta level - each story defines its own to avoid nested routers
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'Main navigation sidebar following *arr family design. Use CSS variables to customize dimensions.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Sidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default sidebar state with Home active
 */
export const Default: Story = {
  decorators: [createSidebarDecorator('/')],
};

/**
 * Sidebar with Settings expanded (showing child items)
 */
export const SettingsExpanded: Story = {
  decorators: [createSidebarDecorator('/settings')],
};

/**
 * Sidebar with Config Audit active (nested route)
 */
export const ConfigAuditActive: Story = {
  decorators: [createSidebarDecorator('/settings/config-audit')],
};

/**
 * Sidebar showing Chat as active
 */
export const ChatActive: Story = {
  decorators: [createSidebarDecorator('/chat')],
};
