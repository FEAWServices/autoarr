/**
 * Service Status Card Component
 *
 * Displays health status and recommendations for a single service
 * - Mobile-first responsive design
 * - WCAG 2.1 AA accessible
 * - Color-coded health scores
 */

import { Download, Tv, Film, Server } from 'lucide-react';
import type { ServiceHealth } from '../../types/config';
import { formatDistanceToNow } from '../../utils/date';

interface ServiceCardProps {
  serviceHealth: ServiceHealth;
}

const serviceIcons = {
  sabnzbd: Download,
  sonarr: Tv,
  radarr: Film,
  plex: Server,
};

const serviceNames = {
  sabnzbd: 'SABnzbd',
  sonarr: 'Sonarr',
  radarr: 'Radarr',
  plex: 'Plex',
};

function getHealthColor(score: number): string {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-red-600 dark:text-red-400';
}

function getHealthBgColor(score: number): string {
  if (score >= 80) return 'bg-green-50 dark:bg-green-900/20';
  if (score >= 60) return 'bg-yellow-50 dark:bg-yellow-900/20';
  return 'bg-red-50 dark:bg-red-900/20';
}

export function ServiceCard({ serviceHealth }: ServiceCardProps) {
  const serviceName =
    serviceNames[serviceHealth.service as keyof typeof serviceNames] || serviceHealth.service;
  const Icon = serviceIcons[serviceHealth.service as keyof typeof serviceIcons] || Server;
  const healthColor = getHealthColor(serviceHealth.healthScore);
  const healthBgColor = getHealthBgColor(serviceHealth.healthScore);

  return (
    <div
      className="group relative bg-white/5 dark:bg-white/5 backdrop-blur-md rounded-2xl shadow-glass border border-white/10 dark:border-white/10 p-5 hover:shadow-glass-hover hover:bg-white/10 dark:hover:bg-white/8 transition-all duration-300 hover:scale-105 hover:-translate-y-1 animate-slide-up overflow-hidden"
      data-testid={`service-card-${serviceHealth.service}`}
    >
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div
              className="p-2.5 rounded-xl bg-gradient-primary shadow-glow group-hover:shadow-glow-lg transition-all duration-300"
              data-testid="service-icon"
            >
              <Icon className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-bold text-white bg-gradient-to-r from-white to-text-secondary bg-clip-text">
              {serviceName}
            </h2>
          </div>

          {/* Health Score */}
          <div
            className={`${healthBgColor} px-3 py-1.5 rounded-full backdrop-blur-sm shadow-lg`}
            data-testid="health-score"
            aria-label={`Health score: ${serviceHealth.healthScore} out of 100`}
            title={`Health score: ${serviceHealth.healthScore}/100`}
          >
            <span className={`text-sm font-bold ${healthColor}`}>{serviceHealth.healthScore}</span>
          </div>
        </div>

        {/* Recommendations Count */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">High Priority</span>
            <span
              className="font-semibold text-red-600 dark:text-red-400"
              data-testid="rec-count-high"
              aria-label={`${serviceHealth.recommendations.high} high priority recommendations`}
            >
              {serviceHealth.recommendations.high}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Medium Priority</span>
            <span
              className="font-semibold text-yellow-600 dark:text-yellow-400"
              data-testid="rec-count-medium"
              aria-label={`${serviceHealth.recommendations.medium} medium priority recommendations`}
            >
              {serviceHealth.recommendations.medium}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Low Priority</span>
            <span
              className="font-semibold text-blue-600 dark:text-blue-400"
              data-testid="rec-count-low"
              aria-label={`${serviceHealth.recommendations.low} low priority recommendations`}
            >
              {serviceHealth.recommendations.low}
            </span>
          </div>
        </div>

        {/* Last Audit */}
        {serviceHealth.lastAudit && (
          <div
            className="text-xs text-text-muted border-t border-white/10 pt-3 mt-1"
            data-testid="last-audit-time"
            aria-label={`Last audited ${formatDistanceToNow(serviceHealth.lastAudit)}`}
          >
            Last audit: {formatDistanceToNow(serviceHealth.lastAudit)}
          </div>
        )}
      </div>
    </div>
  );
}
