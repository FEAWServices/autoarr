# LLM Provider Plugin Architecture

## Overview

AutoArr uses a plugin-based architecture for LLM providers, allowing easy integration of different AI models across both free (GPL) and premium versions.

## Design Principles

1. **Provider Abstraction**: All LLM providers implement a common interface
2. **Configuration-Driven**: Provider selection via environment variables
3. **Fallback Support**: Graceful degradation when providers are unavailable
4. **Async-First**: All operations are asynchronous for performance
5. **Extensible**: Easy to add new providers without modifying core code

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  (configuration_manager, intelligent_recommendation, etc.)  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Provider Factory                      │
│    - Selects provider based on configuration                │
│    - Handles fallback chain                                 │
│    - Manages provider lifecycle                             │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┬──────────────┐
          ▼                             ▼              ▼
┌──────────────────┐         ┌──────────────────┐  ┌─────────────┐
│  ClaudeProvider  │         │  OllamaProvider  │  │   Custom    │
│   (Free/Premium) │         │   (Free only)    │  │  (Premium)  │
└──────────────────┘         └──────────────────┘  └─────────────┘
         │                            │                    │
         └────────────────┬───────────┴────────────────────┘
                          ▼
              ┌────────────────────────┐
              │  BaseLLMProvider       │
              │  (Abstract Interface)  │
              └────────────────────────┘
```

## Core Interface

### BaseLLMProvider (Abstract Base Class)

Location: `/app/autoarr/shared/llm/base_provider.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator
from pydantic import BaseModel

class LLMMessage(BaseModel):
    """Standard message format for all providers."""
    role: str  # "system", "user", "assistant"
    content: str

class LLMResponse(BaseModel):
    """Standard response format for all providers."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name: str = "base"
        self.available_models: List[str] = []

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion for the given messages."""
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion for the given messages."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider."""
        pass

    async def get_models(self) -> List[str]:
        """Get list of available models for this provider."""
        return self.available_models
```

## Provider Implementations

### 1. ClaudeProvider (Free & Premium)

**Location**: `/app/autoarr/shared/llm/claude_provider.py`

**Configuration**:

```env
LLM_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
```

**Features**:

- Full Claude API support (Sonnet, Opus, Haiku)
- Streaming responses
- Function calling support
- Vision capabilities

**Usage**:

```python
provider = ClaudeProvider({
    "api_key": os.getenv("CLAUDE_API_KEY"),
    "default_model": "claude-3-5-sonnet-20241022"
})

response = await provider.complete(messages=[
    LLMMessage(role="user", content="Analyze this configuration...")
])
```

### 2. OllamaProvider (Free Version Only)

**Location**: `/app/autoarr/shared/llm/ollama_provider.py`

**Configuration**:

```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=120
```

**Features**:

- Local model inference
- No API key required
- Supports Qwen, Llama, Mistral, etc.
- Model download/management

**Usage**:

```python
provider = OllamaProvider({
    "base_url": "http://localhost:11434",
    "default_model": "qwen2.5:7b"
})

# Ensure model is downloaded
await provider.ensure_model_available("qwen2.5:7b")

response = await provider.complete(messages=[
    LLMMessage(role="user", content="Classify this content...")
])
```

### 3. CustomModelProvider (Premium Only)

**Location**: `/autoarr-paid/autoarr_premium/shared/llm/custom_model_provider.py`

**Configuration**:

```env
LLM_PROVIDER=custom
CUSTOM_MODEL_PATH=/models/autoarr-premium-v1.0
CUSTOM_MODEL_DEVICE=cuda
CUSTOM_MODEL_QUANTIZATION=4bit
```

**Features**:

- Custom-trained models
- Optimized for media domain
- GPU acceleration support
- Quantization for efficiency

**Usage**:

```python
provider = CustomModelProvider({
    "model_path": "/models/autoarr-premium-v1.0",
    "device": "cuda",
    "quantization": "4bit"
})

response = await provider.complete(messages=[
    LLMMessage(role="user", content="Suggest quality cascade for this title...")
])
```

## LLM Provider Factory

**Location**: `/app/autoarr/shared/llm/provider_factory.py`

```python
from typing import Optional
from .base_provider import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .ollama_provider import OllamaProvider

class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers = {
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a new provider (for premium version)."""
        cls._providers[name] = provider_class

    @classmethod
    async def create_provider(
        cls,
        provider_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLLMProvider:
        """Create a provider instance with fallback logic."""

        # Determine provider order
        providers_to_try = []

        if provider_name:
            providers_to_try.append(provider_name)
        else:
            # Default fallback chain
            providers_to_try = ["ollama", "claude"]

        # Try each provider
        for prov in providers_to_try:
            if prov not in cls._providers:
                continue

            try:
                provider = cls._providers[prov](config or {})
                if await provider.is_available():
                    return provider
            except Exception as e:
                logger.warning(f"Provider {prov} unavailable: {e}")
                continue

        raise ValueError("No LLM providers available")
```

## Configuration System

### Environment Variables

```env
# Provider Selection (free version)
LLM_PROVIDER=ollama  # "ollama" (default) or "claude"

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=120
OLLAMA_AUTO_DOWNLOAD=true

# Claude Configuration (optional)
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096

# Fallback Behavior
LLM_FALLBACK_ENABLED=true
LLM_FALLBACK_ORDER=ollama,claude
```

### Premium Configuration

```env
# Provider Selection (premium version)
LLM_PROVIDER=custom  # "custom", "claude", or "ollama"

# Custom Model Configuration
CUSTOM_MODEL_PATH=/models/autoarr-premium-v1.0
CUSTOM_MODEL_DEVICE=cuda
CUSTOM_MODEL_QUANTIZATION=4bit
CUSTOM_MODEL_CACHE_DIR=/models/cache
```

## Usage in Application Code

### Configuration Manager Example

```python
from autoarr.shared.llm.provider_factory import LLMProviderFactory

class ConfigurationManager:
    def __init__(self):
        self.llm_provider = None

    async def initialize(self):
        """Initialize with automatic provider selection."""
        self.llm_provider = await LLMProviderFactory.create_provider()
        logger.info(f"Using LLM provider: {self.llm_provider.provider_name}")

    async def audit_configuration(self, config: Dict) -> List[Recommendation]:
        """Audit configuration using available LLM provider."""
        messages = [
            LLMMessage(role="system", content=AUDIT_SYSTEM_PROMPT),
            LLMMessage(role="user", content=f"Configuration: {config}")
        ]

        response = await self.llm_provider.complete(
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )

        return self._parse_recommendations(response.content)
```

## Provider Selection Logic

### Free Version (AutoArr)

1. **Default**: Ollama with Qwen 2.5 7B
2. **Fallback**: Claude (if API key provided)
3. **User Choice**: Via `LLM_PROVIDER` env var

### Premium Version (AutoArr Premium)

1. **Default**: Custom trained model
2. **Fallback**: Claude (for complex queries)
3. **User Choice**: Via `LLM_PROVIDER` env var

## Testing Strategy

### Unit Tests

```python
@pytest.fixture
async def mock_provider():
    """Mock LLM provider for testing."""
    class MockProvider(BaseLLMProvider):
        async def complete(self, messages, **kwargs):
            return LLMResponse(
                content="Mock response",
                model="mock-model",
                provider="mock"
            )

        async def is_available(self):
            return True

    return MockProvider({})

async def test_configuration_manager_with_mock(mock_provider):
    """Test configuration manager with mock provider."""
    manager = ConfigurationManager()
    manager.llm_provider = mock_provider

    recommendations = await manager.audit_configuration({"test": "config"})
    assert len(recommendations) > 0
```

### Integration Tests

```python
@pytest.mark.integration
async def test_ollama_provider():
    """Test Ollama provider with real Ollama instance."""
    provider = OllamaProvider({"base_url": "http://localhost:11434"})

    if not await provider.is_available():
        pytest.skip("Ollama not available")

    response = await provider.complete(messages=[
        LLMMessage(role="user", content="Say hello")
    ])

    assert response.content
    assert response.provider == "ollama"
```

## Migration Guide

### Migrating Existing Code

**Before** (Direct Claude usage):

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.getenv("CLAUDE_API_KEY"))
response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**After** (Provider abstraction):

```python
from autoarr.shared.llm.provider_factory import LLMProviderFactory
from autoarr.shared.llm.base_provider import LLMMessage

provider = await LLMProviderFactory.create_provider()
response = await provider.complete(messages=[
    LLMMessage(role="user", content="Hello")
])
```

## Extension Points

### Adding New Providers

1. Create new provider class extending `BaseLLMProvider`
2. Implement required abstract methods
3. Register with factory:
   ```python
   LLMProviderFactory.register_provider("my_provider", MyProvider)
   ```

### Custom Prompt Templates

Providers can override prompt formatting:

```python
class CustomProvider(BaseLLMProvider):
    def format_messages(self, messages: List[LLMMessage]) -> str:
        """Custom message formatting for this provider."""
        return "\n".join([f"{m.role}: {m.content}" for m in messages])
```

## Performance Considerations

- **Caching**: Implement response caching for repeated queries
- **Batching**: Support batch inference where possible
- **Timeouts**: Configure appropriate timeouts per provider
- **Rate Limiting**: Respect API rate limits

## Security Considerations

- **API Keys**: Never log or expose API keys
- **Prompt Injection**: Sanitize user inputs
- **Model Access**: Validate model paths and permissions
- **License Validation**: Verify premium features before use

## Future Enhancements

1. **Multi-Provider Routing**: Route queries to best provider based on complexity
2. **Cost Optimization**: Track and optimize API costs
3. **Quality Monitoring**: Monitor response quality across providers
4. **A/B Testing**: Compare provider performance
5. **Local Model Training**: Tools for fine-tuning local models

---

**Last Updated**: 2025-01-23
**Version**: 1.0
**Status**: ✅ Ready for Implementation
