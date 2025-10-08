# AutoArr Frequently Asked Questions (FAQ)

## General Questions

### What is AutoArr?

AutoArr is an intelligent orchestration platform that sits above your media automation stack (SABnzbd, Sonarr, Radarr, Plex). It provides autonomous configuration optimization, intelligent download recovery, and natural language content requests.

### Why should I use AutoArr?

AutoArr saves time and reduces maintenance burden by:

- Automatically auditing and optimizing configurations
- Recovering failed downloads intelligently
- Providing a unified interface for all your media apps
- Learning from best practices to keep your setup optimal

### Is AutoArr free?

Yes! AutoArr is open-source under the MIT license. You can use it for free forever. We're planning optional premium features for the future.

## Installation & Setup

### What are the system requirements?

**Minimum**:

- Docker & Docker Compose
- 1 GB RAM
- 2 CPU cores
- 1 GB disk space

**Recommended**:

- 2 GB RAM
- 4 CPU cores
- 5 GB disk space

### Do I need to install Python or Node.js?

No! If you use Docker (recommended), everything is included in the container. Python is only needed if you're developing AutoArr.

### Can I run AutoArr on my Synology NAS?

Yes! AutoArr is designed to work great on Synology NAS. See our [Synology Deployment Guide](SYNOLOGY_SETUP.md).

### Does AutoArr work with my existing setup?

Yes! AutoArr integrates with your existing Sonarr, Radarr, SABnzbd, and Plex installations. It doesn't replace them—it enhances them.

## Configuration

### How do I get my API keys?

**SABnzbd**: Config → General → Security → API Key

**Sonarr**: Settings → General → Security → API Key

**Radarr**: Settings → General → Security → API Key

**Plex**: Account → Settings → Show Advanced → Show Token

### Can I use AutoArr with multiple Sonarr/Radarr instances?

Not yet. Multiple instance support is planned for v1.1. Currently, AutoArr supports one instance of each service.

### Do I need Claude API access?

No! Claude API is optional. AutoArr's core features (configuration auditing, download monitoring) work without it. You'll just miss out on AI-powered recommendations.

### Can I use a local LLM instead of Claude?

Yes! Local LLM support is planned for v1.2. You'll be able to use Ollama with Llama 3 or other models.

## Features

### What is configuration auditing?

AutoArr scans your SABnzbd, Sonarr, and Radarr configurations and compares them against community best practices. It then recommends optimizations with clear explanations.

### How does automatic download recovery work?

AutoArr monitors your SABnzbd queue every 2 minutes. When it detects a failed download, it:

1. Analyzes the failure reason
2. Determines the best recovery strategy
3. Automatically triggers a new search or adjusts quality settings
4. Notifies you of the action taken

### Does AutoArr modify my settings without permission?

No! AutoArr never changes settings without your explicit approval. It only recommends changes—you decide whether to apply them.

### Can I roll back configuration changes?

Yes! AutoArr tracks all configuration changes and allows you to roll back to previous versions.

## Privacy & Security

### Does AutoArr send my data anywhere?

By default, no. AutoArr runs entirely locally. The only external calls are:

- To your local apps (SABnzbd, Sonarr, etc.)
- Optional: Claude API (if you configure it)
- Optional: Web search for latest best practices

### Is my API key data secure?

Yes. API keys are:

- Stored encrypted in your database
- Never logged or exposed
- Only used for authenticated API calls

### Does AutoArr log my download activity?

AutoArr logs actions it takes (like "Retried download for Show S01E01") but not specific content details. Logs stay local unless you configure external log shipping.

## Performance

### How much overhead does AutoArr add?

Minimal. AutoArr:

- Uses < 200 MB RAM
- CPU usage is negligible except during audits
- Network overhead is < 1 KB/s

### Will AutoArr slow down my downloads?

No! AutoArr doesn't touch your download traffic. It only interacts with APIs.

### How often does AutoArr poll my services?

- **Health checks**: Every 60 seconds
- **Download queue**: Every 120 seconds
- **Configuration audits**: Only when you trigger them

## Troubleshooting

### AutoArr says my service is "unhealthy"

Check:

1. Is the service running?
2. Is the API key correct?
3. Can you access the service from AutoArr's network?
4. Check firewall rules

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

### Configuration audit returns no recommendations

This means your setup is already optimal! Consider:

1. Enabling web search to find latest recommendations
2. Running the audit again after updating your apps
3. Checking for new best practices in the community

### Failed downloads aren't being retried

Check:

1. Is download monitoring enabled? (`ENABLE_DOWNLOAD_MONITORING=true`)
2. Is auto-retry enabled? (`ENABLE_AUTO_RETRY=true`)
3. Check circuit breaker status for SABnzbd
4. View logs for error messages

## Development

### How can I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development environment setup
- Coding standards
- Pull request process
- Using Claude Code for development

### Can I create custom integrations?

Yes! See [MCP_SERVER_GUIDE.md](MCP_SERVER_GUIDE.md) to learn how to create MCP servers for new applications.

### Where can I report bugs?

Open an issue on GitHub: https://github.com/autoarr/autoarr/issues

Please include:

- AutoArr version
- Environment (Docker, bare metal, Synology)
- Steps to reproduce
- Relevant logs

## Roadmap

### What features are planned?

See our [BUILD-PLAN.md](BUILD-PLAN.md) for the complete roadmap. Highlights:

**v1.1** (Q1 2025):

- Natural language content requests
- WebSocket real-time updates
- Mobile-optimized UI

**v1.2** (Q2 2025):

- Local LLM support
- Plugin system
- Advanced analytics

**v2.0** (Q3 2025):

- SaaS option
- Multi-instance support
- Enterprise features

### Will there be a mobile app?

Yes! A Progressive Web App (PWA) is planned for v1.1, followed by native iOS/Android apps in v1.3.

### Will AutoArr support Lidarr/Readarr?

Yes! Additional \*arr integrations are planned for v1.3+. We're prioritizing based on community demand.

## Business Model

### How will AutoArr make money?

AutoArr follows an **Open Core** model:

**Free** (MIT License):

- Configuration auditing
- Download monitoring
- REST API
- Self-hosted deployment

**Premium** ($4.99/month, planned):

- Advanced AI features
- Cloud configuration sync
- Priority support
- Analytics dashboard

**Enterprise** (Custom pricing):

- Multi-location support
- SLA support
- Custom integrations
- Dedicated support

### Will features be removed from the free version?

No! Everything currently free will remain free forever. Premium features are _additions_, not subtractions.

## Getting Help

### Where can I get support?

- **Documentation**: Check our comprehensive docs first
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Discord** (coming soon): Chat with the community

### How do I report a security issue?

See [SECURITY.md](SECURITY.md) for our security policy and responsible disclosure process.

---

**Don't see your question?** Ask on [GitHub Discussions](https://github.com/autoarr/autoarr/discussions).
