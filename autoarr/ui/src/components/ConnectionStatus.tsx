import { useState, useEffect, useCallback } from 'react';
import { WifiOff, RefreshCw, X } from 'lucide-react';

interface ConnectionStatusProps {
  checkInterval?: number; // How often to check (ms)
  healthEndpoint?: string;
}

export const ConnectionStatus = ({
  checkInterval = 10000, // Check every 10 seconds
  healthEndpoint = '/health',
}: ConnectionStatusProps) => {
  const [isConnected, setIsConnected] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  // @ts-expect-error - failureCount is used internally by setFailureCount callback
  const [failureCount, setFailureCount] = useState(0);

  // Returns true if connection succeeded
  const checkConnection = useCallback(async (): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(healthEndpoint, {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        setIsConnected(true);
        setFailureCount(0);
        setIsDismissed(false); // Reset dismissal on reconnect
        return true;
      } else {
        throw new Error('Health check failed');
      }
    } catch {
      setFailureCount((prev) => {
        const newCount = prev + 1;
        // Only show disconnected after 2 consecutive failures
        if (newCount >= 2) {
          setIsConnected(false);
        }
        return newCount;
      });
      return false;
    }
  }, [healthEndpoint]);

  // Initial check and periodic polling
  useEffect(() => {
    // Initial check
    checkConnection();

    // Set up interval
    const interval = setInterval(checkConnection, checkInterval);

    return () => clearInterval(interval);
  }, [checkConnection, checkInterval]);

  // Manual retry
  const handleRetry = async () => {
    setIsRetrying(true);
    const success = await checkConnection();
    setIsRetrying(false);

    // If still not connected after retry, reload the page to get a fresh start
    if (!success) {
      window.location.reload();
    }
    // If successful, the modal will automatically hide due to isConnected becoming true
  };

  // Don't show anything if connected or dismissed
  if (isConnected || isDismissed) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-gray-900 border border-red-500/50 rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-red-500/10 px-6 py-4 border-b border-red-500/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-full">
              <WifiOff className="w-6 h-6 text-red-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">Connection Lost</h2>
          </div>
          <button
            onClick={() => setIsDismissed(true)}
            className="p-1 hover:bg-gray-800 rounded transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          <p className="text-gray-300 mb-4">
            Unable to connect to the AutoArr backend server. This could be because:
          </p>
          <ul className="text-gray-400 text-sm space-y-2 mb-6">
            <li className="flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              The server is restarting or updating
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              There's a network connectivity issue
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              The Docker container has stopped
            </li>
          </ul>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
              {isRetrying ? 'Reconnecting...' : 'Retry Connection'}
            </button>
            <button
              onClick={() => setIsDismissed(true)}
              className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium rounded-lg transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>

        {/* Footer hint */}
        <div className="px-6 py-3 bg-gray-800/50 border-t border-gray-700">
          <p className="text-xs text-gray-500 text-center">
            The connection will be checked automatically. You can also refresh the page.
          </p>
        </div>
      </div>
    </div>
  );
};
