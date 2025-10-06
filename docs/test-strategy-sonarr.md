# Test Strategy: Sonarr MCP Server

## Overview

This document defines the comprehensive test strategy for the Sonarr MCP Server following Test-Driven Development (TDD) principles. All tests are written BEFORE implementation to drive the development process through the red-green-refactor cycle.

## Test Coverage Goals

- **Overall Coverage Target**: 90%+ for all Sonarr MCP Server code
- **Critical Path Coverage**: 100% for API communication and MCP tool execution
- **Test Pyramid Distribution**:
  - 70% Unit Tests (fast, isolated, focused)
  - 20% Integration Tests (component interaction)
  - 10% E2E Tests (MCP protocol compliance)

## Test File Structure

```
tests/
├── unit/
│   └── mcp_servers/
│       └── sonarr/
│           ├── __init__.py
│           ├── test_sonarr_client.py          # Client unit tests
│           └── test_sonarr_server.py          # MCP server unit tests
├── integration/
│   └── mcp_servers/
│       └── sonarr/
│           ├── __init__.py
│           ├── test_sonarr_api_integration.py # Real API interaction tests
│           └── test_sonarr_mcp_integration.py # MCP protocol integration
└── fixtures/
    └── sonarr_test_data.py                    # Test data factories
```

## 1. Test Data Factories

### Series Factory
Creates mock Sonarr series (TV shows) with realistic data:
- Series metadata (title, tvdbId, imdbId, year, status)
- Season/episode counts
- Quality profile configuration
- Root folder paths
- Monitoring settings

### Episode Factory
Creates mock episodes with:
- Episode numbers and titles
- Air dates and monitoring status
- File information (quality, size, path)
- Download status

### Quality Profile Factory
Creates quality profiles with:
- Profile names and cutoff settings
- Quality item lists
- Upgrade allowed settings

### Command Factory
Creates Sonarr command responses:
- Command status (queued, started, completed, failed)
- Progress tracking
- Command-specific payloads

### Calendar/Queue/Wanted Factories
- Calendar: Upcoming episodes with air dates
- Queue: Active downloads with progress
- Wanted: Missing episodes that need download

## 2. Unit Tests: SonarrClient Class

### 2.1 Initialization and Connection Tests

**Test Specifications:**

1. **test_client_requires_url**
   - GIVEN: Missing or empty URL
   - WHEN: Creating SonarrClient
   - THEN: Raises ValueError

2. **test_client_requires_api_key**
   - GIVEN: Missing or empty API key
   - WHEN: Creating SonarrClient
   - THEN: Raises ValueError

3. **test_client_normalizes_url**
   - GIVEN: URL with trailing slash
   - WHEN: Creating SonarrClient
   - THEN: URL is normalized (slash removed)

4. **test_client_accepts_custom_timeout**
   - GIVEN: Custom timeout value
   - WHEN: Creating SonarrClient
   - THEN: Client stores timeout correctly

5. **test_client_validates_connection_on_create**
   - GIVEN: validate_connection=True
   - WHEN: Using factory method
   - THEN: Makes health check request

6. **test_health_check_returns_true_when_healthy**
   - GIVEN: Sonarr responds with valid status
   - WHEN: Calling health_check()
   - THEN: Returns True

7. **test_health_check_returns_false_when_unreachable**
   - GIVEN: Sonarr is unreachable
   - WHEN: Calling health_check()
   - THEN: Returns False without raising

### 2.2 Series Operations Tests

**Test Specifications:**

1. **test_get_series_returns_all_series**
   - GIVEN: Sonarr has multiple series
   - WHEN: Calling get_series()
   - THEN: Returns list of all series

2. **test_get_series_by_id_returns_specific_series**
   - GIVEN: Valid series ID
   - WHEN: Calling get_series_by_id(id)
   - THEN: Returns specific series data

3. **test_get_series_by_id_raises_on_not_found**
   - GIVEN: Invalid series ID
   - WHEN: Calling get_series_by_id(id)
   - THEN: Raises SonarrClientError with 404

4. **test_add_series_sends_correct_payload**
   - GIVEN: Series data with tvdbId, quality profile, root folder
   - WHEN: Calling add_series()
   - THEN: POST request with correct JSON payload

5. **test_add_series_validates_required_fields**
   - GIVEN: Missing tvdbId or root folder
   - WHEN: Calling add_series()
   - THEN: Raises ValueError

6. **test_add_series_with_monitoring_options**
   - GIVEN: Monitoring configuration
   - WHEN: Calling add_series()
   - THEN: Includes monitored and seasonFolder flags

7. **test_search_series_returns_lookup_results**
   - GIVEN: Search term
   - WHEN: Calling search_series(term)
   - THEN: Returns list of matching series from TVDB

8. **test_search_series_by_tvdb_id**
   - GIVEN: TVDB ID
   - WHEN: Calling search_series(tvdb:12345)
   - THEN: Returns specific series lookup

9. **test_delete_series_removes_series**
   - GIVEN: Valid series ID
   - WHEN: Calling delete_series(id)
   - THEN: Sends DELETE request

10. **test_delete_series_with_delete_files_flag**
    - GIVEN: delete_files=True
    - WHEN: Calling delete_series(id, delete_files=True)
    - THEN: Includes deleteFiles query param

### 2.3 Episode Operations Tests

**Test Specifications:**

1. **test_get_episodes_returns_series_episodes**
   - GIVEN: Valid series ID
   - WHEN: Calling get_episodes(series_id)
   - THEN: Returns all episodes for series

2. **test_get_episodes_filters_by_season**
   - GIVEN: Series ID and season number
   - WHEN: Calling get_episodes(series_id, season=1)
   - THEN: Returns only season 1 episodes

3. **test_get_episode_by_id_returns_specific_episode**
   - GIVEN: Valid episode ID
   - WHEN: Calling get_episode_by_id(id)
   - THEN: Returns episode details

4. **test_search_episode_triggers_episode_search**
   - GIVEN: Episode ID
   - WHEN: Calling search_episode(episode_id)
   - THEN: POSTs command to search for episode

5. **test_search_episode_returns_command_id**
   - GIVEN: Episode search initiated
   - WHEN: Calling search_episode()
   - THEN: Returns command ID for tracking

### 2.4 Command Operations Tests

**Test Specifications:**

1. **test_execute_command_posts_to_command_endpoint**
   - GIVEN: Command name and body
   - WHEN: Calling _execute_command()
   - THEN: POSTs to /api/v3/command

2. **test_get_command_status_returns_command_info**
   - GIVEN: Command ID
   - WHEN: Calling get_command(id)
   - THEN: Returns command status and progress

3. **test_series_search_triggers_series_search**
   - GIVEN: Series ID
   - WHEN: Calling search_series_command(series_id)
   - THEN: POSTs SeriesSearch command

4. **test_refresh_series_triggers_refresh**
   - GIVEN: Series ID
   - WHEN: Calling refresh_series(series_id)
   - THEN: POSTs RefreshSeries command

### 2.5 Calendar, Queue, and Wanted Tests

**Test Specifications:**

1. **test_get_calendar_returns_upcoming_episodes**
   - GIVEN: Date range
   - WHEN: Calling get_calendar(start, end)
   - THEN: Returns episodes airing in range

2. **test_get_calendar_defaults_to_today**
   - GIVEN: No date parameters
   - WHEN: Calling get_calendar()
   - THEN: Returns today's upcoming episodes

3. **test_get_queue_returns_download_queue**
   - GIVEN: Active downloads
   - WHEN: Calling get_queue()
   - THEN: Returns queue with download status

4. **test_get_queue_supports_pagination**
   - GIVEN: page and pageSize params
   - WHEN: Calling get_queue(page=2, pageSize=20)
   - THEN: Includes pagination in request

5. **test_get_wanted_missing_returns_missing_episodes**
   - GIVEN: Missing episodes
   - WHEN: Calling get_wanted_missing()
   - THEN: Returns paginated list of missing episodes

6. **test_get_wanted_missing_filters_monitored**
   - GIVEN: includeMonitored=False
   - WHEN: Calling get_wanted_missing()
   - THEN: Returns only monitored missing episodes

### 2.6 Error Handling Tests

**Test Specifications:**

1. **test_handles_401_unauthorized**
   - GIVEN: Invalid API key
   - WHEN: Making any request
   - THEN: Raises SonarrClientError with auth message

2. **test_handles_404_not_found**
   - GIVEN: Non-existent resource
   - WHEN: GET request
   - THEN: Raises SonarrClientError with 404

3. **test_handles_500_server_error**
   - GIVEN: Server error
   - WHEN: Any request
   - THEN: Raises SonarrClientError

4. **test_handles_connection_timeout**
   - GIVEN: Network timeout
   - WHEN: Any request
   - THEN: Raises SonarrConnectionError

5. **test_handles_invalid_json_response**
   - GIVEN: Non-JSON response
   - WHEN: Parsing response
   - THEN: Raises SonarrClientError

6. **test_retries_on_transient_errors**
   - GIVEN: Transient 503 error
   - WHEN: Making request
   - THEN: Retries up to max_retries

7. **test_respects_max_retries**
   - GIVEN: Persistent errors
   - WHEN: Making request
   - THEN: Stops after max_retries attempts

### 2.7 Authentication Tests

**Test Specifications:**

1. **test_includes_api_key_in_headers**
   - GIVEN: Any request
   - WHEN: Making API call
   - THEN: Includes X-Api-Key header

2. **test_api_key_not_in_url**
   - GIVEN: Any request
   - WHEN: Making API call
   - THEN: API key NOT in query params

3. **test_builds_correct_api_url**
   - GIVEN: Endpoint path
   - WHEN: Building request URL
   - THEN: Constructs /api/v3/{endpoint}

## 3. Unit Tests: Sonarr MCP Server

### 3.1 Server Initialization Tests

**Test Specifications:**

1. **test_server_registers_all_tools**
   - GIVEN: Server initialization
   - WHEN: Server starts
   - THEN: All 10 tools are registered

2. **test_server_requires_configuration**
   - GIVEN: Missing config
   - WHEN: Creating server
   - THEN: Raises appropriate error

3. **test_server_validates_sonarr_url**
   - GIVEN: Invalid Sonarr URL
   - WHEN: Creating server
   - THEN: Raises validation error

### 3.2 Tool Execution Tests

**Test Specifications:**

1. **test_get_series_tool_execution**
   - GIVEN: get_series tool call
   - WHEN: Tool is executed
   - THEN: Calls client.get_series() and formats response

2. **test_get_series_by_id_tool_execution**
   - GIVEN: get_series_by_id with ID argument
   - WHEN: Tool is executed
   - THEN: Calls client.get_series_by_id(id)

3. **test_add_series_tool_execution**
   - GIVEN: add_series with required params
   - WHEN: Tool is executed
   - THEN: Calls client.add_series() with correct data

4. **test_search_series_tool_execution**
   - GIVEN: search_series with term
   - WHEN: Tool is executed
   - THEN: Calls client.search_series(term)

5. **test_get_episodes_tool_execution**
   - GIVEN: get_episodes with series_id
   - WHEN: Tool is executed
   - THEN: Calls client.get_episodes(series_id)

6. **test_search_episode_tool_execution**
   - GIVEN: search_episode with episode_id
   - WHEN: Tool is executed
   - THEN: Calls client.search_episode(episode_id)

7. **test_get_wanted_tool_execution**
   - GIVEN: get_wanted tool call
   - WHEN: Tool is executed
   - THEN: Calls client.get_wanted_missing()

8. **test_get_calendar_tool_execution**
   - GIVEN: get_calendar with date range
   - WHEN: Tool is executed
   - THEN: Calls client.get_calendar()

9. **test_get_queue_tool_execution**
   - GIVEN: get_queue tool call
   - WHEN: Tool is executed
   - THEN: Calls client.get_queue()

10. **test_delete_series_tool_execution**
    - GIVEN: delete_series with ID and flags
    - WHEN: Tool is executed
    - THEN: Calls client.delete_series()

### 3.3 Tool Schema Validation Tests

**Test Specifications:**

1. **test_tool_schemas_are_valid_json_schema**
   - GIVEN: All tool definitions
   - WHEN: Validating schemas
   - THEN: All conform to JSON Schema spec

2. **test_required_parameters_are_enforced**
   - GIVEN: Tool call missing required param
   - WHEN: Validating input
   - THEN: Raises validation error

3. **test_optional_parameters_have_defaults**
   - GIVEN: Tool call without optional params
   - WHEN: Executing tool
   - THEN: Uses default values

## 4. Integration Tests

### 4.1 API Integration Tests

**Test Specifications:**

1. **test_full_series_workflow**
   - Search for series → Add series → Get series → Delete series

2. **test_episode_search_workflow**
   - Get series → Get episodes → Search for missing episode

3. **test_queue_monitoring_workflow**
   - Trigger search → Monitor queue → Verify completion

### 4.2 MCP Protocol Integration Tests

**Test Specifications:**

1. **test_mcp_tool_list_request**
   - Verify all tools are listed in capability response

2. **test_mcp_tool_execution_flow**
   - Send tool execution request → Receive formatted response

3. **test_mcp_error_handling**
   - Invalid tool call → Proper error response

## 5. Test Data Factories Implementation

All factories will be in `tests/fixtures/conftest.py`:

### Series Factory
```python
@pytest.fixture
def sonarr_series_factory():
    def _create(
        series_id: int = 1,
        title: str = "Test Series",
        tvdb_id: int = 12345,
        status: str = "continuing",
        monitored: bool = True,
        season_count: int = 3
    ):
        # Returns complete series object
```

### Episode Factory
```python
@pytest.fixture
def sonarr_episode_factory():
    def _create(
        episode_id: int = 1,
        series_id: int = 1,
        season_number: int = 1,
        episode_number: int = 1,
        has_file: bool = False
    ):
        # Returns complete episode object
```

## 6. Mutation Testing Strategy

After achieving 90%+ coverage, implement mutation testing:

1. **Use pytest-mutagen or mutmut**
2. **Target critical paths**: Series operations, episode search
3. **Goal**: 80%+ mutation score
4. **Focus areas**:
   - Error handling logic
   - API parameter validation
   - Response parsing

## 7. Mock Strategies

### HTTP Mocking
- Use `pytest-httpx` HTTPXMock for all HTTP requests
- Mock at transport layer, not client method level
- Verify request headers include X-Api-Key

### Sonarr API Mocking
- Create realistic response fixtures
- Include error scenarios (404, 401, 500)
- Test pagination, filtering, sorting

### MCP Protocol Mocking
- Mock MCP transport layer
- Test tool registration
- Test message format compliance

## 8. CI/CD Integration

### Pre-commit Hooks
- Run unit tests (fast feedback)
- Check coverage threshold (90%+)

### CI Pipeline
- Run full test suite
- Generate coverage reports
- Run mutation tests on critical paths
- Fail build if coverage drops below 90%

## 9. Test Execution Plan

### Phase 1: TDD Red Phase (This Deliverable)
1. Write all test specifications
2. Implement test data factories
3. Write all failing unit tests
4. Write all failing integration tests

### Phase 2: TDD Green Phase (Next Step)
1. Implement SonarrClient to pass tests
2. Implement Sonarr MCP Server to pass tests
3. Verify all tests pass

### Phase 3: TDD Refactor Phase
1. Refactor for clarity and performance
2. Ensure tests still pass
3. Add mutation testing
4. Document edge cases

## 10. Success Criteria

- [ ] All test files created and fail appropriately
- [ ] 90%+ coverage target defined in pytest config
- [ ] Test data factories cover all API responses
- [ ] Unit tests cover all public methods
- [ ] Integration tests cover critical workflows
- [ ] Error handling tests cover all failure modes
- [ ] MCP protocol compliance tests in place
- [ ] Authentication tests verify API key handling
- [ ] All tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Test names clearly describe expected behavior

## 11. Special Considerations for Sonarr

### API Key Authentication
- Unlike SABnzbd (query param), Sonarr uses header-based auth
- Must verify X-Api-Key header in all requests
- Test that API key is NOT leaked in logs/URLs

### API v3 Specifics
- All endpoints use /api/v3/ prefix
- Command execution is async (returns command ID)
- Need to test command status polling

### Search Operations
- Series search uses lookup API (TVDB integration)
- Episode search triggers download queue
- Test both immediate results and async tracking

### Monitoring and Quality Profiles
- Complex nested objects in API responses
- Test parsing of quality profile structures
- Test season-level monitoring settings

## 12. Next Steps After Test Creation

1. Run tests to verify they all fail (red phase)
2. Implement SonarrClient class
3. Implement Sonarr MCP Server
4. Achieve green phase (all tests pass)
5. Refactor for quality
6. Add mutation testing
7. Document any edge cases discovered
