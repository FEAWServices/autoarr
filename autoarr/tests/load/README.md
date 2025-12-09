# AutoArr API Load Tests

Comprehensive load testing suite for AutoArr API endpoints using [Locust](https://locust.io/).

## Overview

This directory contains load tests designed to:

- Validate system performance under various load conditions
- Identify performance bottlenecks and scalability limits
- Ensure system meets performance budgets (SLAs)
- Test concurrent user handling across multiple user scenarios
- Detect memory leaks and resource degradation under sustained load

## Performance Budgets (SLAs)

The test suite enforces these performance budgets:

| Operation Type | p95 (ms) | p99 (ms) |
|---|---|---|
| Health checks | 500 | 1,000 |
| Read operations | 500 | 1,000 |
| Write operations | 2,000 | 5,000 |
| Slow operations (audits, LLM) | 5,000 | 10,000 |
| WebSocket | 1,000 | 3,000 |

## Test Files

### Core Files

- **locustfile.py** - Main Locust test file with all user scenarios and tasks
  - `HealthCheckUser` - Simulates monitoring dashboards (frequent health checks)
  - `MonitoringUser` - Real-time download/activity monitoring
  - `BrowsingUser` - Content library browsing
  - `ConfigurationAuditUser` - Configuration auditing workflows
  - `ContentRequestUser` - Natural language content requests
  - `AdminUser` - Settings and administrative operations

- **test_profiles.py** - Pre-configured load test profiles
  - Baseline (minimal load for baseline metrics)
  - Normal Load (typical production load)
  - Peak Load (expected peak usage)
  - Stress Test (push system to breaking point)
  - Spike Test (sudden traffic increase)
  - Day in the Life (full day simulation)
  - WebSocket Profile (WebSocket connection testing)

- **conftest.py** - Shared utilities and configuration
  - Performance metrics collection
  - Performance budget validation
  - Report generation
  - Environment validation

## Installation

Locust is already included in `pyproject.toml` as a dev dependency:

```bash
poetry install
```

## Running Load Tests

### 1. Start AutoArr API

First, ensure the AutoArr API is running:

```bash
# Using Docker
docker-compose -f docker/docker-compose.local-test.yml up -d

# Or run directly with Poetry
poetry run uvicorn autoarr.api.main:app --host localhost --port 8088
```

Verify the API is running:
```bash
curl http://localhost:8088/health
```

### 2. Run Locust with Web UI (Interactive)

```bash
# Navigate to test directory
cd autoarr/tests/load

# Run with Locust web interface
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --web
```

Then open http://localhost:8089 in your browser to:
- Set number of users
- Set spawn rate
- Start/stop tests
- View real-time metrics
- Download HTML report

### 3. Run Headless (Scripted)

#### Baseline Load (5 minutes, ~30 concurrent users)
```bash
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=30 \
  --spawn-rate=5 \
  --run-time=5m \
  --headless \
  --csv=results/baseline
```

#### Normal Load (10 minutes, ~40 concurrent users)
```bash
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=40 \
  --spawn-rate=5 \
  --run-time=10m \
  --headless \
  --csv=results/normal_load
```

#### Peak Load (15 minutes, ~100 concurrent users)
```bash
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=15m \
  --headless \
  --csv=results/peak_load
```

#### Stress Test (20 minutes, ~225 concurrent users)
```bash
poetry run locust -f locustfile.py \
  --host=http://localhost:8088 \
  --users=225 \
  --spawn-rate=10 \
  --run-time=20m \
  --headless \
  --csv=results/stress_test
```

#### Spike Test (10 minutes with 30-second ramp-up)
```bash
poetry run locust -f locustfile.py \
  --host=localhost:8088 \
  --users=155 \
  --spawn-rate=150 \  # Spawn ~150 users per second for spike
  --run-time=10m \
  --headless \
  --csv=results/spike_test
```

### 4. Using Python Script for Automation

Create a test runner script:

```python
# run_load_test.py
import subprocess
import sys

tests = [
    {
        "name": "baseline",
        "users": 30,
        "spawn_rate": 5,
        "duration": "5m",
    },
    {
        "name": "normal_load",
        "users": 40,
        "spawn_rate": 5,
        "duration": "10m",
    },
    {
        "name": "peak_load",
        "users": 100,
        "spawn_rate": 10,
        "duration": "15m",
    },
]

for test in tests:
    print(f"\n{'='*80}")
    print(f"Running {test['name']} test...")
    print(f"{'='*80}\n")

    cmd = [
        "poetry", "run", "locust",
        "-f", "autoarr/tests/load/locustfile.py",
        f"--host=http://localhost:8088",
        f"--users={test['users']}",
        f"--spawn-rate={test['spawn_rate']}",
        f"--run-time={test['duration']}",
        "--headless",
        f"--csv=results/{test['name']}",
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"❌ Test {test['name']} failed")
        sys.exit(1)

print("\n✓ All tests completed successfully!")
```

Run it with:
```bash
python run_load_test.py
```

## Test Scenarios

### User Classes and Behavior

#### HealthCheckUser (High Frequency)
- **Wait Time**: 2-5 seconds between operations
- **Operations**: Health checks, ping, readiness probes
- **Use Case**: Monitoring dashboards, load balancers
- **Expected Load**: 40% of total users

#### MonitoringUser (Moderate Frequency)
- **Wait Time**: 3-8 seconds between operations
- **Operations**: Download queue, history, activity logs
- **Use Case**: Real-time monitoring dashboards
- **Expected Load**: 30% of total users

#### BrowsingUser (Moderate Frequency)
- **Wait Time**: 4-10 seconds between operations
- **Operations**: Show/movie browsing, library access
- **Use Case**: UI users browsing content
- **Expected Load**: 20% of total users

#### ConfigurationAuditUser (Low Frequency)
- **Wait Time**: 10-20 seconds between operations
- **Operations**: Configuration audits, settings management
- **Use Case**: Administrators running system checks
- **Expected Load**: 5% of total users

#### ContentRequestUser (Low Frequency)
- **Wait Time**: 15-30 seconds between operations
- **Operations**: Content requests, library browsing
- **Use Case**: Users requesting content via natural language
- **Expected Load**: 3% of total users

#### AdminUser (Low Frequency)
- **Wait Time**: 20-40 seconds between operations
- **Operations**: Settings management, configuration
- **Use Case**: System administrators
- **Expected Load**: 2% of total users

## Interpreting Results

### Key Metrics

1. **Response Time Percentiles**
   - **p50**: Median response time (50% of requests)
   - **p95**: 95th percentile (5% slower than this)
   - **p99**: 99th percentile (1% slower than this)
   - **Max**: Worst-case response time

2. **Throughput**
   - **RPS**: Requests per second
   - **Total Requests**: Number of requests during test
   - **Failures**: Failed requests

3. **Error Rate**
   - Percentage of failed requests
   - Common failure modes:
     - Connection errors: Network issues or API unavailable
     - Timeout errors: Slow response times (>timeout threshold)
     - HTTP errors: 5xx from API, 4xx from invalid requests

### Success Criteria

A test passes if:
- ✓ p95 response times meet budgets for all endpoints
- ✓ p99 response times meet budgets for all endpoints
- ✓ Error rate < 1% (expect some errors under extreme load)
- ✓ No memory leaks (RSS memory usage stable)
- ✓ System recovers after load test ends

### Common Issues

#### High Response Times
- Check API logs for errors or slowdowns
- Verify database connections and queries
- Check CPU/memory utilization on server
- Verify no network bottlenecks

#### High Error Rate
- Connection errors → API might be crashing under load
- Timeout errors → Increase timeout or optimize slow endpoints
- HTTP 5xx errors → Check API logs for exceptions

#### Memory Leaks
- Monitor RSS memory during sustained load
- Memory should stabilize after initial growth
- If memory keeps growing → likely memory leak

## Advanced Options

### Environment Variables

```bash
# Set custom base URL
export AUTOARR_BASE_URL=http://your-server:8088

# Run tests
poetry run locust -f locustfile.py --host=$AUTOARR_BASE_URL ...
```

### Custom Load Curves

Create custom shapes for load testing:

```python
# In locustfile.py
from locust import LoadTestShape

class CustomLoadCurve(LoadTestShape):
    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            # Ramp up: 1 user per second
            return (run_time // 1, 1)
        elif run_time < 300:
            # Sustain at 60 users
            return (60, 1)
        elif run_time < 360:
            # Ramp down
            return (max(0, 60 - (run_time - 300)), 1)
        else:
            return None
```

### Tagging

Test specific endpoints with tags:

```bash
# Only test health endpoints
poetry run locust -f locustfile.py \
  -T health \
  --headless

# Exclude specific tasks
poetry run locust -f locustfile.py \
  -E configuration \
  --headless
```

## Reports and Analysis

### Output Files

Locust generates CSV files with metrics:

- `results/baseline_stats.csv` - Endpoint statistics
- `results/baseline_stats_history.csv` - Statistics over time
- `results/baseline_failures.csv` - Failed requests

### HTML Reports

Locust web UI can generate HTML reports:
1. Open http://localhost:8089 in browser
2. Run test
3. Click "Download Report" button

### Manual Analysis

```python
import pandas as pd

# Load statistics
stats = pd.read_csv("results/baseline_stats.csv")

# Get endpoints that exceeded budget
slow_endpoints = stats[stats['95%'] > 500]

print(slow_endpoints[['Name', 'Num Requests', '95%', '99%']])
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

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
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: poetry install
      - name: Run baseline load test
        run: |
          cd autoarr/tests/load
          poetry run locust -f locustfile.py \
            --host=http://localhost:8088 \
            --users=50 \
            --spawn-rate=5 \
            --run-time=5m \
            --headless \
            --csv=results/baseline
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: autoarr/tests/load/results/
```

## Troubleshooting

### "Connection refused" Error
```bash
# Check if API is running
curl http://localhost:8088/health

# Start API if not running
poetry run uvicorn autoarr.api.main:app --host localhost --port 8088
```

### High Failure Rate
1. Check API logs: `docker logs autoarr-local`
2. Reduce user count and spawn rate
3. Increase timeout values
4. Check server resources (CPU, memory, disk)

### Locust Not Found
```bash
# Reinstall dependencies
poetry install --no-cache

# Verify Locust is installed
poetry show locust
```

### Performance Budgets Exceeded
1. Identify slow endpoints from results
2. Profile the endpoint in isolation
3. Check for database query issues
4. Verify caching is working
5. Consider optimization opportunities

## Next Steps

After running load tests:

1. **Baseline Run**: Establish baseline metrics
2. **Normal Load Test**: Validate typical usage
3. **Peak Load Test**: Ensure system handles peaks
4. **Stress Test**: Find breaking points
5. **Optimization**: Address bottlenecks found
6. **Regression Test**: Verify improvements

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://locust.io/best-practices)
- [AutoArr Performance SLAs](../../docs/PERFORMANCE.md)
- [API Documentation](../../docs/API_REFERENCE.md)

## Contributing

When adding new endpoints:

1. Add corresponding task in appropriate TaskSet
2. Update performance budgets if needed
3. Document expected behavior under load
4. Test with baseline profile first
5. Update this README if adding new scenarios

## Support

For issues with load tests:

1. Check test logs: `poetry run locust -f locustfile.py --loglevel=DEBUG`
2. Verify API is responding: `curl -v http://localhost:8088/health`
3. Check system resources during test
4. Review AutoArr API logs for errors
5. Open issue with test output and API logs
