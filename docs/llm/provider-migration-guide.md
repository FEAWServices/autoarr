# LLM Provider Migration Guide

## 📋 Overview

This guide explains how to migrate AutoArr services from direct Claude API usage to the new pluggable LLM provider system.

**Status**: Foundation Complete ✅ | Service Migrations In Progress 🔄

## ✅ What's Complete

### Plugin Architecture (100%)

- ✅ `BaseLLMProvider` abstract interface
- ✅ `LLMProviderFactory` with fallback support
- ✅ `OllamaProvider` (340 lines, full featured)
- ✅ `ClaudeProvider` (240 lines, migrated from ClaudeClient)
- ✅ Documentation (`LLM_PLUGIN_ARCHITECTURE.md`, 450 lines)

### Configuration

- ✅ Environment-based provider selection
- ✅ Automatic fallback chain (Ollama → Claude)
- ✅ Lazy initialization
- ✅ Health checks and diagnostics

## 🔄 Migration Steps

### Step 1: Update Imports

**Before:**

```python
from anthropic import AsyncAnthropic
from autoarr.api.services.llm_agent import ClaudeClient
```

**After:**

```python
from autoarr.shared.llm import LLMProviderFactory, LLMMessage, BaseLLMProvider
```

### Step 2: Initialize Provider

**Before:**

```python
client = ClaudeClient(
    api_key=api_key,
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096
)
```

**After:**

```python
# Auto-select provider (Ollama by default, Claude if API key set)
provider = await LLMProviderFactory.create_provider()

# Or specific provider
provider = await LLMProviderFactory.create_provider(
    provider_name="claude",  # or "ollama"
    config={"api_key": api_key}
)
```

### Step 3: Convert Messages

**Before:**

```python
response = await client.send_message(
    system_prompt="You are an expert...",
    user_message="Analyze this config...",
    temperature=0.7
)
content = response["content"]
usage = response["usage"]
```

**After:**

```python
messages = [
    LLMMessage(role="system", content="You are an expert..."),
    LLMMessage(role="user", content="Analyze this config...")
]

response = await provider.complete(
    messages=messages,
    temperature=0.7,
    max_tokens=4096
)

content = response.content
usage = response.usage  # {"prompt_tokens": N, "completion_tokens": M, "total_tokens": N+M}
```

### Step 4: Handle Streaming (Optional)

**Before:**

```python
# Not supported in old ClaudeClient
```

**After:**

```python
async for chunk in provider.stream_complete(messages=messages):
    print(chunk, end="", flush=True)
```

## 📝 Service Migration Status

### 1. llm_agent.py (In Progress)

**Files:**

- Original: `/app/autoarr/api/services/llm_agent.py` (627 lines)
- Backup: `/app/autoarr/api/services/llm_agent.py.backup`
- Updated template: `/app/autoarr/api/services/llm_agent_updated.py`

**Classes to Migrate:**

- ✅ `ClaudeClient` → **REMOVE** (replaced by `ClaudeProvider` in shared/llm/)
- ⏭️ `PromptTemplate` → **KEEP AS-IS**
- ⏭️ `StructuredOutputParser` → **KEEP AS-IS**
- ⏭️ `TokenUsageTracker` → **KEEP AS-IS**
- ⏭️ `LLMRecommendation` → **KEEP AS-IS**
- 🔄 `LLMAgent` → **UPDATE** to use `LLMProviderFactory`

**Changes Required:**

1. Remove `ClaudeClient` class (lines 41-142)
2. Update imports (remove `anthropic`, add `autoarr.shared.llm`)
3. Update `LLMAgent.__init__()` to use `LLMProviderFactory`
4. Update `analyze_configuration()` to use provider.complete()
5. Update `classify_content_request()` to use provider.complete()
6. Adapt response handling (`.content` instead of `["content"]`)
7. Add backward compatibility for `api_key` parameter

**Example LLMAgent Update:**

```python
class LLMAgent:
    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        api_key: Optional[str] = None,  # Backward compat
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ):
        self._provider = provider
        self._api_key = api_key
        self.max_tokens = max_tokens
        # ... rest of init

    async def _ensure_provider(self):
        """Lazy init provider."""
        if self._provider is None:
            if self._api_key:
                # Use Claude if API key provided
                config = {"api_key": self._api_key}
                self._provider = await LLMProviderFactory.create_provider(
                    provider_name="claude",
                    config=config
                )
            else:
                # Auto-select (Ollama by default)
                self._provider = await LLMProviderFactory.create_provider()
        return self._provider

    async def analyze_configuration(self, context):
        provider = await self._ensure_provider()

        # Build messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message)
        ]

        # Call provider
        response = await provider.complete(messages=messages, temperature=0.7)

        # Use response.content instead of response["content"]
        # ...
```

### 2. configuration_manager.py

**Current Status**: Uses `intelligent_recommendation_engine.py` which uses `llm_agent.py`

**Migration Path**:

1. Update `llm_agent.py` first (see above)
2. `configuration_manager.py` should work without changes (uses high-level API)
3. Verify in integration tests

### 3. request_handler.py

**Current Status**: Uses `llm_agent.py` for content classification

**Migration Path**:

1. Update `llm_agent.py` first
2. `request_handler.py` should work without changes
3. Test classification with both Ollama and Claude

### 4. intelligent_recommendation_engine.py

**Current Status**: Uses `llm_agent.py`

**Migration Path**:

1. Update `llm_agent.py` first
2. Should work without changes (uses `LLMAgent` high-level API)

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/unit/services/test_llm_agent_provider.py

import pytest
from autoarr.api.services.llm_agent import LLMAgent
from autoarr.shared.llm import LLMMessage

@pytest.mark.asyncio
async def test_llm_agent_with_ollama(mock_ollama_provider):
    """Test LLMAgent with Ollama provider."""
    agent = LLMAgent(provider=mock_ollama_provider)

    context = {
        "app": "sonarr",
        "current_config": {"quality": "HD"},
        "best_practice": {"quality": "4K"}
    }

    result = await agent.analyze_configuration(context)
    assert result.priority in ["high", "medium", "low"]

@pytest.mark.asyncio
async def test_llm_agent_backward_compat():
    """Test backward compatibility with API key."""
    agent = LLMAgent(api_key="sk-test-123")
    # Should initialize Claude provider
    provider = await agent._ensure_provider()
    assert provider.provider_name == "claude"
```

### Integration Tests

```python
# tests/integration/services/test_llm_provider_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_real_inference():
    """Test with real Ollama instance."""
    if not ollama_available():
        pytest.skip("Ollama not available")

    agent = LLMAgent()  # Will auto-select Ollama

    result = await agent.classify_content_request("Breaking Bad")
    assert result["content_type"] in ["movie", "tv"]
```

## 🔧 Environment Configuration

### Free Version (Ollama Default)

```env
# Ollama (default)
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_AUTO_DOWNLOAD=true

# Optional Claude fallback
CLAUDE_API_KEY=sk-ant-xxx  # Optional
LLM_FALLBACK_ENABLED=true
```

### With Claude

```env
# Use Claude as primary
LLM_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Ollama as fallback
LLM_FALLBACK_ENABLED=true
LLM_FALLBACK_ORDER=claude,ollama
```

## ⚠️ Breaking Changes

### For External Users

None - The high-level APIs (`LLMAgent.analyze_configuration()`, etc.) remain the same.

### For Internal Code

- `ClaudeClient` class removed - use `ClaudeProvider` from `autoarr.shared.llm`
- Direct anthropic imports should be replaced with provider abstractions
- Response format changed:
  - Old: `response["content"]`, `response["usage"]`
  - New: `response.content`, `response.usage`

## 📊 Migration Checklist

### Phase 1: Foundation (COMPLETE ✅)

- [x] Create `BaseLLMProvider` interface
- [x] Implement `OllamaProvider`
- [x] Implement `ClaudeProvider`
- [x] Create `LLMProviderFactory`
- [x] Write documentation

### Phase 2: Service Migration (IN PROGRESS 🔄)

- [x] Backup `llm_agent.py`
- [ ] Update `llm_agent.py` imports
- [ ] Remove `ClaudeClient` class
- [ ] Update `LLMAgent` class
- [ ] Test `llm_agent.py` changes
- [ ] Verify `configuration_manager.py` still works
- [ ] Verify `request_handler.py` still works
- [ ] Verify `intelligent_recommendation_engine.py` still works

### Phase 3: Testing (PENDING ⏳)

- [ ] Write unit tests for providers
- [ ] Write integration tests with real Ollama
- [ ] Write integration tests with real Claude
- [ ] Update existing tests
- [ ] Test fallback mechanisms
- [ ] Test error handling

### Phase 4: Documentation (PENDING ⏳)

- [ ] Update API documentation
- [ ] Update deployment guides
- [ ] Create migration guide for contributors
- [ ] Update troubleshooting guide

## 🚀 Next Steps

1. **Complete llm_agent.py migration** (Current task)
2. **Run test suite** to verify no regressions
3. **Test with real Ollama** instance
4. **Update deployment docs** with Ollama setup
5. **Create Docker image** with Ollama + Qwen bundled

## 📞 Questions or Issues?

- **Documentation**: `/app/docs/LLM_PLUGIN_ARCHITECTURE.md`
- **Example**: `/app/autoarr/api/services/llm_agent_updated.py`
- **Providers**: `/app/autoarr/shared/llm/`

---

**Last Updated**: 2025-01-23
**Status**: Foundation Complete, Service Migrations In Progress
**Progress**: ~60% of Sequence 2 complete
