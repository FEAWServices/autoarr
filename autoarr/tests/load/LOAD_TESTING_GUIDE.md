# AutoArr Load Testing Complete Guide

## Quick Start (5 Minutes)

### 1. Start the API
```bash
# Option A: Using Docker
docker-compose -f docker/docker-compose.local-test.yml up -d

# Option B: Using Poetry
poetry run uvicorn autoarr.api.main:app --host localhost --port 8088
```

### 2. Run a Quick Test
```bash
cd autoarr/tests/load

# Run with interactive web UI (recommended for first time)
poetry run locust -f locustfile.py --host=http://localhost:8088 --web

# Open http://localhost:8089 in your browser
```

### 3. View Results
Results appear in real-time in the web UI with:
- Requests per second (throughput)
- Response time percentiles (p50, p95, p99)
- Pass/fail rate
- CSV export for detailed analysis

---

## Understanding the Load Tests

### What Gets Tested

The load tests cover all critical AutoArr API endpoints:

| Category | Endpoints | User Type |
|----------|-----------|-----------|
| **Health** | `/health`, `/health/ready`, `/health/live` | HealthCheckUser |
| **Downloads** | `/api/v1/downloads/queue`, `/api/v1/downloads/history` | MonitoringUser |
| **Content** | `/api/v1/shows`, `/api/v1/movies`, `/api/v1/media` | BrowsingUser |
| **Settings** | `/api/v1/settings/*`, `/api/v1/settings/test/*` | AdminUser |
| **Onboarding** | `/api/v1/onboarding/status`, `/api/v1/onboarding/step` | OnboardingFlowTasks |
| **Configuration** | `/api/v1/config/audit/*` | ConfigurationAuditUser |
| **Requests** | `/content/request`, `/content/requests` | ContentRequestUser |
| **Activity** | `/api/v1/activity`, `/api/v1/logs` | ActivityMonitoringTasks |
| **WebSocket** | `/api/v1/ws` | WebSocketUser |

### User Scenarios

Different user types simulate realistic behaviors:

**HealthCheckUser** (40% of load)
- Represents monitoring dashboards and health checkers
- Frequent operations every 2-5 seconds
- Quick health checks, ping, readiness probes
- Low latency requirements (p95 < 500ms)

**MonitoringUser** (30% of load)
- Represents real-time monitoring dashboards
- Moderate frequency operations every 3-8 seconds
- Downloads queue, history, activity logs
- Medium latency tolerance

**BrowsingUser** (20% of load)
- Represents UI users browsing content
- Moderate frequency every 4-10 seconds
- Show/movie browsing, library access

**Administrative Users** (10% of load)
- ConfigurationAuditUser: System audits (10-20 sec intervals)
- ContentRequestUser: Content requests (15-30 sec intervals)
- AdminUser: Settings management (20-40 sec intervals)

---

## Performance Budgets (SLAs)

These are the target performance thresholds:

```
Health Endpoints:      p95 ≤ 500ms,  p99 ≤ 1000ms
Read Endpoints:        p95 ≤ 500ms,  p99 ≤ 1000ms
Write Endpoints:       p95 ≤ 2000ms, p99 ≤ 5000ms
Slow Endpoints:        p95 ≤ 5000ms, p99 ≤ 10000ms (audits, LLM calls)
WebSocket:             p95 ≤ 1000ms, p99 ≤ 3000ms
```

- **p95 (95th percentile)**: 95% of requests must be this fast or faster
- **p99 (99th percentile)**: 99% of requests must be this fast or faster
- Tests FAIL if any endpoint exceeds these budgets under load

---

## Running Different Load Test Profiles

### Using the Shell Script (Recommended)

```bash
cd autoarr/tests/load

# Baseline test (5 min, 30 users)
./run_load_tests.sh baseline

# Normal production load (10 min, 40 users)
./run_load_tests.sh normal

# Peak load (15 min, 100 users)
./run_load_tests.sh peak

# Stress testing (20 min, 225 users)
./run_load_tests.sh stress

# Spike test (10 min, rapid 150 users/sec ramp-up)
./run_load_tests.sh spike

# WebSocket test (8 min, 50 connections)
./run_load_tests.sh websocket

# All tests sequentially
./run_load_tests.sh all

# Validate API is accessible
./run_load_tests.sh validate

# Generate summary report
./run_load_tests.sh summary
```

### Using Locust Directly

```bash
# Baseline (minimal load for comparison)
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=30 \
  --spawn-rate=5 \
  --run-time=5m \
  --headless \
  --csv=results/baseline

# Normal load
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=40 \
  --spawn-rate=5 \
  --run-time=10m \
  --headless

# Peak load
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=15m \
  --headless

# Stress test
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=225 \
  --spawn-rate=10 \
  --run-time=20m \
  --headless

# Spike test (rapid ramp-up)
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=155 \
  --spawn-rate=150 \
  --run-time=10m \
  --headless
```

---

## Analyzing Results

### Viewing Real-Time Results (Web UI)

1. Start test with `--web` flag
2. Open http://localhost:8089
3. Set users and spawn rate
4. Click "Start"
5. Watch metrics update in real-time:
   - RPS (requests per second)
   - Response time percentiles
   - Failure rate
   - Individual endpoint metrics

### CSV Analysis

Locust creates CSV files after each run:

```bash
# Parse and analyze results
python analyze_results.py results/baseline_20231215_120000_stats.csv

# Output shows:
# - Endpoint details (request count, response times)
# - Performance violations (if any)
# - Optimization recommendations
# - Pass/fail status
```

### Manual Analysis with Python

```python
import pandas as pd

# Load results
stats = pd.read_csv("results/baseline_stats.csv")

# View slowest endpoints
slow = stats.nlargest(5, '95%')[['Name', '# requests', '95%', '99%']]
print(slow)

# Find endpoints with high error rates
errors = stats[stats['# failures'] > 0]
print(errors[['Name', '# failures', 'Failure Rate']])

# Average response times
print(stats[['Name', 'Average']].sort_values('Average', ascending=False))
```

---

## Test Execution Workflow

### 1. Baseline Run (Establish Metrics)
```bash
./run_load_tests.sh baseline
```
- Minimal load (30 users)
- Establishes baseline performance
- Identifies any obvious bottlenecks
- Should complete in 5-8 minutes

**Success Criteria:**
- All endpoints respond within budgets
- Error rate < 0.5%
- No memory leaks visible

### 2. Normal Load Test (Verify Production Load)
```bash
./run_load_tests.sh normal
```
- Expected production load (40 users)
- Tests realistic distribution
- Should complete in 10-12 minutes

**Success Criteria:**
- All endpoints within budgets
- Error rate < 1%
- Response times stable throughout

### 3. Peak Load Test (Validate Scalability)
```bash
./run_load_tests.sh peak
```
- Expected peak usage (100 users)
- Tests system under peak conditions
- Should complete in 15-18 minutes

**Success Criteria:**
- Most endpoints within budgets
- p95 times may be at upper limit
- Error rate < 2%
- System recovers cleanly after test

### 4. Stress Test (Find Breaking Point)
```bash
./run_load_tests.sh stress
```
- Push system to breaking point (225 users)
- Tests beyond normal expectations
- Should complete in 20-25 minutes

**Expected Results:**
- Some endpoints will exceed budgets
- Errors increase as load increases
- Identifies failure points
- Used to understand system limits

### 5. Spike Test (Test Resilience)
```bash
./run_load_tests.sh spike
```
- Sudden traffic spike (150 users in 30 seconds)
- Tests system recovery
- Should complete in 10-12 minutes

**Success Criteria:**
- System handles spike without crashing
- Recovers to baseline after spike
- Error rate is temporary and recovers

---

## Interpreting Performance Metrics

### Response Time Percentiles

```
Min:    Fastest request (best case)
p50:    Median (50% of requests faster than this)
p95:    95th percentile (5% of requests slower)
p99:    99th percentile (1% of requests slower)
Max:    Slowest request (worst case)
```

Example:
```
Endpoint: /api/v1/downloads/queue
  Min:  45.2ms
  p50:  120.5ms
  p95:  420.3ms  ← Most important for SLAs
  p99:  850.1ms
  Max:  2140.5ms
```

The p95 of 420.3ms is well within the 500ms budget ✓

### Failure Rates

- **< 0.5%**: Excellent, acceptable during normal testing
- **0.5-2%**: Acceptable during stress testing
- **> 2%**: Investigate - likely API errors
- **> 5%**: Serious issue - API degrading under load

### Common Issues and Causes

| Symptom | Likely Cause |
|---------|-------------|
| All p95/p99 times exceed budget | Slow database queries, missing indexes |
| Specific endpoints slow | Endpoint-specific optimization needed |
| Errors increase with load | Resource exhaustion (connections, memory) |
| Sporadic slow requests | Cache misses, garbage collection pauses |
| Memory grows during test | Memory leak in endpoint or dependency |
| Gradual slowdown over time | Resource leak or cache growth |

---

## WebSocket Load Testing

### Running WebSocket Tests

```bash
# Using shell script
./run_load_tests.sh websocket

# Using Locust directly
poetry run locust -f websocket_load_test.py \
  --host=http://localhost:8088 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=8m \
  --headless
```

### What Gets Tested

- **Connection Establishment**: Time to connect to WebSocket
- **Message Throughput**: Messages/second handling
- **Connection Stability**: Handling of long-lived connections
- **Message Delivery**: Proper message receipt and handling
- **Connection Loss Recovery**: Reconnection handling

### Expected Performance

- Connection establishment: p95 < 1000ms
- Message send/receive: p95 < 500ms
- Stress (100+ messages/sec): p95 < 1000ms

---

## Troubleshooting

### "Connection refused" Error

```bash
# Check if API is running
curl http://localhost:8088/health

# Start API
docker-compose -f docker/docker-compose.local-test.yml up -d

# Or check logs
docker logs autoarr-local
```

### High Failure Rate During Test

```bash
# Reduce load
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=20 \
  --spawn-rate=2 \
  --headless

# Check API logs
docker logs autoarr-local --tail 100

# Check API health
curl http://localhost:8088/health | jq
```

### "Locust not found" Error

```bash
# Reinstall dependencies
poetry install --no-cache

# Verify locust is installed
poetry show locust

# Upgrade to latest
poetry lock
poetry install
```

### Memory Issues During Test

```bash
# Reduce number of users
./run_load_tests.sh baseline  # Start with minimal load

# Monitor system resources
# macOS: open Activity Monitor, watch Memory tab
# Linux: watch -n 1 'free -h && ps aux | grep python'
# Windows: Task Manager > Performance
```

### Test Takes Too Long / Hangs

```bash
# Check API responsiveness
curl -w "Time: %{time_total}s\n" http://localhost:8088/health

# Reduce run time and user count
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=10 \
  --spawn-rate=1 \
  --run-time=2m \
  --headless
```

---

## Performance Optimization Workflow

### When Tests Fail

1. **Identify the Slowest Endpoints**
   ```bash
   python analyze_results.py results/baseline_stats.csv
   # Shows endpoints with p95/p99 violations
   ```

2. **Profile the Slow Endpoint**
   ```python
   # Add timing to endpoint code
   import time
   start = time.time()
   result = await expensive_operation()
   print(f"Operation took {time.time() - start}s")
   ```

3. **Common Optimizations**
   - Add database indexes on frequently queried columns
   - Implement response caching (HTTP caching headers)
   - Optimize database queries (check execution plans)
   - Add response pagination/filtering
   - Use connection pooling
   - Batch operations where possible

4. **Re-test**
   ```bash
   ./run_load_tests.sh baseline
   # Verify improvements
   ```

5. **Document Results**
   - Before optimization: `results/baseline_before_*.csv`
   - After optimization: `results/baseline_after_*.csv`
   - Compare and document improvement percentage

---

## Continuous Integration

### Running Load Tests in CI/CD

```yaml
# .github/workflows/load-test.yml
name: Load Testing
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    services:
      autoarr:
        image: autoarr:latest
        ports:
          - 8088:8088
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: poetry install
      - run: |
          cd autoarr/tests/load
          ./run_load_tests.sh baseline
      - uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: autoarr/tests/load/results/
```

---

## Performance Budgets Reference

### Why These Budgets?

The performance budgets are based on:
- **User experience**: P95 is what most users experience
- **Industry standards**: Aiming for responsive feel
- **AWS recommendations**: Standard for cloud applications
- **AutoArr use cases**: Reflects typical usage patterns

### Adjusting Budgets

If budgets don't match your requirements:

1. Edit `locustfile.py`:
   ```python
   PERFORMANCE_BUDGETS = {
       "health_check": {"p95": 500, "p99": 1000},  # Edit these
       ...
   }
   ```

2. Edit `conftest.py`:
   ```python
   PERFORMANCE_BUDGETS = {
       "health_endpoints": {"p95": 500, "p99": 1000},  # Edit these
       ...
   }
   ```

3. Update documentation and run tests again

---

## Next Steps

1. **Run Baseline Test**: Establish current performance
2. **Analyze Results**: Identify bottlenecks
3. **Optimize**: Address identified issues
4. **Regression Test**: Verify improvements
5. **Schedule Regular Tests**: Catch performance regressions

---

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [API Reference](../../docs/API_REFERENCE.md)
- [Architecture Guide](../../docs/ARCHITECTURE.md)
- [Performance FAQ](PERFORMANCE_FAQ.md)

## Getting Help

For issues with load testing:

1. Check this guide and the README
2. Review Locust logs: `--loglevel=DEBUG`
3. Check API logs: `docker logs autoarr-local`
4. Verify system resources are available
5. Open an issue with test output and logs
