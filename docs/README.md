# AutoArr

> Intelligent cruise control for your *arr media automation stack

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://img.shields.io/docker/pulls/autoarr/autoarr)](https://hub.docker.com/r/autoarr/autoarr)
[![GitHub Stars](https://img.shields.io/github/stars/autoarr/autoarr)](https://github.com/autoarr/autoarr)
[![Coverage](https://img.shields.io/codecov/c/github/autoarr/autoarr)](https://codecov.io/gh/autoarr/autoarr)

---

## 🎯 What is AutoArr?

AutoArr is an intelligent orchestration layer that sits over your media automation stack (SABnzbd, Sonarr, Radarr, Plex), acting as cruise control for your media server. It automatically optimizes configurations, recovers from failed downloads, and provides a natural language interface for content requests.

### The Problem

Managing a media automation stack is complex:
- ⚙️ Dozens of configuration settings that need optimization
- 🔄 Failed downloads require manual intervention
- 🎬 Multiple UIs to request and manage content
- 📚 Best practices constantly evolving

### The Solution

AutoArr provides:
- 🔍 **Configuration Intelligence**: Audits your setup and recommends optimizations
- 🤖 **Autonomous Recovery**: Automatically retries failed downloads intelligently
- 💬 **Natural Language Interface**: Request content in plain English
- 🚀 **Set & Forget**: Runs continuously, keeping everything optimal

---

## ✨ Features

### 🎛️ Configuration Optimization
- Scans all connected applications (SABnzbd, Sonarr, Radarr, Plex)
- Compares against latest best practices
- Uses AI to recommend optimal settings
- One-click application of recommendations
- Tracks configuration history for rollback

### 🔄 Automatic Download Recovery
- Monitors SABnzbd queue in real-time
- Detects failed downloads immediately
- Automatically searches for alternatives
- Intelligently manages quality fallbacks
- Keeps wanted lists clean

### 💬 Natural Language Content Requests
- "Add the new Dune movie in 4K"
- "Get all seasons of Breaking Bad"
- Automatically determines movie vs. TV show
- Confirms before adding to library
- Real-time status updates

### 📊 Unified Dashboard
- At-a-glance health status
- Configuration recommendations
- Active downloads tracking
- Recent activity feed
- Mobile-first responsive design

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Running instances of: SABnzbd, Sonarr, Radarr (Plex optional)
- API keys for each application

### Installation

1. **Create docker-compose.yml**:

```yaml
version: '3.8'

services:
  autoarr:
    image: autoarr/autoarr:latest
    container_name: autoarr
    ports:
      - "3000:3000"
    environment:
      # Claude API for intelligence features (optional)
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      
      # SABnzbd
      - SABNZBD_URL=http://sabnzbd:8080
      - SABNZBD_API_KEY=${SABNZBD_API_KEY}
      
      # Sonarr
      - SONARR_URL=http://sonarr:8989
      - SONARR_API_KEY=${SONARR_API_KEY}
      
      # Radarr
      - RADARR_URL=http://radarr:7878
      - RADARR_API_KEY=${RADARR_API_KEY}
      
      # Plex (optional)
      - PLEX_URL=http://plex:32400
      - PLEX_TOKEN=${PLEX_TOKEN}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    restart: unless-stopped
```

2. **Create .env file**:

```bash
# Get your API keys from each application
SABNZBD_API_KEY=your_sabnzbd_key
SONARR_API_KEY=your_sonarr_key
RADARR_API_KEY=your_radarr_key
PLEX_TOKEN=your_plex_token
CLAUDE_API_KEY=your_claude_key  # Optional, for AI features
```

3. **Start AutoArr**:

```bash
docker-compose up -d
```

4. **Access the UI**:

Open http://localhost:3000 in your browser.

---

## 📖 Documentation

- [Vision Document](VISION.md) - Product vision and strategy
- [Architecture](ARCHITECTURE.md) - Technical architecture
- [Build Plan](BUILD-PLAN.md) - Development roadmap
- [User Guide](docs/USER-GUIDE.md) - How to use AutoArr
- [API Reference](docs/API.md) - REST API documentation
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history

---

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **MCP**: Model Context Protocol for app integration
- **Database**: SQLite (container) / PostgreSQL (SaaS)
- **Intelligence**: Claude API + local LLM fallback

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Testing**: Playwright
- **Build**: Vite

### Infrastructure
- **Container**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana

---

## 🏗️ Architecture

AutoArr uses a microservices architecture with MCP (Model Context Protocol) as the integration backbone:

```
┌─────────────────┐
│   React UI      │
│  (Mobile-First) │
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI        │
│  API Gateway    │
└────────┬────────┘
         │
┌────────▼────────────────────────┐
│   Core Services                 │
│  • Configuration Manager        │
│  • Monitoring Service          │
│  • Request Handler             │
│  • Intelligence Engine (LLM)   │
└────────┬────────────────────────┘
         │
┌────────▼────────────────────────┐
│   MCP Orchestrator              │
└───┬────┬────┬────┬──────────────┘
    │    │    │    │
┌───▼┐ ┌─▼─┐ ┌▼──┐ ┌▼───┐
│SAB │ │Sonarr│ │Radarr│ │Plex│
│nzbd│ │ MCP│ │ MCP│ │MCP │
└────┘ └────┘ └────┘ └────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

---

## 🤝 Contributing

We welcome contributions! AutoArr is built with Test-Driven Development (TDD) and uses Claude Code agents for accelerated development.

### Development Setup

1. **Clone the repository**:
```bash
git clone https://github.com/autoarr/autoarr.git
cd autoarr
```

2. **Start development environment**:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

3. **Install dependencies**:
```bash
# Backend
cd api && poetry install

# Frontend
cd ui && pnpm install
```

4. **Run tests**:
```bash
# Backend tests
pytest tests/ --cov

# Frontend tests
pnpm test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📋 Roadmap

### ✅ Phase 1: Foundation (Completed)
- [x] MCP server infrastructure
- [x] Basic API gateway
- [x] Development environment

### 🚧 Phase 2: Intelligence (In Progress)
- [x] Configuration auditing
- [x] LLM integration
- [ ] Web search for best practices
- [ ] Configuration UI

### 📅 Phase 3: Monitoring (Planned - Q4 2025)
- [ ] Download queue monitoring
- [ ] Automatic failure recovery
- [ ] Activity logging
- [ ] Real-time WebSocket updates

### 📅 Phase 4: Natural Language (Planned - Q1 2026)
- [ ] Content request parsing
- [ ] Movie vs. TV classification
- [ ] Chat interface
- [ ] Request status tracking

### 📅 Phase 5: Polish (Planned - Q2 2026)
- [ ] Mobile optimization
- [ ] Performance tuning
- [ ] Comprehensive documentation
- [ ] v1.0 release

See [BUILD-PLAN.md](BUILD-PLAN.md) for detailed roadmap.

---

## 💰 Business Model

AutoArr follows an **open-core** model:

### Free (Open Source)
- ✅ Configuration auditing
- ✅ Basic download recovery
- ✅ REST API
- ✅ Community support

### Premium ($4.99/month)
- 🤖 Advanced AI recommendations
- 💬 Natural language interface
- 🔄 Multi-location sync
- 🎯 Priority support

### Enterprise ($49.99/month)
- 🏢 Unlimited locations
- 📊 Advanced analytics
- 🔌 Custom integrations
- 📞 SLA support

See [VISION.md](VISION.md) for business strategy.

---

## 🎖️ Credits

AutoArr is built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [Claude](https://anthropic.com/claude) - AI intelligence
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS

Special thanks to the communities behind SABnzbd, Sonarr, Radarr, and Plex.

---

## 📄 License

AutoArr is licensed under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2025 AutoArr Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=autoarr/autoarr&type=Date)](https://star-history.com/#autoarr/autoarr&Date)

---

## 💬 Community

- 💬 [Discord Server](https://discord.gg/autoarr) - Chat with the community
- 🐛 [GitHub Issues](https://github.com/autoarr/autoarr/issues) - Report bugs
- 💡 [GitHub Discussions](https://github.com/autoarr/autoarr/discussions) - Feature requests
- 🐦 [Twitter](https://twitter.com/autoarr) - Updates and announcements

---

## 🙏 Support

If you find AutoArr useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting features
- 📝 Contributing code or documentation
- 💰 Sponsoring development

---

<p align="center">
  Made with ❤️ by the AutoArr community
</p>

<p align="center">
  <sub>Disclaimer: AutoArr is not affiliated with SABnzbd, Sonarr, Radarr, or Plex.</sub>
</p>
