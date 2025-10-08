/**
 * Skeleton Loader Components
 *
 * Loading state placeholders for various UI elements
 * Features:
 * - Animated shimmer effect
 * - Responsive sizing
 * - Accessible (hidden from screen readers)
 */

interface SkeletonProps {
  className?: string;
}

export const Skeleton = ({ className = "" }: SkeletonProps) => {
  return (
    <div
      className={`animate-pulse bg-background-tertiary rounded ${className}`}
      aria-hidden="true"
    />
  );
};

export const SkeletonCard = () => {
  return (
    <div
      className="bg-background-secondary rounded-lg p-6 space-y-4"
      aria-hidden="true"
    >
      <div className="flex items-center gap-4">
        <Skeleton className="w-12 h-12 rounded-md" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-32" />
        </div>
      </div>
      <Skeleton className="h-20 w-full" />
      <div className="flex justify-between">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  );
};

export const SkeletonActivityItem = () => {
  return (
    <div className="bg-background-secondary rounded-lg p-4" aria-hidden="true">
      <div className="flex items-start gap-4">
        <Skeleton className="w-1 h-16 rounded-full" />
        <Skeleton className="w-10 h-10 rounded-lg" />
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </div>
    </div>
  );
};

export const SkeletonRecommendationCard = () => {
  return (
    <div
      className="bg-background-secondary rounded-lg p-6 space-y-4"
      aria-hidden="true"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-md" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <Skeleton className="h-20 w-full rounded-md" />
      <Skeleton className="h-4 w-full" />
      <div className="flex justify-end">
        <Skeleton className="h-10 w-24 rounded-md" />
      </div>
    </div>
  );
};

export const SkeletonServiceCard = () => {
  return (
    <div
      className="bg-background-secondary rounded-lg p-6 space-y-4"
      aria-hidden="true"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="w-8 h-8 rounded" />
          <Skeleton className="h-5 w-24" />
        </div>
        <Skeleton className="h-8 w-12 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-3 w-3/4" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-12 rounded-full" />
        <Skeleton className="h-6 w-12 rounded-full" />
        <Skeleton className="h-6 w-12 rounded-full" />
      </div>
    </div>
  );
};

interface SkeletonListProps {
  count?: number;
  type?: "card" | "activity" | "recommendation" | "service";
}

export const SkeletonList = ({
  count = 3,
  type = "card",
}: SkeletonListProps) => {
  const SkeletonComponent = {
    card: SkeletonCard,
    activity: SkeletonActivityItem,
    recommendation: SkeletonRecommendationCard,
    service: SkeletonServiceCard,
  }[type];

  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <span className="sr-only">Loading...</span>
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonComponent key={index} />
      ))}
    </div>
  );
};
