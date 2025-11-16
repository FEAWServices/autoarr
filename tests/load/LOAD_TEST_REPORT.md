# Load Testing Report

## Executive Summary

This report documents load testing results for AutoArr API using Locust.

**Test Date**: 2025-10-08
**Testing Tool**: Locust 2.x
**Environment**: Development (Local)
**Duration**: Various scenarios (1-10 minutes each)

## Performance Targets

| Metric                  | Target              | Status              |
| ----------------------- | ------------------- | ------------------- |
| API Response Time (p95) | < 200ms             | To be measured      |
| API Response Time (p99) | < 500ms             | To be measured      |
| Throughput              | 100 req/s sustained | To be measured      |
| WebSocket Latency       | < 50ms              | Not implemented yet |
| Database Queries (p95)  | < 50ms              | To be measured      |
| Memory Usage (idle)     | < 512MB             | To be measured      |
| Memory Usage (load)     | < 1GB               | To be measured      |
| CPU Usage (normal)      | < 50%               | To be measured      |

## Test Scenarios

### Scenario 1: Configuration Audit Load

**Description**: Simulates users running configuration audits across services.

**User Profile**:

- Tasks: Get SABnzbd config (30%), Get Sonarr config (30%), Run audit (20%)
- Think time: 1-3 seconds between tasks
- Concurrent users: 10, 25, 50

**Expected Results**:

```
Users: 50
Duration: 5 minutes
Target RPS: 20-30
```

**Actual Results**:

```
[To be filled after running tests]
Total Requests: TBD
Failures: TBD
Median Response Time: TBD ms
95th Percentile: TBD ms
99th Percentile: TBD ms
Requests/second: TBD
```

**Analysis**:
[To be added after testing]

---

### Scenario 2: Content Request Load

**Description**: Simulates users requesting movies and TV shows.

**User Profile**:

- Tasks: Request movie (40%), Request TV show (40%), List content (20%)
- Think time: 2-5 seconds between tasks
- Concurrent users: 10, 25, 50

**Expected Results**:

```
Users: 50
Duration: 5 minutes
Target RPS: 15-20
```

**Actual Results**:

```
[To be filled after running tests]
Total Requests: TBD
Failures: TBD
Median Response Time: TBD ms
95th Percentile: TBD ms
99th Percentile: TBD ms
Requests/second: TBD
```

**Analysis**:
[To be added after testing]

**Notes**:

- Content request endpoint not yet implemented
- Tests will skip this endpoint (404 responses)

---

### Scenario 3: Monitoring Load

**Description**: Simulates users monitoring downloads and activity.

**User Profile**:

- Tasks: Check activity log (50%), Check queue (30%), Check history (20%)
- Think time: 0.5-2 seconds (frequent polling)
- Concurrent users: 10, 25, 50

**Expected Results**:

```
Users: 50
Duration: 5 minutes
Target RPS: 40-60
```

**Actual Results**:

```
[To be filled after running tests]
Total Requests: TBD
Failures: TBD
Median Response Time: TBD ms
95th Percentile: TBD ms
99th Percentile: TBD ms
Requests/second: TBD
```

**Analysis**:
[To be added after testing]

---

### Scenario 4: Mixed Workload (Realistic)

**Description**: Realistic mix of all operations based on expected user behavior.

**User Profile**:

- Browse activity (50%)
- Check downloads (25%)
- Check health (15%)
- Request content (8%)
- Run audit (2%)
- Think time: 1-5 seconds (variable)
- Concurrent users: 25, 50, 100

**Expected Results**:

```
Users: 100
Duration: 10 minutes
Target RPS: 50-100
```

**Actual Results**:

```
[To be filled after running tests]
Total Requests: TBD
Failures: TBD
Median Response Time: TBD ms
95th Percentile: TBD ms
99th Percentile: TBD ms
Requests/second: TBD
```

**Analysis**:
[To be added after testing]

---

## Bottleneck Analysis

### Database Performance

**Queries Analyzed**:

- Activity log queries
- Settings queries
- Configuration audit queries
- Best practices queries

**Findings**:
[To be added after testing]

**Recommendations**:

- [ ] Add indexes on frequently queried columns
- [ ] Implement query result caching
- [ ] Optimize N+1 query patterns
- [ ] Use select_related/prefetch_related for ORM queries

---

### MCP Orchestrator Performance

**Operations Analyzed**:

- MCP server connections
- Tool invocations
- Parallel operations
- Connection pooling

**Findings**:
[To be added after testing]

**Recommendations**:

- [ ] Implement connection pooling
- [ ] Add request coalescing for duplicate requests
- [ ] Optimize parallel operation batching
- [ ] Add caching for frequently accessed data

---

### API Layer Performance

**Endpoints Analyzed**:

- `/api/v1/monitoring/activity`
- `/api/v1/downloads/queue`
- `/api/v1/downloads/history`
- `/api/v1/config/audit`
- `/health`

**Findings**:
[To be added after testing]

**Recommendations**:

- [ ] Add response caching for expensive operations
- [ ] Implement pagination for large result sets
- [ ] Add compression for large responses
- [ ] Optimize serialization

---

## Resource Utilization

### Memory Usage

**Idle State**:

```
[To be measured]
RSS: TBD MB
VMS: TBD MB
```

**Under Load (50 users)**:

```
[To be measured]
RSS: TBD MB
VMS: TBD MB
Peak: TBD MB
```

**Under Load (100 users)**:

```
[To be measured]
RSS: TBD MB
VMS: TBD MB
Peak: TBD MB
```

**Memory Leaks**:
[To be analyzed]

---

### CPU Usage

**Idle State**: TBD%

**Under Load (50 users)**: TBD%

**Under Load (100 users)**: TBD%

**CPU Bottlenecks**:
[To be analyzed]

---

### Network I/O

**Bandwidth Usage**:

- Request: TBD MB/s
- Response: TBD MB/s
- Total: TBD MB/s

**Connection Pool**:

- Active connections: TBD
- Idle connections: TBD
- Max connections: TBD

---

## Error Analysis

### Error Types

| Error Type   | Count | Percentage | Status Code |
| ------------ | ----- | ---------- | ----------- |
| Not Found    | TBD   | TBD%       | 404         |
| Server Error | TBD   | TBD%       | 500         |
| Timeout      | TBD   | TBD%       | 504         |
| Bad Request  | TBD   | TBD%       | 400         |

### Error Patterns

[To be added after testing]

---

## Scalability Analysis

### Horizontal Scaling

**Single Instance**:

- Max throughput: TBD req/s
- Max concurrent users: TBD

**Multiple Instances** (if tested):

- 2 instances: TBD req/s
- 4 instances: TBD req/s
- Scaling efficiency: TBD%

### Vertical Scaling

**Resource Impact**:

- 2 CPU cores: TBD req/s
- 4 CPU cores: TBD req/s
- 8 CPU cores: TBD req/s

---

## Optimization Recommendations

### High Priority

1. **Implement Database Indexing**

   - Impact: High
   - Effort: Low
   - Add indexes on: `activity_log.correlation_id`, `config_audit.service`, `setting.key`

2. **Add Response Caching**

   - Impact: High
   - Effort: Medium
   - Cache frequently accessed data with Redis
   - TTL: 30-60 seconds for dynamic data, 5-10 minutes for static data

3. **Optimize Database Queries**
   - Impact: High
   - Effort: Medium
   - Use select_related/prefetch_related for related objects
   - Implement pagination for large result sets

### Medium Priority

4. **Connection Pooling**

   - Impact: Medium
   - Effort: Medium
   - Implement connection pooling for MCP servers
   - Reuse HTTP connections

5. **Request Coalescing**

   - Impact: Medium
   - Effort: High
   - Coalesce duplicate concurrent requests
   - Return cached results for identical operations

6. **Compression**
   - Impact: Medium
   - Effort: Low
   - Enable gzip compression for responses
   - Reduce payload sizes

### Low Priority

7. **Code Splitting**

   - Impact: Low
   - Effort: Medium
   - Lazy load non-critical components
   - Reduce initial load time

8. **CDN for Static Assets**
   - Impact: Low
   - Effort: Low
   - Serve static files from CDN
   - Reduce server load

---

## Before/After Comparison

### Baseline (Before Optimization)

```
[To be measured]
RPS: TBD
p95: TBD ms
p99: TBD ms
CPU: TBD%
Memory: TBD MB
```

### After Optimization

```
[To be measured after implementing optimizations]
RPS: TBD
p95: TBD ms
p99: TBD ms
CPU: TBD%
Memory: TBD MB
Improvement: TBD%
```

---

## Running Load Tests

### Prerequisites

```bash
# Install Locust
poetry add --group dev locust

# Ensure API is running
poetry run uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088
```

### Basic Load Test

```bash
# Run with 10 users
locust -f tests/load/locustfile.py --host=http://localhost:8088 --users 10 --spawn-rate 1 --run-time 1m --headless

# Run with 50 users
locust -f tests/load/locustfile.py --host=http://localhost:8088 --users 50 --spawn-rate 5 --run-time 5m --headless

# Run with 100 users
locust -f tests/load/locustfile.py --host=http://localhost:8088 --users 100 --spawn-rate 10 --run-time 10m --headless
```

### Specific User Classes

```bash
# Configuration audit load
locust -f tests/load/locustfile.py --host=http://localhost:8088 ConfigAuditUser --users 50 --spawn-rate 5 --run-time 5m --headless

# Content request load
locust -f tests/load/locustfile.py --host=http://localhost:8088 ContentRequestUser --users 50 --spawn-rate 5 --run-time 5m --headless

# Monitoring load
locust -f tests/load/locustfile.py --host=http://localhost:8088 MonitoringUser --users 100 --spawn-rate 10 --run-time 5m --headless

# Mixed workload (default)
locust -f tests/load/locustfile.py --host=http://localhost:8088 --users 100 --spawn-rate 10 --run-time 10m --headless
```

### Web UI

```bash
# Run with web UI for real-time monitoring
locust -f tests/load/locustfile.py --host=http://localhost:8088

# Open browser to http://localhost:8089
```

---

## Monitoring During Tests

### Metrics to Track

1. **API Metrics**:

   - Response times (median, p95, p99)
   - Request rate (RPS)
   - Error rate
   - Success rate

2. **System Metrics**:

   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

3. **Database Metrics**:

   - Query execution time
   - Active connections
   - Lock waits
   - Cache hit ratio

4. **Application Metrics**:
   - Request queue depth
   - Worker thread pool usage
   - MCP connection pool usage

### Tools

- **Locust**: Real-time load testing metrics
- **htop/top**: System resource monitoring
- **iostat**: Disk I/O monitoring
- **netstat**: Network monitoring
- **PostgreSQL pg_stat**: Database metrics (if applicable)

---

## Conclusions

### Target Achievement

| Target       | Status | Notes         |
| ------------ | ------ | ------------- |
| p95 < 200ms  | TBD    | [To be added] |
| p99 < 500ms  | TBD    | [To be added] |
| 100 RPS      | TBD    | [To be added] |
| Memory < 1GB | TBD    | [To be added] |
| CPU < 50%    | TBD    | [To be added] |

### Key Findings

1. [To be added after testing]
2. [To be added after testing]
3. [To be added after testing]

### Next Steps

1. [ ] Implement database indexing
2. [ ] Add Redis caching layer
3. [ ] Optimize database queries
4. [ ] Implement connection pooling
5. [ ] Add rate limiting
6. [ ] Re-run load tests after optimizations
7. [ ] Update this report with results

---

**Report Version**: 1.0
**Last Updated**: 2025-10-08
**Next Review**: After implementing optimizations
