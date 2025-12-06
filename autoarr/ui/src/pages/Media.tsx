import { useState, useEffect } from 'react';
import { Server, Loader2 } from 'lucide-react';
import { ServiceNotConnected } from '../components/ServiceNotConnected';

interface ServiceHealth {
  healthy: boolean;
}

/**
 * Media Server Page
 *
 * Shows Plex media server integration when connected,
 * or an engaging prompt to connect when not configured.
 */
export const Media = () => {
  const [plexStatus, setPlexStatus] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkPlex = async () => {
      try {
        const response = await fetch('/health/plex');
        if (response.ok) {
          const data = await response.json();
          setPlexStatus({ healthy: data.healthy === true });
        } else {
          setPlexStatus({ healthy: false });
        }
      } catch {
        setPlexStatus({ healthy: false });
      } finally {
        setLoading(false);
      }
    };

    checkPlex();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // Plex is connected - show the media server interface
  if (plexStatus?.healthy) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-foreground mb-6">Media Server</h1>
        <p className="text-muted-foreground">Plex integration coming soon...</p>
      </div>
    );
  }

  // Plex not connected - show engaging connection prompt
  return (
    <ServiceNotConnected
      icon={Server}
      serviceName="Plex"
      description="Stream your media anywhere with Plex integration. Browse libraries, trigger scans, and keep your collection organized."
      colorClass="amber"
      features={[
        { emoji: '🎥', title: 'Library Browse', description: 'View all your media' },
        { emoji: '🔄', title: 'Auto Scan', description: 'Detect new content' },
        { emoji: '📱', title: 'Stream Anywhere', description: 'Watch on any device' },
      ]}
      docsUrl="https://support.plex.tv/"
      testId="media-not-connected"
    />
  );
};
