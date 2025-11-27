#!/bin/bash
# AutoArr Setup Verification Script
# Checks if your environment is properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Track overall status
ERRORS=0
WARNINGS=0

print_header "AutoArr Setup Verification"
echo ""

# Check .env file exists
print_info "Checking environment configuration..."

if [ ! -f ".env" ]; then
    print_error ".env file not found"
    print_info "Run: cp .env.local .env"
    ERRORS=$((ERRORS + 1))
else
    print_success ".env file exists"

    # Source .env file
    source .env

    # Check required variables
    if [ -z "$SABNZBD_API_KEY" ] || [ "$SABNZBD_API_KEY" = "your_actual_sabnzbd_api_key_here" ]; then
        print_warning "SABNZBD_API_KEY not configured"
        WARNINGS=$((WARNINGS + 1))
    else
        print_success "SABnzbd API key configured"
    fi

    if [ -z "$SONARR_API_KEY" ] || [ "$SONARR_API_KEY" = "your_actual_sonarr_api_key_here" ]; then
        print_warning "SONARR_API_KEY not configured"
        WARNINGS=$((WARNINGS + 1))
    else
        print_success "Sonarr API key configured"
    fi

    if [ -z "$RADARR_API_KEY" ] || [ "$RADARR_API_KEY" = "your_actual_radarr_api_key_here" ]; then
        print_warning "RADARR_API_KEY not configured"
        WARNINGS=$((WARNINGS + 1))
    else
        print_success "Radarr API key configured"
    fi
fi

echo ""
print_header "Testing Service Connectivity"
echo ""

# Test SABnzbd
if [ ! -z "$SABNZBD_URL" ] && [ ! -z "$SABNZBD_API_KEY" ] && [ "$SABNZBD_API_KEY" != "your_actual_sabnzbd_api_key_here" ]; then
    print_info "Testing SABnzbd at $SABNZBD_URL..."
    if curl -f -s "$SABNZBD_URL/api?mode=version&apikey=$SABNZBD_API_KEY" > /dev/null 2>&1; then
        print_success "SABnzbd connection successful"
    else
        print_error "Cannot connect to SABnzbd"
        print_info "Check URL and API key, ensure SABnzbd is running"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_warning "Skipping SABnzbd test (not configured)"
fi

# Test Sonarr
if [ ! -z "$SONARR_URL" ] && [ ! -z "$SONARR_API_KEY" ] && [ "$SONARR_API_KEY" != "your_actual_sonarr_api_key_here" ]; then
    print_info "Testing Sonarr at $SONARR_URL..."
    if curl -f -s -H "X-Api-Key: $SONARR_API_KEY" "$SONARR_URL/api/v3/system/status" > /dev/null 2>&1; then
        print_success "Sonarr connection successful"
    else
        print_error "Cannot connect to Sonarr"
        print_info "Check URL and API key, ensure Sonarr is running"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_warning "Skipping Sonarr test (not configured)"
fi

# Test Radarr
if [ ! -z "$RADARR_URL" ] && [ ! -z "$RADARR_API_KEY" ] && [ "$RADARR_API_KEY" != "your_actual_radarr_api_key_here" ]; then
    print_info "Testing Radarr at $RADARR_URL..."
    if curl -f -s -H "X-Api-Key: $RADARR_API_KEY" "$RADARR_URL/api/v3/system/status" > /dev/null 2>&1; then
        print_success "Radarr connection successful"
    else
        print_error "Cannot connect to Radarr"
        print_info "Check URL and API key, ensure Radarr is running"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_warning "Skipping Radarr test (not configured)"
fi

# Test Plex (optional)
if [ "$PLEX_ENABLED" = "true" ] && [ ! -z "$PLEX_URL" ] && [ ! -z "$PLEX_TOKEN" ]; then
    print_info "Testing Plex at $PLEX_URL..."
    if curl -f -s -H "X-Plex-Token: $PLEX_TOKEN" "$PLEX_URL/identity" > /dev/null 2>&1; then
        print_success "Plex connection successful"
    else
        print_warning "Cannot connect to Plex (optional)"
        print_info "Check URL and token, ensure Plex is running"
    fi
else
    print_info "Plex integration disabled (optional)"
fi

echo ""
print_header "Checking Dependencies"
echo ""

# Check Docker
print_info "Checking Docker..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker running (version $DOCKER_VERSION)"
    else
        print_error "Docker is installed but not running"
        print_info "Start Docker Desktop"
        ERRORS=$((ERRORS + 1))
    fi
else
    print_error "Docker not found"
    print_info "Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    ERRORS=$((ERRORS + 1))
fi

# Check Node.js
print_info "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js installed ($NODE_VERSION)"
else
    print_warning "Node.js not found (required for frontend)"
    print_info "Install Node.js 20+: https://nodejs.org/"
    WARNINGS=$((WARNINGS + 1))
fi

# Check pnpm
print_info "Checking pnpm..."
if command -v pnpm &> /dev/null; then
    PNPM_VERSION=$(pnpm --version)
    print_success "pnpm installed ($PNPM_VERSION)"
else
    print_warning "pnpm not found (required for frontend)"
    print_info "Install pnpm: npm install -g pnpm"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
print_header "Summary"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    print_success "All checks passed! You're ready to start AutoArr."
    echo ""
    print_info "Next step: ./scripts/quickstart.sh"
elif [ $ERRORS -eq 0 ]; then
    print_warning "$WARNINGS warning(s) found, but you can proceed"
    echo ""
    print_info "Next step: ./scripts/quickstart.sh"
else
    print_error "$ERRORS error(s) found. Please fix the issues above."
    echo ""
    print_info "See docs/LOCAL_TESTING_GUIDE.md for help"
    exit 1
fi

echo ""
