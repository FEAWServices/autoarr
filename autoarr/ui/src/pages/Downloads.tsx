import { useState, useEffect } from 'react';
import { Download, Loader2, Play, Pause, X, RefreshCw, Clock, HardDrive } from 'lucide-react';
import { ServiceNotConnected } from '../components/ServiceNotConnected';
import { websocketService } from '../services/websocket';
import type { WebSocketEvent } from '../types/chat';

interface ServiceHealth {
  healthy: boolean;
}

interface QueueItem {
  nzo_id: string;
  filename: string;
  status: string;
  percentage: number;
  mb_left: number;
  mb_total: number;
  category: string;
  priority: string;
  eta: string;
  speed?: string;
}

/**
 * Progress bar component with color based on percentage
 */
const ProgressBar = ({ percentage }: { percentage: number }) => {
  const getColor = (pct: number) => {
    if (pct < 30) return 'bg-red-500';
    if (pct < 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
      <div
        className={`h-2.5 ${getColor(percentage)} transition-all duration-300`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

/**
 * Download card component
 */
const DownloadCard = ({ item }: { item: QueueItem }) => {
  const statusColors: Record<string, string> = {
    downloading: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    paused: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    queued: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    extracting: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
    moving: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  };

  const statusColor = statusColors[item.status.toLowerCase()] || statusColors.queued;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:border-gray-300 dark:hover:border-gray-600 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {item.filename}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-2 py-0.5 rounded-full ${statusColor}`}>
              {item.status}
            </span>
            {item.category && (
              <span className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                {item.category}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            title="Pause/Resume"
          >
            {item.status.toLowerCase() === 'paused' ? (
              <Play className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            ) : (
              <Pause className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            )}
          </button>
          <button
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            title="Cancel"
          >
            <X className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span className="font-medium">{item.percentage}%</span>
          <span>
            {item.mb_left.toFixed(2)} MB / {item.mb_total.toFixed(2)} MB
          </span>
        </div>
        <ProgressBar percentage={item.percentage} />
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-4">
          {item.speed && (
            <div className="flex items-center gap-1">
              <Download className="w-3 h-3" />
              <span>{item.speed}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{item.eta || 'Unknown'}</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
            {item.priority}
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * Downloads Page
 *
 * Shows download monitoring when SABnzbd is connected,
 * or an engaging prompt to connect when not configured.
 */
export const Downloads = () => {
  const [sabnzbdStatus, setSabnzbdStatus] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [queueStats, setQueueStats] = useState({ speed: '0 MB/s', total: 0 });

  // Check SABnzbd health
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

  // Fetch queue data
  const fetchQueue = async () => {
    try {
      const response = await fetch('/api/v1/downloads/queue');
      if (response.ok) {
        const data = await response.json();
        setQueue(data.items || []);
        setQueueStats({
          speed: data.speed || '0 MB/s',
          total: data.items?.length || 0,
        });
      }
    } catch (error) {
      console.error('Failed to fetch queue:', error);
    }
  };

  // Initial fetch and periodic refresh
  useEffect(() => {
    if (sabnzbdStatus?.healthy) {
      fetchQueue();
      const interval = setInterval(fetchQueue, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [sabnzbdStatus]);

  // Listen for WebSocket download events
  useEffect(() => {
    const handleDownloadEvent = (event: WebSocketEvent) => {
      if (event.type === 'event') {
        const eventType = event.event_type;

        // Refresh queue on download state changes
        if (
          eventType === 'download_started' ||
          eventType === 'download_completed' ||
          eventType === 'download_failed' ||
          eventType === 'download_paused' ||
          eventType === 'download_resumed' ||
          eventType === 'download_state_changed'
        ) {
          // Debounce queue refresh
          setTimeout(fetchQueue, 500);
        }
      }
    };

    websocketService.on('event', handleDownloadEvent);

    return () => {
      websocketService.off('event', handleDownloadEvent);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  // SABnzbd not connected - show engaging connection prompt
  if (!sabnzbdStatus?.healthy) {
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
  }

  // SABnzbd is connected - show the downloads interface
  return (
    <div className="flex flex-col h-full" style={{ padding: 'var(--page-padding, 50px)' }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Download className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Downloads</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {queueStats.total} active downloads • {queueStats.speed}
            </p>
          </div>
        </div>

        <button
          onClick={fetchQueue}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <Download className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Speed</span>
          </div>
          <div className="text-xl font-bold text-gray-900 dark:text-white">
            {queueStats.speed}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <HardDrive className="w-4 h-4 text-green-600 dark:text-green-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Queue</span>
          </div>
          <div className="text-xl font-bold text-gray-900 dark:text-white">
            {queueStats.total}
          </div>
        </div>
      </div>

      {/* Queue List */}
      <div className="flex-1 overflow-auto">
        {queue.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <Download className="w-12 h-12 mb-4 opacity-50" />
            <p>No active downloads</p>
          </div>
        ) : (
          <div className="space-y-4">
            {queue.map((item) => (
              <DownloadCard key={item.nzo_id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
