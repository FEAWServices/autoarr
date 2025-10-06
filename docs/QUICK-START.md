# AutoArr Quick Start Guide

This guide will get you from zero to first commit in 30 minutes.

## 🚀 Immediate Next Steps

### 1. Create GitHub Repository (5 minutes)

```bash
# Create the repo on GitHub
# Repository name: autoarr
# Description: Intelligent cruise control for your *arr media automation stack
# Public repository
# Add MIT license
# Add .gitignore for Python and Node.js

# Clone locally
git clone https://github.com/YOUR_USERNAME/autoarr.git
cd autoarr

# Add documentation files
cp /path/to/downloaded/files/*.md .
git add .
git commit -m "docs: add project documentation and vision"
git push origin main

# Create develop branch
git checkout -b develop
git push origin develop
```

### 2. Set Up Project Structure (10 minutes)

```bash
# Create directory structure
mkdir -p api/services api/intelligence api/mcp api/routes api/models api/tests
mkdir -p ui/src/components ui/src/hooks ui/src/services ui/src/store ui/src/types ui/tests
mkdir -p mcp-servers/sabnzbd/tools mcp-servers/sabnzbd/tests
mkdir -p mcp-servers/sonarr/tools mcp-servers/sonarr/tests
mkdir -p mcp-servers/radarr/tools mcp-servers/radarr/tests
mkdir -p mcp-servers/plex/tools mcp-servers/plex/tests
mkdir -p shared/types shared/utils
mkdir -p docs
mkdir -p docker
mkdir -p .github/workflows

# Create placeholder files
touch api/main.py
touch ui/src/App.tsx
touch mcp-servers/sabnzbd/server.py
touch docker/Dockerfile
touch docker/docker-compose.yml
touch docker/docker-compose.dev.yml

# Commit structure
git add .
git commit -m "chore: create initial project structure"
git push origin develop
```

### 3. Initialize Backend (Python) (5 minutes)

```bash
cd api

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "autoarr-api"
version = "0.1.0"
description = "AutoArr API Backend"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.5.0"
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
httpx = "^0.26.0"
anthropic = "^0.8.0"
mcp = "^0.1.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
black = "^24.1.0"
flake8 = "^7.0.0"
mypy = "^1.8.0"
isort = "^5.13.2"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
EOF

# Install dependencies
poetry install

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.env
.env.local
*.db
*.sqlite3
EOF

cd ..
```

### 4. Initialize Frontend (React) (5 minutes)

```bash
cd ui

# Create with Vite
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install -D tailwindcss postcss autoprefixer
npm install zustand @tanstack/react-query
npm install -D @playwright/test
npm install -D eslint prettier eslint-config-prettier

# Initialize Tailwind
npx tailwindcss init -p

# Update tailwind.config.js
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#10B981',
      },
    },
  },
  plugins: [],
}
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
node_modules
dist
.env
.env.local
coverage
.vite
EOF

cd ..
```

### 5. Create Development Environment (5 minutes)

```bash
cd docker

# Create docker-compose.dev.yml
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  sabnzbd:
    image: lscr.io/linuxserver/sabnzbd:latest
    container_name: sabnzbd-test
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    ports:
      - "8080:8080"
    volumes:
      - ./test-data/sabnzbd:/config
      - ./test-data/downloads:/downloads
    restart: unless-stopped

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr-test
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    ports:
      - "8989:8989"
    volumes:
      - ./test-data/sonarr:/config
      - ./test-data/downloads:/downloads
      - ./test-data/tv:/tv
    restart: unless-stopped

  radarr:
    image: lscr.io/linuxserver/radarr:latest
    container_name: radarr-test
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    ports:
      - "7878:7878"
    volumes:
      - ./test-data/radarr:/config
      - ./test-data/downloads:/downloads
      - ./test-data/movies:/movies
    restart: unless-stopped

  plex:
    image: lscr.io/linuxserver/plex:latest
    container_name: plex-test
    environment:
      - PUID=1000
      - PGID=1000
      - VERSION=docker
    ports:
      - "32400:32400"
    volumes:
      - ./test-data/plex:/config
      - ./test-data/tv:/tv
      - ./test-data/movies:/movies
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: autoarr-db
    environment:
      - POSTGRES_DB=autoarr
      - POSTGRES_USER=autoarr
      - POSTGRES_PASSWORD=autoarr
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: autoarr-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres-data:
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Claude API (optional, for AI features)
CLAUDE_API_KEY=

# SABnzbd
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=

# Sonarr
SONARR_URL=http://localhost:8989
SONARR_API_KEY=

# Radarr
RADARR_URL=http://localhost:7878
RADARR_API_KEY=

# Plex (optional)
PLEX_URL=http://localhost:32400
PLEX_TOKEN=

# Database
DATABASE_URL=postgresql://autoarr:autoarr@localhost:5432/autoarr

# Redis
REDIS_URL=redis://localhost:6379
EOF

cd ..
```

## 🎯 First Sprint Goals (Week 1-2)

### Your Immediate Tasks

1. **Day 1: Environment Setup**
   - [ ] Create GitHub repo
   - [ ] Set up local development environment
   - [ ] Start Docker containers: `docker-compose -f docker/docker-compose.dev.yml up -d`
   - [ ] Configure test applications (get API keys)

2. **Day 2-3: SABnzbd MCP Server (TDD)**
   - [ ] Write test for connecting to SABnzbd
   - [ ] Implement connection
   - [ ] Write test for `get_queue` tool
   - [ ] Implement `get_queue`
   - [ ] Write test for `get_history` tool
   - [ ] Implement `get_history`

3. **Day 4-5: Basic API Gateway**
   - [ ] Write test for health endpoint
   - [ ] Implement FastAPI app with health check
   - [ ] Write test for MCP proxy endpoint
   - [ ] Implement basic MCP call proxy

4. **Day 6-7: Basic UI**
   - [ ] Create Dashboard component
   - [ ] Connect to API health endpoint
   - [ ] Display SABnzbd queue status
   - [ ] Add loading/error states

### Using Claude Code for Rapid Development

For each task, you can use Claude Code to accelerate:

```bash
# Example: Create SABnzbd MCP Server with TDD
claude-code implement mcp-server \
  --app=sabnzbd \
  --tools=get_queue,get_history,retry_download \
  --tdd=true \
  --test-framework=pytest \
  --coverage-target=90

# Example: Create Dashboard component
claude-code create component \
  --name=Dashboard \
  --framework=react \
  --typescript=true \
  --test-framework=playwright \
  --mobile-first=true

# Example: Generate API tests
claude-code create tests \
  --target=api/main.py \
  --framework=pytest \
  --include=unit,integration
```

## 🔧 Development Commands

### Backend

```bash
# Start API server
cd api
poetry run uvicorn main:app --reload

# Run tests
poetry run pytest tests/ --cov

# Format code
poetry run black .
poetry run isort .

# Lint
poetry run flake8 .
poetry run mypy .
```

### Frontend

```bash
# Start dev server
cd ui
npm run dev

# Run tests
npm test

# Run E2E tests
npm run test:e2e

# Lint & format
npm run lint
npm run format
```

### Docker

```bash
# Start all services
docker-compose -f docker/docker-compose.dev.yml up -d

# Stop all services
docker-compose -f docker/docker-compose.dev.yml down

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f

# Reset everything
docker-compose -f docker/docker-compose.dev.yml down -v
```

## 📚 Essential Reading Order

1. **VISION.md** - Understand the product vision
2. **ARCHITECTURE.md** - Understand technical approach
3. **BUILD-PLAN.md** - Understand development roadmap
4. **CONTRIBUTING.md** - Understand development workflow

## 🎬 Getting API Keys

### SABnzbd
1. Open http://localhost:8080
2. Complete initial setup wizard
3. Go to Config → General → Security
4. Copy API Key

### Sonarr
1. Open http://localhost:8989
2. Complete initial setup wizard
3. Go to Settings → General → Security
4. Copy API Key

### Radarr
1. Open http://localhost:7878
2. Complete initial setup wizard
3. Go to Settings → General → Security
4. Copy API Key

### Plex (Optional)
1. Open http://localhost:32400/web
2. Log in to Plex account
3. Go to Settings → Account
4. Show Token
5. Copy Token

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] All Docker containers running: `docker-compose ps`
- [ ] Can access SABnzbd: http://localhost:8080
- [ ] Can access Sonarr: http://localhost:8989
- [ ] Can access Radarr: http://localhost:7878
- [ ] Can access Plex: http://localhost:32400
- [ ] Backend tests pass: `pytest tests/`
- [ ] Frontend builds: `npm run build`
- [ ] Git repository connected: `git remote -v`

## 🆘 Common Issues

### Docker containers won't start
```bash
# Check logs
docker-compose -f docker/docker-compose.dev.yml logs sabnzbd

# Remove and recreate
docker-compose -f docker/docker-compose.dev.yml down -v
docker-compose -f docker/docker-compose.dev.yml up -d
```

### Poetry not found
```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### Node modules issues
```bash
cd ui
rm -rf node_modules package-lock.json
npm install
```

## 🎉 You're Ready!

You now have:
- ✅ Complete project documentation
- ✅ Technical architecture defined
- ✅ Development roadmap planned
- ✅ Development environment ready
- ✅ First sprint goals defined

**Next command to run:**

```bash
cd docker
docker-compose -f docker-compose.dev.yml up -d
cd ../api
poetry install
cd ../ui
npm install
```

Then start building! 🚀

---

## 📞 Need Help?

- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [BUILD-PLAN.md](BUILD-PLAN.md) for detailed implementation steps

Good luck building AutoArr! 🎬✨
