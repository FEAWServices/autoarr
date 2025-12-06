import { useState, useEffect } from 'react';
import { Film, Loader2 } from 'lucide-react';
import { ServiceNotConnected } from '../components/ServiceNotConnected';

interface ServiceHealth {
  healthy: boolean;
}

/**
 * Movies Page
 *
 * Shows movie management when Radarr is connected,
 * or an engaging prompt to connect when not configured.
 */
export const Movies = () => {
  const [radarrStatus, setRadarrStatus] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkRadarr = async () => {
      try {
        const response = await fetch('/health/radarr');
        if (response.ok) {
          const data = await response.json();
          setRadarrStatus({ healthy: data.healthy === true });
        } else {
          setRadarrStatus({ healthy: false });
        }
      } catch {
        setRadarrStatus({ healthy: false });
      } finally {
        setLoading(false);
      }
    };

    checkRadarr();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // Radarr is connected - show the movies interface
  if (radarrStatus?.healthy) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-foreground mb-6">Movies</h1>
        <p className="text-muted-foreground">Movie management coming soon...</p>
      </div>
    );
  }

  // Radarr not connected - show engaging connection prompt
  return (
    <ServiceNotConnected
      icon={Film}
      serviceName="Radarr"
      description="Build your movie collection with AutoArr. Discover films, track releases, and automatically download in your preferred quality."
      colorClass="orange"
      features={[
        { emoji: '🎬', title: 'Movie Discovery', description: 'Find new films' },
        { emoji: '⬆️', title: 'Auto-Upgrade', description: 'Better quality when available' },
        { emoji: '📅', title: 'Release Tracking', description: 'Get movies on release' },
      ]}
      docsUrl="https://wiki.servarr.com/radarr"
      testId="movies-not-connected"
    />
  );
};
