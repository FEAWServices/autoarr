# AutoArr Code Examples

This document provides starter code examples to help you begin implementation immediately.

---

## 🐍 Backend Examples

### 1. SABnzbd MCP Server (Starter)

**File**: `mcp-servers/sabnzbd/server.py`

```python
"""SABnzbd MCP Server

This server provides tools to interact with SABnzbd via its API.
"""

import asyncio
import httpx
from typing import Any, Dict, List, Optional
from mcp import MCPServer, Tool


class SABnzbdClient:
    """Client for SABnzbd API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _request(self, mode: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to SABnzbd API."""
        url = f"{self.base_url}/api"
        params = params or {}
        params.update({
            'mode': mode,
            'apikey': self.api_key,
            'output': 'json'
        })
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ConnectionError(f"SABnzbd API error: {e}")
    
    async def get_queue(self) -> Dict[str, Any]:
        """Get current download queue."""
        return await self._request('queue')
    
    async def get_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get download history."""
        return await self._request('history', {'limit': limit})
    
    async def retry_download(self, nzo_id: str) -> Dict[str, Any]:
        """Retry a failed download."""
        return await self._request('retry', {'value': nzo_id})
    
    async def get_config(self) -> Dict[str, Any]:
        """Get SABnzbd configuration."""
        return await self._request('get_config')
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()


class SABnzbdMCPServer(MCPServer):
    """MCP Server for SABnzbd."""
    
    def __init__(self, url: str, api_key: str):
        super().__init__()
        self.client = SABnzbdClient(url, api_key)
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools."""
        self.add_tool(
            Tool(
                name="get_queue",
                description="Get the current download queue from SABnzbd",
                handler=self._get_queue
            )
        )
        
        self.add_tool(
            Tool(
                name="get_history",
                description="Get download history from SABnzbd",
                handler=self._get_history,
                parameters={
                    "limit": {
                        "type": "integer",
                        "description": "Number of history items to retrieve",
                        "default": 50
                    }
                }
            )
        )
        
        self.add_tool(
            Tool(
                name="retry_download",
                description="Retry a failed download",
                handler=self._retry_download,
                parameters={
                    "nzo_id": {
                        "type": "string",
                        "description": "ID of the download to retry",
                        "required": True
                    }
                }
            )
        )
    
    async def _get_queue(self, **kwargs) -> Dict[str, Any]:
        """Tool handler for get_queue."""
        return await self.client.get_queue()
    
    async def _get_history(self, limit: int = 50, **kwargs) -> Dict[str, Any]:
        """Tool handler for get_history."""
        return await self.client.get_history(limit=limit)
    
    async def _retry_download(self, nzo_id: str, **kwargs) -> Dict[str, Any]:
        """Tool handler for retry_download."""
        return await self.client.retry_download(nzo_id)
    
    async def cleanup(self):
        """Clean up resources."""
        await self.client.close()


async def main():
    """Run the MCP server."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    url = os.getenv('SABNZBD_URL', 'http://localhost:8080')
    api_key = os.getenv('SABNZBD_API_KEY')
    
    if not api_key:
        raise ValueError("SABNZBD_API_KEY environment variable is required")
    
    server = SABnzbdMCPServer(url, api_key)
    
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Configuration Manager Service

**File**: `api/services/configuration_manager.py`

```python
"""Configuration Manager Service

Handles auditing and optimizing application configurations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..mcp.orchestrator import MCPOrchestrator


@dataclass
class Recommendation:
    """A configuration recommendation."""
    app_name: str
    setting: str
    current_value: any
    recommended_value: any
    priority: str  # 'high', 'medium', 'low'
    reason: str
    impact: str


@dataclass
class AuditResult:
    """Result of a configuration audit."""
    app_name: str
    timestamp: datetime
    recommendations: List[Recommendation]
    overall_score: int  # 0-100
    
    @property
    def has_recommendations(self) -> bool:
        return len(self.recommendations) > 0


class ConfigurationManager:
    """Manages configuration auditing and optimization."""
    
    def __init__(self, orchestrator: MCPOrchestrator):
        self.orchestrator = orchestrator
        self.best_practices = self._load_best_practices()
    
    def _load_best_practices(self) -> Dict[str, List[Dict]]:
        """Load best practices from database."""
        # TODO: Load from database
        return {
            'sabnzbd': [
                {
                    'setting': 'download_dir',
                    'condition': lambda v: v != '',
                    'recommendation': '/downloads',
                    'priority': 'high',
                    'reason': 'Download directory should be explicitly set'
                },
                {
                    'setting': 'incomplete_dir',
                    'condition': lambda v: v != '',
                    'recommendation': '/downloads/incomplete',
                    'priority': 'high',
                    'reason': 'Separate incomplete directory prevents issues'
                },
                {
                    'setting': 'servers',
                    'condition': lambda v: len(v) > 1,
                    'recommendation': 'multiple',
                    'priority': 'medium',
                    'reason': 'Multiple servers provide redundancy'
                },
            ],
            'sonarr': [
                {
                    'setting': 'recycling_bin',
                    'condition': lambda v: v != '',
                    'recommendation': '/recycle',
                    'priority': 'medium',
                    'reason': 'Recycling bin prevents accidental deletions'
                },
            ],
            'radarr': [
                {
                    'setting': 'recycling_bin',
                    'condition': lambda v: v != '',
                    'recommendation': '/recycle',
                    'priority': 'medium',
                    'reason': 'Recycling bin prevents accidental deletions'
                },
            ],
        }
    
    async def audit_application(
        self,
        app_name: str,
        config: Optional[Dict] = None
    ) -> AuditResult:
        """Audit an application's configuration.
        
        Args:
            app_name: Name of the application to audit
            config: Optional configuration dict (will fetch if not provided)
            
        Returns:
            AuditResult with recommendations
        """
        # Get current configuration if not provided
        if config is None:
            config = await self._fetch_config(app_name)
        
        # Get best practices for this app
        practices = self.best_practices.get(app_name, [])
        
        # Generate recommendations
        recommendations = []
        for practice in practices:
            setting = practice['setting']
            current_value = config.get(setting)
            
            # Check if current value meets best practice
            if not practice['condition'](current_value):
                recommendations.append(
                    Recommendation(
                        app_name=app_name,
                        setting=setting,
                        current_value=current_value,
                        recommended_value=practice['recommendation'],
                        priority=practice['priority'],
                        reason=practice['reason'],
                        impact=self._estimate_impact(practice['priority'])
                    )
                )
        
        # Calculate overall score
        score = self._calculate_score(len(practices), len(recommendations))
        
        return AuditResult(
            app_name=app_name,
            timestamp=datetime.utcnow(),
            recommendations=recommendations,
            overall_score=score
        )
    
    async def _fetch_config(self, app_name: str) -> Dict:
        """Fetch configuration from application via MCP."""
        result = await self.orchestrator.call_tool(
            server=app_name,
            tool='get_config',
            params={}
        )
        
        if not result.success:
            raise ValueError(f"Failed to fetch config from {app_name}")
        
        return result.data
    
    def _calculate_score(self, total_checks: int, issues: int) -> int:
        """Calculate configuration score (0-100)."""
        if total_checks == 0:
            return 100
        return int(((total_checks - issues) / total_checks) * 100)
    
    def _estimate_impact(self, priority: str) -> str:
        """Estimate impact of implementing recommendation."""
        impact_map = {
            'high': 'Significant improvement in reliability',
            'medium': 'Moderate improvement in functionality',
            'low': 'Minor optimization'
        }
        return impact_map.get(priority, 'Unknown impact')
    
    async def apply_configuration(
        self,
        app_name: str,
        changes: Dict[str, any]
    ) -> bool:
        """Apply configuration changes.
        
        Args:
            app_name: Name of application
            changes: Dict of setting -> new value
            
        Returns:
            True if successful
        """
        result = await self.orchestrator.call_tool(
            server=app_name,
            tool='set_config',
            params={'changes': changes}
        )
        
        return result.success
```

---

## ⚛️ Frontend Examples

### 1. Dashboard Component

**File**: `ui/src/components/Dashboard/Dashboard.tsx`

```typescript
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { StatusCard } from './StatusCard';
import { AuditResults } from './AuditResults';

interface SystemStatus {
  sabnzbd: {
    connected: boolean;
    queue_count: number;
  };
  sonarr: {
    connected: boolean;
    wanted_count: number;
  };
  radarr: {
    connected: boolean;
    wanted_count: number;
  };
}

export function Dashboard() {
  const [auditRunning, setAuditRunning] = useState(false);

  // Fetch system status
  const { data: status, isLoading } = useQuery<SystemStatus>({
    queryKey: ['system-status'],
    queryFn: () => api.getStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch audit results
  const { data: auditResults, refetch: refetchAudit } = useQuery({
    queryKey: ['audit-results'],
    queryFn: () => api.getAuditResults(),
    enabled: false, // Only fetch when triggered
  });

  const handleRunAudit = async () => {
    setAuditRunning(true);
    try {
      await api.triggerAudit();
      await refetchAudit();
    } finally {
      setAuditRunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          AutoArr Dashboard
        </h1>
        <p className="text-gray-600">
          Intelligent cruise control for your media server
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatusCard
          title="SABnzbd"
          connected={status?.sabnzbd.connected ?? false}
          metric={{
            label: 'Queue',
            value: status?.sabnzbd.queue_count ?? 0,
          }}
        />
        <StatusCard
          title="Sonarr"
          connected={status?.sonarr.connected ?? false}
          metric={{
            label: 'Wanted',
            value: status?.sonarr.wanted_count ?? 0,
          }}
        />
        <StatusCard
          title="Radarr"
          connected={status?.radarr.connected ?? false}
          metric={{
            label: 'Wanted',
            value: status?.radarr.wanted_count ?? 0,
          }}
        />
      </div>

      {/* Audit Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Configuration Audit</h2>
          <button
            onClick={handleRunAudit}
            disabled={auditRunning}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {auditRunning ? (
              <>
                <span className="animate-spin inline-block mr-2">⏳</span>
                Running Audit...
              </>
            ) : (
              'Run Audit'
            )}
          </button>
        </div>

        {auditResults && <AuditResults results={auditResults} />}
      </div>

      {/* Activity Feed */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        {/* TODO: Implement activity feed */}
        <p className="text-gray-500 text-sm">No recent activity</p>
      </div>
    </div>
  );
}
```

### 2. API Client

**File**: `ui/src/services/api.ts`

```typescript
/**
 * API Client for AutoArr Backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8088';

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchJSON<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new APIError(
      data.message || 'API request failed',
      response.status,
      data
    );
  }

  return response.json();
}

export const api = {
  // System Status
  getStatus: () => fetchJSON('/api/v1/monitoring/status'),

  // Configuration Audit
  triggerAudit: () => fetchJSON('/api/v1/config/audit', { method: 'POST' }),
  getAuditResults: () => fetchJSON('/api/v1/config/recommendations'),
  applyConfig: (appName: string, changes: Record<string, any>) =>
    fetchJSON('/api/v1/config/apply', {
      method: 'POST',
      body: JSON.stringify({ app_name: appName, changes }),
    }),

  // Content Requests
  requestContent: (query: string) =>
    fetchJSON('/api/v1/request/content', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),
  getRequestStatus: (requestId: string) =>
    fetchJSON(`/api/v1/request/status/${requestId}`),

  // Activity Log
  getActivity: (limit: number = 50) =>
    fetchJSON(`/api/v1/activity?limit=${limit}`),
};

export { APIError };
```

---

## 🧪 Testing Examples

### 1. Backend Test (pytest)

**File**: `api/tests/services/test_configuration_manager.py`

```python
"""Tests for Configuration Manager."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from services.configuration_manager import (
    ConfigurationManager,
    AuditResult,
    Recommendation
)


@pytest.fixture
def mock_orchestrator():
    """Create a mock MCP orchestrator."""
    orchestrator = AsyncMock()
    return orchestrator


@pytest.fixture
def config_manager(mock_orchestrator):
    """Create a Configuration Manager instance."""
    return ConfigurationManager(mock_orchestrator)


@pytest.mark.asyncio
async def test_audit_identifies_missing_download_dir(config_manager, mock_orchestrator):
    """Test that audit identifies missing download directory."""
    # Arrange
    mock_config = {
        'download_dir': '',  # Missing!
        'incomplete_dir': '/downloads/incomplete',
        'servers': ['server1', 'server2']
    }
    
    mock_orchestrator.call_tool.return_value = MagicMock(
        success=True,
        data=mock_config
    )
    
    # Act
    result = await config_manager.audit_application('sabnzbd')
    
    # Assert
    assert result.has_recommendations
    assert any(
        r.setting == 'download_dir'
        for r in result.recommendations
    )
    assert result.overall_score < 100


@pytest.mark.asyncio
async def test_audit_with_optimal_config(config_manager, mock_orchestrator):
    """Test that audit gives high score for optimal config."""
    # Arrange
    mock_config = {
        'download_dir': '/downloads',
        'incomplete_dir': '/downloads/incomplete',
        'servers': ['server1', 'server2']
    }
    
    mock_orchestrator.call_tool.return_value = MagicMock(
        success=True,
        data=mock_config
    )
    
    # Act
    result = await config_manager.audit_application('sabnzbd')
    
    # Assert
    assert not result.has_recommendations
    assert result.overall_score == 100


@pytest.mark.asyncio
async def test_apply_configuration(config_manager, mock_orchestrator):
    """Test applying configuration changes."""
    # Arrange
    changes = {'download_dir': '/downloads'}
    mock_orchestrator.call_tool.return_value = MagicMock(success=True)
    
    # Act
    success = await config_manager.apply_configuration('sabnzbd', changes)
    
    # Assert
    assert success
    mock_orchestrator.call_tool.assert_called_once_with(
        server='sabnzbd',
        tool='set_config',
        params={'changes': changes}
    )
```

### 2. Frontend Test (Playwright)

**File**: `ui/tests/dashboard.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/monitoring/status', async (route) => {
      await route.fulfill({
        json: {
          sabnzbd: { connected: true, queue_count: 3 },
          sonarr: { connected: true, wanted_count: 5 },
          radarr: { connected: true, wanted_count: 2 },
        },
      });
    });

    await page.goto('http://localhost:3000');
  });

  test('should display status cards', async ({ page }) => {
    // Check that all status cards are visible
    await expect(page.getByText('SABnzbd')).toBeVisible();
    await expect(page.getByText('Sonarr')).toBeVisible();
    await expect(page.getByText('Radarr')).toBeVisible();

    // Check queue counts
    await expect(page.getByText('Queue: 3')).toBeVisible();
    await expect(page.getByText('Wanted: 5')).toBeVisible();
    await expect(page.getByText('Wanted: 2')).toBeVisible();
  });

  test('should run configuration audit', async ({ page }) => {
    // Mock audit endpoint
    await page.route('**/api/v1/config/audit', async (route) => {
      await route.fulfill({ json: { success: true } });
    });

    await page.route('**/api/v1/config/recommendations', async (route) => {
      await route.fulfill({
        json: {
          sabnzbd: {
            score: 75,
            recommendations: [
              {
                setting: 'download_dir',
                current_value: '',
                recommended_value: '/downloads',
                priority: 'high',
                reason: 'Download directory should be explicitly set',
              },
            ],
          },
        },
      });
    });

    // Click Run Audit button
    await page.getByRole('button', { name: 'Run Audit' }).click();

    // Should show loading state
    await expect(page.getByText('Running Audit...')).toBeVisible();

    // Should show results
    await expect(page.getByText('download_dir')).toBeVisible();
    await expect(
      page.getByText('Download directory should be explicitly set')
    ).toBeVisible();
  });

  test('should be mobile responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Status cards should stack vertically
    const cards = page.locator('[data-testid="status-card"]');
    const firstCardBox = await cards.first().boundingBox();
    const secondCardBox = await cards.nth(1).boundingBox();

    // Second card should be below first card (not beside)
    expect(secondCardBox!.y).toBeGreaterThan(firstCardBox!.y + firstCardBox!.height);
  });
});
```

---

## 🐳 Docker Examples

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: autoarr-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://autoarr:autoarr@postgres:5432/autoarr
      - REDIS_URL=redis://redis:6379
      - SABNZBD_URL=${SABNZBD_URL}
      - SABNZBD_API_KEY=${SABNZBD_API_KEY}
      - SONARR_URL=${SONARR_URL}
      - SONARR_API_KEY=${SONARR_API_KEY}
      - RADARR_URL=${RADARR_URL}
      - RADARR_API_KEY=${RADARR_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    volumes:
      - ./api:/app
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  ui:
    build:
      context: ./ui
      dockerfile: Dockerfile
    container_name: autoarr-ui
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:8088
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: autoarr-postgres
    environment:
      - POSTGRES_DB=autoarr
      - POSTGRES_USER=autoarr
      - POSTGRES_PASSWORD=autoarr
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: autoarr-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres-data:
```

---

## 📝 Notes

These examples are **starter implementations** to help you begin development. They demonstrate:

1. ✅ **Async/await patterns** in Python
2. ✅ **Type hints** for better code quality
3. ✅ **React hooks** and modern patterns
4. ✅ **TDD approach** with comprehensive tests
5. ✅ **API client** with error handling
6. ✅ **Docker setup** for easy deployment

### Next Steps

1. Copy these examples into your project structure
2. Run tests to verify setup
3. Start implementing additional features
4. Follow BUILD-PLAN.md for detailed roadmap

Happy coding! 🚀
