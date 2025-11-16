#!/bin/bash
# AutoArr Quickstart Script
# Sets up and runs AutoArr for local testing with your existing media services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running from correct directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the AutoArr root directory"
    exit 1
fi

print_header "AutoArr Quickstart"
echo ""

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop first."
    print_info "Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_success "Docker is running"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    print_warning "docker-compose command not found, trying 'docker compose'..."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

print_success "Docker Compose is available"

# Step 2: Environment configuration
print_header "Environment Configuration"

if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    if [ -f ".env.local" ]; then
        print_info "Copying .env.local to .env..."
        cp .env.local .env
        print_success "Created .env file"
        echo ""
        print_warning "IMPORTANT: You MUST edit .env and add your API keys!"
        print_info "Required API keys:"
        echo "  - SABNZBD_API_KEY (from SABnzbd → Settings → General → API Key)"
        echo "  - SONARR_API_KEY (from Sonarr → Settings → General → API Key)"
        echo "  - RADARR_API_KEY (from Radarr → Settings → General → API Key)"
        echo "  - ANTHROPIC_API_KEY (optional, from https://console.anthropic.com/)"
        echo ""
        read -p "Press Enter when you've updated .env with your API keys, or Ctrl+C to exit..."
    else
        print_error ".env.local template not found!"
        exit 1
    fi
else
    print_success ".env file exists"
fi

# Step 3: Create data directories
print_header "Creating Data Directories"

mkdir -p dev-data/data
mkdir -p dev-data/logs

print_success "Data directories created"

# Step 4: Build and start services
print_header "Building and Starting AutoArr"

print_info "This may take a few minutes on first run..."
$COMPOSE_CMD -f docker-compose.dev.yml build

print_info "Starting AutoArr backend..."
$COMPOSE_CMD -f docker-compose.dev.yml up -d

# Step 5: Wait for services to be ready
print_header "Waiting for Services"

print_info "Waiting for AutoArr API to be ready..."
MAX_WAIT=120
WAITED=0
while ! curl -s http://localhost:8088/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        print_error "AutoArr API did not start within $MAX_WAIT seconds"
        print_info "Check logs with: $COMPOSE_CMD -f docker-compose.dev.yml logs"
        exit 1
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done
echo ""

print_success "AutoArr API is running!"

# Step 6: Display access information
print_header "AutoArr is Ready!"

echo ""
print_success "Backend API: http://localhost:8088"
print_success "API Documentation: http://localhost:8088/docs"
print_success "Health Check: http://localhost:8088/health"
echo ""

print_info "To access the frontend UI:"
echo "  cd autoarr/ui"
echo "  pnpm install"
echo "  pnpm dev"
echo "  Then open: http://localhost:3000"
echo ""

print_info "Useful commands:"
echo "  View logs:    $COMPOSE_CMD -f docker-compose.dev.yml logs -f"
echo "  Stop:         $COMPOSE_CMD -f docker-compose.dev.yml down"
echo "  Restart:      $COMPOSE_CMD -f docker-compose.dev.yml restart"
echo "  Rebuild:      $COMPOSE_CMD -f docker-compose.dev.yml build"
echo ""

print_header "Next Steps"
echo ""
echo "1. Verify AutoArr can connect to your services:"
echo "   curl http://localhost:8088/health"
echo ""
echo "2. Check service connections:"
echo "   Open http://localhost:8088/docs and try the /health/services endpoint"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd autoarr/ui && pnpm install && pnpm dev"
echo ""
echo "4. Access the UI at http://localhost:3000 and:"
echo "   - Go to Settings to verify service connections"
echo "   - Go to Dashboard and run a configuration audit"
echo "   - Try the Chat interface for content requests"
echo ""

print_info "For troubleshooting, see: docs/LOCAL_TESTING_GUIDE.md"
echo ""
