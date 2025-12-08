import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// API backend target - localhost within the container
const API_TARGET = 'http://127.0.0.1:8088';

// Common proxy options to fix latency in Docker
const proxyOptions = {
  target: API_TARGET,
  changeOrigin: true,
  // These timeouts help with proxy responsiveness
  timeout: 5000,
  proxyTimeout: 5000,
  // Configure proxy to avoid hanging connections
  configure: (proxy: { on: (event: string, handler: (...args: unknown[]) => void) => void }) => {
    proxy.on('proxyReq', (proxyReq: { setHeader: (name: string, value: string) => void }) => {
      // Disable connection keep-alive to prevent hanging
      proxyReq.setHeader('Connection', 'close');
    });
  },
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    // Allow all hosts for Docker container access (dev only)
    allowedHosts: 'all',
    proxy: {
      // WebSocket endpoints need explicit handling
      '/api/v1/ws': {
        target: API_TARGET,
        changeOrigin: true,
        ws: true,
        timeout: 30000,
      },
      '/api/v1/logs/stream': {
        target: API_TARGET,
        changeOrigin: true,
        ws: true,
        timeout: 30000,
      },
      '/api': proxyOptions,
      '/health': proxyOptions,
    },
    // HMR configuration for Docker/WSL2 port mapping (9080 -> 5173)
    hmr: {
      host: 'localhost',
      clientPort: process.env.VITE_HMR_CLIENT_PORT
        ? parseInt(process.env.VITE_HMR_CLIENT_PORT)
        : 9080,
    },
    // File watching for Docker/Windows volume mounts
    watch: {
      // Use polling for Windows volume mounts (required for HMR to work)
      usePolling: true,
      interval: 1000,
    },
  },
});
