import { useState, useEffect } from 'react';
import { Tv, Loader2 } from 'lucide-react';
import { ServiceNotConnected } from '../components/ServiceNotConnected';

interface ServiceHealth {
  healthy: boolean;
}

/**
 * TV Shows Page
 *
 * Shows TV series management when Sonarr is connected,
 * or an engaging prompt to connect when not configured.
 */
export const Shows = () => {
  const [sonarrStatus, setSonarrStatus] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkSonarr = async () => {
      try {
        const response = await fetch('/health/sonarr');
        if (response.ok) {
          const data = await response.json();
          setSonarrStatus({ healthy: data.healthy === true });
        } else {
          setSonarrStatus({ healthy: false });
        }
      } catch {
        setSonarrStatus({ healthy: false });
      } finally {
        setLoading(false);
      }
    };

    checkSonarr();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // Sonarr is connected - show the TV shows interface
  if (sonarrStatus?.healthy) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-foreground mb-6">TV Shows</h1>
        <p className="text-muted-foreground">TV show management coming soon...</p>
      </div>
    );
  }

  // Sonarr not connected - show engaging connection prompt
  return (
    <ServiceNotConnected
      icon={Tv}
      serviceName="Sonarr"
      description="Manage your TV show collection with AutoArr. Track series, monitor new episodes, and automate your downloads."
      colorClass="blue"
      features={[
        { emoji: '📺', title: 'Series Tracking', description: 'Never miss an episode' },
        { emoji: '🎯', title: 'Quality Profiles', description: 'Get the best releases' },
        { emoji: '🔔', title: 'Auto-Download', description: 'Episodes on release' },
      ]}
      docsUrl="https://wiki.servarr.com/sonarr"
      testId="shows-not-connected"
    />
  );
};
