#!/bin/bash
# Start AutoArr development container with hot-reload support
# This script provides an easy way to run the app in Docker with mounted files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╭─────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│   AutoArr Development Container Setup    │${NC}"
echo -e "${BLUE}╰─────────────────────────────────────────╯${NC}"
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists (for API keys)
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating template...${NC}"
    cat > "$PROJECT_ROOT/.env.example.dev" << 'EOF'
# AutoArr Development Configuration

# Service API Keys (optional for dev)
SABNZBD_API_KEY=your_key_here
SONARR_API_KEY=your_key_here
RADARR_API_KEY=your_key_here
PLEX_TOKEN=your_token_here

# AI Features (optional)
ANTHROPIC_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here

# GitHub (optional)
GITHUB_ADMIN_TOKEN=your_token_here
GH_TOKEN=your_token_here

# Database (PostgreSQL optional)
POSTGRES_PASSWORD=autoarr

# Git Configuration
GIT_NAME="Your Name"
GIT_EMAIL="your.email@example.com"
EOF
    echo -e "${YELLOW}  Created .env.example.dev - copy to .env and add your keys${NC}"
    echo ""
fi

# Show options
echo -e "${BLUE}Options:${NC}"
echo "  1) Start simple container (fastest startup)"
echo "  2) Start with Redis and PostgreSQL"
echo "  3) Stop container"
echo "  4) Remove container and volumes"
echo "  5) View logs"
echo "  6) Open shell in container"
echo ""

read -p "Choose option [1-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}Starting AutoArr dev container (simple)...${NC}"
        cd "$SCRIPT_DIR"
        docker-compose -f docker-compose.dev-simple.yml up -d autoarr-dev
        sleep 3
        echo ""
        echo -e "${GREEN}✓ Container started!${NC}"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "  1. Open a new terminal and run:"
        echo "     docker exec -it autoarr-dev /bin/bash"
        echo ""
        echo "  2. Inside the container, run one of:"
        echo "     • Backend:  poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload"
        echo "     • Frontend: cd autoarr/ui && pnpm dev"
        echo "     • Both:     ./run_dev.sh (if available)"
        echo ""
        echo -e "${BLUE}Access the app:${NC}"
        echo "  • API:        http://localhost:8088"
        echo "  • API Docs:   http://localhost:8088/docs"
        echo "  • UI:         http://localhost:3000"
        echo ""
        echo -e "${BLUE}Useful commands:${NC}"
        echo "  • View logs:       docker logs -f autoarr-dev"
        echo "  • Stop container:  docker-compose -f docker/docker-compose.dev.yml down"
        echo "  • Clean up:        docker-compose -f docker/docker-compose.dev.yml down -v"
        ;;

    2)
        echo -e "${GREEN}Starting AutoArr with Redis and PostgreSQL...${NC}"
        cd "$SCRIPT_DIR"
        docker-compose -f docker-compose.dev.yml up -d
        sleep 5
        echo ""
        echo -e "${GREEN}✓ All services started!${NC}"
        echo ""
        echo -e "${BLUE}Services running:${NC}"
        docker-compose -f docker-compose.dev.yml ps
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "  1. Open a new terminal and run:"
        echo "     docker exec -it autoarr-dev /bin/bash"
        echo ""
        echo "  2. Inside the container, run one of:"
        echo "     • Backend:  poetry run python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload"
        echo "     • Frontend: cd autoarr/ui && pnpm dev"
        echo ""
        echo -e "${BLUE}Access the app:${NC}"
        echo "  • API:         http://localhost:8088"
        echo "  • UI:          http://localhost:3000"
        echo "  • Redis:       localhost:6379"
        echo "  • PostgreSQL:  localhost:5432 (user: autoarr)"
        echo ""
        echo -e "${BLUE}Useful commands:${NC}"
        echo "  • View logs:       docker logs -f autoarr-dev"
        echo "  • Stop services:   docker-compose -f docker/docker-compose.dev.yml down"
        echo "  • Clean up:        docker-compose -f docker/docker-compose.dev.yml down -v"
        ;;

    3)
        echo -e "${YELLOW}Stopping AutoArr dev container...${NC}"
        cd "$SCRIPT_DIR"
        # Stop whichever compose file is running
        if docker ps | grep -q autoarr-dev; then
            docker-compose down
        fi
        echo -e "${GREEN}✓ Container stopped${NC}"
        ;;

    4)
        echo -e "${RED}⚠ This will remove the container and all volumes${NC}"
        read -p "Are you sure? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            cd "$SCRIPT_DIR"
            docker-compose down -v
            echo -e "${GREEN}✓ Container and volumes removed${NC}"
        else
            echo "Cancelled"
        fi
        ;;

    5)
        docker logs -f autoarr-dev
        ;;

    6)
        echo -e "${GREEN}Opening shell in container...${NC}"
        docker exec -it autoarr-dev /bin/bash
        ;;

    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
