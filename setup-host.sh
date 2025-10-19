#!/bin/bash
# AutoArr Host Setup Script
# Run this script on your host machine to set up and start AutoArr in Docker

set -e

echo "🚀 Setting up AutoArr for Docker Desktop..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data
mkdir -p logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file..."
    cat > .env << 'EOF'
# AutoArr Environment Configuration
# Basic setup for local testing

# Application Settings
APP_ENV=development
LOG_LEVEL=DEBUG
PORT=8088

# Database (SQLite by default)
DATABASE_URL=sqlite:////data/autoarr.db

# Redis (in-memory by default)
REDIS_URL=memory://

# Media Server Configuration (Optional - leave empty for testing)
# You can configure these later when you connect to actual services
SABNZBD_ENABLED=false
SABNZBD_URL=
SABNZBD_API_KEY=

SONARR_ENABLED=false
SONARR_URL=
SONARR_API_KEY=

RADARR_ENABLED=false
RADARR_URL=
RADARR_API_KEY=

PLEX_ENABLED=false
PLEX_URL=
PLEX_TOKEN=

# AI Features (Optional)
ANTHROPIC_API_KEY=
BRAVE_API_KEY=
EOF
else
    echo "✅ .env file already exists"
fi

# Create docker-compose.yml if it doesn't exist
if [ ! -f docker-compose.yml ]; then
    echo "🐳 Creating docker-compose.yml..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  autoarr:
    build: .
    container_name: autoarr
    restart: unless-stopped
    ports:
      - "8088:8088"
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - APP_ENV=development
      - LOG_LEVEL=DEBUG
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
EOF
else
    echo "✅ docker-compose.yml already exists"
fi

# Build and start the application
echo "🔨 Building AutoArr container..."
docker-compose build

echo "🚀 Starting AutoArr..."
docker-compose up -d

# Wait for the application to start
echo "⏳ Waiting for AutoArr to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:8088/health >/dev/null 2>&1; then
    echo "✅ AutoArr is running successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Main Application: http://localhost:8088"
    echo "   API Documentation: http://localhost:8088/docs"
    echo "   Health Check: http://localhost:8088/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop: docker-compose down"
    echo "   Restart: docker-compose restart"
    echo "   Rebuild: docker-compose down && docker-compose up --build -d"
else
    echo "⚠️  AutoArr may still be starting. Check logs with:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🌐 Try accessing: http://localhost:8088"
fi
