# AutoArr Load Testing Suite - Complete Summary

## Overview

A comprehensive load testing suite for AutoArr API endpoints using Locust, designed to validate system performance under realistic and extreme load conditions.

**Status**: ✓ Complete and ready for use
**Last Updated**: December 9, 2025
**Framework**: Locust 2.42.5
**Python**: 3.11+

---

## What Was Created

### Core Test Files

#### 1. **locustfile.py** (17.8 KB)
Main Locust load test file with multiple user scenarios.

**Contents:**
- 6 User Classes:
  - `HealthCheckUser`: Frequent health monitoring (40% of load)
  - `MonitoringUser`: Real-time activity/download monitoring (30% of load)
  - `BrowsingUser`: Content library browsing (20% of load)
  - `ConfigurationAuditUser`: System configuration audits (5% of load)
  - `ContentRequestUser`: Content request submission (3% of load)
  - `AdminUser`: Settings and administrative operations (2% of load)

- 8 Task Sets covering all API endpoints:
  - `HealthCheckTasks`: Health probes and readiness checks
  - `DownloadsMonitoringTasks`: SABnzbd queue and history monitoring
  - `ContentLibraryTasks`: Sonarr/Radarr/Plex library operations
  - `OnboardingFlowTasks`: Setup wizard simulation
  - `SettingsManagementTasks`: Settings and connection testing
  - `ConfigurationAuditTasks`: Configuration auditing workflow
  - `ContentRequestTasks`: Natural language content requests
  - `ActivityMonitoringTasks`: Activity log monitoring

**Performance Budgets Defined:**
- Health: p95 ≤ 500ms, p99 ≤ 1000ms
- Reads: p95 ≤ 500ms, p99 ≤ 1000ms
- Writes: p95 ≤ 2000ms, p99 ≤ 5000ms
- WebSocket: p95 ≤ 1000ms, p99 ≤ 3000ms

#### 2. **test_profiles.py** (9.9 KB)
Pre-configured load test profiles for different scenarios.

**Profiles Included:**
- **Baseline**: 30 users, 5 min, minimal load (establish baseline)
- **Normal Load**: 40 users, 10 min, typical production load
- **Peak Load**: 100 users, 15 min, expected peak usage
- **Stress Test**: 225 users, 20 min, find breaking point
- **Spike Test**: 155 users with 30-sec ramp, sudden traffic spike
- **Day in Life**: 50 users, 60 min, full day simulation
- **WebSocket**: 50 WebSocket connections, 8 min

Each profile includes:
- User distribution across different user types
- Ramp-up and ramp-down times
- Total duration
- Helper functions for profile management

#### 3. **websocket_load_test.py** (13.2 KB)
Specialized WebSocket load testing.

**Features:**
- `WebSocketClient`: Async WebSocket client with Locust integration
- `WebSocketUser`: Standard WebSocket user with connection stability
- `WebSocketStressUser`: Rapid message stress testing
- `LongConnectionUser`: Long-lived connection resilience testing

**Tests:**
- Connection establishment time
- Message send/receive throughput
- Connection stability under load
- Recovery from disconnections

#### 4. **conftest.py** (12.2 KB)
Shared configuration and utility functions.

**Classes:**
- `PerformanceMetrics`: Collect and analyze metrics from tests
- `PerformanceBudgetValidator`: Validate response times against budgets

**Functions:**
- `validate_environment()`: Check API accessibility
- `build_url()`: Construct endpoint URLs
- `generate_test_payload()`: Create test data
- Performance budget definitions

#### 5. **analyze_results.py** (15 KB)
Results analysis and performance validation script.

**Features:**
- Parse Locust CSV output
- Validate against performance budgets
- Generate detailed performance reports
- Identify bottlenecks and violations
- Provide optimization recommendations
- Color-coded output for easy reading

**Usage:**
```bash
python analyze_results.py results/baseline_20231215_120000_stats.csv
```

### Documentation Files

#### 6. **README.md** (12.6 KB)
Comprehensive README with full instructions for running tests.

**Sections:**
- Overview and performance budgets
- Installation instructions
- Running tests (web UI, headless, with Docker)
- Test scenarios and user descriptions
- Interpreting results
- Advanced options and CI/CD integration
- Troubleshooting guide

#### 7. **LOAD_TESTING_GUIDE.md** (17 KB)
Complete guide with examples and workflows.

**Sections:**
- Quick start (5 minutes to first test)
- Understanding the load tests
- Performance budgets and SLAs
- Different profile descriptions
- Running each profile step-by-step
- Analyzing results
- Test execution workflow (5 steps)
- Interpreting metrics
- WebSocket testing
- Troubleshooting
- Performance optimization workflow
- CI/CD integration examples

#### 8. **SUMMARY.md** (This File)
Overview and index of all load testing components.

### Utility Files

#### 9. **run_load_tests.sh** (9.5 KB)
Convenience shell script for running tests.

**Commands:**
- `baseline`: Run baseline test
- `normal`: Run normal load test
- `peak`: Run peak load test
- `stress`: Run stress test
- `spike`: Run spike test
- `websocket`: Run WebSocket test
- `all`: Run all tests sequentially
- `ui`: Run with interactive web UI
- `validate`: Validate API is accessible
- `summary`: Generate summary report

**Features:**
- Automatic API connectivity checking
- Timestamped result files
- Color-coded output
- Error handling
- Results directory management

#### 10. **__init__.py** (1.4 KB)
Package initialization file for load testing module.

---

## Quick Start Guide

### Installation
```bash
# Dependencies already installed in pyproject.toml
poetry install
```

### Run Your First Test (5 minutes)
```bash
cd autoarr/tests/load

# Option A: Interactive Web UI (recommended for first time)
poetry run locust -f locustfile.py --host=http://localhost:8088 --web
# Open http://localhost:8089

# Option B: Quick command-line test
./run_load_tests.sh baseline
```

### Analyze Results
```bash
# Automatic analysis
python analyze_results.py results/baseline_*_stats.csv
```

---

## File Structure

```
autoarr/tests/load/
├── __init__.py                      # Package initialization
├── locustfile.py                    # Main load test file (6 user classes)
├── test_profiles.py                 # 7 pre-configured test profiles
├── websocket_load_test.py           # WebSocket-specific tests
├── conftest.py                      # Shared configuration & utilities
├── analyze_results.py               # Results analysis tool
├── run_load_tests.sh                # Convenience test runner
├── README.md                        # Installation & running tests
├── LOAD_TESTING_GUIDE.md            # Complete guide with examples
└── SUMMARY.md                       # This file
```

---

## Test Coverage

### API Endpoints Tested (30+ endpoints)

| Category | Endpoints | User Type | Operations |
|----------|-----------|-----------|------------|
| **Health** | `/health`, `/health/ready`, `/health/live` | HealthCheckUser | Monitoring |
| **Downloads** | `/api/v1/downloads/queue`, `history`, `failed` | MonitoringUser | Read |
| **Shows** | `/api/v1/shows` | BrowsingUser | Read |
| **Movies** | `/api/v1/movies` | BrowsingUser | Read |
| **Media** | `/api/v1/media/libraries` | BrowsingUser | Read |
| **Settings** | `/api/v1/settings/all`, `test/*` | AdminUser | Read/Write |
| **Onboarding** | `/api/v1/onboarding/status`, `step` | OnboardingFlowTasks | Read/Write |
| **Configuration** | `/api/v1/config/audit/*` | ConfigurationAuditUser | Read/Write |
| **Requests** | `/content/request`, `/content/requests` | ContentRequestUser | Write |
| **Activity** | `/api/v1/activity` | ActivityMonitoringTasks | Read |
| **Logs** | `/api/v1/logs` | ActivityMonitoringTasks | Read |
| **WebSocket** | `/api/v1/ws` | WebSocketUser | Real-time |

### Test Scenarios Covered

1. **Baseline Performance** - Establish baseline metrics
2. **Normal Load** - Typical production usage (40 concurrent users)
3. **Peak Load** - Expected maximum load (100 concurrent users)
4. **Stress Testing** - Push to breaking point (225 concurrent users)
5. **Spike Testing** - Sudden traffic increase (30-second ramp-up)
6. **Day-in-Life** - Full day simulation (60 minutes)
7. **WebSocket Connections** - Long-lived connections (50 concurrent)

---

## Performance Budgets

### SLAs Enforced

```
Endpoint Type          | p95 Budget | p99 Budget | Example Endpoints
-----------------------|------------|------------|-------------------
Health Checks          | 500 ms     | 1000 ms    | /health, /ping
Read Operations        | 500 ms     | 1000 ms    | /shows, /movies, /queue
Write Operations       | 2000 ms    | 5000 ms    | /settings/test, POST ops
Slow Operations        | 5000 ms    | 10000 ms   | /config/audit (LLM)
WebSocket              | 1000 ms    | 3000 ms    | /ws message latency
```

- **p95**: 95th percentile (5% of requests can be slower)
- **p99**: 99th percentile (1% of requests can be slower)
- Tests FAIL if any endpoint exceeds budgets

---

## Running Different Tests

### Quick Reference

```bash
# Web UI (interactive, recommended)
poetry run locust -f locustfile.py --web

# Using shell script
./run_load_tests.sh baseline       # 30 users, 5 min
./run_load_tests.sh normal         # 40 users, 10 min
./run_load_tests.sh peak           # 100 users, 15 min
./run_load_tests.sh stress         # 225 users, 20 min
./run_load_tests.sh spike          # 155 users, rapid ramp
./run_load_tests.sh all            # Run all sequentially

# Direct Locust commands
poetry run locust -f locustfile.py --users=100 --spawn-rate=10 --run-time=15m --headless

# WebSocket testing
poetry run locust -f websocket_load_test.py --users=50 --run-time=8m --headless
```

---

## Key Features

### 1. Multiple User Scenarios
- 6 different user types simulating real behavior
- Each with realistic wait times and operation frequencies
- Weighted distribution based on expected production load

### 2. Comprehensive Endpoint Coverage
- 30+ API endpoints tested
- All critical paths included
- Read, write, and real-time operations

### 3. Performance Validation
- Defined SLAs for each endpoint category
- Automatic budget validation
- Clear pass/fail reporting

### 4. Analysis Tools
- Real-time metrics in web UI
- CSV output for further analysis
- Automated analysis script with recommendations
- Color-coded violation reporting

### 5. Easy to Use
- Shell script for common operations
- Pre-configured profiles for different scenarios
- No complex configuration needed
- Clear documentation and examples

### 6. Extensible
- Easy to add new endpoints
- New user types can be created
- Custom load curves supported
- Profile system for different scenarios

---

## Typical Workflow

### 1. Establish Baseline (Day 1)
```bash
./run_load_tests.sh baseline
# Understand current performance
python analyze_results.py results/baseline_*_stats.csv
```

### 2. Test Normal Load (Day 1)
```bash
./run_load_tests.sh normal
# Verify typical load handling
```

### 3. Find Limits (Day 2)
```bash
./run_load_tests.sh stress
./run_load_tests.sh spike
# Understand breaking points
```

### 4. Identify Issues (Day 2)
```bash
python analyze_results.py results/stress_test_*_stats.csv
# Generate optimization recommendations
```

### 5. Optimize & Retest (Day 3+)
```bash
# Fix identified bottlenecks
# Run tests again
./run_load_tests.sh normal
# Verify improvements
```

### 6. Schedule Regular Testing (Ongoing)
```bash
# Add to CI/CD pipeline
# Run daily/weekly
# Track trends over time
```

---

## Expected Results

### Successful Test Run
- All endpoints within performance budgets
- p95 response times < 500ms for reads
- p99 response times < 1000ms for reads
- Error rate < 1% during peak load
- No memory leaks (RSS stable)
- Clean recovery after test completes

### Common Issues & Fixes
| Issue | Cause | Fix |
|-------|-------|-----|
| p95 > 500ms on reads | Missing database indexes | Add indexes on queried columns |
| p95 > 2000ms on writes | Slow transactions | Optimize transaction scope |
| Errors increase with load | Resource exhaustion | Increase connection pool size |
| Memory grows over time | Memory leak | Check for circular references |
| Sporadic slow requests | Cache misses | Implement caching layer |

---

## File Descriptions & Usage

### Core Test Files (Use for Running Tests)

| File | Purpose | How to Use |
|------|---------|-----------|
| `locustfile.py` | Main test scenarios | `poetry run locust -f locustfile.py` |
| `websocket_load_test.py` | WebSocket tests | `poetry run locust -f websocket_load_test.py` |
| `run_load_tests.sh` | Convenience runner | `./run_load_tests.sh baseline` |

### Configuration & Analysis (Support Files)

| File | Purpose | How to Use |
|------|---------|-----------|
| `test_profiles.py` | Test profile definitions | Referenced by shell script |
| `conftest.py` | Shared utilities | Used by test files |
| `analyze_results.py` | Results analysis | `python analyze_results.py <csv_file>` |

### Documentation (For Learning)

| File | Purpose | When to Read |
|------|---------|-------------|
| `README.md` | Installation & how to run | First time setup |
| `LOAD_TESTING_GUIDE.md` | Complete guide with examples | Learning and troubleshooting |
| `SUMMARY.md` | This overview document | Quick reference |

---

## System Requirements

### Hardware
- **CPU**: 2+ cores (more cores = faster tests)
- **RAM**: 2+ GB (for running tests)
- **Disk**: 100 MB free (for test results)

### Software
- Python 3.11+
- Poetry (for dependency management)
- Locust 2.42.5 (included in dev dependencies)
- AutoArr API running (on localhost:8088)

### Network
- API must be accessible at http://localhost:8088
- Or configure via `AUTOARR_BASE_URL` environment variable

---

## Performance Tuning Tips

### For Fastest Test Execution
```bash
# Reduce spawn rate to complete faster
poetry run locust -f locustfile.py --users=20 --spawn-rate=10 --run-time=3m
```

### For Most Accurate Results
```bash
# Use longer ramp-up and run time
./run_load_tests.sh normal
./run_load_tests.sh peak
```

### For Finding Bottlenecks
```bash
# Slow ramp-up shows exact breaking point
poetry run locust -f locustfile.py --users=200 --spawn-rate=2 --run-time=30m
```

---

## Next Steps

1. **Get Started**: Follow "Quick Start Guide" section
2. **Run Tests**: Execute `./run_load_tests.sh baseline`
3. **Analyze Results**: Use `analyze_results.py` to review
4. **Understand Metrics**: Read "LOAD_TESTING_GUIDE.md"
5. **Schedule Testing**: Add to CI/CD pipeline
6. **Optimize**: Address any bottlenecks found

---

## Integration with CI/CD

### GitHub Actions Example
See `LOAD_TESTING_GUIDE.md` for complete CI/CD setup

### Important Notes
- Run tests in dedicated test environment
- Don't run during production hours
- Monitor resource usage during tests
- Archive results for trend analysis
- Fail CI on performance regressions

---

## Support & Troubleshooting

### Common Issues

**Cannot connect to API**
```bash
# Check if running
curl http://localhost:8088/health

# Start API
docker-compose -f docker/docker-compose.local-test.yml up -d
```

**Locust not found**
```bash
poetry install --no-cache
```

**High failure rate**
```bash
# Check API logs
docker logs autoarr-local

# Reduce load
./run_load_tests.sh baseline
```

See `README.md` and `LOAD_TESTING_GUIDE.md` for more troubleshooting.

---

## Performance Metrics Explained

### Response Time Percentiles
- **p50**: Median (typical response)
- **p95**: What 95% of users experience
- **p99**: Worst case for most users
- **Max**: Absolute worst case

Example: If p95 = 500ms, then 95% of requests complete in ≤500ms

### Throughput
- **RPS**: Requests per second
- Higher RPS = better performance
- RPS decreases as response times increase

### Error Rate
- **< 1%**: Acceptable
- **1-2%**: Investigate
- **> 2%**: Critical issue

---

## Version Information

- **Load Testing Suite Version**: 1.0.0
- **Locust Version**: 2.42.5+
- **Python Version**: 3.11+
- **Last Updated**: December 9, 2025

---

## Summary Statistics

- **Total Lines of Code**: ~2,500 lines
- **Total Test Scenarios**: 7 profiles
- **User Types**: 6 different scenarios
- **API Endpoints Covered**: 30+
- **Performance Budgets**: 5 categories
- **Documentation Pages**: 3 (README, Guide, Summary)
- **Analysis Tools**: 1 (analyze_results.py)

---

## Getting More Help

1. **README.md** - Installation and basic usage
2. **LOAD_TESTING_GUIDE.md** - Complete guide with examples
3. Locust documentation: https://docs.locust.io/
4. Check AutoArr logs: `docker logs autoarr-local`
5. Verify API health: `curl http://localhost:8088/health`

---

**Load Testing Suite Status**: ✓ Complete and production-ready
**Date Created**: December 9, 2025
**Maintained By**: AutoArr Team
