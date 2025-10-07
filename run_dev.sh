#!/bin/bash
# Local development server script for AutoArr
# Run this in the devcontainer to test the API in your browser

set -e

echo "🚀 Starting AutoArr development server..."

# Set development environment variables
export APP_ENV=development
export LOG_LEVEL=DEBUG
export DATABASE_URL=sqlite:///./data/autoarr.db
export REDIS_URL=memory://
export HOST=0.0.0.0
export PORT=8088

# Create data directory if it doesn't exist
mkdir -p ./data

# Run the FastAPI server with hot reload
echo "📡 API will be available at: http://localhost:8088"
echo "📚 API docs available at: http://localhost:8088/docs"
echo ""

cd /app/autoarr && poetry run uvicorn api.main:app --host 0.0.0.0 --port 8088 --reload
