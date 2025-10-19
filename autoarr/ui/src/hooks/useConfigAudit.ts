/**
 * React Query hooks for Configuration Audit API
 *
 * Provides data fetching, caching, and state management for audit operations
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  ConfigAuditResponse,
  RecommendationsListResponse,
  ApplyConfigRequest,
  ApplyConfigResponse,
} from "../types/config";

// @ts-expect-error - Vite env
const API_BASE_URL = import.meta.env?.VITE_API_URL || "/api/v1";

// ============================================================================
// API Client Functions
// ============================================================================

async function fetchRecommendations(
  service?: string,
  priority?: string,
  category?: string,
  page: number = 1,
  pageSize: number = 100,
): Promise<RecommendationsListResponse> {
  const params = new URLSearchParams();
  if (service) params.append("service", service);
  if (priority) params.append("priority", priority);
  if (category) params.append("category", category);
  params.append("page", page.toString());
  params.append("page_size", pageSize.toString());

  const response = await fetch(
    `${API_BASE_URL}/config/recommendations?${params}`,
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
  }

  return response.json();
}

async function triggerAudit(
  services: string[] = ["sabnzbd", "sonarr", "radarr", "plex"],
  includeWebSearch: boolean = false,
): Promise<ConfigAuditResponse> {
  const response = await fetch(`${API_BASE_URL}/config/audit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      services,
      include_web_search: includeWebSearch,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to run audit: ${response.statusText}`);
  }

  return response.json();
}

async function applyRecommendations(
  request: ApplyConfigRequest,
): Promise<ApplyConfigResponse> {
  const response = await fetch(`${API_BASE_URL}/config/apply`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to apply recommendations: ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// React Query Hooks
// ============================================================================

export function useRecommendations(
  service?: string,
  priority?: string,
  category?: string,
  page: number = 1,
  pageSize: number = 100,
) {
  return useQuery({
    queryKey: ["recommendations", service, priority, category, page, pageSize],
    queryFn: () =>
      fetchRecommendations(service, priority, category, page, pageSize),
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}

export function useAuditMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      services,
      includeWebSearch,
    }: {
      services?: string[];
      includeWebSearch?: boolean;
    }) => triggerAudit(services, includeWebSearch),
    onSuccess: () => {
      // Invalidate and refetch recommendations
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}

export function useApplyRecommendations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: applyRecommendations,
    onSuccess: () => {
      // Invalidate and refetch recommendations
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
