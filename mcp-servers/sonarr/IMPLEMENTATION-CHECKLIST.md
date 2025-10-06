# Sonarr MCP Server - Implementation Checklist

## Quick Reference for TDD Green Phase

This checklist guides you through implementing the Sonarr MCP Server to pass all 238 tests.

## ✅ Prerequisites

- [ ] All tests reviewed: `tests/unit/mcp_servers/sonarr/`
- [ ] Test strategy read: `docs/test-strategy-sonarr.md`
- [ ] RED phase verified: Tests fail with `ModuleNotFoundError`

## 📋 Implementation Checklist

### Phase 1: Setup (5 min)

- [ ] Create `mcp-servers/sonarr/__init__.py`
  ```python
  """Sonarr MCP Server package."""
  from .client import SonarrClient, SonarrClientError, SonarrConnectionError
  from .server import SonarrMCPServer

  __all__ = [
      "SonarrClient",
      "SonarrClientError",
      "SonarrConnectionError",
      "SonarrMCPServer",
  ]
  ```

### Phase 2: Client Implementation (60-90 min)

#### File: `mcp-servers/sonarr/client.py`

- [ ] **Import required modules**
  ```python
  import json
  from typing import Any, Dict, List, Optional
  from urllib.parse import urljoin
  import httpx
  from httpx import AsyncClient, HTTPError
  ```

- [ ] **Define exception classes**
  - [ ] `SonarrClientError(Exception)` - Base exception
  - [ ] `SonarrConnectionError(SonarrClientError)` - Connection failures

- [ ] **Implement SonarrClient class**

  **Initialization:**
  - [ ] `__init__(url, api_key, timeout=30.0)`
    - Validate URL (not empty)
    - Validate API key (not empty)
    - Normalize URL (remove trailing slash)
    - Store timeout
    - Initialize _client as None

  - [ ] `@classmethod async create(url, api_key, timeout, validate_connection)`
    - Create instance
    - Optionally call health_check()
    - Return instance

  - [ ] `async close()` - Close HTTP client
  - [ ] `async __aenter__() / __aexit__()` - Context manager

  **Core Methods:**
  - [ ] `_get_client()` - Get or create AsyncClient
  - [ ] `_build_url(endpoint)` - Build `/api/v3/{endpoint}` URL
  - [ ] `async _request(method, endpoint, **kwargs)`
    - Add X-Api-Key header (CRITICAL!)
    - Add Content-Type for POST
    - Implement retry logic for 503
    - Handle errors (401, 404, 500, network)
    - Parse JSON response

  **Series Operations (5 methods):**
  - [ ] `async get_series() -> List[Dict]`
    - GET /api/v3/series

  - [ ] `async get_series_by_id(series_id: int) -> Dict`
    - GET /api/v3/series/{id}
    - Raise SonarrClientError on 404

  - [ ] `async add_series(series_data: Dict) -> Dict`
    - Validate required fields (tvdbId, rootFolderPath)
    - POST /api/v3/series
    - Return created series

  - [ ] `async search_series(term: str) -> List[Dict]`
    - GET /api/v3/series/lookup?term={term}

  - [ ] `async delete_series(series_id, delete_files=False, add_import_exclusion=False)`
    - DELETE /api/v3/series/{id}?deleteFiles={bool}&addImportExclusion={bool}

  **Episode Operations (3 methods):**
  - [ ] `async get_episodes(series_id: int, season_number: Optional[int] = None) -> List[Dict]`
    - GET /api/v3/episode?seriesId={id}&seasonNumber={num}

  - [ ] `async get_episode_by_id(episode_id: int) -> Dict`
    - GET /api/v3/episode/{id}

  - [ ] `async search_episode(episode_id: int) -> Dict`
    - POST /api/v3/command
    - Body: {"name": "EpisodeSearch", "episodeIds": [id]}
    - Return command response

  **Command Operations (5 methods):**
  - [ ] `async _execute_command(name: str, body: Dict) -> Dict`
    - POST /api/v3/command
    - Body: {"name": name, ...body}

  - [ ] `async get_command(command_id: int) -> Dict`
    - GET /api/v3/command/{id}

  - [ ] `async search_series_command(series_id: int) -> Dict`
    - Execute SeriesSearch command

  - [ ] `async refresh_series(series_id: int) -> Dict`
    - Execute RefreshSeries command

  - [ ] `async rescan_series(series_id: int) -> Dict`
    - Execute RescanSeries command

  **Other Operations (4 methods):**
  - [ ] `async get_calendar(start_date: str = None, end_date: str = None) -> List[Dict]`
    - GET /api/v3/calendar?start={date}&end={date}

  - [ ] `async get_queue(page: int = 1, page_size: int = 20) -> Dict`
    - GET /api/v3/queue?page={num}&pageSize={num}

  - [ ] `async get_wanted_missing(page: int = 1, page_size: int = 20, include_series: bool = None) -> Dict`
    - GET /api/v3/wanted/missing?page={num}&pageSize={num}

  - [ ] `async get_system_status() -> Dict`
    - GET /api/v3/system/status

  - [ ] `async health_check() -> bool`
    - Call get_system_status()
    - Return True on success, False on error

### Phase 3: Server Implementation (45-60 min)

#### File: `mcp-servers/sonarr/server.py`

- [ ] **Import required modules**
  ```python
  import json
  from typing import Any, Dict, List
  from mcp.server import Server
  from mcp.types import Tool, TextContent
  from .client import SonarrClient, SonarrClientError, SonarrConnectionError
  ```

- [ ] **Implement SonarrMCPServer class**

  **Initialization:**
  - [ ] `__init__(client: SonarrClient)`
    - Validate client is not None
    - Store client
    - Set name = "sonarr"
    - Set version
    - Create MCP Server instance
    - Call _setup_handlers()

  - [ ] `_setup_handlers()`
    - Register list_tools handler
    - Register call_tool handler

  **Tool Definition:**
  - [ ] `_get_tools() -> List[Tool]`
    - Return list of 10 Tool objects with schemas

    **Tool 1: sonarr_get_series**
    - Description: List all TV series
    - Input schema: {} (no required params)

    **Tool 2: sonarr_get_series_by_id**
    - Description: Get specific series details
    - Required: series_id (integer)

    **Tool 3: sonarr_add_series**
    - Description: Add new TV series
    - Required: title, tvdb_id, quality_profile_id, root_folder_path
    - Optional: monitored, season_folder

    **Tool 4: sonarr_search_series**
    - Description: Search for TV shows
    - Required: term (string)

    **Tool 5: sonarr_get_episodes**
    - Description: Get episodes for a series
    - Required: series_id
    - Optional: season_number

    **Tool 6: sonarr_search_episode**
    - Description: Trigger episode search
    - Required: episode_id

    **Tool 7: sonarr_get_wanted**
    - Description: Get missing/wanted episodes
    - Optional: page, page_size, include_series

    **Tool 8: sonarr_get_calendar**
    - Description: Get upcoming episodes
    - Optional: start_date, end_date

    **Tool 9: sonarr_get_queue**
    - Description: Get download queue
    - Optional: page, page_size

    **Tool 10: sonarr_delete_series**
    - Description: Remove a series
    - Required: series_id
    - Optional: delete_files, add_import_exclusion

  **Tool Execution:**
  - [ ] `async _call_tool(name: str, arguments: Dict) -> List[TextContent]`
    - Try/except wrapper
    - Dispatch to handler based on name
    - Format success response: `{"success": True, "data": result}`
    - Format error response: `{"success": False, "error": str(error)}`
    - Return as List[TextContent]

  **Tool Handlers (10 methods):**
  - [ ] `async _handle_get_series(arguments)` → call client.get_series()
  - [ ] `async _handle_get_series_by_id(arguments)` → validate series_id, call client
  - [ ] `async _handle_add_series(arguments)` → build series_data dict, call client
  - [ ] `async _handle_search_series(arguments)` → validate term, call client
  - [ ] `async _handle_get_episodes(arguments)` → extract series_id/season, call client
  - [ ] `async _handle_search_episode(arguments)` → validate episode_id, call client
  - [ ] `async _handle_get_wanted(arguments)` → extract pagination params, call client
  - [ ] `async _handle_get_calendar(arguments)` → extract dates, call client
  - [ ] `async _handle_get_queue(arguments)` → extract pagination, call client
  - [ ] `async _handle_delete_series(arguments)` → extract id and flags, call client

### Phase 4: Testing (30 min)

- [ ] **Run unit tests**
  ```bash
  pytest tests/unit/mcp_servers/sonarr/test_sonarr_client.py -v
  ```
  Expected: All 112 tests pass

- [ ] **Run server tests**
  ```bash
  pytest tests/unit/mcp_servers/sonarr/test_sonarr_server.py -v
  ```
  Expected: All 68 tests pass

- [ ] **Run integration tests**
  ```bash
  pytest tests/integration/mcp_servers/sonarr/ -v
  ```
  Expected: All 58 tests pass

- [ ] **Check coverage**
  ```bash
  pytest tests/unit/mcp_servers/sonarr/ tests/integration/mcp_servers/sonarr/ \
    --cov=mcp_servers.sonarr \
    --cov-report=term-missing \
    --cov-fail-under=90
  ```
  Expected: 90%+ coverage

### Phase 5: Refactor (30 min)

- [ ] Extract common patterns
- [ ] Add comprehensive type hints
- [ ] Add detailed docstrings
- [ ] Improve error messages
- [ ] Optimize performance
- [ ] Run tests again (ensure still passing)

### Phase 6: Mutation Testing (optional, 30 min)

- [ ] Install mutmut: `pip install mutmut`
- [ ] Run mutation tests: `mutmut run --paths-to-mutate=mcp-servers/sonarr/`
- [ ] Check results: `mutmut results`
- [ ] Fix surviving mutants
- [ ] Target: 80%+ mutation score

## 🔑 Critical Implementation Notes

### Authentication (MOST IMPORTANT!)

```python
# ✅ CORRECT - Use headers
headers = {
    "X-Api-Key": self.api_key,
    "Content-Type": "application/json"  # For POST/PUT
}
response = await client.get(url, headers=headers)

# ❌ WRONG - Don't use query params
url = f"{base_url}?apikey={api_key}"  # This is SABnzbd pattern!
```

### URL Building

```python
# ✅ CORRECT
def _build_url(self, endpoint: str) -> str:
    return f"{self.url}/api/v3/{endpoint.lstrip('/')}"

# Example: _build_url("series") → "http://localhost:8989/api/v3/series"
```

### Error Handling

```python
# Handle specific status codes
if response.status_code == 401:
    raise SonarrClientError("Unauthorized: Invalid API key")
elif response.status_code == 404:
    raise SonarrClientError(f"Resource not found (404)")
elif response.status_code >= 500:
    raise SonarrClientError(f"Server error: {response.status_code}")
```

### Retry Logic

```python
# Retry on 503 Service Unavailable
for attempt in range(max_retries):
    try:
        response = await client.request(...)
        if response.status_code == 503 and attempt < max_retries - 1:
            continue  # Retry
        # Process response
        break
    except HTTPError as e:
        if attempt < max_retries - 1:
            continue  # Retry
        raise SonarrConnectionError(f"Connection failed: {e}")
```

### MCP Response Format

```python
# Success
return [TextContent(
    type="text",
    text=json.dumps({"success": True, "data": result})
)]

# Error
return [TextContent(
    type="text",
    text=json.dumps({"success": False, "error": str(error)})
)]
```

## 📚 Quick Reference

### Test Files
- `tests/unit/mcp_servers/sonarr/test_sonarr_client.py` - Client tests
- `tests/unit/mcp_servers/sonarr/test_sonarr_server.py` - Server tests
- `tests/integration/mcp_servers/sonarr/test_sonarr_api_integration.py` - API tests
- `tests/integration/mcp_servers/sonarr/test_sonarr_mcp_integration.py` - MCP tests

### Documentation
- `docs/test-strategy-sonarr.md` - Full strategy
- `docs/SONARR-TEST-SUMMARY.md` - Summary
- `docs/SONARR-TDD-DELIVERABLES.md` - Deliverables

### Reference Implementation
- `mcp-servers/sabnzbd/client.py` - Similar pattern (BUT different auth!)
- `mcp-servers/sabnzbd/server.py` - MCP server pattern

## ⏱️ Time Estimates

- Setup: 5 min
- Client implementation: 60-90 min
- Server implementation: 45-60 min
- Testing & debugging: 30 min
- Refactoring: 30 min
- **Total: 2.5 - 3.5 hours**

## ✅ Done Criteria

- [ ] All 238 tests pass
- [ ] Coverage ≥ 90%
- [ ] No pylint/mypy errors
- [ ] All docstrings complete
- [ ] Code reviewed and refactored
- [ ] Mutation score ≥ 80% (optional)

## 🚨 Common Pitfalls to Avoid

1. **DON'T use query param auth** (use X-Api-Key header)
2. **DON'T forget /api/v3/ prefix** in URLs
3. **DON'T skip retry logic** for 503 errors
4. **DON'T ignore parameter validation** in handlers
5. **DON'T forget to validate required fields** before API calls
6. **DON'T return client exceptions directly** (wrap in MCP format)

## 🎯 Success Indicators

- Tests go from RED (failing) to GREEN (passing)
- Coverage report shows 90%+
- All test categories pass (initialization, series, episodes, commands, etc.)
- Integration tests validate full workflows
- MCP protocol tests confirm compliance

---

**Good luck with the implementation!** Follow this checklist and you'll pass all 238 tests. 🚀
