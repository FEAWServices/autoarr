/**
 * Activity Feed Page
 *
 * Real-time activity log with filtering, search, and infinite scroll
 * Features:
 * - Real-time updates via WebSocket
 * - Filter by type, service, level
 * - Search functionality
 * - Infinite scroll pagination
 * - Mobile-first responsive design
 * - WCAG 2.1 AA accessibility
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Download,
  Search as SearchIcon,
  AlertCircle,
  RefreshCw,
  Filter,
  X,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Info,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useWebSocket } from "../hooks/useWebSocket";
import type {
  Activity as ActivityType,
  ActivityType as ActivityTypeEnum,
  ActivityService,
  ActivityLevel,
  ActivityFilters,
} from "../types/activity";

// Mock API function (replace with actual API call)
async function fetchActivities(
  page: number,
  filters: ActivityFilters,
  searchTerm: string,
): Promise<{
  activities: ActivityType[];
  has_more: boolean;
}> {
  const params = new URLSearchParams();
  params.append("page", page.toString());
  params.append("page_size", "20");

  if (filters.type && filters.type.length > 0) {
    params.append("type", filters.type.join(","));
  }
  if (filters.service && filters.service.length > 0) {
    params.append("service", filters.service.join(","));
  }
  if (filters.level && filters.level.length > 0) {
    params.append("level", filters.level.join(","));
  }
  if (searchTerm) {
    params.append("search", searchTerm);
  }

  const response = await fetch(`/api/v1/activity?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Failed to fetch activities");
  }
  return response.json();
}

export const Activity = () => {
  const [activities, setActivities] = useState<ActivityType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState<ActivityFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // WebSocket connection
  const { isConnected, subscribe } = useWebSocket({
    autoConnect: true,
  });

  // Load initial activities
  const loadActivities = useCallback(
    async (resetPage = false) => {
      try {
        const currentPage = resetPage ? 1 : page;
        if (resetPage) {
          setIsLoading(true);
        } else {
          setIsLoadingMore(true);
        }

        const data = await fetchActivities(currentPage, filters, searchTerm);

        if (resetPage) {
          setActivities(data.activities);
          setPage(1);
        } else {
          setActivities((prev) => [...prev, ...data.activities]);
        }

        setHasMore(data.has_more);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load activities",
        );
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [page, filters, searchTerm],
  );

  // Initial load
  useEffect(() => {
    loadActivities(true);
  }, [filters, searchTerm]);

  // Subscribe to real-time activity updates
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = subscribe<ActivityType>("activity", (newActivity) => {
      setActivities((prev) => [newActivity, ...prev]);
    });

    return unsubscribe;
  }, [isConnected, subscribe]);

  // Infinite scroll observer
  useEffect(() => {
    if (!hasMore || isLoadingMore) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
          setPage((prev) => prev + 1);
          loadActivities(false);
        }
      },
      { threshold: 0.1 },
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, isLoadingMore, loadActivities]);

  // Filter handlers
  const handleFilterChange = (
    filterType: keyof ActivityFilters,
    value: string,
  ) => {
    if (!value) {
      setFilters((prev) => {
        const newFilters = { ...prev };
        delete newFilters[filterType];
        return newFilters;
      });
    } else {
      setFilters((prev) => ({
        ...prev,
        [filterType]: [
          value as ActivityTypeEnum | ActivityService | ActivityLevel,
        ],
      }));
    }
  };

  const clearFilters = () => {
    setFilters({});
  };

  const hasActiveFilters =
    Object.keys(filters).length > 0 || searchTerm.length > 0;

  // Get icon for activity type
  const getActivityIcon = (type: ActivityTypeEnum, level: ActivityLevel) => {
    const iconClass = "w-5 h-5";

    if (level === "error") {
      return <AlertCircle className={iconClass} />;
    }
    if (level === "warning") {
      return <AlertTriangle className={iconClass} />;
    }
    if (level === "success") {
      return <CheckCircle2 className={iconClass} />;
    }

    switch (type) {
      case "download":
        return <Download className={iconClass} />;
      case "search":
        return <SearchIcon className={iconClass} />;
      default:
        return <Info className={iconClass} />;
    }
  };

  // Get color for activity level
  const getLevelColor = (level: ActivityLevel) => {
    switch (level) {
      case "error":
        return "bg-red-500";
      case "warning":
        return "bg-yellow-500";
      case "success":
        return "bg-green-500";
      default:
        return "bg-blue-500";
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      className="min-h-screen bg-background-primary p-4 md:p-6 lg:p-8"
      data-testid="activity-feed-container"
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold text-white">Activity Feed</h1>

            {/* WebSocket Connection Indicator */}
            <div
              className="flex items-center gap-2"
              data-testid="ws-connection-indicator"
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected
                    ? "bg-status-success animate-pulse"
                    : "bg-status-error"
                }`}
                data-testid="ws-connection-status"
                aria-label={isConnected ? "Connected" : "Disconnected"}
              />
              {isConnected ? (
                <Wifi className="w-4 h-4 text-status-success" />
              ) : (
                <WifiOff className="w-4 h-4 text-status-error" />
              )}
              <span className="text-sm text-text-secondary">
                {isConnected ? "Live" : "Offline"}
              </span>
            </div>
          </div>
          <p className="text-text-secondary">
            Real-time activity log across all services
          </p>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-background-secondary rounded-lg p-4 mb-6 space-y-4">
          {/* Search Input */}
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              data-testid="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search activities..."
              className="w-full pl-10 pr-10 py-3 bg-background-tertiary border border-background-tertiary rounded-lg text-white placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              aria-label="Search activities"
            />
            {searchTerm && (
              <button
                data-testid="clear-search-button"
                onClick={() => setSearchTerm("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-white transition-colors"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Filter Toggle Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-background-tertiary hover:bg-background-tertiary/80 text-white rounded-lg transition-colors"
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
            {hasActiveFilters && (
              <span className="px-2 py-0.5 bg-primary text-white text-xs rounded-full">
                Active
              </span>
            )}
          </button>

          {/* Filter Panel */}
          {showFilters && (
            <div
              data-testid="filter-panel"
              className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-background-tertiary"
            >
              {/* Type Filter */}
              <div className="flex-1">
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Type
                </label>
                <select
                  data-testid="filter-type"
                  value={filters.type?.[0] || ""}
                  onChange={(e) => handleFilterChange("type", e.target.value)}
                  className="w-full px-4 py-3 bg-background-tertiary border border-background-tertiary rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary min-h-[44px]"
                  aria-label="Filter by type"
                >
                  <option value="">All Types</option>
                  <option value="download">Download</option>
                  <option value="search">Search</option>
                  <option value="import">Import</option>
                  <option value="config_change">Config Change</option>
                  <option value="error">Error</option>
                  <option value="audit">Audit</option>
                  <option value="system">System</option>
                </select>
              </div>

              {/* Service Filter */}
              <div className="flex-1">
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Service
                </label>
                <select
                  data-testid="filter-service"
                  value={filters.service?.[0] || ""}
                  onChange={(e) =>
                    handleFilterChange("service", e.target.value)
                  }
                  className="w-full px-4 py-3 bg-background-tertiary border border-background-tertiary rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary min-h-[44px]"
                  aria-label="Filter by service"
                >
                  <option value="">All Services</option>
                  <option value="sabnzbd">SABnzbd</option>
                  <option value="sonarr">Sonarr</option>
                  <option value="radarr">Radarr</option>
                  <option value="plex">Plex</option>
                  <option value="autoarr">AutoArr</option>
                  <option value="system">System</option>
                </select>
              </div>

              {/* Level Filter */}
              <div className="flex-1">
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Level
                </label>
                <select
                  data-testid="filter-level"
                  value={filters.level?.[0] || ""}
                  onChange={(e) => handleFilterChange("level", e.target.value)}
                  className="w-full px-4 py-3 bg-background-tertiary border border-background-tertiary rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary min-h-[44px]"
                  aria-label="Filter by level"
                >
                  <option value="">All Levels</option>
                  <option value="info">Info</option>
                  <option value="success">Success</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>

              {/* Clear Filters Button */}
              {hasActiveFilters && (
                <div className="flex items-end">
                  <button
                    data-testid="clear-filters-button"
                    onClick={clearFilters}
                    className="px-4 py-3 bg-background-tertiary hover:bg-background-tertiary/80 text-white rounded-lg transition-colors whitespace-nowrap min-h-[44px]"
                    aria-label="Clear all filters"
                  >
                    Clear All
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div
            className="flex items-center justify-center py-12"
            data-testid="activity-loading"
            role="status"
            aria-live="polite"
          >
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span className="ml-3 text-text-secondary">
              Loading activities...
            </span>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div
            className="bg-red-900/20 border border-red-800 rounded-lg p-6 text-center"
            role="alert"
            data-testid="error-message"
          >
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-red-100 mb-2">
              Failed to Load Activities
            </h3>
            <p className="text-red-300 mb-4">{error}</p>
            <button
              data-testid="retry-button"
              onClick={() => loadActivities(true)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4 inline mr-2" />
              Retry
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && activities.length === 0 && (
          <div
            className="bg-background-secondary rounded-lg p-12 text-center"
            data-testid="empty-state"
          >
            <Info className="w-16 h-16 text-text-muted mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              No Activities Found
            </h3>
            <p className="text-text-secondary">
              {hasActiveFilters
                ? "Try adjusting your filters or search term"
                : "No activities to display yet"}
            </p>
          </div>
        )}

        {/* No Results Message */}
        {!isLoading &&
          !error &&
          activities.length === 0 &&
          searchTerm.length > 0 && (
            <div data-testid="no-results-message" className="sr-only">
              No results found for "{searchTerm}"
            </div>
          )}

        {/* Activity List */}
        {!isLoading && !error && activities.length > 0 && (
          <ul className="space-y-3" role="list">
            {activities.map((activity) => (
              <li
                key={activity.id}
                data-testid="activity-item"
                className="bg-background-secondary rounded-lg p-4 hover:bg-background-tertiary transition-colors"
                role="listitem"
              >
                <div className="flex items-start gap-4">
                  {/* Level Indicator */}
                  <div
                    data-testid="level-indicator"
                    className={`flex-shrink-0 w-1 h-full ${getLevelColor(
                      activity.level,
                    )} rounded-full`}
                    aria-label={`Activity level: ${activity.level}`}
                  />

                  {/* Activity Icon */}
                  <div
                    data-testid="activity-type-icon"
                    className={`flex-shrink-0 p-2 rounded-lg ${
                      activity.level === "error"
                        ? "bg-red-900/20 text-red-400"
                        : activity.level === "warning"
                          ? "bg-yellow-900/20 text-yellow-400"
                          : activity.level === "success"
                            ? "bg-green-900/20 text-green-400"
                            : "bg-blue-900/20 text-blue-400"
                    }`}
                  >
                    {getActivityIcon(activity.type, activity.level)}
                  </div>

                  {/* Activity Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <h3
                        data-testid="activity-title"
                        className="text-base font-semibold text-white"
                      >
                        {activity.title}
                      </h3>
                      <span
                        data-testid="activity-timestamp"
                        className="flex-shrink-0 text-sm text-text-muted"
                      >
                        {formatTimestamp(activity.timestamp)}
                      </span>
                    </div>

                    <p className="text-sm text-text-secondary mb-3">
                      {activity.description}
                    </p>

                    {/* Service Badge */}
                    <span
                      data-testid="service-badge"
                      className="inline-block px-3 py-1 bg-background-tertiary text-text-secondary text-xs font-medium rounded-full uppercase"
                    >
                      {activity.service}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}

        {/* Load More Trigger */}
        {hasMore && !isLoading && (
          <div ref={loadMoreRef} className="py-8">
            {isLoadingMore && (
              <div
                className="flex items-center justify-center"
                data-testid="loading-more-indicator"
                role="status"
                aria-live="polite"
              >
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <span className="ml-3 text-text-secondary">
                  Loading more...
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
