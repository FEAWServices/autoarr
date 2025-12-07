/**
 * Pull to Refresh Component
 *
 * Provides mobile-native pull-to-refresh functionality.
 * Wrap scrollable content with this component to enable refresh on pull-down.
 */

import { useState, useRef, useCallback, type ReactNode } from 'react';
import { RefreshCw } from 'lucide-react';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: ReactNode;
  className?: string;
  /** Minimum pull distance to trigger refresh (default: 80px) */
  threshold?: number;
  /** Whether pull-to-refresh is enabled (default: true) */
  enabled?: boolean;
}

export const PullToRefresh = ({
  onRefresh,
  children,
  className = '',
  threshold = 80,
  enabled = true,
}: PullToRefreshProps) => {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const startY = useRef(0);
  const isPulling = useRef(false);

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (!enabled || isRefreshing) return;

      const container = containerRef.current;
      // Only start pull if at top of scroll
      if (container && container.scrollTop === 0) {
        startY.current = e.touches[0].clientY;
        isPulling.current = true;
      }
    },
    [enabled, isRefreshing]
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!isPulling.current || !enabled || isRefreshing) return;

      const currentY = e.touches[0].clientY;
      const diff = currentY - startY.current;

      // Only allow pulling down (positive diff)
      if (diff > 0) {
        // Apply resistance - pull distance is less than actual finger movement
        const resistance = 0.5;
        const newPullDistance = Math.min(diff * resistance, threshold * 1.5);
        setPullDistance(newPullDistance);

        // Prevent default scroll behavior when pulling
        if (newPullDistance > 10) {
          e.preventDefault();
        }
      }
    },
    [enabled, isRefreshing, threshold]
  );

  const handleTouchEnd = useCallback(async () => {
    if (!isPulling.current || !enabled) return;

    isPulling.current = false;

    if (pullDistance >= threshold && !isRefreshing) {
      setIsRefreshing(true);
      setPullDistance(threshold * 0.6); // Keep indicator visible during refresh

      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
  }, [pullDistance, threshold, isRefreshing, onRefresh, enabled]);

  const progress = Math.min(pullDistance / threshold, 1);
  const shouldTrigger = pullDistance >= threshold;

  return (
    <div
      ref={containerRef}
      className={`relative overflow-y-auto ${className}`}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{ touchAction: pullDistance > 0 ? 'none' : 'auto' }}
    >
      {/* Pull indicator */}
      <div
        className="absolute left-0 right-0 flex items-center justify-center pointer-events-none z-10 transition-opacity"
        style={{
          top: 0,
          height: `${pullDistance}px`,
          opacity: pullDistance > 10 ? 1 : 0,
        }}
      >
        <div
          className={`
            flex items-center justify-center w-10 h-10 rounded-full
            ${shouldTrigger || isRefreshing ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}
            transition-colors
          `}
        >
          <RefreshCw
            className={`w-5 h-5 transition-transform ${isRefreshing ? 'animate-spin' : ''}`}
            style={{
              transform: isRefreshing
                ? undefined
                : `rotate(${progress * 180}deg)`,
            }}
          />
        </div>
      </div>

      {/* Content with pull offset */}
      <div
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: isPulling.current ? 'none' : 'transform 0.2s ease-out',
        }}
      >
        {children}
      </div>

      {/* Release to refresh hint */}
      {pullDistance > 20 && !isRefreshing && (
        <div
          className="absolute left-0 right-0 text-center text-xs text-muted-foreground pointer-events-none"
          style={{ top: pullDistance - 20 }}
        >
          {shouldTrigger ? 'Release to refresh' : 'Pull down to refresh'}
        </div>
      )}
    </div>
  );
};

export default PullToRefresh;
