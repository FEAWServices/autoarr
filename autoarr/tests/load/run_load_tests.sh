#!/bin/bash

# Copyright (C) 2025 AutoArr Contributors
#
# This file is part of AutoArr.
#
# AutoArr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AutoArr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Load test runner script for AutoArr API
# Runs different load test profiles and generates reports

set -e

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
AUTOARR_URL="${AUTOARR_BASE_URL:-http://localhost:8088}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

check_api() {
    print_info "Checking if AutoArr API is running at $AUTOARR_URL..."

    if curl -s -f "$AUTOARR_URL/health" > /dev/null 2>&1; then
        print_success "AutoArr API is accessible"
        return 0
    else
        print_error "Cannot connect to AutoArr API at $AUTOARR_URL"
        print_info "Please ensure the API is running:"
        print_info "  docker-compose -f docker/docker-compose.local-test.yml up -d"
        print_info "  or"
        print_info "  poetry run uvicorn autoarr.api.main:app --host localhost --port 8088"
        return 1
    fi
}

create_results_dir() {
    mkdir -p "$RESULTS_DIR"
    print_success "Results directory: $RESULTS_DIR"
}

run_baseline() {
    print_header "Running Baseline Load Test"
    print_info "Parameters: 30 users, 5 users/sec spawn rate, 5 minutes"

    poetry run locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host="$AUTOARR_URL" \
        --users=30 \
        --spawn-rate=5 \
        --run-time=5m \
        --headless \
        --csv="$RESULTS_DIR/baseline_${TIMESTAMP}" \
        --loglevel=INFO

    print_success "Baseline test completed"
}

run_normal_load() {
    print_header "Running Normal Load Test"
    print_info "Parameters: 40 users, 5 users/sec spawn rate, 10 minutes"

    poetry run locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host="$AUTOARR_URL" \
        --users=40 \
        --spawn-rate=5 \
        --run-time=10m \
        --headless \
        --csv="$RESULTS_DIR/normal_load_${TIMESTAMP}" \
        --loglevel=INFO

    print_success "Normal load test completed"
}

run_peak_load() {
    print_header "Running Peak Load Test"
    print_info "Parameters: 100 users, 10 users/sec spawn rate, 15 minutes"

    poetry run locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host="$AUTOARR_URL" \
        --users=100 \
        --spawn-rate=10 \
        --run-time=15m \
        --headless \
        --csv="$RESULTS_DIR/peak_load_${TIMESTAMP}" \
        --loglevel=INFO

    print_success "Peak load test completed"
}

run_stress_test() {
    print_header "Running Stress Test"
    print_info "Parameters: 225 users, 10 users/sec spawn rate, 20 minutes"

    poetry run locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host="$AUTOARR_URL" \
        --users=225 \
        --spawn-rate=10 \
        --run-time=20m \
        --headless \
        --csv="$RESULTS_DIR/stress_test_${TIMESTAMP}" \
        --loglevel=INFO

    print_success "Stress test completed"
}

run_spike_test() {
    print_header "Running Spike Test"
    print_info "Parameters: 155 users, 150 users/sec spawn rate (rapid), 10 minutes"

    poetry run locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host="$AUTOARR_URL" \
        --users=155 \
        --spawn-rate=150 \
        --run-time=10m \
        --headless \
        --csv="$RESULTS_DIR/spike_test_${TIMESTAMP}" \
        --loglevel=INFO

    print_success "Spike test completed"
}

run_websocket() {
    print_header "Running WebSocket Load Test"
    print_info "Parameters: 50 WebSocket connections, 8 minutes"

    poetry run locust \
        -f "$SCRIPT_DIR/websocket_load_test.py" \
        --host="$AUTOARR_URL" \
        --users=50 \
        --spawn-rate=5 \
        --run-time=8m \
        --headless \
        --csv="$RESULTS_DIR/websocket_${TIMESTAMP}" \
        --loglevel=INFO

    print_success "WebSocket test completed"
}

run_web_ui() {
    print_header "Running Locust with Web UI"
    print_info "Web UI will be available at http://localhost:8089"
    print_info "Press Ctrl+C to stop"

    poetry run locust \
        -f "$SCRIPT_DIR/locustfile.py" \
        --host="$AUTOARR_URL"
}

generate_summary_report() {
    print_header "Generating Summary Report"

    # Find the most recent test results
    latest_baseline=$(ls -t "$RESULTS_DIR"/baseline_*_stats.csv 2>/dev/null | head -1)
    latest_normal=$(ls -t "$RESULTS_DIR"/normal_load_*_stats.csv 2>/dev/null | head -1)
    latest_peak=$(ls -t "$RESULTS_DIR"/peak_load_*_stats.csv 2>/dev/null | head -1)

    if [ -z "$latest_baseline" ]; then
        print_error "No baseline test results found"
        return 1
    fi

    report_file="$RESULTS_DIR/summary_${TIMESTAMP}.txt"

    {
        echo "AutoArr API Load Test Summary"
        echo "Generated: $(date)"
        echo ""
        echo "API URL: $AUTOARR_URL"
        echo ""
        echo "========================================="
        echo "Baseline Test Results"
        echo "========================================="
        head -10 "$latest_baseline"
        echo ""

        if [ -n "$latest_normal" ]; then
            echo "========================================="
            echo "Normal Load Test Results"
            echo "========================================="
            head -10 "$latest_normal"
            echo ""
        fi

        if [ -n "$latest_peak" ]; then
            echo "========================================="
            echo "Peak Load Test Results"
            echo "========================================="
            head -10 "$latest_peak"
            echo ""
        fi

    } > "$report_file"

    print_success "Summary report created: $report_file"
    cat "$report_file"
}

show_usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    baseline        Run baseline load test (5 min, 30 users)
    normal          Run normal load test (10 min, 40 users)
    peak            Run peak load test (15 min, 100 users)
    stress          Run stress test (20 min, 225 users)
    spike           Run spike test (10 min, rapid ramp)
    websocket       Run WebSocket load test (8 min, 50 connections)
    all             Run all tests sequentially
    ui              Run Locust with web UI
    validate        Validate API is accessible
    summary         Generate summary report from latest tests

Environment Variables:
    AUTOARR_BASE_URL    Base URL for AutoArr API (default: http://localhost:8088)

Examples:
    $0 baseline                          # Run only baseline test
    $0 all                               # Run all tests
    AUTOARR_BASE_URL=http://api:8088 $0 peak  # Custom API URL

Results:
    All test results are saved to: $RESULTS_DIR/

EOF
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    print_header "AutoArr API Load Testing Suite"

    print_info "API URL: $AUTOARR_URL"
    print_info "Results Directory: $RESULTS_DIR"
    print_info "Command: ${1:-all}"

    # Check API is accessible
    if ! check_api; then
        exit 1
    fi

    # Create results directory
    create_results_dir

    # Run requested tests
    case "${1:-all}" in
        baseline)
            run_baseline
            ;;
        normal)
            run_normal_load
            ;;
        peak)
            run_peak_load
            ;;
        stress)
            run_stress_test
            ;;
        spike)
            run_spike_test
            ;;
        websocket)
            run_websocket
            ;;
        ui)
            run_web_ui
            ;;
        all)
            run_baseline
            run_normal_load
            run_peak_load
            run_stress_test
            ;;
        validate)
            print_success "API validation successful"
            ;;
        summary)
            generate_summary_report
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    print_header "Test Execution Complete"
    print_info "Results saved to: $RESULTS_DIR"
    print_success "All requested tests completed"
}

# Run main function
main "$@"
