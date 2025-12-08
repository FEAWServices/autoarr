# AutoArr Free Version - Open Source Vision

**License**: GNU General Public License v3.0 (GPL-3.0-or-later)
**Philosophy**: Free and open source forever, community-driven development

---

## 🎯 Mission

AutoArr (free version) provides intelligent orchestration for media automation stacks, making configuration management and media requests accessible to everyone through free, open-source software.

## 🌟 Core Principles

1. **Free Forever**: GPL-3.0 ensures AutoArr remains free and open source
2. **Community-Driven**: Development guided by community needs and contributions
3. **Privacy-First**: No telemetry, no data collection, runs entirely on your infrastructure
4. **Local-First**: Works with local LLMs (Ollama), no cloud dependencies required
5. **Transparent**: All code is open, auditable, and modifiable

## 🎁 Free Version Features

### Configuration Intelligence

- **Automated Configuration Auditing**: Scan all connected applications
- **Best Practices Recommendations**: Compare against community standards
- **Local LLM Integration**: Ollama with Qwen, Llama, Mistral support
- **One-Click Application**: Apply recommendations with rollback safety

### Natural Language Interface

- **Content Requests**: Ask for movies/TV shows in plain English
- **Intelligent Classification**: Automatically determine movie vs TV show
- **TMDB Integration**: Rich metadata and search capabilities
- **Direct Integration**: Seamless connection to Sonarr/Radarr

### MCP Integrations

- **SABnzbd**: Queue monitoring and management
- **Sonarr**: TV show automation
- **Radarr**: Movie automation
- **Plex**: Library management (optional)

### Modern Web UI

- **Responsive Design**: Mobile-first, works on all devices
- **Real-Time Updates**: WebSocket-based live status
- **Accessibility**: WCAG 2.1 AA compliant
- **Progressive Web App**: Install as native app

## 🛠️ Technology Stack

**Backend**:

- Python 3.11+ with FastAPI
- SQLite/PostgreSQL
- Ollama for local LLM inference
- MCP (Model Context Protocol)
- WebSocket for real-time updates

**Frontend**:

- React 18 + TypeScript
- Tailwind CSS
- Zustand for state management
- Playwright for E2E testing

**Infrastructure**:

- Docker + Docker Compose
- Single container deployment
- Synology/QNAP support
- Low resource requirements (2GB RAM, 2 CPU cores)

## 🤝 Community Development Model

### How We Work

- **Public Development**: All development happens in the open on GitHub
- **Community Contributions**: Pull requests welcome from anyone
- **Transparent Roadmap**: Public issue tracker and project boards
- **Regular Releases**: Semantic versioning with changelogs
- **Support**: Community Discord, GitHub Discussions, documentation

### Contributing

- **Code Contributions**: Follow TDD, maintain 85%+ test coverage
- **Documentation**: Help improve guides, tutorials, troubleshooting
- **Bug Reports**: Detailed issues help everyone
- **Feature Requests**: Community votes on priorities
- **Translations**: Help make AutoArr accessible worldwide

## 🚀 Roadmap (Free Version)

### Phase 1: Foundation (Completed)

- ✅ MCP server integrations
- ✅ Configuration auditing
- ✅ Basic LLM integration (Claude)
- ✅ Web UI with activity tracking

### Phase 2: Local LLM (In Progress)

- 🔄 Ollama integration with Qwen 2.5
- 🔄 Plugin architecture for LLM providers
- 🔄 Improved prompt templates
- 🔄 Model management utilities

### Phase 3: Enhanced Features (Next)

- 📋 Advanced filtering and search
- 📋 Custom notification systems
- 📋 Backup/restore configurations
- 📋 Multi-user support

### Phase 4: Community Plugins

- 📋 Plugin system for custom integrations
- 📋 Community plugin marketplace
- 📋 Custom theme support
- 📋 Extended API capabilities

## 💻 System Requirements

### Minimum

- 2GB RAM
- 2 CPU cores
- 10GB disk space
- Docker or Docker Compose

### Recommended

- 4GB RAM
- 4 CPU cores
- 20GB disk space (for local LLM models)
- SSD storage

### Ollama Models

- **Qwen 2.5 7B**: ~4GB (recommended)
- **Llama 3.1 8B**: ~4.7GB
- **Mistral 7B**: ~4.1GB

## 🌍 Philosophy: Why GPL-3.0?

We chose GPL-3.0 to ensure AutoArr remains free and open forever:

1. **Copyleft Protection**: Any modifications must also be open source
2. **Community Ownership**: No single entity can close-source AutoArr
3. **Following Leaders**: Sonarr, Radarr, and other \*arr apps use GPL
4. **Trust Through Transparency**: Users can audit all code
5. **Freedom to Fork**: Community can fork if direction changes

## 🔓 Premium Version Note

AutoArr also offers a premium version with advanced AI features and autonomous capabilities. The premium version is **completely optional** - the free version is fully functional and will always remain free.

Premium features include:

- Custom-trained AI models with media domain expertise
- Autonomous download recovery
- Advanced quality cascade optimization
- Priority support

The existence of a premium version helps sustain development of the free version while keeping all core features available to everyone.

**Learn more**: See README.md for details on both versions

## 📞 Get Involved

- **GitHub**: https://github.com/autoarr/autoarr
- **Discord**: https://discord.gg/autoarr
- **Discussions**: https://github.com/autoarr/autoarr/discussions
- **Documentation**: https://docs.autoarr.io

## 🎓 Inspiration

AutoArr builds on the shoulders of giants:

- **Sonarr/Radarr**: Media automation excellence
- **SABnzbd**: Reliable download management
- **Plex**: Beautiful media serving
- **Ollama**: Local LLM inference made easy

We're grateful to these communities for showing what's possible with open source software.

---

**Built by the community, for the community** 🌟

AutoArr is not affiliated with SABnzbd, Sonarr, Radarr, Plex, or Ollama.
