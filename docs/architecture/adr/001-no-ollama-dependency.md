# ADR-001: Use Direct llama-cpp-python Instead of Ollama

**Date:** 2025-01-12
**Status:** Accepted
**Deciders:** AutoArr Core Team
**Technical Story:** Local LLM Integration for AutoArr GPL Version

---

## Context and Problem Statement

AutoArr (GPL version) requires local LLM capabilities to provide intelligent configuration analysis, natural language content requests, and autonomous decision-making without cloud dependencies. We need to decide how to integrate and run local LLM models (specifically Qwen 2.5-3B quantized).

The key requirements are:

- Simple single-container deployment
- Minimal resource overhead
- Easy model distribution
- No additional services to manage
- Works on NAS devices (Synology, QNAP, etc.)

## Decision Drivers

- **Simplicity**: Users want "docker run" and be done
- **Resource Efficiency**: Target devices have 4-8GB RAM total
- **Deployment Size**: Docker images should be reasonable (<5GB)
- **Reliability**: Fewer moving parts = fewer failure points
- **User Experience**: No separate service management

## Considered Options

### Option 1: Ollama (Service-Based Approach)

**Architecture:**

```
┌─────────────┐     ┌──────────────┐
│  AutoArr    │────▶│   Ollama     │
│  Container  │     │   Service    │
└─────────────┘     └──────────────┘
```

**Pros:**

- ✅ Nice API for model management
- ✅ Easy model switching
- ✅ Community familiar with Ollama
- ✅ Built-in model caching

**Cons:**

- ❌ **Separate service required** (2 containers or host service)
- ❌ **Network dependency** (HTTP API calls add latency)
- ❌ **Resource overhead** (~1GB RAM for Ollama service itself)
- ❌ **Complexity** for users (need to configure Ollama separately)
- ❌ **Port management** (exposing Ollama port 11434)
- ❌ **Docker-in-docker** issues on some NAS devices
- ❌ **Extra failure point** (Ollama service could crash independently)

**Example User Setup:**

```yaml
version: "3.8"
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  autoarr:
    image: autoarr/autoarr:latest
    depends_on:
      - ollama
    environment:
      - OLLAMA_URL=http://ollama:11434
```

❌ **Two containers to manage**, more complexity

### Option 2: llama-cpp-python (Direct Integration) ✅ CHOSEN

**Architecture:**

```
┌─────────────────────────────────┐
│     AutoArr Container           │
│                                 │
│  ┌──────────────────────────┐  │
│  │  FastAPI App             │  │
│  │  ┌──────────────────┐    │  │
│  │  │  llama-cpp-python│    │  │
│  │  │  (embedded)      │    │  │
│  │  └──────────────────┘    │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

**Pros:**

- ✅ **Single container** - simplest deployment
- ✅ **No network overhead** - direct Python API
- ✅ **Lower resource usage** (no separate service)
- ✅ **Easier distribution** - model bundled or auto-downloaded
- ✅ **Fewer failure points** - one service to monitor
- ✅ **Better for NAS** - single Docker container
- ✅ **Faster inference** - no HTTP serialization overhead

**Cons:**

- ❌ Less flexible model switching (requires restart)
- ❌ No centralized model cache across apps
- ⚠️ Model baked into image or downloaded on first run

**Example User Setup:**

```yaml
version: "3.8"
services:
  autoarr:
    image: autoarr/autoarr:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
```

✅ **One container**, that's it!

### Option 3: Cloud LLM APIs (Claude/GPT-4)

**Pros:**

- ✅ Most powerful models
- ✅ No local compute needed

**Cons:**

- ❌ **Violates GPL privacy-first promise**
- ❌ Requires API keys (complexity)
- ❌ Ongoing costs for users
- ❌ Doesn't work offline
- ❌ Rate limits

**Decision:** Rejected for GPL version (available in AutoArrX premium)

---

## Decision Outcome

**Chosen option:** "llama-cpp-python Direct Integration" (Option 2)

### Positive Consequences

- ✅ **Dramatically simpler** user experience: just `docker run`
- ✅ **Lower total memory** footprint (~3GB vs ~4GB with Ollama)
- ✅ **Faster inference** (no HTTP round-trip serialization)
- ✅ **Better NAS compatibility** (single container is key)
- ✅ **Easier testing** and development
- ✅ **More reliable** (fewer services = fewer failures)
- ✅ **Cleaner logs** (one service's logs, not two)

### Negative Consequences

- ❌ **Model switching** requires container restart (acceptable trade-off)
- ❌ **Cannot share models** across multiple apps (minimal impact - AutoArr is standalone)
- ⚠️ **Image size** slightly larger (model bundled or auto-downloaded)

### Mitigation Strategies

**For Model Distribution:**

1. **Option A (Chosen):** Auto-download on first run

   ```python
   # Download model if not present
   if not os.path.exists(MODEL_PATH):
       download_model(MODEL_URL, MODEL_PATH)
   ```

2. **Option B:** Bake into Docker image (adds ~2.5GB)
   ```dockerfile
   RUN curl -L -o /models/qwen2.5-3b.gguf https://...
   ```

**Decision:** Use Option A (auto-download) to keep base image smaller

**For Model Switching (if needed later):**

- Expose `MODEL_PATH` environment variable
- Support hot-reloading of model (reload without restart)
- Document how to mount custom models via volume

---

## Implementation Details

### Integration Code

```python
# autoarr/api/services/llm_service.py
from llama_cpp import Llama
import os

class LocalLLMService:
    def __init__(self):
        model_path = os.getenv("MODEL_PATH", "/models/qwen2.5-3b-instruct-q4_k_m.gguf")

        # Auto-download if not present
        if not os.path.exists(model_path):
            self._download_model(model_path)

        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,  # CPU only
            verbose=False
        )

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            stop=["</s>"]
        )
        return response["choices"][0]["text"]
```

### Docker Configuration

```dockerfile
FROM python:3.11-slim

# Install llama-cpp-python (with CPU optimizations)
RUN pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# Create model directory
RUN mkdir -p /models

# Model will be auto-downloaded on first run
VOLUME ["/models"]

# ... rest of Dockerfile
```

### Environment Variables

```bash
# Optional: Specify custom model
MODEL_PATH=/models/custom-model.gguf

# Optional: Model URL for auto-download
MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-3B-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
```

---

## Comparison Table

| Aspect                    | Ollama                   | llama-cpp-python        | Cloud API            |
| ------------------------- | ------------------------ | ----------------------- | -------------------- |
| **Deployment Complexity** | ❌ Medium (2 containers) | ✅ Simple (1 container) | ⚠️ Medium (API keys) |
| **Resource Overhead**     | ❌ ~4GB RAM              | ✅ ~3GB RAM             | ✅ ~200MB            |
| **Network Latency**       | ⚠️ HTTP calls            | ✅ Direct               | ❌ Internet          |
| **Offline Support**       | ✅ Yes                   | ✅ Yes                  | ❌ No                |
| **NAS Compatibility**     | ⚠️ Fair                  | ✅ Excellent            | ✅ Yes               |
| **Model Switching**       | ✅ Easy                  | ⚠️ Restart required     | ✅ Easy              |
| **Privacy**               | ✅ Local                 | ✅ Local                | ❌ Cloud             |
| **Cost**                  | ✅ Free                  | ✅ Free                 | ❌ $20-50/mo         |
| **Setup Steps**           | 3-4 steps                | 1 step                  | 2 steps              |
| **Failure Points**        | 2 services               | 1 service               | Internet + API       |

**Winner:** llama-cpp-python for AutoArr GPL use case

---

## Alternatives for AutoArrX (Premium)

For users who want more power and are willing to sacrifice privacy:

1. **Cloud LLM** (Claude 3.5 Sonnet, GPT-4)
   - Available in AutoArrX Vault tier ($9.99/mo)
   - Privacy preserved via client-side encryption
   - Used for complex analysis only

2. **Larger Local Models** (Optional)
   - Qwen 2.5-7B or 14B for power users
   - GPU acceleration support
   - Premium feature: auto-detect GPU and use optimal model

---

## References

- [llama-cpp-python Documentation](https://github.com/abetlen/llama-cpp-python)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Qwen 2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
- [AutoArr Architecture](../ARCHITECTURE.md)
- [AutoArr Vision & Pricing](../VISION_AND_PRICING.md)

---

## Decision Log

| Date       | Change                             | Reason                                     |
| ---------- | ---------------------------------- | ------------------------------------------ |
| 2025-01-12 | Initial decision: llama-cpp-python | Simplicity and single-container deployment |

---

_This ADR follows the [MADR format](https://adr.github.io/madr/) for architecture decision records._
