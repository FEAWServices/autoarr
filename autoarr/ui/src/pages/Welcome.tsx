import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Download,
  Tv,
  Film,
  Server,
  Settings,
  ChevronRight,
  ExternalLink,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface ServiceStatus {
  name: string;
  key: string;
  description: string;
  url: string;
  icon: React.ReactNode;
  color: string;
  configured: boolean;
  connected: boolean;
}

/**
 * Welcome / Onboarding Page
 *
 * Shows when no services are configured, guiding users through setup.
 * Once at least one service is configured, shows the regular dashboard.
 */
export const Welcome = () => {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: 'SABnzbd',
      key: 'sabnzbd',
      description: 'Usenet download client for automated binary downloading',
      url: 'https://sabnzbd.org/',
      icon: <Download className="w-8 h-8" />,
      color: 'text-yellow-500',
      configured: false,
      connected: false,
    },
    {
      name: 'Sonarr',
      key: 'sonarr',
      description: 'TV show management and automatic episode downloading',
      url: 'https://sonarr.tv/',
      icon: <Tv className="w-8 h-8" />,
      color: 'text-blue-500',
      configured: false,
      connected: false,
    },
    {
      name: 'Radarr',
      key: 'radarr',
      description: 'Movie collection manager with automatic quality upgrades',
      url: 'https://radarr.video/',
      icon: <Film className="w-8 h-8" />,
      color: 'text-orange-500',
      configured: false,
      connected: false,
    },
    {
      name: 'Plex',
      key: 'plex',
      description: 'Media server to stream your content anywhere',
      url: 'https://www.plex.tv/',
      icon: <Server className="w-8 h-8" />,
      color: 'text-amber-400',
      configured: false,
      connected: false,
    },
  ]);

  const [loading, setLoading] = useState(true);

  // Check which services are configured
  useEffect(() => {
    const serviceKeys = ['sabnzbd', 'sonarr', 'radarr', 'plex'];

    const checkServices = async () => {
      try {
        // Check health of each service
        const healthChecks = await Promise.all(
          serviceKeys.map(async (key) => {
            try {
              const response = await fetch(`/health/${key}`);
              if (response.ok) {
                return { key, configured: true, connected: true };
              }
              // Service configured but not connected
              return { key, configured: true, connected: false };
            } catch {
              return { key, configured: false, connected: false };
            }
          })
        );

        setServices((prev) =>
          prev.map((service) => {
            const check = healthChecks.find((h) => h.key === service.key);
            return check
              ? { ...service, configured: check.configured, connected: check.connected }
              : service;
          })
        );
      } catch (error) {
        console.error('Failed to check service status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkServices();
  }, []);

  const configuredCount = services.filter((s) => s.configured).length;
  const hasAnyConfigured = configuredCount > 0;

  return (
    <div className="min-h-full bg-gradient-to-b from-background to-[hsl(280,50%,15%)] p-10 md:p-16 lg:p-20">
      {/* Hero Section */}
      <section className="max-w-5xl mx-auto text-center mb-28 pt-12">
        {/* Logo with Glow */}
        <div className="relative mb-16 flex justify-center">
          <div className="absolute inset-[-50%] animate-pulse rounded-full bg-primary/30 blur-3xl" />
          <div className="relative p-12 rounded-3xl bg-card/50 border border-primary/30 backdrop-blur-sm shadow-[0_0_60px_rgba(168,85,247,0.4)]">
            <Sparkles className="w-28 h-28 text-primary drop-shadow-[0_0_30px_rgba(168,85,247,0.6)]" />
          </div>
        </div>

        {/* Title */}
        <h1 className="mb-10 bg-gradient-to-r from-primary via-accent to-[hsl(290,90%,70%)] bg-clip-text text-5xl md:text-6xl font-bold text-transparent">
          Welcome to AutoArr
        </h1>

        <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-12 leading-relaxed">
          Your intelligent media automation companion. AutoArr connects to your media stack and
          helps you manage downloads, optimize configurations, and automate your library.
        </p>

        {/* Status indicator */}
        <div className="inline-flex items-center gap-4 px-10 py-5 rounded-full bg-card/50 border border-primary/20 backdrop-blur-sm">
          {loading ? (
            <>
              <div className="w-3 h-3 bg-primary rounded-full animate-pulse" />
              <span className="text-muted-foreground">Checking services...</span>
            </>
          ) : hasAnyConfigured ? (
            <>
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-green-400">
                {configuredCount} of {services.length} services connected
              </span>
            </>
          ) : (
            <>
              <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" />
              <span className="text-yellow-400">No services configured yet</span>
            </>
          )}
        </div>
      </section>

      {/* Get Started Section */}
      <section className="max-w-5xl mx-auto mb-32">
        <div className="flex items-center justify-between mb-12">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4">
              {hasAnyConfigured ? 'Your Media Stack' : 'Get Started'}
            </h2>
            <p className="text-muted-foreground text-lg">
              {hasAnyConfigured
                ? 'Manage your connected services'
                : 'Connect your media automation services to unlock the full power of AutoArr'}
            </p>
          </div>

          <Link
            to="/settings"
            className="flex items-center gap-3 px-8 py-5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl font-medium transition-all duration-300 shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)]"
          >
            <Settings className="w-5 h-5" />
            <span>Configure Services</span>
          </Link>
        </div>

        {/* Service Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {services.map((service) => (
            <div
              key={service.key}
              className={`rounded-2xl border bg-card/50 backdrop-blur-sm p-10 transition-all duration-300 hover:scale-[1.02] ${
                service.connected
                  ? 'border-green-500/30 hover:shadow-[0_0_30px_rgba(34,197,94,0.2)]'
                  : service.configured
                    ? 'border-yellow-500/30 hover:shadow-[0_0_30px_rgba(234,179,8,0.2)]'
                    : 'border-primary/20 hover:shadow-[0_0_30px_rgba(168,85,247,0.2)]'
              }`}
            >
              <div className="flex items-start justify-between mb-8">
                <div className={`p-5 rounded-xl bg-card/80 ${service.color}`}>{service.icon}</div>

                {service.connected ? (
                  <div className="flex items-center gap-2 text-green-400">
                    <CheckCircle className="w-5 h-5" />
                    <span className="text-sm font-medium">Connected</span>
                  </div>
                ) : service.configured ? (
                  <div className="flex items-center gap-2 text-yellow-400">
                    <XCircle className="w-5 h-5" />
                    <span className="text-sm font-medium">Not Reachable</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <span className="text-sm">Not Configured</span>
                  </div>
                )}
              </div>

              <h3 className="text-2xl font-semibold text-foreground mb-4">{service.name}</h3>
              <p className="text-muted-foreground mb-8 leading-relaxed text-base">
                {service.description}
              </p>

              <a
                href={service.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
              >
                Learn more about {service.name}
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-5xl mx-auto pb-16">
        <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-14 text-center">
          What AutoArr Can Do
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          <Link
            to="/chat"
            className="rounded-2xl border border-primary/20 bg-card/50 backdrop-blur-sm p-10 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(168,85,247,0.3)] hover:border-primary/40 group"
          >
            <div className="p-5 rounded-xl bg-primary/20 w-fit mb-8">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
              Natural Language Requests
              <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </h3>
            <p className="text-muted-foreground leading-relaxed text-base">
              Ask AutoArr to download movies or TV shows using natural language. Just describe what
              you want!
            </p>
          </Link>

          <Link
            to="/settings/config-audit"
            className="rounded-2xl border border-primary/20 bg-card/50 backdrop-blur-sm p-10 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(168,85,247,0.3)] hover:border-primary/40 group"
          >
            <div className="p-5 rounded-xl bg-green-500/20 w-fit mb-8">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
              Configuration Audit
              <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </h3>
            <p className="text-muted-foreground leading-relaxed text-base">
              AI-powered analysis of your service configurations with recommendations for optimal
              performance.
            </p>
          </Link>

          <Link
            to="/downloads"
            className="rounded-2xl border border-primary/20 bg-card/50 backdrop-blur-sm p-10 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(168,85,247,0.3)] hover:border-primary/40 group"
          >
            <div className="p-5 rounded-xl bg-blue-500/20 w-fit mb-8">
              <Download className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
              Download Monitoring
              <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </h3>
            <p className="text-muted-foreground leading-relaxed text-base">
              Monitor your downloads in real-time with automatic failure recovery and intelligent
              retry logic.
            </p>
          </Link>
        </div>
      </section>
    </div>
  );
};
// Trigger rebuild 1764243387
