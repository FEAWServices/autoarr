import type { Meta, StoryObj } from '@storybook/react-vite';
import { MemoryRouter } from 'react-router-dom';
import { Welcome } from '../../pages/Welcome';

/**
 * # Welcome / Onboarding Page
 *
 * The main landing page shown when users first access AutoArr.
 *
 * ## Layout Spacing Reference
 *
 * ### Container
 * | Element | Class | Pixels |
 * |---------|-------|--------|
 * | Container padding | p-10 md:p-16 lg:p-20 | 40px / 64px / 80px |
 * | Max width | max-w-5xl | 1024px |
 *
 * ### Hero Section
 * | Element | Class | Pixels |
 * |---------|-------|--------|
 * | Hero bottom margin | mb-28 | 112px |
 * | Hero top padding | pt-12 | 48px |
 * | Logo wrapper margin | mb-16 | 64px |
 * | Logo box padding | p-12 | 48px |
 * | Sparkle icon size | w-28 h-28 | 112px |
 * | Title margin | mb-10 | 40px |
 * | Description margin | mb-12 | 48px |
 * | Status indicator padding | px-10 py-5 | 40px 20px |
 *
 * ### Service Cards Section ("Your Media Stack")
 * | Element | Class | Pixels |
 * |---------|-------|--------|
 * | Section margin | mb-32 | 128px |
 * | Header margin | mb-12 | 48px |
 * | Grid gap | gap-10 | 40px |
 * | Card padding | p-10 | 40px |
 * | Card border radius | rounded-2xl | 16px |
 * | Icon box padding | p-5 | 20px |
 * | Icon margin | mb-8 | 32px |
 * | Title margin | mb-4 | 16px |
 * | Description margin | mb-8 | 32px |
 *
 * ### Features Section ("What AutoArr Can Do")
 * | Element | Class | Pixels |
 * |---------|-------|--------|
 * | Section padding | pb-16 | 64px |
 * | Title margin | mb-14 | 56px |
 * | Grid gap | gap-10 | 40px |
 * | Card padding | p-10 | 40px |
 * | Icon box padding | p-5 | 20px |
 * | Icon margin | mb-8 | 32px |
 * | Title margin | mb-4 | 16px |
 *
 * ### Typography Spacing Tokens (Global)
 * These CSS variables apply to all H3 headings and labels site-wide:
 * | Token | Value | Description |
 * |-------|-------|-------------|
 * | `--h3-padding-y` | 8px | Vertical padding on H3 headings |
 * | `--h3-margin-bottom` | 16px | Bottom margin on H3 headings |
 * | `--label-padding-y` | 4px | Vertical padding on labels |
 * | `--label-margin-bottom` | 8px | Bottom margin on labels |
 * | `--section-heading-mb` | 24px | Bottom margin on H2 section titles |
 */
const meta = {
  title: 'Pages/Welcome',
  component: Welcome,
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div style={{ minHeight: '100vh' }}>
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
          'Onboarding page showing service status and feature highlights. Adjust spacing via Tailwind classes in Welcome.tsx.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Welcome>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default view - shows loading state initially, then service status
 */
export const Default: Story = {};

/**
 * Mobile viewport (375px)
 */
export const Mobile: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};

/**
 * Tablet viewport (768px)
 */
export const Tablet: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'tablet',
    },
  },
};
