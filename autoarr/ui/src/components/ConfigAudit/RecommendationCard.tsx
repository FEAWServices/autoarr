/**
 * RecommendationCard Component
 *
 * Displays a single configuration recommendation with all relevant details.
 * Following WCAG 2.1 AA compliance and mobile-first design principles.
 */

import React from "react";
import {
  Database,
  Download,
  Film,
  Server,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import clsx from "clsx";
import type { Recommendation } from "../../types/config";

interface RecommendationCardProps {
  recommendation: Recommendation;
  onApply: (recommendation: Recommendation) => void;
  isApplying?: boolean;
}

/**
 * Get service icon component based on service name
 */
function getServiceIcon(service: string) {
  const iconClass = "h-5 w-5 sm:h-6 sm:w-6";

  switch (service) {
    case "sabnzbd":
      return <Download className={iconClass} aria-hidden="true" />;
    case "sonarr":
    case "radarr":
      return <Film className={iconClass} aria-hidden="true" />;
    case "plex":
      return <Server className={iconClass} aria-hidden="true" />;
    default:
      return <Database className={iconClass} aria-hidden="true" />;
  }
}

/**
 * Get priority badge styling based on priority level
 */
function getPriorityBadgeClass(priority: string) {
  switch (priority) {
    case "high":
      return "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800";
    case "medium":
      return "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-800";
    case "low":
      return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/20 dark:text-gray-300 dark:border-gray-800";
  }
}

/**
 * Get category display name
 */
function getCategoryDisplayName(category: string): string {
  switch (category) {
    case "best_practices":
      return "Best Practices";
    case "performance":
      return "Performance";
    case "security":
      return "Security";
    case "download":
      return "Download";
    default:
      return category.charAt(0).toUpperCase() + category.slice(1);
  }
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onApply,
  isApplying = false,
}) => {
  const {
    id,
    service,
    category,
    priority,
    title,
    description,
    current_value,
    recommended_value,
    impact,
    applied,
  } = recommendation;

  const isDisabled = applied || isApplying;

  return (
    <article
      data-testid="recommendation-card"
      className={clsx(
        "bg-white dark:bg-gray-800 rounded-lg border shadow-sm",
        "p-4 sm:p-6 space-y-4",
        "transition-all duration-200",
        "hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600",
        applied && "opacity-75 bg-gray-50 dark:bg-gray-900",
        "border-gray-200 dark:border-gray-700",
      )}
      aria-labelledby={`recommendation-${id}-title`}
    >
      {/* Header: Service Icon, Priority Badge, Category */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          {/* Service Icon */}
          <div
            data-testid="service-icon"
            className="flex-shrink-0 p-2 bg-gray-100 dark:bg-gray-700 rounded-md"
            aria-label={`${service} service`}
          >
            {getServiceIcon(service)}
          </div>

          {/* Service Name and Category */}
          <div className="min-w-0">
            <h3
              id={`recommendation-${id}-title`}
              className="text-sm font-medium text-gray-900 dark:text-gray-100 capitalize"
            >
              {service}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {getCategoryDisplayName(category)}
            </p>
          </div>
        </div>

        {/* Priority Badge */}
        <span
          data-testid="priority-badge"
          className={clsx(
            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
            "uppercase tracking-wide",
            getPriorityBadgeClass(priority),
          )}
          aria-label={`Priority: ${priority}`}
        >
          {priority === "high" && (
            <AlertTriangle className="h-3 w-3 mr-1" aria-hidden="true" />
          )}
          {priority}
        </span>
      </div>

      {/* Title and Description */}
      <div className="space-y-2">
        <h4 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {description}
        </p>
      </div>

      {/* Current Value � Recommended Value */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-md p-3 sm:p-4">
        <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              Current
            </p>
            <p
              className="text-sm font-mono text-gray-900 dark:text-gray-100 break-all"
              aria-label={`Current value: ${current_value || "Not set"}`}
            >
              {current_value || (
                <span className="text-gray-400 dark:text-gray-500 italic">
                  Not set
                </span>
              )}
            </p>
          </div>

          <ArrowRight
            className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 dark:text-gray-500 flex-shrink-0"
            aria-hidden="true"
          />

          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              Recommended
            </p>
            <p
              className="text-sm font-mono text-green-700 dark:text-green-400 font-semibold break-all"
              aria-label={`Recommended value: ${recommended_value}`}
            >
              {recommended_value}
            </p>
          </div>
        </div>
      </div>

      {/* Impact Description */}
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 mt-0.5">
          <div className="h-5 w-5 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
            <span className="text-blue-600 dark:text-blue-400 text-xs font-bold">
              i
            </span>
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
            Impact
          </p>
          <p className="text-sm text-gray-700 dark:text-gray-300">{impact}</p>
        </div>
      </div>

      {/* Apply Button */}
      <div className="pt-2 flex justify-end">
        <button
          data-testid="apply-button"
          onClick={() => onApply(recommendation)}
          disabled={isDisabled}
          className={clsx(
            "inline-flex items-center justify-center",
            "px-4 py-2.5 sm:px-5 sm:py-3",
            "min-h-[44px] min-w-[88px]", // Touch-friendly size
            "text-sm font-medium rounded-md",
            "transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-offset-2",
            !isDisabled && [
              "bg-blue-600 hover:bg-blue-700 text-white",
              "focus:ring-blue-500",
              "dark:bg-blue-500 dark:hover:bg-blue-600",
              "shadow-sm hover:shadow-md",
            ],
            isDisabled && [
              "bg-gray-300 text-gray-500 cursor-not-allowed",
              "dark:bg-gray-700 dark:text-gray-400",
            ],
            isApplying && "opacity-75",
          )}
          aria-label={
            applied
              ? `Applied: ${title}`
              : isApplying
                ? `Applying ${title}`
                : `Apply recommendation: ${title}`
          }
          aria-busy={isApplying}
        >
          {isApplying ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Applying...
            </>
          ) : applied ? (
            " Applied"
          ) : (
            "Apply"
          )}
        </button>
      </div>
    </article>
  );
};
