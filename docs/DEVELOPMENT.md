# AutoArr Development Guide

## Quick Start

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git
- Python 3.11+ (for local development)
- Node.js 18+ (for UI development)
- pnpm (for UI package management)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/autoarr/autoarr.git
   cd autoarr
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be ready** (first run takes 2-5 minutes)
   ```bash
   docker-compose logs -f
   ```

5. **Access the applications**
   - AutoArr UI: http://localhost:3000
   - AutoArr API: http://localhost:8000/docs
   - SABnzbd: http://localhost:8080
   - Sonarr: http://localhost:8989
   - Radarr: http://localhost:7878
   - Plex: http://localhost:32400/web

### Configuration

#### SABnzbd Setup
1. Navigate to http://localhost:8080
2. Complete the setup wizard
3. Go to Config > General > API Key
4. Copy the API key to your `.env` file: `SABNZBD_API_KEY=your_key_here`

#### Sonarr Setup
1. Navigate to http://localhost:8989
2. Go to Settings > General
3. Copy the API key to your `.env` file: `SONARR_API_KEY=your_key_here`

#### Radarr Setup
1. Navigate to http://localhost:7878
2. Go to Settings > General
3. Copy the API key to your `.env` file: `RADARR_API_KEY=your_key_here`

#### Plex Setup
1. Navigate to http://localhost:32400/web
2. Sign in with your Plex account
3. Get your token: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
4. Copy the token to your `.env` file: `PLEX_TOKEN=your_token_here`

## Local Development

### Python/API Development

1. **Install Poetry**
   ```bash
   pip install poetry==1.7.1
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Activate virtual environment**
   ```bash
   poetry shell
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Run API locally** (without Docker)
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

### Frontend/UI Development

1. **Navigate to UI directory**
   ```bash
   cd ui
   ```

2. **Install pnpm** (if not already installed)
   ```bash
   npm install -g pnpm
   ```

3. **Install dependencies**
   ```bash
   pnpm install
   ```

4. **Run development server**
   ```bash
   pnpm run dev
   ```

5. **Run tests**
   ```bash
   pnpm run test
   ```

## Testing

### Unit Tests
```bash
# Python tests
pytest tests/unit/ --cov

# Frontend tests
cd ui && pnpm run test:unit
```

### Integration Tests
```bash
# Requires running docker-compose services
pytest tests/integration/ -m integration
```

### E2E Tests
```bash
# Requires running application
cd ui && pnpm run test
```

### Test Coverage
```bash
# Python coverage
pytest tests/ --cov --cov-report=html
open htmlcov/index.html

# Frontend coverage
cd ui && pnpm run test:coverage
```

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Docker Commands

### Start all services
```bash
docker-compose up -d
```

### Stop all services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
```

### Rebuild containers
```bash
docker-compose up -d --build
```

### Reset everything (WARNING: Deletes all data)
```bash
docker-compose down -v
rm -rf docker/
docker-compose up -d
```

## Code Quality

### Run linters
```bash
# Python
black .
flake8 .
mypy api/ mcp-servers/ shared/

# Frontend
cd ui && pnpm run lint
cd ui && pnpm run format
```

### Pre-commit hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Troubleshooting

### Services won't start
1. Check Docker is running: `docker ps`
2. Check logs: `docker-compose logs`
3. Check ports aren't in use: `netstat -an | grep LISTEN`

### Database connection errors
1. Ensure postgres is healthy: `docker-compose ps postgres`
2. Check DATABASE_URL in .env
3. Try resetting: `docker-compose restart postgres`

### API key errors
1. Verify API keys in .env match the applications
2. Restart the API: `docker-compose restart api`

### Port conflicts
Edit `docker-compose.yml` to change port mappings:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001 for host port
```

## Project Structure

```
autoarr/
├── api/                  # FastAPI backend
├── ui/                   # React frontend
├── mcp-servers/          # MCP server implementations
│   ├── sabnzbd/         # SABnzbd MCP server
│   ├── sonarr/          # Sonarr MCP server
│   ├── radarr/          # Radarr MCP server
│   └── plex/            # Plex MCP server
├── shared/               # Shared utilities
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── docker/               # Docker configurations
├── docs/                 # Documentation
├── pyproject.toml        # Python dependencies
└── docker-compose.yml    # Docker orchestration
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE)
