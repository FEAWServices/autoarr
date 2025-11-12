# Documentation Restructure Summary

**Date:** 2025-01-12
**Purpose:** Align documentation with new two-product vision (AutoArr + AutoArrX)

---

## 📋 Changes Made

### 1. New Core Document Created

**`VISION_AND_PRICING.md`** - Comprehensive product vision document
- Clearly separates AutoArr (free/GPL) and AutoArrX (premium)
- Defines 4 premium tiers: Shield, Vault, Phantom, Teams
- Privacy-first architecture details
- Revenue projections and market positioning
- Monorepo strategy for development
- Complete feature comparison matrix

### 2. Documentation Archived

Moved to `/app/docs/archive/`:
- PR_REVIEW_SUMMARY.md (old PR analysis)
- PR_SITUATION_SUMMARY.md (old PR status)
- PROGRESS_SUMMARY.md (outdated progress)
- SPRINT_9_SUMMARY.md (old sprint summary)
- FEATURE_CLARITY.md (replaced by VISION_AND_PRICING.md)
- VISION.md (replaced by VISION_AND_PRICING.md)
- COVERAGE_GAPS.md (outdated test coverage)
- NAME-ANALYSIS.md (historical naming discussion)
- PROJECT-SUMMARY.md (outdated overview)
- DOCKER_BUILD_FIXES.md (temporary fixes)
- PLAYWRIGHT_TEST_FIXES.md (temporary fixes)
- GITHUB_CLI_FIX.md (temporary fixes)
- QUICK-START.md (duplicate, kept QUICK_START.md)
- ideas.md.original (brainstorming notes)

### 3. Core Documents Updated

**`ARCHITECTURE.md`**
- Added reference to VISION_AND_PRICING.md
- Updated design philosophy to include "hybrid architecture"
- Added product structure section (AutoArr vs AutoArrX)
- Expanded summary to cover both free and premium features
- Updated future enhancements section with premium tier breakdown

**`README.md`**
- Added callout box linking to AutoArrX premium features
- Updated "What is AutoArr?" section to mention premium option
- Fixed documentation links (removed archived docs)
- Replaced "No Premium Tiers" section with "Two Products, One Vision"
- Clearly separated free features from premium offerings
- Added key principle about GPL version remaining complete

**`CLAUDE.md`**
- Added two-product strategy section
- Updated documentation list with VISION_AND_PRICING.md
- Noted archived documentation location
- Added AutoArrX limitations to known issues
- Updated deployment section with premium environment variables

---

## 🎯 Key Messaging

### AutoArr (Free/GPL-3.0)
- **100% complete** - no feature limitations
- **Local LLM** (Qwen 2.5-3B) - privacy-first
- **Self-hosted** - no cloud dependencies required
- **GPL-3.0** - free and open source forever
- **Community-driven** - transparent development

### AutoArrX (Premium Cloud)
- **Optional** - AutoArr works perfectly without it
- **Privacy-first** - client-side encryption, we never see your library
- **Smart notifications** - IFTTT/Zapier native integration
- **Advanced AI** - Claude/GPT-4 for complex tasks
- **Predictive** - prevent problems before they happen
- **Multi-instance** - manage multiple servers
- **Family features** - per-user analytics and cost tracking

---

## 📊 Documentation Structure (After Restructure)

```
/app/docs/
├── VISION_AND_PRICING.md          # NEW - Product vision & pricing
├── ARCHITECTURE.md                # UPDATED - Technical architecture
├── README.md                      # UPDATED - Main documentation index
├── BUILD-PLAN.md                  # Development roadmap
├── API_REFERENCE.md               # API documentation
├── QUICK_START.md                 # Installation guide (kept)
├── CONTRIBUTING.md                # Contributor guide
├── TROUBLESHOOTING.md             # Support guide
├── MCP_SERVER_GUIDE.md            # Technical guide
├── LLM_PROVIDER_MIGRATION_GUIDE.md # LLM implementation
├── archive/                       # Obsolete documentation
│   ├── ideas.md.original          # Original brainstorm
│   ├── FEATURE_CLARITY.md         # Old product model
│   ├── VISION.md                  # Old vision doc
│   ├── PR_*.md                    # Old PR analysis
│   └── ...                        # Other archived docs
├── implementation/                # Implementation details
└── testing/                       # Test strategies
```

---

## ✅ Completed Tasks

1. ✅ Created comprehensive VISION_AND_PRICING.md
2. ✅ Archived 14 obsolete documentation files
3. ✅ Updated ARCHITECTURE.md with new vision
4. ✅ Updated README.md with two-product messaging
5. ✅ Updated CLAUDE.md project instructions
6. ✅ Removed duplicate QUICK-START.md (kept QUICK_START.md)

---

## 🔄 Monorepo Strategy

Current approach (development phase):
```
/app/
├── autoarr/              # GPL-3.0 (open source)
├── autoarr_paid/         # Future premium features
│   ├── bridge/
│   ├── cloud_intelligence/
│   ├── notifications/
│   └── privacy/
```

Future split (before public launch):
- **Repository 1:** `autoarr/autoarr` (GPL-3.0, public)
- **Repository 2:** `autoarrx/cloud` (Proprietary, private)

---

## 💡 Key Principles Maintained

1. **GPL remains complete** - No features removed from open source
2. **Privacy-first** - Premium features use client-side encryption
3. **Optional premium** - Core works perfectly standalone
4. **Transparent pricing** - Clear value proposition at each tier
5. **Community trust** - Following Sonarr/Radarr model

---

## 📝 Next Steps

### Documentation
- Consider creating user stories/case studies
- Add architecture diagrams for premium bridge
- Create comparison table with competitors
- Add FAQ section to VISION_AND_PRICING.md

### Development
- Implement monorepo structure (autoarr/ vs autoarr_paid/)
- Add LICENSE.PROPRIETARY for premium code
- Create clear API boundary between GPL and proprietary
- Implement license key validation system

### Marketing
- Create landing page content from VISION_AND_PRICING.md
- Develop pricing calculator tool
- Write blog post announcing two-product strategy
- Create feature comparison infographic

---

_This restructure establishes a clear vision for AutoArr's future while maintaining our 100% open source commitment for the core product._
