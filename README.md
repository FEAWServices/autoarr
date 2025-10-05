# AutoArr

> **Intelligent cruise control for your *arr media automation stack**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/autoarr/autoarr)
[![GitHub](https://img.shields.io/github/stars/autoarr/autoarr)](https://github.com/autoarr/autoarr)

---

## 🎯 What is AutoArr?

AutoArr is an **intelligent orchestration layer** that sits above your media automation stack (SABnzbd, Sonarr, Radarr, and Plex), providing autonomous configuration optimization, intelligent download recovery, and natural language content requests.

Think of it as **cruise control for your media server** — it continuously monitors your setup, learns best practices, and keeps everything running optimally without manual intervention.

### The Problem We Solve

Managing a *arr media automation stack is **complex and time-consuming**:

- ⚙️ **Configuration Overhead**: Each app has dozens of settings that need constant tuning
- 🔄 **Failed Downloads**: Manual intervention required when downloads fail
- 🎬 **Multiple UIs**: Juggling between different interfaces to request and manage content
- 📚 **Evolving Best Practices**: Keeping up with community recommendations is exhausting
- 🔍 **Maintenance Burden**: Constant monitoring and troubleshooting required

### Our Solution

AutoArr provides three core capabilities:

#### 🧠 **Configuration Intelligence**
- Scans all connected applications and audits their settings
- Compares against latest community best practices
- Uses AI (Claude API or local LLM) to understand context and priorities
- Recommends optimizations with clear explanations
- One-click application with rollback safety

#### 🤖 **Autonomous Recovery**
- Monitors SABnzbd queue in real-time
- Detects failed downloads immediately
- Automatically triggers alternative searches intelligently
- Manages quality fallbacks and wanted lists
- Learns from patterns to prevent future failures

#### 💬 **Natural Language Interface**
- Request content in plain English: *"Add the new Dune movie in 4K"*
- Automatically classifies movies vs. TV shows
- Confirms matches before adding to your library
- Provides real-time status updates
- Tracks request history

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Running instances of: **SABnzbd**, **Sonarr**, **Radarr** (Plex optional)
- API keys for each application

### Installation (Coming Soon)

```bash
# 1. Clone the repository
git clone https://github.com/autoarr/autoarr.git
cd autoarr

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start AutoArr
docker-compose up -d

# 4. Access the dashboard
open http://localhost:3000
```

For detailed setup instructions, see [**docs/QUICK-START.md**](docs/QUICK-START.md).

---

## 📚 Documentation

### **Getting Started**
Start here to understand AutoArr and get it running:

1. [**QUICK-START.md**](docs/QUICK-START.md) - Get up and running in 30 minutes
2. [**PROJECT-SUMMARY.md**](docs/PROJECT-SUMMARY.md) - Executive overview and key decisions

### **Understanding the Vision**
Learn about the product strategy and goals:

3. [**VISION.md**](docs/VISION.md) - Product vision, business model, and roadmap
4. [**NAME-ANALYSIS.md**](docs/NAME-ANALYSIS.md) - Why we chose "AutoArr"

### **Technical Deep Dive**
For developers and those interested in how it works:

5. [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - Complete technical architecture
6. [**BUILD-PLAN.md**](docs/BUILD-PLAN.md) - 20-week development roadmap with TDD
7. [**CODE-EXAMPLES.md**](docs/CODE-EXAMPLES.md) - Starter code and implementation patterns

### **AI/LLM Strategy** (Advanced)
For those interested in the local LLM training approach:

8. [**LLM-TRAINING-STRATEGY.md**](docs/LLM-TRAINING-STRATEGY.md) - Complete local LLM strategy with LangChain
9. [**LLM-IMPLEMENTATION-GUIDE.md**](docs/LLM-IMPLEMENTATION-GUIDE.md) - Code and scripts for training

### **Contributing**
Want to help build AutoArr?

10. [**CONTRIBUTING.md**](docs/CONTRIBUTING.md) - Developer guidelines and workflow

---

## ✨ Key Features

### 🎛️ **Intelligent Configuration Auditing**
- Scans SABnzbd, Sonarr, Radarr, and Plex configurations
- Compares against curated best practices database
- Uses web search to find latest community recommendations
- AI-powered contextual analysis and prioritization
- Tracks configuration history for safe rollbacks

### 🔄 **Automatic Download Recovery**
- Real-time monitoring of SABnzbd queue
- Instant detection of failed downloads
- Intelligent retry strategies (quality fallback, alternative releases)
- Proactive wanted list management
- Detailed activity logging

### 💬 **Natural Language Content Requests**
- Chat-based interface for content requests
- Automatic movie vs. TV show classification
- Smart search with disambiguation
- Integration with Sonarr and Radarr
- Real-time download tracking

### 📊 **Unified Dashboard**
- At-a-glance health monitoring
- Configuration audit results
- Active downloads and queue status
- Recent activity feed
- Mobile-first responsive design

---

## 🏗️ Architecture Overview

AutoArr is built on a **microservices architecture** using the **Model Context Protocol (MCP)** for application integration:

```
┌─────────────────────────────────────────────────┐
│           React UI (Mobile-First)               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          FastAPI Gateway                        │
│         (Authentication, Rate Limiting)         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Core Services                      │
│  • Configuration Manager                        │
│  • Monitoring Service                           │
│  • Request Handler                              │
│  • Intelligence Engine (LLM + RAG)              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│           MCP Orchestrator                      │
│     (Connection Pool, Error Handling)           │
└─────┬────────┬──────────┬──────────┬────────────┘
      │        │          │          │
┌─────▼───┐ ┌─▼────┐ ┌───▼────┐ ┌───▼────┐
│SABnzbd  │ │Sonarr│ │ Radarr │ │  Plex  │
│   MCP   │ │  MCP │ │   MCP  │ │  MCP   │
└─────────┘ └──────┘ └────────┘ └────────┘
```

**Key Design Principles:**
- **Non-invasive**: Uses official APIs through MCP abstraction
- **Intelligent**: LLM-powered reasoning, not just rules
- **Transparent**: All actions logged and reversible
- **Extensible**: Plugin architecture for community extensions
- **Privacy-first**: Runs locally, optional local LLM support

See [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) for complete technical details.

---

## 🛠️ Technology Stack

### **Backend**
- **Python 3.11+** with FastAPI for async performance
- **MCP (Model Context Protocol)** for application integration
- **SQLite** (container) / **PostgreSQL** (SaaS)
- **Claude API** or **Local Llama 3.1** for intelligence

### **Frontend**
- **React 18** + **TypeScript** for type safety
- **Tailwind CSS** for mobile-first responsive design
- **Zustand** for lightweight state management
- **React Query** for data fetching and caching
- **Playwright** for E2E testing

### **Infrastructure**
- **Docker** for containerization
- **GitHub Actions** for CI/CD
- **Prometheus + Grafana** for monitoring
- **Ollama** for local LLM serving

---

## 🗓️ Development Roadmap

### ✅ **Phase 1: Foundation** (Weeks 1-4)
- [x] Project structure and development environment
- [ ] MCP servers for SABnzbd, Sonarr, Radarr, Plex
- [ ] Basic API gateway with health checks
- [ ] MCP orchestrator with connection pooling

### 🚧 **Phase 2: Intelligence** (Weeks 5-8) — **CURRENT**
- [ ] Configuration Manager service
- [ ] Best practices database
- [ ] LLM integration (Claude API)
- [ ] Web search for latest recommendations
- [ ] Configuration audit UI

### 📅 **Phase 3: Monitoring** (Weeks 9-12)
- [ ] Download queue monitoring
- [ ] Automatic failure detection and recovery
- [ ] Activity logging and history
- [ ] Real-time WebSocket updates

### 📅 **Phase 4: Natural Language** (Weeks 13-16)
- [ ] Natural language request parsing
- [ ] Content classification (movie vs. TV)
- [ ] Chat interface with history
- [ ] Request status tracking

### 📅 **Phase 5: Launch** (Weeks 17-20)
- [ ] Comprehensive testing and bug fixes
- [ ] Performance optimization
- [ ] Complete documentation
- [ ] Marketing materials and v1.0 release

**Target:** v1.0 launch in **Q2 2025**

See [**BUILD-PLAN.md**](docs/BUILD-PLAN.md) for detailed sprint planning.

---

## 💡 Why AutoArr?

### **Competitive Landscape**

| Solution | Config Mgmt | Download Recovery | NL Interface | Intelligence |
|----------|-------------|-------------------|--------------|--------------|
| **Manual** | ❌ | ❌ | ❌ | ❌ |
| **Overseerr** | ❌ | ❌ | ❌ | ❌ |
| **Custom Scripts** | ⚠️ | ⚠️ | ❌ | ❌ |
| **AutoArr** | ✅ | ✅ | ✅ | ✅ |

**AutoArr is the only solution** that combines:
- Configuration optimization based on best practices
- Intelligent failure recovery with AI reasoning
- Natural language interface for content requests
- Holistic orchestration across the entire stack

### **Business Model**

**Open Core** approach for community growth and sustainability:

#### **Free Tier** (MIT Licensed)
- Configuration auditing
- Basic download recovery
- REST API access
- Community support

#### **Premium** ($4.99/month)
- Advanced AI recommendations
- Natural language interface
- Priority support
- Cloud configuration sync

#### **Enterprise** (Custom pricing)
- Multi-location support
- Advanced analytics
- Custom integrations
- SLA support

---

## 🤝 Contributing

We welcome contributions! AutoArr is developed using **Test-Driven Development (TDD)** with comprehensive test coverage.

### **Development Setup**

```bash
# 1. Clone and enter repo
git clone https://github.com/autoarr/autoarr.git
cd autoarr

# 2. Start development services (SABnzbd, Sonarr, etc.)
docker-compose -f docker/docker-compose.dev.yml up -d

# 3. Install dependencies
cd api && poetry install && cd ..
cd ui && pnpm install && cd ..

# 4. Run tests
pytest tests/ --cov          # Backend
cd ui && pnpm test           # Frontend
```

### **Development Workflow**
- Follow [Conventional Commits](https://www.conventionalcommits.org/)
- Write tests first (TDD)
- Maintain 85%+ test coverage
- Use Claude Code agents for accelerated development

See [**CONTRIBUTING.md**](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 🎖️ Credits & Acknowledgments

AutoArr is built with amazing open-source technologies:

- [**FastAPI**](https://fastapi.tiangolo.com/) - Modern Python web framework
- [**React**](https://react.dev/) - UI library
- [**MCP**](https://modelcontextprotocol.io/) - Model Context Protocol
- [**Claude**](https://anthropic.com/claude) - AI intelligence
- [**LangChain**](https://python.langchain.com/) - LLM orchestration
- [**Ollama**](https://ollama.com/) - Local LLM serving

Special thanks to the communities behind **SABnzbd**, **Sonarr**, **Radarr**, and **Plex** for building the foundation that makes media automation possible.

---

## 📄 License

AutoArr is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

```
Copyright (c) 2025 AutoArr Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 💬 Community & Support

- 💬 **[Discord](https://discord.gg/autoarr)** - Chat with the community
- 🐛 **[GitHub Issues](https://github.com/autoarr/autoarr/issues)** - Report bugs
- 💡 **[Discussions](https://github.com/autoarr/autoarr/discussions)** - Feature requests and Q&A
- 🐦 **[Twitter](https://twitter.com/autoarr)** - Updates and announcements
- 📧 **hello@autoarr.io** - General inquiries

---

## 🌟 Support the Project

If you find AutoArr useful:

- ⭐ **Star this repository** to show your support
- 🐛 **Report bugs** to help us improve
- 💡 **Suggest features** that would help you
- 📝 **Contribute code or documentation**
- 💰 **Sponsor development** (coming soon)

---

<p align="center">
  <strong>Built with ❤️ by the AutoArr community</strong>
</p>

<p align="center">
  <sub>AutoArr is not affiliated with SABnzbd, Sonarr, Radarr, or Plex.</sub>
</p>
