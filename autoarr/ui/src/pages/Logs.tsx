import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Trash2,
  Pause,
  Play,
  Search,
  Filter,
  RefreshCw,
  Download,
  AlertCircle,
  Info,
  Bug,
  AlertTriangle,
} from 'lucide-react';

interface LogEntry {
  timestamp: string;
  level: string;
  logger_name: string;
  message: string;
  request_id?: string;
}

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR'] as const;
type LogLevel = (typeof LOG_LEVELS)[number];

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: 'text-gray-400',
  INFO: 'text-blue-400',
  WARNING: 'text-yellow-400',
  ERROR: 'text-red-400',
  CRITICAL: 'text-red-600',
};

const LEVEL_BG_COLORS: Record<string, string> = {
  DEBUG: 'bg-gray-800',
  INFO: 'bg-blue-900/30',
  WARNING: 'bg-yellow-900/30',
  ERROR: 'bg-red-900/30',
  CRITICAL: 'bg-red-900/50',
};

const LEVEL_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  DEBUG: Bug,
  INFO: Info,
  WARNING: AlertTriangle,
  ERROR: AlertCircle,
  CRITICAL: AlertCircle,
};

export const Logs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [filterLevel, setFilterLevel] = useState<LogLevel | ''>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [currentLogLevel, setCurrentLogLevel] = useState('INFO');
  const [isClearing, setIsClearing] = useState(false);
  const [isChangingLevel, setIsChangingLevel] = useState(false);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pausedLogsRef = useRef<LogEntry[]>([]);

  // Maximum logs to keep in memory to prevent browser slowdown
  const MAX_LOGS = 500;

  // Auto-scroll to bottom when new logs arrive (unless paused)
  const scrollToBottom = useCallback(() => {
    if (!isPaused && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isPaused]);

  // Fetch current log level
  const fetchLogLevel = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/logs/level');
      if (response.ok) {
        const data = await response.json();
        setCurrentLogLevel(data.level);
      }
    } catch (error) {
      console.error('Failed to fetch log level:', error);
    }
  }, []);

  // Fetch initial logs via REST
  const fetchLogs = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: '200' });
      if (filterLevel) params.append('level', filterLevel);
      if (searchTerm) params.append('search', searchTerm);

      const response = await fetch(`/api/v1/logs?${params}`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs);
        setTimeout(scrollToBottom, 100);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  }, [filterLevel, searchTerm, scrollToBottom]);

  // Set up WebSocket connection for real-time logs
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/logs/stream`;

    const connect = () => {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        // Send initial filters
        if (filterLevel) {
          ws.send(JSON.stringify({ type: 'set_level', level: filterLevel }));
        }
        if (searchTerm) {
          ws.send(JSON.stringify({ type: 'set_search', search: searchTerm }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Ignore ping messages
          if (data.type === 'ping') return;

          const entry: LogEntry = data;

          if (isPaused) {
            // Store in paused buffer
            pausedLogsRef.current.push(entry);
            // Limit paused buffer size
            if (pausedLogsRef.current.length > MAX_LOGS) {
              pausedLogsRef.current = pausedLogsRef.current.slice(-MAX_LOGS);
            }
          } else {
            setLogs((prev) => {
              const newLogs = [...prev, entry];
              // Keep only last MAX_LOGS entries
              return newLogs.slice(-MAX_LOGS);
            });
            setTimeout(scrollToBottom, 50);
          }
        } catch (error) {
          console.error('Failed to parse log message:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Reconnect after delay
        setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };

      wsRef.current = ws;
    };

    // Connect WebSocket
    connect();

    // Fetch initial logs and log level
    fetchLogs();
    fetchLogLevel();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update WebSocket filters when they change
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (filterLevel) {
        wsRef.current.send(JSON.stringify({ type: 'set_level', level: filterLevel }));
      } else {
        wsRef.current.send(JSON.stringify({ type: 'clear_filters' }));
      }
    }
  }, [filterLevel]);

  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (searchTerm) {
        wsRef.current.send(JSON.stringify({ type: 'set_search', search: searchTerm }));
      }
    }
  }, [searchTerm]);

  // Handle resume from pause - merge paused logs
  const handleTogglePause = () => {
    if (isPaused) {
      // Resume - merge paused logs
      setLogs((prev) => {
        const merged = [...prev, ...pausedLogsRef.current];
        pausedLogsRef.current = [];
        return merged.slice(-MAX_LOGS);
      });
      setTimeout(scrollToBottom, 100);
    }
    setIsPaused(!isPaused);
  };

  // Clear logs
  const handleClearLogs = async () => {
    setIsClearing(true);
    try {
      const response = await fetch('/api/v1/logs', { method: 'DELETE' });
      if (response.ok) {
        setLogs([]);
        pausedLogsRef.current = [];
      }
    } catch (error) {
      console.error('Failed to clear logs:', error);
    }
    setIsClearing(false);
  };

  // Change log level
  const handleChangeLogLevel = async (level: string) => {
    setIsChangingLevel(true);
    try {
      const response = await fetch('/api/v1/logs/level', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level }),
      });
      if (response.ok) {
        setCurrentLogLevel(level);
      }
    } catch (error) {
      console.error('Failed to change log level:', error);
    }
    setIsChangingLevel(false);
  };

  // Download logs as text file
  const handleDownloadLogs = () => {
    const content = logs
      .map((log) => `[${log.timestamp}] [${log.level}] ${log.logger_name}: ${log.message}`)
      .join('\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `autoarr-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filter logs for display
  const filteredLogs = logs.filter((log) => {
    if (filterLevel) {
      const levelOrder = { DEBUG: 0, INFO: 1, WARNING: 2, ERROR: 3, CRITICAL: 4 };
      const minLevel = levelOrder[filterLevel as keyof typeof levelOrder] ?? 0;
      const logLevel = levelOrder[log.level as keyof typeof levelOrder] ?? 0;
      if (logLevel < minLevel) return false;
    }
    if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div
      className="h-full flex flex-col"
      style={{ padding: 'var(--page-padding)' }}
      data-testid="logs-page"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <Link
            to="/settings"
            className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
            aria-label="Back to Settings"
          >
            <ArrowLeft className="w-5 h-5 text-gray-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">Application Logs</h1>
            <p className="text-sm text-gray-400">
              {isConnected ? (
                <span className="text-green-400">Connected - Real-time streaming</span>
              ) : (
                <span className="text-yellow-400">Reconnecting...</span>
              )}
              {isPaused && <span className="ml-2 text-yellow-400">(Paused)</span>}
            </p>
          </div>
        </div>

        {/* Log Level Control */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">Log Level:</span>
          <select
            value={currentLogLevel}
            onChange={(e) => handleChangeLogLevel(e.target.value)}
            disabled={isChangingLevel}
            className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Filter by level */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value as LogLevel | '')}
            className="px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Levels</option>
            {LOG_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleTogglePause}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-md transition-colors ${
              isPaused
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-700 hover:bg-gray-600 text-white'
            }`}
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            {isPaused ? 'Resume' : 'Pause'}
          </button>

          <button
            onClick={fetchLogs}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={handleDownloadLogs}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
            title="Download logs"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={handleClearLogs}
            disabled={isClearing}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors disabled:opacity-50"
            title="Clear logs"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex items-center gap-4 mb-2 text-xs text-gray-500">
        <span>Showing {filteredLogs.length} logs</span>
        <span>|</span>
        <span>
          Buffer: {logs.length}/{MAX_LOGS}
        </span>
        {isPaused && pausedLogsRef.current.length > 0 && (
          <>
            <span>|</span>
            <span className="text-yellow-400">
              {pausedLogsRef.current.length} new logs while paused
            </span>
          </>
        )}
      </div>

      {/* Log entries */}
      <div
        ref={logsContainerRef}
        className="flex-1 overflow-auto bg-gray-900 rounded-lg border border-gray-800 font-mono text-xs"
      >
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            No logs to display
          </div>
        ) : (
          <div className="p-2 space-y-0.5">
            {filteredLogs.map((log, index) => {
              const LevelIcon = LEVEL_ICONS[log.level] || Info;
              return (
                <div
                  key={`${log.timestamp}-${index}`}
                  className={`flex items-start gap-2 px-2 py-1 rounded ${LEVEL_BG_COLORS[log.level] || ''}`}
                >
                  <LevelIcon
                    className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${LEVEL_COLORS[log.level]}`}
                  />
                  <span className="text-gray-500 flex-shrink-0 w-[140px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`flex-shrink-0 w-[60px] ${LEVEL_COLORS[log.level]}`}>
                    {log.level}
                  </span>
                  <span className="text-gray-500 flex-shrink-0 max-w-[200px] truncate">
                    {log.logger_name}
                  </span>
                  <span className="text-gray-200 flex-1 break-all">{log.message}</span>
                </div>
              );
            })}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};
