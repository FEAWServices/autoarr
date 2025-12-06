import type { Meta, StoryObj } from '@storybook/react-vite';
import { Bot } from 'lucide-react';

/**
 * # AIConnectionStatus
 *
 * Shows the real-time connection status of the AI Assistant.
 * This indicator appears in the Chat header to inform users whether
 * live updates are available.
 *
 * ## States
 * - **Online** (green): AI Assistant connected, real-time updates active
 * - **Connecting** (yellow): Establishing connection to AI Assistant
 * - **Offline** (yellow): No live updates, but chat still works
 *
 * ## Usage
 * The component uses native `title` attribute for tooltip on hover.
 * Users can hover to understand what the status means.
 *
 * ## Component Reference
 * | data-component | Description |
 * |----------------|-------------|
 * | `AIConnectionStatus` | The status indicator container |
 *
 * ## Test IDs
 * | data-testid | Description |
 * |-------------|-------------|
 * | `connection-status` | The status indicator element |
 */

// Standalone component for Storybook
const AIConnectionStatus = ({
  status,
}: {
  status: 'connected' | 'connecting' | 'disconnected';
}) => {
  const getTooltip = () => {
    switch (status) {
      case 'connected':
        return 'AI Assistant is online and ready to help with real-time updates';
      case 'connecting':
        return 'Connecting to AI Assistant for real-time updates...';
      default:
        return 'AI Assistant offline - chat still works, but no live updates';
    }
  };

  const getLabel = () => {
    switch (status) {
      case 'connected':
        return 'AI Online';
      case 'connecting':
        return 'Connecting...';
      default:
        return 'AI Offline';
    }
  };

  const isOnline = status === 'connected';

  return (
    <div
      data-testid="connection-status"
      data-component="AIConnectionStatus"
      className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-card/50 border border-primary/20 cursor-help"
      aria-label={`AI Assistant status: ${status}`}
      title={getTooltip()}
    >
      <Bot
        className={`w-3.5 h-3.5 ${isOnline ? 'text-green-500' : 'text-yellow-500'}`}
      />
      <span
        className={`text-xs font-medium ${isOnline ? 'text-green-500' : 'text-yellow-500'}`}
      >
        {getLabel()}
      </span>
    </div>
  );
};

const meta = {
  title: 'Chat/AIConnectionStatus',
  component: AIConnectionStatus,
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'dark',
      values: [{ name: 'dark', value: 'hsl(222 47% 11%)' }],
    },
    docs: {
      description: {
        component:
          'Displays the AI Assistant connection status with tooltip explanation. Uses Bot icon instead of WiFi to clearly indicate this is about the AI service.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    status: {
      control: 'select',
      options: ['connected', 'connecting', 'disconnected'],
      description: 'Current connection status',
    },
  },
} satisfies Meta<typeof AIConnectionStatus>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * AI Assistant is online and ready for real-time updates
 */
export const Online: Story = {
  args: {
    status: 'connected',
  },
};

/**
 * Currently establishing connection to AI Assistant
 */
export const Connecting: Story = {
  args: {
    status: 'connecting',
  },
};

/**
 * AI Assistant is offline - chat still works but no live updates
 */
export const Offline: Story = {
  args: {
    status: 'disconnected',
  },
};

/**
 * All three states displayed together for comparison
 */
export const AllStates: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <span className="text-xs text-gray-400 w-24">Online:</span>
        <AIConnectionStatus status="connected" />
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs text-gray-400 w-24">Connecting:</span>
        <AIConnectionStatus status="connecting" />
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs text-gray-400 w-24">Offline:</span>
        <AIConnectionStatus status="disconnected" />
      </div>
    </div>
  ),
};
