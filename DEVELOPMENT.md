# AutoArr Development Guide

## 🚀 Quick Start

### Running Locally in DevContainer

**Start Backend API:**

```bash
./run_dev.sh
```

- API: http://localhost:8088
- API Docs: http://localhost:8088/docs
- Health Check: http://localhost:8088/health

**Start Frontend (separate terminal):**

```bash
cd ui
pnpm install  # First time only
pnpm run dev
```

- Frontend: http://localhost:3000
- Auto-proxies API calls to port 8088

### Full Stack Running

With both running, you have:

- **Frontend UI**: http://localhost:3000 with hot reload
- **Backend API**: http://localhost:8088 with hot reload
- **API Docs**: http://localhost:8088/docs (Swagger UI)

## 📁 Project Structure

```
autoarr/
├── api/                      # FastAPI backend
│   ├── main.py              # Main app entry point
│   ├── config.py            # Settings configuration
│   ├── dependencies.py      # Dependency injection
│   ├── middleware.py        # Custom middleware
│   ├── models.py            # Pydantic models
│   └── routers/             # API endpoints
│       ├── health.py        # Health checks
│       ├── settings.py      # Settings API
│       ├── downloads.py     # SABnzbd integration
│       ├── shows.py         # Sonarr integration
│       ├── movies.py        # Radarr integration
│       └── media.py         # Plex integration
│
├── ui/                       # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   │   ├── SplashScreen.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── pages/           # Page components
│   │   │   ├── Home.tsx     # Chat interface
│   │   │   ├── Settings.tsx # Settings page
│   │   │   └── Placeholder.tsx
│   │   ├── layouts/         # Layout components
│   │   │   └── MainLayout.tsx
│   │   ├── App.tsx          # Main app component
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Global styles
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── mcp-servers/             # MCP server implementations
│   └── mcp_servers/
│       ├── sabnzbd/         # SABnzbd client
│       ├── sonarr/          # Sonarr client
│       ├── radarr/          # Radarr client
│       └── plex/            # Plex client
│
├── shared/                   # Shared code
│   └── core/
│       ├── mcp_orchestrator.py
│       └── config.py
│
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
│
├── .github/workflows/        # CI/CD workflows
│   ├── ci.yml               # Test & lint
│   └── docker-publish.yml   # Build & publish Docker
│
├── Dockerfile               # Production Docker image
├── docker-compose.yml       # Development compose
├── docker-compose.prod.yml  # Production compose
├── docker-compose.synology.yml  # Synology deployment
├── run_dev.sh              # Dev server script
└── pyproject.toml          # Python dependencies
```

## 🎨 Frontend Architecture

### Tech Stack

- **React 18** with TypeScript
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Vite** for build tooling
- **Tanstack Query** for API state management
- **Zustand** for client state (if needed)
- **Lucide React** for icons

### Key Features

#### 1. Splash Screen

Beautiful animated splash screen shown on initial load (like Sonarr/Radarr).

#### 2. Sidebar Navigation

- Fixed left sidebar with app logo
- Navigation links for all sections
- Active state highlighting
- Status indicator at bottom

#### 3. Settings Page

- Service configuration for SABnzbd, Sonarr, Radarr, Plex
- Show/hide API keys with eye icon
- Test connection buttons
- Save settings to backend
- AI & Search configuration (Anthropic, Brave)
- Application settings (log level, timezone)

#### 4. Home Page (Chat Interface)

- AI assistant chat interface
- Message input with send button
- Suggested prompts for getting started
- Placeholder for future LLM integration

#### 5. Placeholder Pages

- Downloads, Shows, Movies, Media, Activity
- Coming soon indicators
- Consistent layout

### Styling Conventions

**Colors:**

- Background: `bg-gray-950` (darkest)
- Cards/Panels: `bg-gray-800` / `bg-gray-900`
- Borders: `border-gray-700` / `border-gray-800`
- Text: `text-white` / `text-gray-400`
- Primary: `bg-indigo-600` / `text-indigo-500`
- Accent: `bg-purple-600`

**Layout:**

- Use Flexbox and Grid
- Mobile-first responsive design
- Consistent padding: `p-6` for cards, `p-8` for pages
- Rounded corners: `rounded-lg` / `rounded-2xl`

## 🔧 Backend Architecture

### FastAPI Application

**Main Components:**

- **Settings**: Pydantic Settings with env var loading
- **Middleware**: CORS, error handling, request logging, security headers
- **Dependencies**: Orchestrator injection
- **Routers**: Modular endpoint organization

### API Endpoints

**Settings API (`/api/v1/settings`)**

- `GET /` - Get all service configurations
- `GET /{service}` - Get specific service config
- `POST /` - Save all settings at once
- `PUT /{service}` - Update specific service
- `POST /test/{service}` - Test connection without saving
- `POST /save-to-env` - Persist to .env file

**Health API (`/health`)**

- `GET /health` - Overall system health
- `GET /health/{service}` - Specific service health
- `GET /health/circuit-breaker/{service}` - Circuit breaker status

### Configuration

All settings are managed through `api/config.py` using Pydantic Settings.

**Environment Variables:**

```bash
# Services
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=...
SONARR_URL=http://localhost:8989
SONARR_API_KEY=...
RADARR_URL=http://localhost:7878
RADARR_API_KEY=...
PLEX_URL=http://localhost:32400
PLEX_TOKEN=...

# AI (optional)
ANTHROPIC_API_KEY=...
BRAVE_API_KEY=...

# App
APP_ENV=development
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./data/autoarr.db
REDIS_URL=memory://
```

## 🧪 Testing

### Backend Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov

# Specific test file
poetry run pytest tests/unit/api/test_settings.py

# Watch mode (requires pytest-watch)
poetry run ptw
```

### Frontend Tests

```bash
cd ui

# Unit tests (Vitest - TODO)
pnpm run test:unit

# E2E tests (Playwright)
pnpm run test

# E2E tests with UI
pnpm run test:ui
```

### Linting & Formatting

**Backend:**

```bash
# Format code
poetry run black .

# Lint
poetry run flake8 api/ mcp-servers/mcp_servers/ shared/

# Type check
poetry run mypy api/ mcp-servers/mcp_servers/ shared/

# All checks (pre-commit)
poetry run pre-commit run --all-files
```

**Frontend:**

```bash
cd ui

# Lint
pnpm run lint

# Format
pnpm run format

# Format check
pnpm run format --check
```

## 📦 Building

### Frontend Build

```bash
cd ui
pnpm run build
# Output: ui/dist/
```

### Docker Build

```bash
# Single container (frontend + backend)
docker build -t autoarr:latest .

# Run locally
docker run -p 8088:8088 -v ./data:/data autoarr:latest
```

## 🐛 Debugging

### Backend Debugging

- Logs go to stdout/stderr
- Set `LOG_LEVEL=DEBUG` for verbose logging
- Use `breakpoint()` for pdb debugging
- FastAPI auto-reload on code changes

### Frontend Debugging

- React DevTools browser extension
- Vite HMR (Hot Module Replacement)
- Check browser console for errors
- Network tab for API calls

### Common Issues

**Port already in use:**

```bash
# Find process using port 8088
lsof -i :8088
kill -9 <PID>
```

**Frontend can't connect to API:**

- Check Vite proxy config in `vite.config.ts`
- Ensure API is running on port 8088
- Check browser console for CORS errors

**Settings not saving:**

- Check API logs for errors
- Verify permissions on data directory
- Try `/api/v1/settings` endpoint directly in browser/Postman

## 🚢 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.

See [docs/SYNOLOGY_DEPLOYMENT.md](docs/SYNOLOGY_DEPLOYMENT.md) for Synology NAS deployment.

## 📚 Additional Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vite Docs](https://vitejs.dev/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/autoarr/issues)
- **Documentation**: Check `docs/` folder
- **API Docs**: http://localhost:8088/docs (when running)
