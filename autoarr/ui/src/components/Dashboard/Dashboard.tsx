/**
 * Main Dashboard Component
 *
 * Configuration Audit Dashboard with:
 * - Mobile-first responsive design
 * - Service health status cards
 * - Run audit functionality
 * - Real-time loading states
 * - Error handling with toast notifications
 * - WCAG 2.1 AA accessibility compliance
 */

import { useState, useMemo } from "react";
import { AlertCircle, CheckCircle, Loader2, RefreshCw } from "lucide-react";
import {
  useRecommendations,
  useAuditMutation,
} from "../../hooks/useConfigAudit";
import { ServiceCard } from "./ServiceCard";
import { RecommendationCard } from "./RecommendationCard";
import type {
  ServiceHealth,
  SystemHealth,
  Recommendation,
} from "../../types/config";
import toast, { Toaster } from "react-hot-toast";

export function Dashboard() {
  const [isRunningAudit, setIsRunningAudit] = useState(false);

  // Fetch recommendations
  const {
    data: recommendationsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useRecommendations(undefined, undefined, undefined, 1, 100);

  // Audit mutation
  const auditMutation = useAuditMutation();

  // Calculate service health from recommendations
  const systemHealth = useMemo<SystemHealth>(() => {
    if (!recommendationsData) {
      return {
        overallScore: 100,
        totalRecommendations: 0,
        highPriority: 0,
        mediumPriority: 0,
        lowPriority: 0,
        services: [
          {
            service: "sabnzbd",
            healthScore: 100,
            recommendations: { high: 0, medium: 0, low: 0 },
          },
          {
            service: "sonarr",
            healthScore: 100,
            recommendations: { high: 0, medium: 0, low: 0 },
          },
          {
            service: "radarr",
            healthScore: 100,
            recommendations: { high: 0, medium: 0, low: 0 },
          },
          {
            service: "plex",
            healthScore: 100,
            recommendations: { high: 0, medium: 0, low: 0 },
          },
        ],
      };
    }

    const recommendations = recommendationsData.recommendations;
    const services = ["sabnzbd", "sonarr", "radarr", "plex"];

    const serviceHealthMap: Record<string, ServiceHealth> = {};

    // Initialize all services
    services.forEach((service) => {
      serviceHealthMap[service] = {
        service,
        healthScore: 100,
        recommendations: { high: 0, medium: 0, low: 0 },
        lastAudit: new Date().toISOString(),
      };
    });

    // Count recommendations per service
    recommendations.forEach((rec) => {
      const service = rec.service.toLowerCase();
      if (serviceHealthMap[service]) {
        serviceHealthMap[service].recommendations[
          rec.priority as "high" | "medium" | "low"
        ]++;
      }
    });

    // Calculate health scores (100 - weighted penalty for recommendations)
    Object.values(serviceHealthMap).forEach((serviceHealth) => {
      const penalty =
        serviceHealth.recommendations.high * 15 +
        serviceHealth.recommendations.medium * 8 +
        serviceHealth.recommendations.low * 3;
      serviceHealth.healthScore = Math.max(0, 100 - penalty);
    });

    // Calculate overall health
    const totalServices = services.length;
    const overallScore = Math.round(
      Object.values(serviceHealthMap).reduce(
        (sum, s) => sum + s.healthScore,
        0,
      ) / totalServices,
    );

    const highPriority = recommendations.filter(
      (r) => r.priority === "high",
    ).length;
    const mediumPriority = recommendations.filter(
      (r) => r.priority === "medium",
    ).length;
    const lowPriority = recommendations.filter(
      (r) => r.priority === "low",
    ).length;

    return {
      overallScore,
      totalRecommendations: recommendations.length,
      highPriority,
      mediumPriority,
      lowPriority,
      services: services.map((s) => serviceHealthMap[s]),
    };
  }, [recommendationsData]);

  // Handle audit button click
  const handleRunAudit = async () => {
    setIsRunningAudit(true);

    try {
      await auditMutation.mutateAsync({
        services: ["sabnzbd", "sonarr", "radarr", "plex"],
        includeWebSearch: false,
      });

      toast.success("Audit completed successfully!", {
        icon: <CheckCircle className="w-5 h-5" />,
        duration: 4000,
      });

      // Refetch recommendations
      await refetch();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Failed to run audit: ${errorMessage}`, {
        icon: <AlertCircle className="w-5 h-5" />,
        duration: 5000,
      });
    } finally {
      setIsRunningAudit(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-6 lg:p-8">
      {/* Toast Container */}
      <Toaster
        position="top-right"
        toastOptions={{
          className: "dark:bg-gray-800 dark:text-white",
          style: {
            borderRadius: "8px",
            padding: "12px 16px",
          },
        }}
      />

      <div className="max-w-7xl mx-auto" data-testid="dashboard-container">
        {/* Header */}
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Configuration Audit
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor and optimize your media server configuration
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div
            className="flex items-center justify-center py-12"
            data-testid="dashboard-loading"
            role="status"
            aria-live="polite"
          >
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600 dark:text-gray-400">
              Loading dashboard...
            </span>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
            role="alert"
            aria-live="assertive"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100 mb-1">
                  Failed to load recommendations
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300">
                  {error instanceof Error
                    ? error.message
                    : "An unknown error occurred"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        {!isLoading && !isError && (
          <>
            {/* Overall System Health */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    System Health Overview
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Overall configuration health across all services
                  </p>
                </div>

                {/* Run Audit Button */}
                <button
                  onClick={handleRunAudit}
                  disabled={isRunningAudit}
                  className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:cursor-not-allowed min-h-[44px]"
                  aria-label="Run configuration audit"
                >
                  {isRunningAudit ? (
                    <>
                      <Loader2
                        className="w-5 h-5 animate-spin"
                        data-testid="audit-loading-spinner"
                        aria-hidden="true"
                      />
                      <span>Running Audit...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-5 h-5" aria-hidden="true" />
                      <span>Run Audit</span>
                    </>
                  )}
                </button>
              </div>

              {/* Health Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    Overall Health
                  </div>
                  <div
                    className="text-3xl font-bold"
                    data-testid="overall-health-score"
                    aria-label={`Overall health score: ${systemHealth.overallScore} out of 100`}
                  >
                    <span
                      className={
                        systemHealth.overallScore >= 80
                          ? "text-green-600 dark:text-green-400"
                          : systemHealth.overallScore >= 60
                            ? "text-yellow-600 dark:text-yellow-400"
                            : "text-red-600 dark:text-red-400"
                      }
                    >
                      {systemHealth.overallScore}
                    </span>
                    <span className="text-base text-gray-500 dark:text-gray-400">
                      /100
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    Total Recommendations
                  </div>
                  <div
                    className="text-3xl font-bold text-gray-900 dark:text-gray-100"
                    data-testid="total-recommendations"
                    aria-label={`${systemHealth.totalRecommendations} total recommendations`}
                  >
                    {systemHealth.totalRecommendations}
                  </div>
                </div>

                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                  <div className="text-sm text-red-700 dark:text-red-400 mb-1">
                    High Priority
                  </div>
                  <div
                    className="text-3xl font-bold text-red-600 dark:text-red-400"
                    data-testid="total-high-priority"
                    aria-label={`${systemHealth.highPriority} high priority recommendations`}
                  >
                    {systemHealth.highPriority}
                  </div>
                </div>

                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                  <div className="text-sm text-yellow-700 dark:text-yellow-400 mb-1">
                    Medium Priority
                  </div>
                  <div
                    className="text-3xl font-bold text-yellow-600 dark:text-yellow-400"
                    data-testid="total-medium-priority"
                    aria-label={`${systemHealth.mediumPriority} medium priority recommendations`}
                  >
                    {systemHealth.mediumPriority}
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 sm:col-span-2 lg:col-span-1">
                  <div className="text-sm text-blue-700 dark:text-blue-400 mb-1">
                    Low Priority
                  </div>
                  <div
                    className="text-3xl font-bold text-blue-600 dark:text-blue-400"
                    data-testid="total-low-priority"
                    aria-label={`${systemHealth.lowPriority} low priority recommendations`}
                  >
                    {systemHealth.lowPriority}
                  </div>
                </div>
              </div>
            </div>

            {/* Service Status Cards */}
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Service Status
              </h2>
              <div
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
                data-testid="service-cards-grid"
              >
                {systemHealth.services.map((service) => (
                  <ServiceCard key={service.service} serviceHealth={service} />
                ))}
              </div>
            </div>

            {/* Recommendations List */}
            {recommendationsData &&
              recommendationsData.recommendations.length > 0 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Active Recommendations
                  </h2>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {recommendationsData.recommendations.map(
                      (recommendation: Recommendation) => (
                        <RecommendationCard
                          key={recommendation.id}
                          recommendation={recommendation}
                        />
                      ),
                    )}
                  </div>
                </div>
              )}

            {/* No Recommendations State */}
            {recommendationsData &&
              recommendationsData.recommendations.length === 0 && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-8 text-center">
                  <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-1">
                    All Systems Optimal
                  </h3>
                  <p className="text-green-700 dark:text-green-300">
                    No configuration recommendations at this time. Your services
                    are well configured!
                  </p>
                </div>
              )}
          </>
        )}
      </div>
    </div>
  );
}
