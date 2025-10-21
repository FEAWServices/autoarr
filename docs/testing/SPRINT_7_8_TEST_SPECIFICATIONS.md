# Sprint 7-8 Test Specifications

**Test-Driven Development (TDD) Specifications for Content Request Handler and WebSocket Manager**

**Author**: Test Architecture Team
**Date**: 2025-10-18
**Sprint Coverage**: Sprint 7 (Content Request Handler) & Sprint 8 (WebSocket Manager)
**Target Coverage**: 85%+ with comprehensive edge case coverage

---

## Table of Contents

1. [Sprint 7: Content Request Handler](#sprint-7-content-request-handler)
   - [RequestHandler Service Tests](#requesthandler-service-tests)
   - [API Endpoint Tests](#api-endpoint-tests)
   - [Database Model Tests](#database-model-tests)
2. [Sprint 8: WebSocket Manager](#sprint-8-websocket-manager)
   - [WebSocketManager Service Tests](#websocketmanager-service-tests)
   - [WebSocket Endpoint Tests](#websocket-endpoint-tests)
   - [Integration Tests](#integration-tests)
3. [Test Data Factories](#test-data-factories)
4. [Mock Strategies](#mock-strategies)
5. [Implementation Checklist](#implementation-checklist)

---

## Sprint 7: Content Request Handler

### RequestHandler Service Tests

**File**: `/app/autoarr/tests/unit/services/test_request_handler.py`

#### Test Class: TestRequestHandler

##### 1. Initialization Tests

```python
@pytest.mark.asyncio
async def test_request_handler_initialization(self) -> None:
    """Test that RequestHandler initializes with correct dependencies."""
    # GIVEN: Valid configuration and dependencies
    # WHEN: RequestHandler is instantiated
    # THEN: All dependencies are properly initialized
    # - LLM agent is available
    # - TMDB client is configured
    # - Orchestrator is available
    # - Database session is active
```

##### 2. Natural Language Parsing Tests

```python
@pytest.mark.asyncio
async def test_parse_simple_movie_request(self) -> None:
    """Test parsing simple movie request: 'Add Inception'."""
    # GIVEN: User input "Add Inception"
    # WHEN: parse_request() is called
    # THEN: Returns ParsedRequest with:
    # - media_type: "movie" (inferred)
    # - title: "Inception"
    # - year: None
    # - quality: None (default will be used)
    # - confidence: high

@pytest.mark.asyncio
async def test_parse_movie_with_year(self) -> None:
    """Test parsing movie with year: 'Add The Matrix 1999'."""
    # GIVEN: User input "Add The Matrix 1999"
    # WHEN: parse_request() is called
    # THEN: Returns ParsedRequest with:
    # - title: "The Matrix"
    # - year: 1999
    # - media_type: "movie"

@pytest.mark.asyncio
async def test_parse_movie_with_quality(self) -> None:
    """Test parsing movie with quality: 'Add Inception in 4K'."""
    # GIVEN: User input "Add Inception in 4K"
    # WHEN: parse_request() is called
    # THEN: Returns ParsedRequest with:
    # - title: "Inception"
    # - quality: "4K" or "2160p"
    # - quality_profile_override: True

@pytest.mark.asyncio
async def test_parse_tv_show_request(self) -> None:
    """Test parsing TV show request: 'Add Breaking Bad TV show'."""
    # GIVEN: User input "Add Breaking Bad TV show"
    # WHEN: parse_request() is called
    # THEN: Returns ParsedRequest with:
    # - media_type: "tv"
    # - title: "Breaking Bad"

@pytest.mark.asyncio
async def test_parse_ambiguous_request_uses_llm(self) -> None:
    """Test that ambiguous requests use LLM for classification."""
    # GIVEN: User input "Add Fargo" (both movie and TV show)
    # WHEN: parse_request() is called
    # THEN: LLM is consulted for disambiguation
    # - LLM receives context about title
    # - Returns most likely media type
    # - Includes both options in search results

@pytest.mark.asyncio
async def test_parse_request_with_special_characters(self) -> None:
    """Test parsing request with special characters."""
    # GIVEN: User input "Add Spider-Man: No Way Home"
    # WHEN: parse_request() is called
    # THEN: Special characters are preserved
    # - title: "Spider-Man: No Way Home"
    # - Search query properly escaped

@pytest.mark.asyncio
async def test_parse_empty_request_raises_error(self) -> None:
    """Test that empty request raises ValidationError."""
    # GIVEN: Empty user input ""
    # WHEN: parse_request() is called
    # THEN: Raises ValueError with message "Request cannot be empty"

@pytest.mark.asyncio
async def test_parse_request_extracts_season_info(self) -> None:
    """Test parsing TV show with season info."""
    # GIVEN: User input "Add Breaking Bad season 3"
    # WHEN: parse_request() is called
    # THEN: Returns ParsedRequest with:
    # - media_type: "tv"
    # - title: "Breaking Bad"
    # - season: 3
    # - monitor_specific_season: True
```

##### 3. Movie vs TV Classification Tests

```python
@pytest.mark.asyncio
async def test_classify_known_movie(self) -> None:
    """Test classification of known movie title."""
    # GIVEN: Title "Inception" with TMDB results
    # WHEN: classify_media_type() is called
    # THEN: Returns "movie" with high confidence

@pytest.mark.asyncio
async def test_classify_known_tv_show(self) -> None:
    """Test classification of known TV show."""
    # GIVEN: Title "Breaking Bad"
    # WHEN: classify_media_type() is called
    # THEN: Returns "tv" with high confidence

@pytest.mark.asyncio
async def test_classify_uses_llm_for_ambiguous(self) -> None:
    """Test LLM is used for ambiguous titles."""
    # GIVEN: Title "Fargo" (exists as both movie and show)
    # WHEN: classify_media_type() is called
    # THEN: LLM is called with:
    # - Title and TMDB results
    # - Context about both options
    # - Returns classification with reasoning

@pytest.mark.asyncio
async def test_classify_handles_llm_failure(self) -> None:
    """Test fallback when LLM classification fails."""
    # GIVEN: LLM API error
    # WHEN: classify_media_type() is called
    # THEN: Falls back to heuristic classification
    # - Prefers movie if both available
    # - Logs warning about LLM failure

@pytest.mark.asyncio
async def test_classify_respects_explicit_type(self) -> None:
    """Test that explicit media type is respected."""
    # GIVEN: User input "Add Fargo movie" (explicit)
    # WHEN: classify_media_type() is called
    # THEN: Returns "movie" without LLM consultation
    # - No TMDB search needed
    # - High confidence

@pytest.mark.asyncio
async def test_classify_caches_results(self) -> None:
    """Test that classification results are cached."""
    # GIVEN: Title classified once
    # WHEN: Same title classified again
    # THEN: Uses cached result
    # - No duplicate LLM calls
    # - No duplicate TMDB calls
```

##### 4. Metadata Extraction Tests

```python
@pytest.mark.asyncio
async def test_extract_year_from_parentheses(self) -> None:
    """Test year extraction from parentheses."""
    # GIVEN: User input "The Matrix (1999)"
    # WHEN: extract_metadata() is called
    # THEN: Returns year: 1999

@pytest.mark.asyncio
async def test_extract_quality_keywords(self) -> None:
    """Test quality keyword extraction."""
    # GIVEN: Various quality inputs
    # WHEN: extract_metadata() is called
    # THEN: Maps to correct quality profiles:
    # - "4K" -> "Ultra-HD" or "2160p"
    # - "1080p" -> "HD-1080p"
    # - "720p" -> "HD-720p"
    # - "BluRay" -> "Bluray-1080p"

@pytest.mark.asyncio
async def test_extract_handles_multiple_years(self) -> None:
    """Test extraction when multiple years present."""
    # GIVEN: "2001: A Space Odyssey (1968)"
    # WHEN: extract_metadata() is called
    # THEN: Correctly identifies 1968 as release year

@pytest.mark.asyncio
async def test_extract_season_and_episode(self) -> None:
    """Test season/episode extraction for TV shows."""
    # GIVEN: "Breaking Bad S03E13"
    # WHEN: extract_metadata() is called
    # THEN: Returns season: 3, episode: 13
```

##### 5. Search Integration Tests

```python
@pytest.mark.asyncio
async def test_search_movie_on_tmdb(self) -> None:
    """Test searching for movie on TMDB."""
    # GIVEN: Movie title "Inception"
    # WHEN: search_media() is called
    # THEN: TMDB API is called with correct params
    # - Returns list of SearchResult objects
    # - Results include TMDB ID, title, year, overview

@pytest.mark.asyncio
async def test_search_tv_on_tmdb(self) -> None:
    """Test searching for TV show on TMDB."""
    # GIVEN: TV show title "Breaking Bad"
    # WHEN: search_media() is called
    # THEN: TMDB API returns TV results
    # - Includes TVDB ID mapping
    # - Contains season count

@pytest.mark.asyncio
async def test_search_movie_on_radarr(self) -> None:
    """Test searching for movie on Radarr."""
    # GIVEN: Movie title from TMDB
    # WHEN: search_on_radarr() is called
    # THEN: Radarr MCP tool is called
    # - Uses TMDB ID for accurate matching
    # - Returns availability status

@pytest.mark.asyncio
async def test_search_tv_on_sonarr(self) -> None:
    """Test searching for TV show on Sonarr."""
    # GIVEN: TV show title from TMDB
    # WHEN: search_on_sonarr() is called
    # THEN: Sonarr MCP tool is called
    # - Uses TVDB ID
    # - Returns series info

@pytest.mark.asyncio
async def test_search_handles_no_results(self) -> None:
    """Test handling when no results found."""
    # GIVEN: Non-existent title "XYZ123NonExistent"
    # WHEN: search_media() is called
    # THEN: Returns empty results list
    # - No error raised
    # - Logs warning about no results

@pytest.mark.asyncio
async def test_search_handles_tmdb_rate_limit(self) -> None:
    """Test handling TMDB rate limiting."""
    # GIVEN: TMDB returns 429 rate limit
    # WHEN: search_media() is called
    # THEN: Implements retry with exponential backoff
    # - Max 3 retries
    # - Returns partial results or error

@pytest.mark.asyncio
async def test_search_combines_results_from_multiple_sources(self) -> None:
    """Test combining results from TMDB, Radarr, Sonarr."""
    # GIVEN: Movie exists in TMDB and Radarr
    # WHEN: search_media() is called
    # THEN: Results are merged with:
    # - TMDB metadata (title, year, overview)
    # - Radarr availability (already added, monitored)
    # - Quality profile recommendations
```

##### 6. Disambiguation Tests

```python
@pytest.mark.asyncio
async def test_handle_multiple_matches(self) -> None:
    """Test handling multiple search matches."""
    # GIVEN: Search returns 5+ results
    # WHEN: handle_disambiguation() is called
    # THEN: Returns top 5 matches with:
    # - Relevance scores
    # - Distinguishing info (year, type)
    # - User prompt for selection

@pytest.mark.asyncio
async def test_disambiguate_by_year(self) -> None:
    """Test disambiguation using year."""
    # GIVEN: Multiple "Batman" movies
    # WHEN: User specifies year in follow-up
    # THEN: Selects correct match by year

@pytest.mark.asyncio
async def test_disambiguate_by_type(self) -> None:
    """Test disambiguation by media type."""
    # GIVEN: "Fargo" has both movie and TV results
    # WHEN: User clarifies "the TV show"
    # THEN: Filters to TV results only

@pytest.mark.asyncio
async def test_auto_select_single_match(self) -> None:
    """Test auto-selection when only one match."""
    # GIVEN: Search returns single result
    # WHEN: handle_disambiguation() is called
    # THEN: Auto-selects without user prompt
    # - Confidence: high
    # - Proceeds to next step
```

##### 7. Request Tracking Tests

```python
@pytest.mark.asyncio
async def test_create_content_request_record(self) -> None:
    """Test creating ContentRequest database record."""
    # GIVEN: Parsed and searched request
    # WHEN: create_request() is called
    # THEN: Database record created with:
    # - user_input (original text)
    # - media_type
    # - title, year
    # - status: "pending"
    # - search_results (JSON)
    # - created_at timestamp

@pytest.mark.asyncio
async def test_update_request_status(self) -> None:
    """Test updating request status."""
    # GIVEN: Existing request with status "pending"
    # WHEN: update_status("processing") is called
    # THEN: Status updated in database
    # - updated_at timestamp updated
    # - Status history tracked

@pytest.mark.asyncio
async def test_track_request_progress(self) -> None:
    """Test tracking request through lifecycle."""
    # GIVEN: New request
    # WHEN: Request progresses through states
    # THEN: Each state change tracked:
    # - pending -> searching -> found -> adding -> completed
    # - Timestamps for each transition
    # - Events emitted for WebSocket

@pytest.mark.asyncio
async def test_handle_request_failure(self) -> None:
    """Test handling request failures."""
    # GIVEN: Request that fails to add
    # WHEN: Error occurs during processing
    # THEN: Request marked as "failed"
    # - Error message stored
    # - Retry available
    # - User notified

@pytest.mark.asyncio
async def test_cancel_pending_request(self) -> None:
    """Test canceling a pending request."""
    # GIVEN: Request in "pending" or "searching" state
    # WHEN: cancel_request() is called
    # THEN: Request status set to "cancelled"
    # - Processing stopped
    # - Resources cleaned up
```

##### 8. Integration with Sonarr/Radarr Tests

```python
@pytest.mark.asyncio
async def test_add_movie_to_radarr(self) -> None:
    """Test adding movie to Radarr."""
    # GIVEN: Valid movie search result
    # WHEN: add_to_service() is called
    # THEN: Radarr MCP tool invoked with:
    # - TMDB ID
    # - Quality profile
    # - Root folder path
    # - Monitor settings

@pytest.mark.asyncio
async def test_add_tv_to_sonarr(self) -> None:
    """Test adding TV show to Sonarr."""
    # GIVEN: Valid TV show search result
    # WHEN: add_to_service() is called
    # THEN: Sonarr MCP tool invoked with:
    # - TVDB ID
    # - Quality profile
    # - Season monitoring options

@pytest.mark.asyncio
async def test_handle_already_exists(self) -> None:
    """Test handling media already in library."""
    # GIVEN: Movie already in Radarr
    # WHEN: add_to_service() is called
    # THEN: Returns "already_exists" status
    # - No duplicate added
    # - User notified
    # - Option to search for media

@pytest.mark.asyncio
async def test_trigger_search_after_add(self) -> None:
    """Test triggering search after adding media."""
    # GIVEN: Media successfully added
    # WHEN: add_to_service() completes
    # THEN: Search triggered via MCP
    # - Movie search or Series search
    # - Search status tracked
```

##### 9. Error Handling Tests

```python
@pytest.mark.asyncio
async def test_handle_llm_api_error(self) -> None:
    """Test handling LLM API errors."""
    # GIVEN: Claude API returns error
    # WHEN: parse_request() is called
    # THEN: Falls back to rule-based parsing
    # - Error logged
    # - Request still processed

@pytest.mark.asyncio
async def test_handle_tmdb_connection_error(self) -> None:
    """Test handling TMDB connection errors."""
    # GIVEN: TMDB API unreachable
    # WHEN: search_media() is called
    # THEN: Returns error response
    # - User-friendly error message
    # - Retry option provided

@pytest.mark.asyncio
async def test_handle_mcp_orchestrator_error(self) -> None:
    """Test handling MCP orchestrator errors."""
    # GIVEN: MCP service unavailable
    # WHEN: add_to_service() is called
    # THEN: Request marked as "failed"
    # - Error details captured
    # - Auto-retry scheduled

@pytest.mark.asyncio
async def test_handle_database_error(self) -> None:
    """Test handling database errors."""
    # GIVEN: Database connection lost
    # WHEN: create_request() is called
    # THEN: Raises DatabaseError
    # - Request not lost
    # - Retry mechanism triggered
```

##### 10. Performance Tests

```python
@pytest.mark.asyncio
async def test_parse_request_performance(self) -> None:
    """Test request parsing performance."""
    # GIVEN: Simple movie request
    # WHEN: parse_request() is called
    # THEN: Completes in < 100ms (without LLM)
    # - Rule-based parsing is fast
    # - LLM calls batched if needed

@pytest.mark.asyncio
async def test_search_caching(self) -> None:
    """Test search result caching."""
    # GIVEN: Same title searched twice
    # WHEN: search_media() called second time
    # THEN: Uses cached results
    # - No duplicate API calls
    # - Cache TTL: 1 hour

@pytest.mark.asyncio
async def test_concurrent_requests(self) -> None:
    """Test handling concurrent requests."""
    # GIVEN: 10 simultaneous requests
    # WHEN: All processed concurrently
    # THEN: All complete successfully
    # - No race conditions
    # - Database transactions isolated
    # - Rate limits respected
```

---

### API Endpoint Tests

**File**: `/app/autoarr/tests/unit/api/test_request_endpoints.py`

#### Test Class: TestRequestEndpoints

##### 1. POST /api/v1/requests - Create Request

```python
@pytest.mark.asyncio
async def test_create_request_success(self, client, mock_orchestrator):
    """Test creating a new content request."""
    # GIVEN: Valid request payload
    # WHEN: POST /api/v1/requests
    # THEN: Returns 201 with request ID
    # - Request created in database
    # - Status: "pending"
    # - Processing started in background

@pytest.mark.asyncio
async def test_create_request_with_explicit_type(self, client):
    """Test creating request with explicit media type."""
    # GIVEN: Payload with media_type specified
    # WHEN: POST /api/v1/requests
    # THEN: Uses specified type
    # - No LLM classification needed

@pytest.mark.asyncio
async def test_create_request_validation_error(self, client):
    """Test validation error on invalid request."""
    # GIVEN: Empty user_input
    # WHEN: POST /api/v1/requests
    # THEN: Returns 422 Unprocessable Entity
    # - Error details included

@pytest.mark.asyncio
async def test_create_request_triggers_processing(self, client):
    """Test request processing triggered."""
    # GIVEN: Valid request
    # WHEN: POST /api/v1/requests
    # THEN: Background task started
    # - WebSocket event emitted
    # - Status updates sent via WS

@pytest.mark.asyncio
async def test_create_request_rate_limiting(self, client):
    """Test rate limiting on request creation."""
    # GIVEN: Multiple rapid requests
    # WHEN: POST /api/v1/requests (11th time in 1 minute)
    # THEN: Returns 429 Too Many Requests
    # - Rate limit: 10 requests/minute
```

##### 2. GET /api/v1/requests - List Requests

```python
@pytest.mark.asyncio
async def test_list_requests_success(self, client, db_session):
    """Test listing all content requests."""
    # GIVEN: 5 requests in database
    # WHEN: GET /api/v1/requests
    # THEN: Returns 200 with list
    # - All 5 requests included
    # - Sorted by created_at (desc)

@pytest.mark.asyncio
async def test_list_requests_pagination(self, client, db_session):
    """Test pagination of request list."""
    # GIVEN: 25 requests in database
    # WHEN: GET /api/v1/requests?limit=10&offset=0
    # THEN: Returns first 10 requests
    # - Total count included
    # - Next page link

@pytest.mark.asyncio
async def test_list_requests_filter_by_status(self, client, db_session):
    """Test filtering requests by status."""
    # GIVEN: Requests with various statuses
    # WHEN: GET /api/v1/requests?status=pending
    # THEN: Returns only pending requests

@pytest.mark.asyncio
async def test_list_requests_filter_by_type(self, client, db_session):
    """Test filtering by media type."""
    # GIVEN: Mix of movie and TV requests
    # WHEN: GET /api/v1/requests?media_type=movie
    # THEN: Returns only movie requests

@pytest.mark.asyncio
async def test_list_requests_empty(self, client, db_session):
    """Test listing when no requests exist."""
    # GIVEN: Empty database
    # WHEN: GET /api/v1/requests
    # THEN: Returns 200 with empty list
    # - Total: 0
```

##### 3. GET /api/v1/requests/{id} - Get Request Details

```python
@pytest.mark.asyncio
async def test_get_request_success(self, client, db_session):
    """Test getting request details."""
    # GIVEN: Request with ID 123
    # WHEN: GET /api/v1/requests/123
    # THEN: Returns 200 with full details
    # - All fields included
    # - Search results expanded

@pytest.mark.asyncio
async def test_get_request_not_found(self, client, db_session):
    """Test getting non-existent request."""
    # GIVEN: No request with ID 999
    # WHEN: GET /api/v1/requests/999
    # THEN: Returns 404 Not Found
    # - Error message descriptive

@pytest.mark.asyncio
async def test_get_request_includes_history(self, client, db_session):
    """Test request includes status history."""
    # GIVEN: Request with multiple status changes
    # WHEN: GET /api/v1/requests/123
    # THEN: Returns status_history array
    # - Each transition timestamped
    # - Ordered chronologically
```

##### 4. PUT /api/v1/requests/{id} - Update Request

```python
@pytest.mark.asyncio
async def test_update_request_status(self, client, db_session):
    """Test updating request status."""
    # GIVEN: Request in "pending" state
    # WHEN: PUT /api/v1/requests/123 with status="completed"
    # THEN: Returns 200 with updated request
    # - Status changed to "completed"
    # - updated_at timestamp updated

@pytest.mark.asyncio
async def test_update_request_invalid_status(self, client, db_session):
    """Test updating with invalid status."""
    # GIVEN: Valid request
    # WHEN: PUT with status="invalid_status"
    # THEN: Returns 422 Validation Error
    # - Allowed statuses listed

@pytest.mark.asyncio
async def test_update_request_selected_result(self, client, db_session):
    """Test updating selected search result."""
    # GIVEN: Request with multiple search results
    # WHEN: PUT with selected_result_id
    # THEN: Request updated
    # - Processing continues with selection

@pytest.mark.asyncio
async def test_update_request_not_found(self, client, db_session):
    """Test updating non-existent request."""
    # GIVEN: No request with ID 999
    # WHEN: PUT /api/v1/requests/999
    # THEN: Returns 404 Not Found
```

##### 5. DELETE /api/v1/requests/{id} - Cancel Request

```python
@pytest.mark.asyncio
async def test_cancel_request_success(self, client, db_session):
    """Test canceling a pending request."""
    # GIVEN: Request in "pending" state
    # WHEN: DELETE /api/v1/requests/123
    # THEN: Returns 200
    # - Status changed to "cancelled"
    # - Processing stopped

@pytest.mark.asyncio
async def test_cancel_completed_request_fails(self, client, db_session):
    """Test cannot cancel completed request."""
    # GIVEN: Request in "completed" state
    # WHEN: DELETE /api/v1/requests/123
    # THEN: Returns 400 Bad Request
    # - Error: Cannot cancel completed request

@pytest.mark.asyncio
async def test_cancel_request_not_found(self, client, db_session):
    """Test canceling non-existent request."""
    # GIVEN: No request with ID 999
    # WHEN: DELETE /api/v1/requests/999
    # THEN: Returns 404 Not Found
```

---

### Database Model Tests

**File**: `/app/autoarr/tests/unit/api/test_content_request_model.py`

#### Test Class: TestContentRequestModel

```python
def test_create_content_request(self, db_session):
    """Test creating ContentRequest model."""
    # GIVEN: Valid request data
    # WHEN: ContentRequest created
    # THEN: All fields set correctly
    # - ID auto-generated
    # - Timestamps set
    # - Status defaults to "pending"

def test_content_request_relationships(self, db_session):
    """Test model relationships."""
    # GIVEN: ContentRequest with search results
    # WHEN: Accessing search_results field
    # THEN: JSON properly serialized/deserialized

def test_content_request_status_enum(self, db_session):
    """Test status field validation."""
    # GIVEN: Invalid status value
    # WHEN: Setting status
    # THEN: Raises ValidationError
    # - Allowed: pending, searching, found, adding, completed, failed, cancelled

def test_content_request_repr(self, db_session):
    """Test string representation."""
    # GIVEN: ContentRequest instance
    # WHEN: str(request) or repr(request)
    # THEN: Returns readable string with ID and title
```

---

## Sprint 8: WebSocket Manager

### WebSocketManager Service Tests

**File**: `/app/autoarr/tests/unit/services/test_websocket_manager.py`

#### Test Class: TestWebSocketManager

##### 1. Initialization Tests

```python
@pytest.mark.asyncio
async def test_websocket_manager_initialization(self):
    """Test WebSocketManager initialization."""
    # GIVEN: WebSocketManager instantiated
    # WHEN: Manager created
    # THEN: Connection tracking initialized
    # - Empty connections dict
    # - Event subscriptions empty

@pytest.mark.asyncio
async def test_manager_singleton_pattern(self):
    """Test manager uses singleton pattern."""
    # GIVEN: Multiple get_manager() calls
    # WHEN: Retrieving manager instance
    # THEN: Same instance returned
    # - Shared state across application
```

##### 2. Connection Management Tests

```python
@pytest.mark.asyncio
async def test_connect_client(self, ws_manager, mock_websocket):
    """Test connecting a new client."""
    # GIVEN: New WebSocket connection
    # WHEN: connect() is called
    # THEN: Client added to connections
    # - Connection ID generated
    # - Welcome message sent
    # - Connection count incremented

@pytest.mark.asyncio
async def test_disconnect_client(self, ws_manager, mock_websocket):
    """Test disconnecting a client."""
    # GIVEN: Connected client
    # WHEN: disconnect() is called
    # THEN: Client removed from connections
    # - Connection ID removed
    # - Connection count decremented
    # - Cleanup performed

@pytest.mark.asyncio
async def test_handle_multiple_connections(self, ws_manager):
    """Test managing multiple simultaneous connections."""
    # GIVEN: 10 WebSocket connections
    # WHEN: All connect concurrently
    # THEN: All tracked correctly
    # - Unique IDs assigned
    # - No collisions

@pytest.mark.asyncio
async def test_connection_state_tracking(self, ws_manager, mock_websocket):
    """Test tracking connection state."""
    # GIVEN: Connected client
    # WHEN: Checking connection state
    # THEN: State is "connected"
    # - Last activity timestamp updated
    # - Ping/pong handled
```

##### 3. Event Broadcasting Tests

```python
@pytest.mark.asyncio
async def test_broadcast_to_all_clients(self, ws_manager, mock_websockets):
    """Test broadcasting event to all clients."""
    # GIVEN: 5 connected clients
    # WHEN: broadcast() is called
    # THEN: All clients receive event
    # - Message sent to all connections
    # - Failed sends handled gracefully

@pytest.mark.asyncio
async def test_broadcast_to_specific_client(self, ws_manager, mock_websocket):
    """Test sending event to specific client."""
    # GIVEN: Client with connection_id "abc123"
    # WHEN: send_to_client("abc123", event) is called
    # THEN: Only that client receives event
    # - Other clients not affected

@pytest.mark.asyncio
async def test_broadcast_handles_disconnected_client(self, ws_manager):
    """Test broadcasting when client disconnected during send."""
    # GIVEN: Client disconnects mid-broadcast
    # WHEN: broadcast() is called
    # THEN: Disconnected client removed from connections
    # - Other clients still receive message
    # - No error raised

@pytest.mark.asyncio
async def test_broadcast_event_serialization(self, ws_manager, mock_websocket):
    """Test event properly serialized to JSON."""
    # GIVEN: Event with complex data
    # WHEN: broadcast() is called
    # THEN: Event serialized to JSON
    # - Timestamps converted to ISO format
    # - Nested objects handled
```

##### 4. Subscription Management Tests

```python
@pytest.mark.asyncio
async def test_subscribe_to_event_type(self, ws_manager, mock_websocket):
    """Test subscribing to specific event type."""
    # GIVEN: Client wants only "request.status" events
    # WHEN: subscribe("request.status") is called
    # THEN: Client subscription recorded
    # - Only subscribed events sent

@pytest.mark.asyncio
async def test_unsubscribe_from_event_type(self, ws_manager, mock_websocket):
    """Test unsubscribing from event type."""
    # GIVEN: Client subscribed to "request.status"
    # WHEN: unsubscribe("request.status") is called
    # THEN: Subscription removed
    # - Events no longer sent

@pytest.mark.asyncio
async def test_filter_events_by_subscription(self, ws_manager, mock_websocket):
    """Test event filtering based on subscriptions."""
    # GIVEN: Client subscribed to "request.*" only
    # WHEN: Various events broadcasted
    # THEN: Only request events sent to client
    # - "download.progress" not sent
    # - "request.status" sent

@pytest.mark.asyncio
async def test_wildcard_subscription(self, ws_manager, mock_websocket):
    """Test wildcard subscription (all events)."""
    # GIVEN: Client subscribed to "*"
    # WHEN: Any event broadcasted
    # THEN: All events sent to client
    # - No filtering applied
```

##### 5. Reconnection Handling Tests

```python
@pytest.mark.asyncio
async def test_handle_client_reconnect(self, ws_manager, mock_websocket):
    """Test handling client reconnection."""
    # GIVEN: Client disconnects and reconnects
    # WHEN: New connection established with same client_id
    # THEN: Connection updated
    # - Old connection cleaned up
    # - Subscriptions restored if stored

@pytest.mark.asyncio
async def test_send_missed_events_on_reconnect(self, ws_manager):
    """Test sending missed events after reconnect."""
    # GIVEN: Events occurred while client offline
    # WHEN: Client reconnects
    # THEN: Missed events sent (if buffered)
    # - Event buffer size: 50 events max
    # - Oldest events dropped if buffer full

@pytest.mark.asyncio
async def test_connection_timeout(self, ws_manager, mock_websocket):
    """Test connection timeout handling."""
    # GIVEN: Client inactive for 5 minutes
    # WHEN: Timeout check runs
    # THEN: Inactive connection closed
    # - Cleanup performed
    # - Resources freed
```

##### 6. Error Handling Tests

```python
@pytest.mark.asyncio
async def test_handle_websocket_send_error(self, ws_manager, mock_websocket):
    """Test handling WebSocket send errors."""
    # GIVEN: WebSocket.send() raises error
    # WHEN: broadcast() is called
    # THEN: Error logged
    # - Connection marked for cleanup
    # - Other connections unaffected

@pytest.mark.asyncio
async def test_handle_malformed_message(self, ws_manager, mock_websocket):
    """Test handling malformed incoming message."""
    # GIVEN: Client sends invalid JSON
    # WHEN: Message received
    # THEN: Error response sent to client
    # - Connection not closed
    # - Error logged

@pytest.mark.asyncio
async def test_handle_connection_closed_abruptly(self, ws_manager):
    """Test handling abrupt connection closure."""
    # GIVEN: Connection closed without close frame
    # WHEN: Next operation attempted
    # THEN: Connection removed gracefully
    # - Resources cleaned up
    # - No exceptions propagated
```

##### 7. Performance Tests

```python
@pytest.mark.asyncio
async def test_broadcast_performance(self, ws_manager):
    """Test broadcast performance with many clients."""
    # GIVEN: 100 connected clients
    # WHEN: broadcast() is called
    # THEN: Completes in < 100ms
    # - All clients receive message
    # - Non-blocking

@pytest.mark.asyncio
async def test_connection_tracking_memory(self, ws_manager):
    """Test memory usage with many connections."""
    # GIVEN: 500 connections
    # WHEN: All tracked concurrently
    # THEN: Memory usage reasonable
    # - < 10MB for connection tracking
    # - No memory leaks

@pytest.mark.asyncio
async def test_concurrent_operations(self, ws_manager):
    """Test concurrent connect/disconnect/broadcast."""
    # GIVEN: Simultaneous operations
    # WHEN: Clients connecting/disconnecting while broadcasting
    # THEN: No race conditions
    # - Thread-safe operations
    # - Consistent state
```

---

### WebSocket Endpoint Tests

**File**: `/app/autoarr/tests/integration/test_websocket_integration.py`

#### Test Class: TestWebSocketEndpoint

```python
@pytest.mark.asyncio
async def test_websocket_connect(self, client):
    """Test WebSocket connection establishment."""
    # GIVEN: WebSocket endpoint /api/v1/ws
    # WHEN: Client connects via WebSocket
    # THEN: Connection accepted
    # - Welcome message received
    # - Connection ID provided

@pytest.mark.asyncio
async def test_websocket_receive_events(self, client, event_bus):
    """Test receiving events via WebSocket."""
    # GIVEN: Connected WebSocket client
    # WHEN: Event published to event bus
    # THEN: Client receives event via WebSocket
    # - Event format correct
    # - Timestamp included

@pytest.mark.asyncio
async def test_websocket_subscription(self, client):
    """Test WebSocket event subscription."""
    # GIVEN: Connected client
    # WHEN: Client sends subscribe message
    # THEN: Subscription confirmed
    # - Only subscribed events received

@pytest.mark.asyncio
async def test_websocket_ping_pong(self, client):
    """Test WebSocket ping/pong keepalive."""
    # GIVEN: Connected client
    # WHEN: Server sends ping
    # THEN: Client responds with pong
    # - Connection stays alive

@pytest.mark.asyncio
async def test_websocket_disconnect(self, client):
    """Test WebSocket disconnection."""
    # GIVEN: Connected client
    # WHEN: Client closes connection
    # THEN: Server handles disconnect gracefully
    # - Connection cleaned up
    # - No errors logged

@pytest.mark.asyncio
async def test_websocket_reconnect(self, client):
    """Test WebSocket reconnection."""
    # GIVEN: Previously connected client
    # WHEN: Client reconnects after disconnect
    # THEN: New connection established
    # - Previous connection cleaned up
    # - Subscriptions can be re-established

@pytest.mark.asyncio
async def test_websocket_event_types(self, client, event_bus):
    """Test different event types via WebSocket."""
    # GIVEN: Connected client
    # WHEN: Various events published
    # THEN: All event types received correctly:
    # - request.created
    # - request.status_changed
    # - request.completed
    # - download.progress
    # - system.notification

@pytest.mark.asyncio
async def test_websocket_authentication(self, client):
    """Test WebSocket authentication (if implemented)."""
    # GIVEN: Authentication enabled
    # WHEN: Client connects without auth
    # THEN: Connection rejected (401)
    # OR: Connection accepted with limited access
```

---

## Integration Tests

**File**: `/app/autoarr/tests/integration/test_request_flow_integration.py`

```python
@pytest.mark.asyncio
async def test_complete_request_flow(self, client, db_session, event_bus):
    """Test complete content request flow end-to-end."""
    # GIVEN: User submits "Add Inception in 4K"
    # WHEN: Processing through entire pipeline
    # THEN: Complete flow succeeds:
    # 1. Request created (status: pending)
    # 2. Request parsed (title: "Inception", quality: "4K")
    # 3. TMDB search performed
    # 4. Radarr search performed
    # 5. Movie added to Radarr
    # 6. Search triggered
    # 7. Status updated to completed
    # 8. WebSocket events emitted at each step

@pytest.mark.asyncio
async def test_request_with_disambiguation(self, client, db_session):
    """Test request requiring disambiguation."""
    # GIVEN: User submits "Add Fargo"
    # WHEN: Processing detects ambiguity
    # THEN: Disambiguation flow:
    # 1. Multiple results returned
    # 2. Status: "needs_disambiguation"
    # 3. User selects option
    # 4. Processing continues
    # 5. Completed successfully

@pytest.mark.asyncio
async def test_request_with_websocket_updates(self, client, ws_client, db_session):
    """Test WebSocket updates during request processing."""
    # GIVEN: Connected WebSocket client
    # WHEN: Content request submitted
    # THEN: WebSocket receives real-time updates:
    # - request.created event
    # - request.status_changed (searching)
    # - request.status_changed (found)
    # - request.status_changed (adding)
    # - request.completed event
```

---

## Test Data Factories

**File**: `/app/autoarr/tests/factories.py`

```python
"""
Test data factories for Sprint 7-8.

Provides reusable factory functions for creating test data objects
with sensible defaults and easy customization.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


class ContentRequestFactory:
    """Factory for creating ContentRequest test data."""

    @staticmethod
    def create(
        id: Optional[int] = None,
        user_input: str = "Add Inception",
        media_type: Optional[str] = None,
        title: Optional[str] = "Inception",
        year: Optional[int] = 2010,
        quality: Optional[str] = None,
        status: str = "pending",
        search_results: Optional[List[Dict[str, Any]]] = None,
        selected_result_id: Optional[str] = None,
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create a ContentRequest test object."""
        return {
            "id": id or 1,
            "user_input": user_input,
            "media_type": media_type or "movie",
            "title": title,
            "year": year,
            "quality": quality,
            "status": status,
            "search_results": search_results or [],
            "selected_result_id": selected_result_id,
            "error_message": error_message,
            "created_at": created_at or datetime.now(timezone.utc),
            "updated_at": updated_at or datetime.now(timezone.utc),
        }

    @staticmethod
    def create_batch(count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple ContentRequest objects."""
        return [
            ContentRequestFactory.create(id=i, **kwargs)
            for i in range(1, count + 1)
        ]


class SearchResultFactory:
    """Factory for creating search result test data."""

    @staticmethod
    def create_tmdb_movie_result(
        tmdb_id: int = 27205,
        title: str = "Inception",
        year: int = 2010,
        overview: str = "A skilled thief...",
    ) -> Dict[str, Any]:
        """Create a TMDB movie search result."""
        return {
            "id": tmdb_id,
            "title": title,
            "release_date": f"{year}-07-16",
            "overview": overview,
            "poster_path": "/path/to/poster.jpg",
            "vote_average": 8.8,
            "media_type": "movie",
        }

    @staticmethod
    def create_tmdb_tv_result(
        tmdb_id: int = 1396,
        name: str = "Breaking Bad",
        first_air_date: str = "2008-01-20",
    ) -> Dict[str, Any]:
        """Create a TMDB TV search result."""
        return {
            "id": tmdb_id,
            "name": name,
            "first_air_date": first_air_date,
            "overview": "A chemistry teacher...",
            "poster_path": "/path/to/poster.jpg",
            "vote_average": 9.5,
            "media_type": "tv",
        }

    @staticmethod
    def create_radarr_result(
        tmdb_id: int = 27205,
        title: str = "Inception",
        monitored: bool = False,
        has_file: bool = False,
    ) -> Dict[str, Any]:
        """Create a Radarr search result."""
        return {
            "tmdbId": tmdb_id,
            "title": title,
            "year": 2010,
            "monitored": monitored,
            "hasFile": has_file,
            "status": "released",
        }


class WebSocketEventFactory:
    """Factory for creating WebSocket event test data."""

    @staticmethod
    def create(
        event_type: str = "request.created",
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a WebSocket event."""
        return {
            "type": event_type,
            "data": data or {},
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
        }

    @staticmethod
    def create_request_status_event(
        request_id: int,
        status: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a request status change event."""
        return WebSocketEventFactory.create(
            event_type="request.status_changed",
            data={
                "request_id": request_id,
                "status": status,
                "message": f"Request {status}",
            },
            **kwargs
        )


class MockWebSocketFactory:
    """Factory for creating mock WebSocket connections."""

    @staticmethod
    def create(connection_id: Optional[str] = None):
        """Create a mock WebSocket connection."""
        from unittest.mock import AsyncMock, MagicMock

        ws = AsyncMock()
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        ws.client_state = MagicMock()
        ws.connection_id = connection_id or str(uuid.uuid4())

        return ws


class LLMResponseFactory:
    """Factory for creating mock LLM responses."""

    @staticmethod
    def create_classification_response(
        media_type: str = "movie",
        confidence: float = 0.95,
        reasoning: str = "Based on title...",
    ) -> Dict[str, Any]:
        """Create LLM classification response."""
        return {
            "content": {
                "media_type": media_type,
                "confidence": confidence,
                "reasoning": reasoning,
            },
            "usage": {
                "input_tokens": 150,
                "output_tokens": 50,
            },
        }
```

---

## Mock Strategies

### 1. LLM Service Mocking

```python
# Mock Claude API calls
@pytest.fixture
def mock_llm_agent(mocker):
    """Mock LLM agent for request parsing."""
    mock = mocker.patch("autoarr.api.services.request_handler.LLMAgent")
    mock.classify_media_type = AsyncMock(
        return_value={
            "media_type": "movie",
            "confidence": 0.95,
            "reasoning": "Based on TMDB results",
        }
    )
    return mock
```

### 2. TMDB API Mocking

```python
# Mock TMDB searches
@pytest.fixture
def mock_tmdb_client(httpx_mock):
    """Mock TMDB API responses."""
    httpx_mock.add_response(
        url="https://api.themoviedb.org/3/search/movie",
        json={
            "results": [
                SearchResultFactory.create_tmdb_movie_result()
            ]
        },
    )
    return httpx_mock
```

### 3. MCP Orchestrator Mocking

```python
# Mock MCP calls to Radarr/Sonarr
@pytest.fixture
def mock_mcp_orchestrator(mocker):
    """Mock MCP orchestrator for service integration."""
    mock = mocker.patch("autoarr.api.dependencies.get_orchestrator")
    mock.call_tool = AsyncMock(
        return_value=SearchResultFactory.create_radarr_result()
    )
    return mock
```

### 4. WebSocket Connection Mocking

```python
# Mock WebSocket connections
@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    return MockWebSocketFactory.create()

@pytest.fixture
def mock_websocket_manager(mocker):
    """Mock WebSocket manager."""
    mock = mocker.patch("autoarr.api.services.websocket_manager.WebSocketManager")
    mock.broadcast = AsyncMock()
    mock.send_to_client = AsyncMock()
    return mock
```

### 5. Event Bus Mocking

```python
# Mock event bus for testing event emission
@pytest.fixture
def mock_event_bus(mocker):
    """Mock event bus."""
    mock = mocker.patch("autoarr.api.services.event_bus.EventBus")
    mock.publish = AsyncMock()
    mock.subscribe = AsyncMock()
    return mock
```

### 6. Database Mocking

```python
# Use in-memory SQLite for database tests
@pytest.fixture
async def db_session():
    """Create in-memory database session."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from autoarr.api.database import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()
```

---

## Implementation Checklist

### Sprint 7: Content Request Handler

- [ ] **Phase 1: Service Layer (TDD)**
  - [ ] Write RequestHandler initialization tests
  - [ ] Implement RequestHandler class
  - [ ] Write natural language parsing tests
  - [ ] Implement parse_request() method
  - [ ] Write classification tests
  - [ ] Implement classify_media_type() with LLM integration
  - [ ] Write metadata extraction tests
  - [ ] Implement extract_metadata() method
  - [ ] Write search integration tests
  - [ ] Implement TMDB/Radarr/Sonarr search integration
  - [ ] Write disambiguation tests
  - [ ] Implement disambiguation flow
  - [ ] Write request tracking tests
  - [ ] Implement database operations

- [ ] **Phase 2: API Endpoints (TDD)**
  - [ ] Write POST /requests endpoint tests
  - [ ] Implement POST /requests endpoint
  - [ ] Write GET /requests list tests
  - [ ] Implement GET /requests with pagination
  - [ ] Write GET /requests/{id} tests
  - [ ] Implement GET /requests/{id}
  - [ ] Write PUT /requests/{id} tests
  - [ ] Implement PUT /requests/{id}
  - [ ] Write DELETE /requests/{id} tests
  - [ ] Implement DELETE /requests/{id}

- [ ] **Phase 3: Database Models (TDD)**
  - [ ] Write ContentRequest model tests
  - [ ] Create ContentRequest database model
  - [ ] Create database migration
  - [ ] Add model validation
  - [ ] Test model serialization

### Sprint 8: WebSocket Manager

- [ ] **Phase 1: WebSocket Service (TDD)**
  - [ ] Write WebSocketManager initialization tests
  - [ ] Implement WebSocketManager class
  - [ ] Write connection management tests
  - [ ] Implement connect/disconnect methods
  - [ ] Write broadcasting tests
  - [ ] Implement broadcast functionality
  - [ ] Write subscription management tests
  - [ ] Implement event filtering
  - [ ] Write reconnection tests
  - [ ] Implement reconnection logic
  - [ ] Write error handling tests
  - [ ] Implement error recovery

- [ ] **Phase 2: WebSocket Endpoint (TDD)**
  - [ ] Write WebSocket endpoint tests
  - [ ] Implement /api/v1/ws endpoint
  - [ ] Write message handling tests
  - [ ] Implement message routing
  - [ ] Write authentication tests (if applicable)
  - [ ] Implement auth middleware

- [ ] **Phase 3: Integration (TDD)**
  - [ ] Write event bus integration tests
  - [ ] Connect WebSocket to event bus
  - [ ] Write complete flow integration tests
  - [ ] Test request flow with WebSocket updates
  - [ ] Write performance tests
  - [ ] Optimize for production

### Testing & Quality Assurance

- [ ] **Code Coverage**
  - [ ] Achieve 85%+ line coverage
  - [ ] Achieve 80%+ branch coverage
  - [ ] 100% coverage of critical paths

- [ ] **Integration Testing**
  - [ ] All E2E flows tested
  - [ ] WebSocket integration verified
  - [ ] Database transactions tested

- [ ] **Performance Testing**
  - [ ] Request parsing < 100ms
  - [ ] WebSocket broadcast < 100ms (100 clients)
  - [ ] Database queries optimized

- [ ] **Documentation**
  - [ ] API documentation updated
  - [ ] Test documentation complete
  - [ ] Code comments added

---

## Expected Test Metrics

### Sprint 7 Metrics

- **Unit Tests**: 60-70 tests
- **API Endpoint Tests**: 15-20 tests
- **Integration Tests**: 5-10 tests
- **Total Tests**: ~80-100 tests
- **Coverage Target**: 85%+

### Sprint 8 Metrics

- **Unit Tests**: 40-50 tests
- **Integration Tests**: 10-15 tests
- **WebSocket Tests**: 15-20 tests
- **Total Tests**: ~65-85 tests
- **Coverage Target**: 85%+

### Combined Sprint 7-8

- **Total Tests**: 145-185 tests
- **Overall Coverage**: 85%+
- **Execution Time**: < 30 seconds (unit tests)
- **Execution Time**: < 2 minutes (all tests)

---

## Notes

1. **TDD Approach**: Write tests BEFORE implementation
2. **Async Testing**: Use pytest-asyncio for all async operations
3. **Mocking Strategy**: Mock external dependencies (LLM, TMDB, MCP)
4. **Database Testing**: Use in-memory SQLite for speed
5. **WebSocket Testing**: Use FastAPI WebSocketTestClient
6. **Event Testing**: Verify event emission and handling
7. **Error Scenarios**: Test all error paths and edge cases
8. **Performance**: Monitor test execution time and optimize

---

**Last Updated**: 2025-10-18
**Status**: Ready for TDD Implementation
