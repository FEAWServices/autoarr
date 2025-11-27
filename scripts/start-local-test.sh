#!/bin/bash
# =============================================================================
# Start AutoArr Local Testing Container with Live Reloading
# =============================================================================
# This script starts the local test container with live code reloading.
# It uses the same Docker socket as the devcontainer.
#
# Usage:
#   ./scripts/start-local-test.sh [start|stop|logs|status]
#
# Requirements:
#   - Docker Desktop with docker.sock available
#   - Source code mounted at /app in the devcontainer
# =============================================================================

set -e

DOCKER_COMPOSE_FILE="/app/docker/docker-compose.local-test.yml"
CONTAINER_NAME="autoarr-local-test"

# Set Docker host to use docker.sock
export DOCKER_HOST="unix:///var/run/docker.sock"

# Function to detect the Windows path from the devcontainer mount
detect_source_path() {
    # Check if running in devcontainer by looking for mounted /app
    if mount | grep -q "/app.*9p"; then
        # We're in a devcontainer with Windows bind mount
        # Get the Windows path from the mount options
        MOUNT_INFO=$(cat /proc/mounts | grep " /app ")
        # The mount shows C:\134 which is encoded - just use /app path directly
        # since Docker Desktop can resolve it
        echo "/app"
    else
        # Fallback to relative path
        echo ".."
    fi
}

start() {
    echo "Starting AutoArr local test container..."

    # Build and start
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build

    echo ""
    echo "Container started! Access the app at: http://localhost:8001"
    echo ""
    echo "Commands:"
    echo "  View logs:    $0 logs"
    echo "  Stop:         $0 stop"
    echo "  Status:       $0 status"
}

stop() {
    echo "Stopping AutoArr local test container..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    echo "Container stopped."
}

logs() {
    docker logs -f "$CONTAINER_NAME"
}

status() {
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

restart() {
    stop
    start
}

# Main
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 [start|stop|logs|status|restart]"
        exit 1
        ;;
esac
