// Copyright (C) 2025 AutoArr Contributors
//
// This file is part of AutoArr.
//
// AutoArr is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// AutoArr is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity as ActivityIcon,
  RefreshCw,
  Trash2,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Info,
  AlertTriangle,
  CheckCircle,
  Filter,
} from "lucide-react";

// Types
interface ActivityLog {
  id: number;
  service: string;
  activity_type: string;
  severity: string;
  message: string;
  correlation_id: string | null;
  metadata: Record<string, unknown>;
  timestamp: string;
  created_at: string;
  user_id: string | null;
}

interface PaginatedResponse {
  items: ActivityLog[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface ActivityStats {
  total_count: number;
  by_type: Record<string, number>;
  by_service: Record<string, number>;
  by_severity: Record<string, number>;
}

// Severity badge component
const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const config: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    critical: {
      bg: "bg-red-100 dark:bg-red-900/30",
      text: "text-red-800 dark:text-red-300",
      icon: <AlertCircle className="w-3 h-3" />,
    },
    error: {
      bg: "bg-red-100 dark:bg-red-900/30",
      text: "text-red-800 dark:text-red-300",
      icon: <AlertCircle className="w-3 h-3" />,
    },
    warning: {
      bg: "bg-yellow-100 dark:bg-yellow-900/30",
      text: "text-yellow-800 dark:text-yellow-300",
      icon: <AlertTriangle className="w-3 h-3" />,
    },
    info: {
      bg: "bg-blue-100 dark:bg-blue-900/30",
      text: "text-blue-800 dark:text-blue-300",
      icon: <Info className="w-3 h-3" />,
    },
    success: {
      bg: "bg-green-100 dark:bg-green-900/30",
      text: "text-green-800 dark:text-green-300",
      icon: <CheckCircle className="w-3 h-3" />,
    },
  };

  const style = config[severity.toLowerCase()] || config.info;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}
    >
      {style.icon}
      {severity}
    </span>
  );
};

// Service badge component
const ServiceBadge: React.FC<{ service: string }> = ({ service }) => {
  const colors: Record<string, string> = {
    sabnzbd: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    sonarr: "bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300",
    radarr: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
    plex: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
    system: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
    chat: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  };

  const colorClass = colors[service.toLowerCase()] || colors.system;

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {service}
    </span>
  );
};

// Main Activity Page Component
const Activity: React.FC = () => {
  // State
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [stats, setStats] = useState<ActivityStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [serviceFilter, setServiceFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);

  // Available filter options
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);
  const [availableSeverities, setAvailableSeverities] = useState<string[]>([]);

  // Fetch activities
  const fetchActivities = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        order_by: "timestamp",
        order: "desc",
      });

      if (searchQuery) params.append("search", searchQuery);
      if (serviceFilter) params.append("service", serviceFilter);
      if (severityFilter) params.append("severity", severityFilter);
      if (typeFilter) params.append("activity_type", typeFilter);

      const response = await fetch(`/api/v1/activity?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch activities: ${response.statusText}`);
      }

      const data: PaginatedResponse = await response.json();
      setActivities(data.items);
      setTotalPages(data.total_pages);
      setTotalItems(data.total_items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch activities");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchQuery, serviceFilter, severityFilter, typeFilter]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/activity/stats");
      if (response.ok) {
        const data: ActivityStats = await response.json();
        setStats(data);
      }
    } catch {
      // Stats are optional, don't show error
    }
  }, []);

  // Fetch filter options
  const fetchFilterOptions = useCallback(async () => {
    try {
      const [typesRes, severitiesRes] = await Promise.all([
        fetch("/api/v1/activity/types"),
        fetch("/api/v1/activity/severities"),
      ]);

      if (typesRes.ok) {
        setAvailableTypes(await typesRes.json());
      }
      if (severitiesRes.ok) {
        setAvailableSeverities(await severitiesRes.json());
      }
    } catch {
      // Filter options are optional
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  // Fetch when filters or page change
  useEffect(() => {
    fetchActivities();
    fetchStats();
  }, [fetchActivities, fetchStats]);

  // Handle cleanup
  const handleCleanup = async (retentionDays: number) => {
    if (!confirm(`Delete all activities older than ${retentionDays} days?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/api/v1/activity/cleanup?retention_days=${retentionDays}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        fetchActivities();
        fetchStats();
      } else {
        throw new Error("Cleanup failed");
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Cleanup failed");
    }
  };

  // Export activities
  const handleExport = () => {
    const dataStr = JSON.stringify(activities, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `activity-log-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Get unique services from stats
  const availableServices = stats ? Object.keys(stats.by_service) : [];

  return (
    <div className="flex flex-col h-full" style={{ padding: "var(--page-padding, 50px)" }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <ActivityIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Activity</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {totalItems} total activities
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => fetchActivities()}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={() => handleCleanup(30)}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-white dark:bg-gray-800 border border-red-300 dark:border-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            <Trash2 className="w-4 h-4" />
            Cleanup
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total_count}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {(stats.by_severity.error || 0) + (stats.by_severity.critical || 0)}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Errors</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {stats.by_severity.warning || 0}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Warnings</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {stats.by_severity.success || 0}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Success</div>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search activities..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border ${
              showFilters
                ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-600"
                : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600"
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
        </div>

        {/* Filter Dropdowns */}
        {showFilters && (
          <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <select
              value={serviceFilter}
              onChange={(e) => {
                setServiceFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
            >
              <option value="">All Services</option>
              {availableServices.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            <select
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
            >
              <option value="">All Severities</option>
              {availableSeverities.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
            >
              <option value="">All Types</option>
              {availableTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>

            {(serviceFilter || severityFilter || typeFilter || searchQuery) && (
              <button
                onClick={() => {
                  setServiceFilter("");
                  setSeverityFilter("");
                  setTypeFilter("");
                  setSearchQuery("");
                  setPage(1);
                }}
                className="px-3 py-2 text-sm text-purple-600 dark:text-purple-400 hover:underline"
              >
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Activity List */}
      <div className="flex-1 overflow-auto">
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {loading && activities.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
          </div>
        ) : activities.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <ActivityIcon className="w-12 h-12 mb-4 opacity-50" />
            <p>No activities found</p>
          </div>
        ) : (
          <div className="space-y-2">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <ServiceBadge service={activity.service} />
                    <SeverityBadge severity={activity.severity} />
                    <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                      {activity.activity_type}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400 dark:text-gray-500 sm:ml-auto whitespace-nowrap">
                    {formatTime(activity.timestamp)}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                  {activity.message}
                </p>
                {activity.correlation_id && (
                  <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 font-mono">
                    Correlation: {activity.correlation_id}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Activity;
