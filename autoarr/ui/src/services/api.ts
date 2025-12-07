/**
 * Shared API configuration for all frontend services.
 *
 * In development with Docker, the browser accesses the app via a mapped port (e.g., localhost:9080)
 * but API calls need to go through the proxy or directly to the backend port.
 *
 * Environment variable VITE_API_BASE_URL can be set to bypass the Vite proxy:
 * - For Docker local-test: "http://localhost:9081" (direct API access)
 * - For production: "" (empty string, use relative paths)
 */

// API base URL - use env variable or empty for relative paths (through proxy)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Helper to construct API URLs
export const apiUrl = (path: string): string => {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

// API v1 prefix helper
export const apiV1Url = (path: string): string => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return apiUrl(`/api/v1${normalizedPath}`);
};

// Health endpoint helper
export const healthUrl = (path: string = ''): string => {
  const normalizedPath = path.startsWith('/') ? path : path ? `/${path}` : '';
  return apiUrl(`/health${normalizedPath}`);
};
