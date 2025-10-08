/**
 * ConfigAudit Component
 *
 * Main component for the Configuration Audit UI.
 * Displays recommendations with filtering, sorting, and pagination.
 * Includes apply functionality with confirmation dialog and toast notifications.
 */

import React, { useState, useMemo } from "react";
import { Toaster, toast } from "react-hot-toast";
import {
  ArrowUpDown,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import clsx from "clsx";
import {
  useRecommendations,
  useApplyRecommendations,
} from "../../hooks/useConfigAudit";
import { RecommendationCard } from "./RecommendationCard";
import { FilterPanel } from "./FilterPanel";
import { ConfirmationDialog } from "./ConfirmationDialog";
import type {
  Service,
  Priority,
  Category,
  Recommendation,
  SortOption,
} from "../../types/config";

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "priority", label: "Priority" },
  { value: "service", label: "Service" },
  { value: "category", label: "Category" },
];

const PRIORITY_ORDER: Record<Priority, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

export const ConfigAudit: React.FC = () => {
  // Filter state
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [selectedPriority, setSelectedPriority] = useState<Priority | null>(
    null,
  );
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(
    null,
  );

  // Sort state
  const [sortBy, setSortBy] = useState<SortOption>("priority");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] =
    useState<Recommendation | null>(null);
  const [applyingId, setApplyingId] = useState<number | null>(null);

  // Fetch recommendations with filters
  const { data, isLoading, isError, error } = useRecommendations(
    selectedService || undefined,
    selectedPriority || undefined,
    selectedCategory || undefined,
    1, // Always fetch page 1 from API (we'll handle pagination client-side for now)
    100, // Fetch more items for client-side sorting/pagination
  );

  // Apply mutation
  const applyMutation = useApplyRecommendations();

  // Sort and paginate recommendations client-side
  const sortedAndPaginatedRecommendations = useMemo(() => {
    if (!data?.recommendations) return [];

    let sorted = [...data.recommendations];

    // Sort
    switch (sortBy) {
      case "priority":
        sorted.sort(
          (a, b) => PRIORITY_ORDER[b.priority] - PRIORITY_ORDER[a.priority],
        );
        break;
      case "service":
        sorted.sort((a, b) => a.service.localeCompare(b.service));
        break;
      case "category":
        sorted.sort((a, b) => a.category.localeCompare(b.category));
        break;
    }

    // Paginate
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return sorted.slice(startIndex, endIndex);
  }, [data?.recommendations, sortBy, currentPage]);

  const totalPages = Math.ceil((data?.recommendations?.length || 0) / pageSize);

  // Handle clear filters
  const handleClearFilters = () => {
    setSelectedService(null);
    setSelectedPriority(null);
    setSelectedCategory(null);
    setCurrentPage(1);
  };

  // Handle apply button click
  const handleApplyClick = (recommendation: Recommendation) => {
    setSelectedRecommendation(recommendation);
    setDialogOpen(true);
  };

  // Handle confirm apply
  const handleConfirmApply = async (dryRun: boolean) => {
    if (!selectedRecommendation) return;

    setApplyingId(selectedRecommendation.id);

    try {
      const result = await applyMutation.mutateAsync({
        recommendation_ids: [selectedRecommendation.id],
        dry_run: dryRun,
      });

      const applyResult = result.results[0];

      if (applyResult.success) {
        toast.success(
          dryRun
            ? "Dry run completed successfully"
            : "Setting applied successfully",
          {
            icon: <CheckCircle2 className="h-5 w-5 text-green-500" />,
            duration: 4000,
            position: "top-right",
          },
        );
      } else {
        toast.error(applyResult.message || "Failed to apply recommendation", {
          icon: <AlertCircle className="h-5 w-5 text-red-500" />,
          duration: 5000,
          position: "top-right",
        });
      }
    } catch (err) {
      toast.error("Failed to connect to service", {
        icon: <AlertCircle className="h-5 w-5 text-red-500" />,
        duration: 5000,
        position: "top-right",
      });
    } finally {
      setApplyingId(null);
      setDialogOpen(false);
      setSelectedRecommendation(null);
    }
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      // Scroll to top of recommendations
      document
        .getElementById("recommendations-container")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Toaster />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Page Header */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
            Configuration Audit
          </h1>
          <p className="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-400">
            Review and apply configuration recommendations to optimize your
            services
          </p>
        </div>

        {/* Filter Panel */}
        <div className="mb-6">
          <FilterPanel
            selectedService={selectedService}
            selectedPriority={selectedPriority}
            selectedCategory={selectedCategory}
            onServiceChange={setSelectedService}
            onPriorityChange={setSelectedPriority}
            onCategoryChange={setSelectedCategory}
            onClearFilters={handleClearFilters}
          />
        </div>

        {/* Sort Control */}
        <div className="mb-4 flex items-center justify-between flex-wrap gap-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {data?.total || 0} recommendation{data?.total !== 1 ? "s" : ""}{" "}
            found
          </p>

          <div className="flex items-center gap-2">
            <label
              htmlFor="sort-select"
              className="text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Sort by:
            </label>
            <select
              id="sort-select"
              data-testid="sort-select"
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value as SortOption);
                setCurrentPage(1);
              }}
              className={clsx(
                "rounded-md border px-3 py-1.5 text-sm",
                "bg-white dark:bg-gray-800",
                "border-gray-300 dark:border-gray-600",
                "text-gray-900 dark:text-gray-100",
                "focus:outline-none focus:ring-2 focus:ring-blue-500",
                "transition-colors",
              )}
              aria-label="Sort recommendations"
            >
              {SORT_OPTIONS.map(({ value, label }) => (
                <option key={value} value={value} data-value={value}>
                  {label}
                </option>
              ))}
            </select>
            <ArrowUpDown
              className="h-4 w-4 text-gray-400 dark:text-gray-500"
              aria-hidden="true"
            />
          </div>
        </div>

        {/* Recommendations List */}
        <div
          id="recommendations-container"
          data-testid="recommendations-container"
          className="space-y-4"
          aria-live="polite"
          aria-atomic="false"
        >
          {isLoading && (
            <div
              data-testid="loading-spinner"
              className="flex items-center justify-center py-12"
            >
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 dark:text-blue-400" />
              <span className="ml-3 text-gray-600 dark:text-gray-400">
                Loading recommendations...
              </span>
            </div>
          )}

          {isError && (
            <div
              className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center"
              role="alert"
            >
              <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-900 dark:text-red-300 mb-2">
                Failed to load recommendations
              </h3>
              <p className="text-sm text-red-700 dark:text-red-400">
                {error instanceof Error
                  ? error.message
                  : "An unexpected error occurred"}
              </p>
            </div>
          )}

          {!isLoading &&
            !isError &&
            sortedAndPaginatedRecommendations.length === 0 && (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-12 text-center">
                <div className="mx-auto h-12 w-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4">
                  <AlertCircle className="h-6 w-6 text-gray-400 dark:text-gray-500" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  No recommendations found
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Try adjusting your filters or run a new configuration audit.
                </p>
              </div>
            )}

          {!isLoading &&
            !isError &&
            sortedAndPaginatedRecommendations.map((recommendation) => (
              <RecommendationCard
                key={recommendation.id}
                recommendation={recommendation}
                onApply={handleApplyClick}
                isApplying={applyingId === recommendation.id}
              />
            ))}
        </div>

        {/* Pagination */}
        {!isLoading && !isError && totalPages > 1 && (
          <div
            data-testid="pagination"
            className="mt-6 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 pt-6"
          >
            <div className="flex flex-1 justify-between sm:hidden">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={clsx(
                  "relative inline-flex items-center px-4 py-2 text-sm font-medium rounded-md",
                  currentPage === 1
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600"
                    : "bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700",
                  "border border-gray-300 dark:border-gray-600",
                )}
              >
                Previous
              </button>
              <button
                data-testid="next-page"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={clsx(
                  "relative ml-3 inline-flex items-center px-4 py-2 text-sm font-medium rounded-md",
                  currentPage === totalPages
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600"
                    : "bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700",
                  "border border-gray-300 dark:border-gray-600",
                )}
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  Showing{" "}
                  <span className="font-medium">
                    {(currentPage - 1) * pageSize + 1}
                  </span>{" "}
                  to{" "}
                  <span className="font-medium">
                    {Math.min(
                      currentPage * pageSize,
                      data?.recommendations?.length || 0,
                    )}
                  </span>{" "}
                  of{" "}
                  <span className="font-medium">
                    {data?.recommendations?.length || 0}
                  </span>{" "}
                  results
                </p>
              </div>
              <div>
                <nav
                  className="isolate inline-flex -space-x-px rounded-md shadow-sm"
                  aria-label="Pagination"
                >
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className={clsx(
                      "relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 dark:ring-gray-600",
                      currentPage === 1
                        ? "cursor-not-allowed opacity-50"
                        : "hover:bg-gray-50 dark:hover:bg-gray-700 focus:z-20 focus:outline-offset-0",
                    )}
                  >
                    <span className="sr-only">Previous</span>
                    <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                  </button>

                  {[...Array(totalPages)].map((_, index) => {
                    const page = index + 1;
                    const isCurrent = page === currentPage;

                    // Show first, last, current, and pages around current
                    if (
                      page === 1 ||
                      page === totalPages ||
                      (page >= currentPage - 1 && page <= currentPage + 1)
                    ) {
                      return (
                        <button
                          key={page}
                          onClick={() => handlePageChange(page)}
                          className={clsx(
                            "relative inline-flex items-center px-4 py-2 text-sm font-semibold",
                            isCurrent
                              ? "z-10 bg-blue-600 text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                              : "text-gray-900 dark:text-gray-100 ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 focus:z-20 focus:outline-offset-0",
                          )}
                        >
                          {page}
                        </button>
                      );
                    } else if (
                      page === currentPage - 2 ||
                      page === currentPage + 2
                    ) {
                      return (
                        <span
                          key={page}
                          className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 ring-1 ring-inset ring-gray-300 dark:ring-gray-600"
                        >
                          ...
                        </span>
                      );
                    }
                    return null;
                  })}

                  <button
                    data-testid="next-page"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className={clsx(
                      "relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 dark:ring-gray-600",
                      currentPage === totalPages
                        ? "cursor-not-allowed opacity-50"
                        : "hover:bg-gray-50 dark:hover:bg-gray-700 focus:z-20 focus:outline-offset-0",
                    )}
                  >
                    <span className="sr-only">Next</span>
                    <ChevronRight className="h-5 w-5" aria-hidden="true" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setSelectedRecommendation(null);
        }}
        onConfirm={handleConfirmApply}
        recommendation={selectedRecommendation}
        isApplying={applyingId !== null}
      />
    </div>
  );
};
