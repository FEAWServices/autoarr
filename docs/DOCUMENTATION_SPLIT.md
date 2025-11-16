# Documentation Repository Split

**Date**: 2025-01-23
**Reason**: Preparing AutoArr for open-source release under GPL-3.0

## 📋 Overview

To prepare AutoArr for open-source release, we've split documentation between the free (GPL-3.0) and premium (proprietary) repositories.

## 🆓 Free Repository (/app/docs/)

**What Stays Here:**
- ✅ GPL-3.0 technical documentation
- ✅ Free feature documentation
- ✅ Architecture (non-proprietary aspects)
- ✅ Installation and deployment guides
- ✅ API reference (free endpoints)
- ✅ Contributing guidelines
- ✅ Troubleshooting guides
- ✅ LLM plugin architecture (explains both versions)
- ✅ Test strategies and TDD guides

**Examples:**
- `VISION.md` - Open-source vision and roadmap
- `LLM_PLUGIN_ARCHITECTURE.md` - Plugin system (free + premium interfaces)
- `LICENSE_COMPATIBILITY.md` - GPL compatibility verification
- `ARCHITECTURE.md` - System architecture (non-proprietary)
- `API_REFERENCE.md` - Public API documentation
- `CONTRIBUTING.md` - How to contribute to GPL version

## 💎 Premium Repository (/autoarr-paid/docs/)

**What Moved There:**
- ✅ Business strategy and monetization plans
- ✅ Pricing models and revenue projections
- ✅ Premium feature implementation details
- ✅ Custom model training methodology
- ✅ Autonomous recovery architecture (premium-only)
- ✅ License validation systems
- ✅ SaaS infrastructure designs
- ✅ Customer support workflows
- ✅ Billing integration details

**Examples:**
- `VISION_BUSINESS_MODEL.md` - Pricing, revenue, market strategy
- `CUSTOM_MODEL_TRAINING.md` - Proprietary training pipeline
- `AUTONOMOUS_RECOVERY.md` - Premium recovery system
- `LICENSE_VALIDATION.md` - Anti-piracy measures
- `SAAS_ARCHITECTURE.md` - Multi-tenant infrastructure

## 🔍 Documents Moved

| Document | From (GPL) | To (Premium) | Reason |
|----------|-----------|--------------|---------|
| `VISION.md` | ✅ Replaced | `VISION_BUSINESS_MODEL.md` | Contains pricing, business model, revenue projections |

**Note**: Only the business/proprietary aspects were moved. The free repo now has `VISION.md` focused on GPL development.

## 📝 Documentation Guidelines

### Free Repository (GPL-3.0)
- **License**: All docs are GPL-3.0 compatible
- **Content**: Technical, educational, community-focused
- **Audience**: Public, open-source contributors
- **Transparency**: Everything is auditable and modifiable

### Premium Repository (Proprietary)
- **License**: Proprietary, confidential
- **Content**: Business strategy, proprietary tech, pricing
- **Audience**: Internal team, premium customers (selected docs)
- **Security**: Not for public release

## 🎯 Why This Split?

1. **GPL Compliance**: GPL requires all documentation be open
2. **Business Protection**: Proprietary strategies remain confidential
3. **Clear Separation**: Free contributors don't see premium code/docs
4. **Trust**: Community knows exactly what's open vs closed
5. **Legal Clarity**: No ambiguity about what's GPL vs proprietary

## 🤝 Contributing

### To Free Version
- All documentation welcome
- Must be GPL-3.0 compatible
- Focus on improving free features
- Community-driven priorities

### To Premium Version
- Internal team only
- NDA required
- Proprietary information
- Business-driven priorities

## 📚 Document Types by Repository

### Architecture Documents
- **Free**: High-level architecture, public APIs, plugin systems
- **Premium**: Proprietary algorithms, custom models, license validation

### Feature Documents
- **Free**: Free feature specifications and guides
- **Premium**: Premium-only features (autonomous recovery, custom models)

### API Documentation
- **Free**: Public API endpoints anyone can use
- **Premium**: Premium API endpoints requiring license

### Deployment
- **Free**: Docker deployment, self-hosting guides
- **Premium**: SaaS infrastructure, multi-tenant deployment

## 🔒 Security Note

**Premium documentation contains confidential information and should:**
- ❌ Never be committed to public repos
- ❌ Never be shared without authorization
- ❌ Never be discussed in public channels
- ✅ Be kept in private repository
- ✅ Require team access for viewing
- ✅ Follow information security policies

## 📞 Questions?

- **Free Version Docs**: Open an issue in the public repo
- **Premium Docs**: Contact the internal team

---

This split ensures AutoArr can be fully open-source (GPL-3.0) while protecting proprietary business information. It's a common model used by companies offering both open-source and commercial products (e.g., GitLab, Sentry, Grafana).
