/**
 * FilterPanel Component
 *
 * Provides filtering controls for recommendations by service, priority, and category.
 * Mobile-responsive with accessible select controls.
 */

import React from "react";
import { X, Filter as FilterIcon } from "lucide-react";
import clsx from "clsx";
import type { Service, Priority, Category } from "../../types/config";

interface FilterPanelProps {
  selectedService: Service | null;
  selectedPriority: Priority | null;
  selectedCategory: Category | null;
  onServiceChange: (service: Service | null) => void;
  onPriorityChange: (priority: Priority | null) => void;
  onCategoryChange: (category: Category | null) => void;
  onClearFilters: () => void;
}

const SERVICES: { value: Service; label: string }[] = [
  { value: "sabnzbd", label: "SABnzbd" },
  { value: "sonarr", label: "Sonarr" },
  { value: "radarr", label: "Radarr" },
  { value: "plex", label: "Plex" },
];

const PRIORITIES: { value: Priority; label: string }[] = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const CATEGORIES: { value: Category; label: string }[] = [
  { value: "performance", label: "Performance" },
  { value: "security", label: "Security" },
  { value: "best_practices", label: "Best Practices" },
  { value: "download", label: "Download" },
];

export const FilterPanel: React.FC<FilterPanelProps> = ({
  selectedService,
  selectedPriority,
  selectedCategory,
  onServiceChange,
  onPriorityChange,
  onCategoryChange,
  onClearFilters,
}) => {
  const hasActiveFilters =
    selectedService || selectedPriority || selectedCategory;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FilterIcon
            className="h-5 w-5 text-gray-500 dark:text-gray-400"
            aria-hidden="true"
          />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Filters
          </h2>
        </div>

        {hasActiveFilters && (
          <button
            data-testid="clear-filters"
            onClick={onClearFilters}
            className={clsx(
              "inline-flex items-center gap-1.5",
              "px-3 py-1.5 text-sm font-medium",
              "text-gray-700 dark:text-gray-200",
              "hover:text-gray-900 dark:hover:text-gray-100",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md",
              "transition-colors",
            )}
            aria-label="Clear all filters"
          >
            <X className="h-4 w-4" aria-hidden="true" />
            Clear
          </button>
        )}
      </div>

      {/* Filters Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Service Filter */}
        <div className="space-y-2">
          <label
            htmlFor="filter-service"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Service
          </label>
          <select
            id="filter-service"
            data-testid="filter-service"
            value={selectedService || ""}
            onChange={(e) =>
              onServiceChange((e.target.value as Service) || null)
            }
            className={clsx(
              "block w-full rounded-md border",
              "px-3 py-2 text-sm",
              "bg-white dark:bg-gray-900",
              "border-gray-300 dark:border-gray-600",
              "text-gray-900 dark:text-gray-100",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors",
            )}
            aria-label="Filter by service"
          >
            <option value="">All Services</option>
            {SERVICES.map(({ value, label }) => (
              <option key={value} value={value} data-value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Priority Filter */}
        <div className="space-y-2">
          <label
            htmlFor="filter-priority"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Priority
          </label>
          <select
            id="filter-priority"
            data-testid="filter-priority"
            value={selectedPriority || ""}
            onChange={(e) =>
              onPriorityChange((e.target.value as Priority) || null)
            }
            className={clsx(
              "block w-full rounded-md border",
              "px-3 py-2 text-sm",
              "bg-white dark:bg-gray-900",
              "border-gray-300 dark:border-gray-600",
              "text-gray-900 dark:text-gray-100",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors",
            )}
            aria-label="Filter by priority"
          >
            <option value="">All Priorities</option>
            {PRIORITIES.map(({ value, label }) => (
              <option key={value} value={value} data-value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Category Filter */}
        <div className="space-y-2">
          <label
            htmlFor="filter-category"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Category
          </label>
          <select
            id="filter-category"
            data-testid="filter-category"
            value={selectedCategory || ""}
            onChange={(e) =>
              onCategoryChange((e.target.value as Category) || null)
            }
            className={clsx(
              "block w-full rounded-md border",
              "px-3 py-2 text-sm",
              "bg-white dark:bg-gray-900",
              "border-gray-300 dark:border-gray-600",
              "text-gray-900 dark:text-gray-100",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors",
            )}
            aria-label="Filter by category"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(({ value, label }) => (
              <option key={value} value={value} data-value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Active filters:{" "}
            {[
              selectedService && `Service: ${selectedService}`,
              selectedPriority && `Priority: ${selectedPriority}`,
              selectedCategory &&
                `Category: ${selectedCategory.replace("_", " ")}`,
            ]
              .filter(Boolean)
              .join(", ")}
          </p>
        </div>
      )}
    </div>
  );
};
