# AutoArr Feature Clarity

**Last Updated:** 2025-01-12
**Status:** Official Project Direction

---

## Open Source First

**AutoArr is 100% open source (GPL-3.0)** - just like Sonarr and Radarr.

There is NO premium tier, NO subscription requirement, NO license keys. Everything in this repository is free and open source forever.

---

## Product Model

AutoArr follows the **same model as Sonarr and Radarr**:

```
┌─────────────────────────────────────────────────────────┐
│              AutoArr (GPL-3.0 Open Source)              │
│                                                          │
│  ✅ Full configuration intelligence                     │
│  ✅ Natural language requests (local LLM)               │
│  ✅ Automatic download monitoring                        │
│  ✅ Intelligent retry strategies                         │
│  ✅ All service integrations                             │
│  ✅ Activity tracking and logs                           │
│  ✅ Beautiful web UI                                     │
│  ✅ Self-hosted, no external dependencies               │
│                                                          │
│  100% Free Forever - Community Driven                    │
└─────────────────────────────────────────────────────────┘
```

---

## Premium Services (Future - Undefined)

There **may** be optional premium services in the future that provide:

- Advanced cloud-based AI models
- Enhanced MCP coordination services
- Premium support channels

**But these are:**

- Not yet designed or implemented
- Completely optional add-ons
- Not required for any core functionality
- Not documented because they don't exist yet

**The base AutoArr will always be fully functional and open source.**

---

## Architecture: Integrated Single Container

AutoArr uses a **simple, integrated architecture** (not complex microservices):

```
┌────────────────────────────────────────────────────────────┐
│                   AutoArr Container                        │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                      │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │  Local LLM (Qwen 2.5-3B Quantized)             │ │ │
│  │  │  - Natural language understanding                │ │ │
│  │  │  - Content classification                        │ │ │
│  │  │  - Decision making                               │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │  Service Integrations                           │ │ │
│  │  │  - Radarr API Client                            │ │ │
│  │  │  - Sonarr API Client                            │ │ │
│  │  │  - SABnzbd API Client                           │ │ │
│  │  │  - Plex API Client                              │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │  Core Services                                  │ │ │
│  │  │  - Configuration Manager                        │ │ │
│  │  │  - Monitoring Service                           │ │ │
│  │  │  - Recovery Service                             │ │ │
│  │  │  - Activity Logger                              │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │  SQLite Database                                │ │ │
│  │  │  - Configuration history                        │ │ │
│  │  │  - Activity logs                                │ │ │
│  │  │  - Request tracking                             │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              React Web UI                            │ │
│  │  - Dashboard                                         │ │
│  │  - Chat Interface                                    │ │
│  │  │  - Configuration Audit                            │ │
│  │  - Activity Feed                                     │ │
│  │  - Settings                                          │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
             ▼          ▼          ▼          ▼
        ┌────────┐ ┌────────┐ ┌─────────┐ ┌──────┐
        │ Radarr │ │ Sonarr │ │ SABnzbd │ │ Plex │
        └────────┘ └────────┘ └─────────┘ └──────┘
```

**Key Design Principles:**

- **Single container** - Easy deployment, low resource usage
- **Direct API integration** - No complex MCP protocol overhead
- **Local LLM** - Privacy-first, no external dependencies
- **Integrated services** - Shared resources, efficient memory usage
- **Self-contained** - Everything needed in one place

---

## No MCP Protocol Requirement

**Previous documentation mentioned MCP (Model Context Protocol) extensively.**

**Current reality:**

- MCP is **not required** for core functionality
- Direct API integration with Sonarr/Radarr/SABnzbd/Plex is simpler and more reliable
- MCP may be used internally for optional features, but it's not a user-facing requirement

**If you see references to "MCP servers" in old docs, they're outdated.**

---

## LLM: Local and Private

AutoArr uses **Qwen 2.5-3B** (quantized) running locally:

```python
# Integrated LLM - no external API calls
llm = Llama(
    model_path="/app/models/qwen2.5-3b-instruct-q4_k_m.gguf",
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=0  # CPU only for NAS compatibility
)
```

**Benefits:**

- ✅ **Privacy** - Nothing leaves your server
- ✅ **No API costs** - No Claude/OpenAI subscription needed
- ✅ **Fast** - Local inference, no network latency
- ✅ **Reliable** - No external service dependencies
- ✅ **Efficient** - Quantized model uses ~3GB RAM

**Performance:**

- Content classification: ~200ms
- Natural language parsing: ~500ms
- Configuration analysis: ~1-2s

---

## Resource Requirements

**Minimum:**

- 4GB RAM (2GB for app, 2GB for LLM)
- 2 CPU cores
- 10GB disk space

**Recommended:**

- 8GB RAM
- 4 CPU cores
- 20GB disk space

**Perfect for:**

- Synology NAS (DS920+, DS1520+, etc.)
- Raspberry Pi 4 (8GB model)
- Any x86 Linux server
- Docker-capable NAS devices

---

## Feature Roadmap

All features are **open source and free**:

### Phase 1: Foundation ✅ (Complete)

- Service API integrations
- Basic configuration management
- Web UI framework

### Phase 2: Intelligence 🚧 (In Progress)

- Configuration auditing
- Best practices database
- Recommendation engine

### Phase 3: Automation 📅 (Next)

- Download monitoring
- Automatic retry logic
- Failure pattern recognition

### Phase 4: Natural Language 📅 (Next)

- Chat interface
- Content requests ("Add Inception in 4K")
- Smart classification (movie vs TV)

### Phase 5: Polish 📅 (Future)

- Enhanced UI/UX
- Mobile app
- Advanced analytics

---

## Contributing

AutoArr is community-driven open source:

- 🐛 **Report bugs** - Help us improve
- 💡 **Suggest features** - Tell us what you need
- 🔧 **Submit PRs** - Code contributions welcome
- 📖 **Improve docs** - Documentation is always needed
- ⭐ **Star the repo** - Show your support

**No premium features to worry about** - everything you build benefits everyone.

---

## Comparison to Similar Projects

| Project     | License     | Model                |
| ----------- | ----------- | -------------------- |
| **Sonarr**  | GPL-3.0     | 100% open source     |
| **Radarr**  | GPL-3.0     | 100% open source     |
| **AutoArr** | GPL-3.0     | **100% open source** |
| Overseerr   | MIT         | 100% open source     |
| Plex        | Proprietary | Freemium (Plex Pass) |

**AutoArr follows the Sonarr/Radarr model** - trusted, transparent, community-first.

---

## Questions?

**Q: Will features be locked behind a paywall?**
A: No. AutoArr is fully open source like Sonarr and Radarr.

**Q: Do I need a Claude/OpenAI API key?**
A: No. AutoArr uses a local LLM (Qwen 2.5-3B).

**Q: Is there a premium version?**
A: Not currently. Future optional premium services are undefined and not required.

**Q: Can I self-host everything?**
A: Yes! That's the entire point. Single container, no external dependencies.

**Q: Will this work on my Synology NAS?**
A: Yes! Optimized for NAS devices with limited resources.

**Q: What about MCP servers mentioned in docs?**
A: Old documentation. Current design uses direct API integration (simpler).

---

## Summary

**AutoArr is:**

- ✅ 100% open source (GPL-3.0)
- ✅ Self-hosted, single container
- ✅ Local LLM, no external APIs
- ✅ Free forever, no subscriptions
- ✅ Community-driven development

**AutoArr is NOT:**

- ❌ Freemium with premium features
- ❌ Requiring external API subscriptions
- ❌ Using complex MCP protocol
- ❌ Dependent on cloud services

**Build with confidence** - everything you create benefits the entire community.

---

**For the latest architecture and build instructions, see:**

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [BUILD-PLAN.md](./BUILD-PLAN.md) - Development roadmap
- [CONTRIBUTING.md](./CONTRIBUTING.md) - How to contribute
