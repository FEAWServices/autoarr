import { Link } from 'react-router-dom';
import { Settings, Plug, ArrowRight, LucideIcon } from 'lucide-react';

export interface ServiceFeature {
  emoji: string;
  title: string;
  description: string;
}

export interface ServiceNotConnectedProps {
  /** The icon to display (from lucide-react) */
  icon: LucideIcon;
  /** Service name (e.g., "SABnzbd", "Sonarr", "Radarr") */
  serviceName: string;
  /** Main description of what this service does */
  description: string;
  /** Color theme for the service (tailwind color name without prefix) */
  colorClass: string;
  /** Three features to highlight */
  features: [ServiceFeature, ServiceFeature, ServiceFeature];
  /** URL to documentation */
  docsUrl: string;
  /** Optional test ID */
  testId?: string;
}

/**
 * ServiceNotConnected Component
 *
 * Displays an engaging prompt when a service is not connected,
 * explaining what the service does and how to connect it.
 */
export const ServiceNotConnected = ({
  icon: Icon,
  serviceName,
  description,
  colorClass,
  features,
  docsUrl,
  testId,
}: ServiceNotConnectedProps) => {
  // Map color class to actual tailwind classes
  const getColorClasses = (color: string) => {
    const colorMap: Record<string, { glow: string; border: string; text: string; icon: string }> = {
      yellow: {
        glow: 'bg-yellow-500/20',
        border: 'border-yellow-500/30',
        text: 'text-yellow-400',
        icon: 'text-yellow-500',
      },
      blue: {
        glow: 'bg-blue-500/20',
        border: 'border-blue-500/30',
        text: 'text-blue-400',
        icon: 'text-blue-500',
      },
      orange: {
        glow: 'bg-orange-500/20',
        border: 'border-orange-500/30',
        text: 'text-orange-400',
        icon: 'text-orange-500',
      },
      amber: {
        glow: 'bg-amber-500/20',
        border: 'border-amber-500/30',
        text: 'text-amber-400',
        icon: 'text-amber-500',
      },
    };
    return colorMap[color] || colorMap.yellow;
  };

  const colors = getColorClasses(colorClass);

  return (
    <div
      data-testid={testId}
      data-component="ServiceNotConnected"
      className="flex items-center justify-center h-full p-8 bg-gradient-to-b from-background to-[hsl(280,50%,15%)]"
    >
      <div className="text-center max-w-lg">
        {/* Icon with glow effect */}
        <div
          data-component="ServiceIcon"
          className="relative mb-8 flex justify-center"
        >
          <div className={`absolute inset-[-30%] animate-pulse rounded-full ${colors.glow} blur-2xl`} />
          <div className={`relative p-6 rounded-2xl bg-card/50 ${colors.border} backdrop-blur-sm shadow-[0_0_40px_rgba(168,85,247,0.2)]`}>
            <Icon className={`w-12 h-12 ${colors.icon}`} />
          </div>
        </div>

        {/* Title */}
        <h1
          data-component="ServiceTitle"
          className="text-3xl font-bold text-foreground mb-4"
        >
          Connect to {serviceName}
        </h1>

        {/* Description */}
        <p
          data-component="ServiceDescription"
          className="text-lg text-muted-foreground mb-8 leading-relaxed"
        >
          {description}
        </p>

        {/* Feature highlights */}
        <div
          data-component="FeatureGrid"
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10"
        >
          {features.map((feature, index) => (
            <div
              key={index}
              data-component="FeatureCard"
              className="p-4 rounded-xl bg-card/50 border border-primary/20 backdrop-blur-sm"
            >
              <div className="text-2xl mb-2">{feature.emoji}</div>
              <div className="text-sm font-medium text-foreground">{feature.title}</div>
              <div className="text-xs text-muted-foreground mt-1">{feature.description}</div>
            </div>
          ))}
        </div>

        {/* Connection status indicator */}
        <div
          data-component="StatusIndicator"
          className={`inline-flex items-center gap-3 px-5 py-3 rounded-full bg-card/50 ${colors.border} backdrop-blur-sm mb-8`}
        >
          <Plug className={`w-4 h-4 ${colors.icon}`} />
          <span className={`text-sm ${colors.text}`}>{serviceName} not connected</span>
        </div>

        {/* CTA Button */}
        <div data-component="CTAButton">
          <Link
            to="/settings"
            className="inline-flex items-center gap-3 px-8 py-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl font-medium transition-all duration-300 shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)] hover:scale-105"
          >
            <Settings className="w-5 h-5" />
            <span>Configure {serviceName}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Help text */}
        <p
          data-component="HelpText"
          className="mt-6 text-sm text-muted-foreground"
        >
          Need help? Check out{' '}
          <a
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 underline"
          >
            {serviceName} documentation
          </a>
        </p>
      </div>
    </div>
  );
};
