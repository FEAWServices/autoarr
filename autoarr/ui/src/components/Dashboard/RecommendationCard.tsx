/**
 * Recommendation Card Component
 *
 * Displays a single configuration recommendation
 * - Priority badge with color coding
 * - Service identification
 * - Current vs recommended values
 */

import type { Recommendation } from "../../types/config";

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const priorityColors = {
  high: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  medium:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  low: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
};

const categoryLabels = {
  performance: "Performance",
  security: "Security",
  best_practices: "Best Practices",
};

export function RecommendationCard({
  recommendation,
}: RecommendationCardProps) {
  const priorityColor =
    priorityColors[recommendation.priority as keyof typeof priorityColors];
  const categoryLabel =
    categoryLabels[recommendation.category as keyof typeof categoryLabels] ||
    recommendation.category;

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
      data-testid="recommendation-card"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
            {recommendation.title}
          </h3>
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-xs font-medium text-gray-600 dark:text-gray-400"
              data-testid="recommendation-service"
            >
              {recommendation.service.toUpperCase()}
            </span>
            <span className="text-gray-400 dark:text-gray-600">•</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {categoryLabel}
            </span>
          </div>
        </div>

        {/* Priority Badge */}
        <span
          className={`px-2 py-1 rounded-md text-xs font-semibold uppercase ${priorityColor}`}
          data-testid="priority-badge"
          aria-label={`${recommendation.priority} priority`}
        >
          {recommendation.priority.toUpperCase()}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {recommendation.description}
      </p>

      {/* Values */}
      {recommendation.current_value && (
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <div className="text-gray-500 dark:text-gray-400 mb-1">Current</div>
            <div className="font-mono font-medium text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-900/50 px-2 py-1 rounded">
              {recommendation.current_value}
            </div>
          </div>
          <div>
            <div className="text-gray-500 dark:text-gray-400 mb-1">
              Recommended
            </div>
            <div className="font-mono font-medium text-gray-900 dark:text-gray-100 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded">
              {recommendation.recommended_value}
            </div>
          </div>
        </div>
      )}

      {/* Impact */}
      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">Impact:</div>
        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {recommendation.impact}
        </div>
      </div>
    </div>
  );
}
