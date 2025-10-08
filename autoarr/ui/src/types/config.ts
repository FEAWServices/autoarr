/**
 * TypeScript types for Configuration Audit API models
 *
 * These types mirror the Pydantic models from the backend API
 * to ensure type safety in the frontend.
 */

/**
 * Priority levels for recommendations
 */
export type Priority = "high" | "medium" | "low";

/**
 * Category types for recommendations
 */
export type Category =
  | "performance"
  | "security"
  | "best_practices"
  | "download";

/**
 * Service names
 */
export type Service = "sabnzbd" | "sonarr" | "radarr" | "plex";

/**
 * Configuration recommendation model
 */
export interface Recommendation {
  id: number;
  service: Service;
  category: Category;
  priority: Priority;
  title: string;
  description: string;
  current_value: string | null;
  recommended_value: string;
  impact: string;
  source?: string | null;
  applied: boolean;
  applied_at: string | null;
}

/**
 * Detailed recommendation with explanation and references
 */
export interface DetailedRecommendation extends Recommendation {
  explanation: string;
  references: string[];
}

/**
 * Response model for configuration audit
 */
export interface ConfigAuditResponse {
  audit_id: string;
  timestamp: string;
  services: string[];
  recommendations: Recommendation[];
  total_recommendations: number;
  web_search_used?: boolean;
}

/**
 * Response model for listing recommendations
 */
export interface RecommendationsListResponse {
  recommendations: Recommendation[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Request model for applying configuration changes
 */
export interface ApplyConfigRequest {
  recommendation_ids: number[];
  dry_run: boolean;
}

/**
 * Result of applying a single recommendation
 */
export interface ApplyResult {
  recommendation_id: number;
  success: boolean;
  message: string;
  service?: string | null;
  applied_at?: string | null;
  dry_run?: boolean | null;
}

/**
 * Response model for applying configuration changes
 */
export interface ApplyConfigResponse {
  results: ApplyResult[];
  total_requested: number;
  total_successful: number;
  total_failed: number;
  dry_run?: boolean;
}

/**
 * Sort options for recommendations
 */
export type SortOption = "priority" | "service" | "category";

/**
 * Audit history item
 */
export interface AuditHistoryItem {
  audit_id: string;
  timestamp: string;
  services: string[];
  total_recommendations: number;
  applied_recommendations: number;
  web_search_used: boolean;
}

/**
 * Response model for audit history
 */
export interface AuditHistoryResponse {
  audits: AuditHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Service health metrics
 */
export interface ServiceHealth {
  service: string;
  healthScore: number;
  recommendations: {
    high: number;
    medium: number;
    low: number;
  };
  lastAudit?: string;
}

/**
 * Overall system health
 */
export interface SystemHealth {
  overallScore: number;
  totalRecommendations: number;
  highPriority: number;
  mediumPriority: number;
  lowPriority: number;
  services: ServiceHealth[];
}
