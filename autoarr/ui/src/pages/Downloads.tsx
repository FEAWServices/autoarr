import { useState, useEffect } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { ServiceNotConnected } from '../components/ServiceNotConnected';

interface ServiceHealth {
  healthy: boolean;
}

/**
 * Downloads Page
 *
 * Shows download monitoring when SABnzbd is connected,
 * or an engaging prompt to connect when not configured.
 */
export const Downloads = () => {
  const [sabnzbdStatus, setSabnzbdStatus] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkSabnzbd = async () => {
      try {
        const response = await fetch('/health/sabnzbd');
        if (response.ok) {
          const data = await response.json();
          setSabnzbdStatus({ healthy: data.healthy === true });
        } else {
          setSabnzbdStatus({ healthy: false });
        }
      } catch {
        setSabnzbdStatus({ healthy: false });
      } finally {
        setLoading(false);
      }
    };

    checkSabnzbd();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // SABnzbd is connected - show the downloads interface
  if (sabnzbdStatus?.healthy) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-foreground mb-6">Downloads</h1>
        <p className="text-muted-foreground">Download monitoring coming soon...</p>
      </div>
    );
  }

  // SABnzbd not connected - show engaging connection prompt
  return (
    <ServiceNotConnected
      icon={Download}
      serviceName="SABnzbd"
      description="Monitor your downloads in real-time with AutoArr. Track progress, manage queues, and get automatic failure recovery."
      colorClass="yellow"
      features={[
        { emoji: '📊', title: 'Real-time Progress', description: 'Live speed and ETA' },
        { emoji: '🔄', title: 'Smart Recovery', description: 'Auto-retry failures' },
        { emoji: '📋', title: 'Queue Control', description: 'Pause, resume, prioritize' },
      ]}
      docsUrl="https://sabnzbd.org/wiki/configuration"
      testId="downloads-not-connected"
    />
  );
};
