import { useState, useEffect, useCallback } from 'react';

interface OptimizationCheck {
  id: string;
  category: string;
  status: 'critical' | 'warning' | 'recommendation' | 'good';
  title: string;
  description: string;
  recommendation?: string;
  current_value?: string;
  optimal_value?: string;
  auto_fix: boolean;
  fix_action?: string;
  fix_params?: Record<string, unknown>;
  min_version?: string;
}

interface OptimizationSummary {
  total_checks: number;
  critical: number;
  warnings: number;
  recommendations: number;
  good: number;
}

interface ServiceOptimizationResult {
  service: string;
  version?: string;
  overall_status: string;
  overall_score: number;
  summary: OptimizationSummary;
  checks: OptimizationCheck[];
}

interface AllServicesResult {
  services: ServiceOptimizationResult[];
  overall_score: number;
  overall_status: string;
}

const statusColors = {
  critical: 'bg-red-500/20 border-red-500 text-red-400',
  warning: 'bg-yellow-500/20 border-yellow-500 text-yellow-400',
  recommendation: 'bg-blue-500/20 border-blue-500 text-blue-400',
  good: 'bg-green-500/20 border-green-500 text-green-400',
};

const statusIcons = {
  critical: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  recommendation: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  good: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

// Service logos - use actual logo images
const serviceLogos: Record<string, string> = {
  sabnzbd: '/logos/sabnzbd.png',
  sonarr: '/logos/sonarr.png',
  radarr: '/logos/radarr.png',
  plex: '/logos/plex.png',
};

// Fallback icons for services without logos
const serviceIcons: Record<string, React.ReactNode> = {
  sabnzbd: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  ),
  sonarr: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  radarr: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
    </svg>
  ),
  plex: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
    </svg>
  ),
};

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#eab308';
    if (s >= 40) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          className="text-gray-700"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold">{score}</span>
      </div>
    </div>
  );
}

function CheckCard({
  check,
  onFix,
  isFixing,
}: {
  check: OptimizationCheck;
  onFix: (check: OptimizationCheck) => void;
  isFixing: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`border rounded-lg p-4 ${statusColors[check.status]} transition-all duration-200`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">{statusIcons[check.status]}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-medium text-white">{check.title}</h4>
            <span className="text-xs px-2 py-0.5 rounded bg-gray-700/50 text-gray-300">
              {check.category}
            </span>
          </div>
          <p className="text-sm text-gray-300 mt-1">{check.description}</p>

          {(check.current_value || check.optimal_value) && (
            <div className="mt-2 flex flex-wrap gap-3 text-xs">
              {check.current_value && (
                <span className="text-gray-400">
                  Current: <span className="text-white">{check.current_value}</span>
                </span>
              )}
              {check.optimal_value && (
                <span className="text-gray-400">
                  Optimal: <span className="text-green-400">{check.optimal_value}</span>
                </span>
              )}
            </div>
          )}

          {check.recommendation && expanded && (
            <div className="mt-3 p-3 bg-gray-800/50 rounded text-sm text-gray-300">
              <strong className="text-white">Recommendation:</strong> {check.recommendation}
            </div>
          )}

          <div className="mt-3 flex items-center gap-2">
            {check.recommendation && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-gray-400 hover:text-white"
              >
                {expanded ? 'Hide details' : 'Show details'}
              </button>
            )}
            {check.auto_fix && check.fix_action && (
              <button
                onClick={() => onFix(check)}
                disabled={isFixing}
                className="ml-auto text-xs px-3 py-1.5 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 rounded font-medium transition-colors"
              >
                {isFixing ? 'Fixing...' : 'Auto-Fix'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ServiceCard({
  result,
  onFix,
  fixingCheckId,
}: {
  result: ServiceOptimizationResult;
  onFix: (service: string, check: OptimizationCheck) => void;
  fixingCheckId: string | null;
}) {
  const [showGood, setShowGood] = useState(false);

  const issueChecks = result.checks.filter((c) => c.status !== 'good');
  const goodChecks = result.checks.filter((c) => c.status === 'good');

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'Excellent';
      case 'good':
        return 'Good';
      case 'warning':
        return 'Needs Attention';
      case 'critical':
        return 'Critical Issues';
      case 'not_connected':
        return 'Not Connected';
      default:
        return status;
    }
  };

  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gray-700/50 rounded-lg flex items-center justify-center overflow-hidden">
            {serviceLogos[result.service] ? (
              <img
                src={serviceLogos[result.service]}
                alt={`${result.service} logo`}
                className="w-10 h-10 object-contain"
              />
            ) : (
              <div className="text-teal-400">
                {serviceIcons[result.service] || serviceIcons.sabnzbd}
              </div>
            )}
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold capitalize">{result.service}</h3>
            <p className="text-sm text-gray-400">
              {result.version ? `Version ${result.version}` : 'Version unknown'}
            </p>
          </div>
          <div className="text-center">
            <ScoreRing score={result.overall_score} />
            <p className="text-xs text-gray-400 mt-1">{getStatusLabel(result.overall_status)}</p>
          </div>
        </div>

        {result.overall_status !== 'not_connected' && (
          <div className="mt-4 flex gap-4 text-sm">
            {result.summary.critical > 0 && (
              <span className="text-red-400">
                {result.summary.critical} critical
              </span>
            )}
            {result.summary.warnings > 0 && (
              <span className="text-yellow-400">
                {result.summary.warnings} warning{result.summary.warnings !== 1 ? 's' : ''}
              </span>
            )}
            {result.summary.recommendations > 0 && (
              <span className="text-blue-400">
                {result.summary.recommendations} recommendation{result.summary.recommendations !== 1 ? 's' : ''}
              </span>
            )}
            {result.summary.good > 0 && (
              <span className="text-green-400">
                {result.summary.good} passed
              </span>
            )}
          </div>
        )}
      </div>

      {result.overall_status === 'not_connected' ? (
        <div className="p-6 text-center text-gray-400">
          <p>This service is not connected.</p>
          <a href="/settings" className="text-teal-400 hover:underline mt-2 inline-block">
            Configure in Settings
          </a>
        </div>
      ) : (
        <div className="p-6 space-y-4">
          {issueChecks.length > 0 ? (
            <>
              <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                Issues & Recommendations
              </h4>
              <div className="space-y-3">
                {issueChecks.map((check) => (
                  <CheckCard
                    key={check.id}
                    check={check}
                    onFix={(c) => onFix(result.service, c)}
                    isFixing={fixingCheckId === check.id}
                  />
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-4">
              <div className="inline-flex items-center gap-2 text-green-400">
                {statusIcons.good}
                <span>All checks passed!</span>
              </div>
            </div>
          )}

          {goodChecks.length > 0 && (
            <div className="pt-4 border-t border-gray-700">
              <button
                onClick={() => setShowGood(!showGood)}
                className="text-sm text-gray-400 hover:text-white flex items-center gap-2"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${showGood ? 'rotate-90' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                {showGood ? 'Hide' : 'Show'} {goodChecks.length} passed check{goodChecks.length !== 1 ? 's' : ''}
              </button>

              {showGood && (
                <div className="mt-3 space-y-3">
                  {goodChecks.map((check) => (
                    <CheckCard
                      key={check.id}
                      check={check}
                      onFix={() => {}}
                      isFixing={false}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Optimize() {
  const [data, setData] = useState<AllServicesResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fixingCheckId, setFixingCheckId] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/v1/optimize/assess');
      if (!response.ok) {
        throw new Error('Failed to fetch optimization data');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleFix = async (service: string, check: OptimizationCheck) => {
    if (!check.fix_action) return;

    setFixingCheckId(check.id);
    try {
      const response = await fetch('/api/v1/optimize/fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service,
          check_id: check.id,
          fix_action: check.fix_action,
          fix_params: check.fix_params,
        }),
      });

      if (response.ok) {
        await fetchData();
      } else {
        const err = await response.json();
        alert(`Fix failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Fix failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setFixingCheckId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6" style={{ paddingLeft: '50px', paddingRight: '50px' }}>
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-gray-700 rounded" />
          <div className="h-64 bg-gray-800 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6" style={{ paddingLeft: '50px', paddingRight: '50px' }}>
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-400">
          <h3 className="font-semibold">Error</h3>
          <p>{error}</p>
          <button
            onClick={fetchData}
            className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-500 rounded text-white text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" style={{ paddingLeft: '50px', paddingRight: '50px' }}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Service Health</h1>
          <p className="text-gray-400 mt-1">
            Optimization recommendations for your media automation stack
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-lg text-white font-medium transition-colors disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {data && (
        <>
          <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center gap-6">
              <ScoreRing score={data.overall_score} size={100} />
              <div>
                <h2 className="text-xl font-semibold">Overall Health Score</h2>
                <p className="text-gray-400 mt-1">
                  {data.overall_status === 'excellent'
                    ? 'Your services are optimally configured!'
                    : data.overall_status === 'good'
                    ? 'Minor optimizations available'
                    : data.overall_status === 'warning'
                    ? 'Some issues need attention'
                    : data.overall_status === 'critical'
                    ? 'Critical issues require immediate attention'
                    : 'Connect services to see health status'}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {data.services.map((service) => (
              <ServiceCard
                key={service.service}
                result={service}
                onFix={handleFix}
                fixingCheckId={fixingCheckId}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
