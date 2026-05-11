# Phase 1: LLM Provider Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the monolithic `LLMClient` with a multi-provider abstraction layer supporting OpenAI, Anthropic, and Gemini APIs, with runtime provider management.

**Architecture:** Abstract `LLMProvider` base class with concrete implementations per API format. `LLMRegistry` manages multiple providers, tracks the active one, and is the single entry point for all LLM consumers. DI container registers `LLMRegistry` instead of `LLMClient`.

**Tech Stack:** Python `requests`, `abc`, Pydantic v2, FastAPI

**Spec:** `docs/superpowers/specs/2026-05-11-modular-refactor-design.md` Section 1

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `server/llm/__init__.py` | Package init, exports |
| Create | `server/llm/base.py` | `LLMProvider` abstract base class |
| Create | `server/llm/openai_provider.py` | OpenAI-compatible provider (current LLMClient logic) |
| Create | `server/llm/anthropic_provider.py` | Anthropic Claude provider |
| Create | `server/llm/gemini_provider.py` | Google Gemini provider |
| Create | `server/llm/registry.py` | Multi-provider management |
| Create | `tests/test_llm_providers.py` | Tests for providers + registry |
| Modify | `server/di/container.py` | Register `LLMRegistry` instead of `LLMClient` |
| Modify | `server/host_dm.py` | Use `registry.get_active()` instead of `self.llm` |
| Modify | `server/api/config.py` | New provider management API |
| Modify | `server/api/__init__.py` | Import renamed router |
| Modify | `tests/conftest.py` | Update DI registration |
| Delete | `server/llm_client.py` | Replaced by provider layer |

---

### Task 1: LLMProvider Abstract Base

**Files:**
- Create: `server/llm/__init__.py`
- Create: `server/llm/base.py`
- Create: `tests/test_llm_providers.py`

- [ ] **Step 1: Create package and base class**

```python
# server/llm/__init__.py
from server.llm.base import LLMProvider
from server.llm.registry import LLMRegistry

__all__ = ["LLMProvider", "LLMRegistry"]
```

```python
# server/llm/base.py
from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    """Abstract base for LLM API providers."""

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    def chat(self, messages: list[dict], temperature: float = 0.7, timeout: int = 120) -> str:
        """Send chat messages, return assistant response text."""

    @abstractmethod
    def chat_stream(self, messages: list[dict], temperature: float = 0.7) -> Generator[str, None, None]:
        """Send chat messages, yield response chunks."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Fetch available model IDs from the provider."""

    @abstractmethod
    def test_connection(self) -> str:
        """Quick connection test, returns response text."""

    def get_config(self) -> dict:
        """Return provider config summary (subclasses may override to add fields)."""
        return {
            "name": self.name,
            "type": self.provider_type,
            "model": self.model,
        }

    @property
    def provider_type(self) -> str:
        return self.__class__.__name__.replace("Provider", "").lower()
```

- [ ] **Step 2: Write test for base class**

```python
# tests/test_llm_providers.py
import pytest
from server.llm.base import LLMProvider


class StubProvider(LLMProvider):
    """Stub for testing abstract interface."""
    def __init__(self, name="stub", model="stub-model"):
        super().__init__(name, model)

    def chat(self, messages, temperature=0.7, timeout=120):
        return "stub response"

    def chat_stream(self, messages, temperature=0.7):
        yield "stub "
        yield "chunk"

    def list_models(self):
        return ["stub-model"]

    def test_connection(self):
        return "OK"


def test_provider_type():
    p = StubProvider()
    assert p.provider_type == "stub"


def test_provider_get_config():
    p = StubProvider("test", "model-1")
    config = p.get_config()
    assert config["name"] == "test"
    assert config["type"] == "stub"
    assert config["model"] == "model-1"


def test_provider_chat():
    p = StubProvider()
    result = p.chat([{"role": "user", "content": "hi"}])
    assert result == "stub response"


def test_provider_chat_stream():
    p = StubProvider()
    chunks = list(p.chat_stream([{"role": "user", "content": "hi"}]))
    assert chunks == ["stub ", "chunk"]


def test_cannot_instantiate_base():
    with pytest.raises(TypeError):
        LLMProvider("x", "y")
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_llm_providers.py -v`
Expected: 5 passed

- [ ] **Step 4: Commit**

```bash
git add server/llm/__init__.py server/llm/base.py tests/test_llm_providers.py
git commit -m "feat(llm): add LLMProvider abstract base class"
```

---

### Task 2: OpenAI Provider

**Files:**
- Create: `server/llm/openai_provider.py`
- Modify: `tests/test_llm_providers.py`

- [ ] **Step 1: Write tests for OpenAI provider**

Append to `tests/test_llm_providers.py`:

```python
import json
from unittest.mock import patch, MagicMock
from server.llm.openai_provider import OpenAIProvider


def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


@patch("server.llm.openai_provider.requests.post")
def test_openai_chat(mock_post):
    mock_post.return_value = _mock_response(200, {
        "choices": [{"message": {"content": "Hello!"}}]
    })
    provider = OpenAIProvider("test-openai", "http://localhost:12340", "gpt-4", "sk-test")
    result = provider.chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello!"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "v1/chat/completions" in call_kwargs[0][0] or "v1/chat/completions" in str(call_kwargs)


@patch("server.llm.openai_provider.requests.post")
def test_openai_chat_stream(mock_post):
    lines = [
        b'data: {"choices":[{"delta":{"content":"Hi"}}]}',
        b'data: {"choices":[{"delta":{"content":" there"}}]}',
        b'data: [DONE]',
    ]
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.iter_lines.return_value = lines
    mock_post.return_value = resp

    provider = OpenAIProvider("test", "http://localhost:12340", "gpt-4", "sk-test")
    chunks = list(provider.chat_stream([{"role": "user", "content": "Hi"}]))
    assert chunks == ["Hi", " there"]


@patch("server.llm.openai_provider.requests.get")
def test_openai_list_models(mock_get):
    mock_get.return_value = _mock_response(200, {
        "data": [{"id": "gpt-4"}, {"id": "gpt-3.5-turbo"}]
    })
    provider = OpenAIProvider("test", "http://localhost:12340", "gpt-4", "sk-test")
    models = provider.list_models()
    assert models == ["gpt-4", "gpt-3.5-turbo"]


@patch("server.llm.openai_provider.requests.post")
def test_openai_test_connection(mock_post):
    mock_post.return_value = _mock_response(200, {
        "choices": [{"message": {"content": "Connection OK"}}]
    })
    provider = OpenAIProvider("test", "http://localhost:12340", "gpt-4", "sk-test")
    result = provider.test_connection()
    assert result == "Connection OK"


def test_openai_get_config():
    provider = OpenAIProvider("my-openai", "http://localhost:12340", "gpt-4", "sk-1234567890abcdef")
    config = provider.get_config()
    assert config["name"] == "my-openai"
    assert config["type"] == "openai"
    assert config["model"] == "gpt-4"
    assert "endpoint" in config
    assert config["api_key_set"] is True
    assert config["api_key_masked"].startswith("sk-1234")


@patch("server.llm.openai_provider.requests.post")
def test_openai_retry_on_5xx(mock_post):
    mock_post.side_effect = [
        _mock_response(500, text="Internal Server Error"),
        _mock_response(200, {"choices": [{"message": {"content": "OK"}}]}),
    ]
    provider = OpenAIProvider("test", "http://localhost:12340", "gpt-4", "sk-test")
    result = provider.chat([{"role": "user", "content": "Hi"}])
    assert result == "OK"
    assert mock_post.call_count == 2
```

- [ ] **Step 2: Implement OpenAI provider**

```python
# server/llm/openai_provider.py
import requests
import json
import time
import logging
from typing import Optional, Generator
from server.llm.base import LLMProvider
from server.utils.endpoint import normalize_endpoint as _normalize_endpoint
from server.utils.validation import mask_api_key

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0
CONNECT_TIMEOUT = 10
STREAM_TOTAL_TIMEOUT = 300


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (/v1/chat/completions).

    Works with: OpenAI, z.ai, local-ai, ollama, lmstudio, any compatible endpoint.
    """

    def __init__(self, name: str, endpoint: str, model: str, api_key: str = ""):
        super().__init__(name, model)
        self.endpoint = _normalize_endpoint(endpoint)
        self.api_key = api_key

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages: list[dict], temperature: float = 0.7, timeout: int = 120) -> str:
        url = f"{self.endpoint}/v1/chat/completions"
        payload = {"model": self.model, "messages": messages, "temperature": temperature}
        log.info(f"[LLM:{self.name}] POST {url}, model='{self.model}', msgs={len(messages)}")

        last_exc = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.post(url, headers=self._headers(), json=payload,
                                     timeout=(CONNECT_TIMEOUT, timeout))
                if resp.status_code != 200:
                    body = resp.text[:1000]
                    log.error(f"[LLM:{self.name}] HTTP {resp.status_code}: {body}")
                    if resp.status_code >= 500 and attempt < MAX_RETRIES:
                        time.sleep(RETRY_BACKOFF * (2 ** attempt))
                        continue
                    raise ValueError(f"LLM API {resp.status_code}: {body}")
                data = resp.json()
                if not data.get("choices"):
                    raise ValueError(f"Missing 'choices': {json.dumps(data, ensure_ascii=False)[:500]}")
                return data["choices"][0]["message"]["content"]
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                else:
                    break
            except ValueError:
                raise
        raise ValueError(f"LLM request failed after {MAX_RETRIES + 1} attempts: {last_exc}") from last_exc

    def chat_stream(self, messages: list[dict], temperature: float = 0.7) -> Generator[str, None, None]:
        url = f"{self.endpoint}/v1/chat/completions"
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "stream": True}
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30, stream=True)
        resp.raise_for_status()

        start = time.monotonic()
        try:
            for line in resp.iter_lines():
                if time.monotonic() - start > STREAM_TOTAL_TIMEOUT:
                    log.error(f"[LLM:{self.name}] Stream timed out after {STREAM_TOTAL_TIMEOUT}s")
                    break
                if line:
                    text = line.decode("utf-8")
                    if text.startswith("data: "):
                        data_str = text[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            pass
        except requests.exceptions.Timeout:
            log.error(f"[LLM:{self.name}] Stream read timed out")

    def list_models(self) -> list[str]:
        url = f"{self.endpoint}/v1/models"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]

    def test_connection(self) -> str:
        return self.chat(
            [{"role": "system", "content": "You are an assistant."},
             {"role": "user", "content": "Reply with 'Connection OK'"}],
            temperature=0.1, timeout=60,
        )

    def get_config(self) -> dict:
        base = super().get_config()
        base["endpoint"] = self.endpoint
        base["api_key_set"] = bool(self.api_key)
        base["api_key_masked"] = mask_api_key(self.api_key)
        return base
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_llm_providers.py -v`
Expected: 11 passed

- [ ] **Step 4: Commit**

```bash
git add server/llm/openai_provider.py tests/test_llm_providers.py
git commit -m "feat(llm): add OpenAI provider with retry and streaming"
```

---

### Task 3: Anthropic Provider

**Files:**
- Create: `server/llm/anthropic_provider.py`
- Modify: `tests/test_llm_providers.py`

- [ ] **Step 1: Write tests for Anthropic provider**

Append to `tests/test_llm_providers.py`:

```python
from server.llm.anthropic_provider import AnthropicProvider


@patch("server.llm.anthropic_provider.requests.post")
def test_anthropic_chat(mock_post):
    mock_post.return_value = _mock_response(200, {
        "content": [{"type": "text", "text": "Claude says hi"}]
    })
    provider = AnthropicProvider("test-claude", "https://api.anthropic.com", "claude-sonnet-4-6", "sk-ant-test")
    result = provider.chat([{"role": "user", "content": "Hi"}])
    assert result == "Claude says hi"
    call_kwargs = mock_post.call_args
    assert "/v1/messages" in call_kwargs[0][0]


@patch("server.llm.anthropic_provider.requests.post")
def test_anthropic_chat_stream(mock_post):
    lines = [
        b'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}',
        b'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":" world"}}',
        b'event: message_stop\ndata: {"type":"message_stop"}',
    ]
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.iter_lines.return_value = lines
    mock_post.return_value = resp

    provider = AnthropicProvider("test", "https://api.anthropic.com", "claude-sonnet-4-6", "sk-test")
    chunks = list(provider.chat_stream([{"role": "user", "content": "Hi"}]))
    assert chunks == ["Hello", " world"]


def test_anthropic_provider_type():
    provider = AnthropicProvider("test", "https://api.anthropic.com", "claude-sonnet-4-6", "sk-test")
    assert provider.provider_type == "anthropic"


def test_anthropic_get_config():
    provider = AnthropicProvider("my-claude", "https://api.anthropic.com", "claude-sonnet-4-6", "sk-ant-12345678")
    config = provider.get_config()
    assert config["type"] == "anthropic"
    assert config["api_key_set"] is True
```

- [ ] **Step 2: Implement Anthropic provider**

```python
# server/llm/anthropic_provider.py
import requests
import json
import time
import logging
from typing import Generator
from server.llm.base import LLMProvider
from server.utils.validation import mask_api_key

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0
CONNECT_TIMEOUT = 10
STREAM_TOTAL_TIMEOUT = 300


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude API (/v1/messages)."""

    def __init__(self, name: str, endpoint: str, model: str, api_key: str = ""):
        super().__init__(name, model)
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    def _headers(self, stream: bool = False) -> dict:
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if stream:
            headers["Accept"] = "text/event-stream"
        return headers

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Convert OpenAI-format messages to Anthropic format. Returns (system, messages)."""
        system = ""
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                system += msg["content"] + "\n"
            else:
                converted.append({"role": msg["role"], "content": msg["content"]})
        return system.strip(), converted

    def chat(self, messages: list[dict], temperature: float = 0.7, timeout: int = 120) -> str:
        url = f"{self.endpoint}/v1/messages"
        system, converted = self._convert_messages(messages)
        payload = {"model": self.model, "messages": converted, "max_tokens": 4096, "temperature": temperature}
        if system:
            payload["system"] = system
        log.info(f"[LLM:{self.name}] POST {url}, model='{self.model}'")

        last_exc = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.post(url, headers=self._headers(), json=payload,
                                     timeout=(CONNECT_TIMEOUT, timeout))
                if resp.status_code != 200:
                    body = resp.text[:1000]
                    if resp.status_code >= 500 and attempt < MAX_RETRIES:
                        time.sleep(RETRY_BACKOFF * (2 ** attempt))
                        continue
                    raise ValueError(f"Anthropic API {resp.status_code}: {body}")
                data = resp.json()
                text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
                return "".join(text_blocks)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                else:
                    break
            except ValueError:
                raise
        raise ValueError(f"Anthropic request failed after {MAX_RETRIES + 1} attempts: {last_exc}") from last_exc

    def chat_stream(self, messages: list[dict], temperature: float = 0.7) -> Generator[str, None, None]:
        url = f"{self.endpoint}/v1/messages"
        system, converted = self._convert_messages(messages)
        payload = {"model": self.model, "messages": converted, "max_tokens": 4096,
                   "temperature": temperature, "stream": True}
        if system:
            payload["system"] = system

        resp = requests.post(url, headers=self._headers(stream=True), json=payload, timeout=30, stream=True)
        resp.raise_for_status()

        start = time.monotonic()
        try:
            for line in resp.iter_lines():
                if time.monotonic() - start > STREAM_TOTAL_TIMEOUT:
                    break
                if line:
                    text = line.decode("utf-8")
                    if text.startswith("data: "):
                        try:
                            data = json.loads(text[6:])
                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except json.JSONDecodeError:
                            pass
        except requests.exceptions.Timeout:
            log.error(f"[LLM:{self.name}] Stream timed out")

    def list_models(self) -> list[str]:
        # Anthropic doesn't have a models listing endpoint — return known models
        return ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5"]

    def test_connection(self) -> str:
        return self.chat(
            [{"role": "user", "content": "Reply with 'Connection OK'"}],
            temperature=0.1, timeout=60,
        )

    def get_config(self) -> dict:
        base = super().get_config()
        base["endpoint"] = self.endpoint
        base["api_key_set"] = bool(self.api_key)
        base["api_key_masked"] = mask_api_key(self.api_key)
        return base
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_llm_providers.py -v`
Expected: 15 passed

- [ ] **Step 4: Commit**

```bash
git add server/llm/anthropic_provider.py tests/test_llm_providers.py
git commit -m "feat(llm): add Anthropic Claude provider"
```

---

### Task 4: Gemini Provider

**Files:**
- Create: `server/llm/gemini_provider.py`
- Modify: `tests/test_llm_providers.py`

- [ ] **Step 1: Write tests for Gemini provider**

Append to `tests/test_llm_providers.py`:

```python
from server.llm.gemini_provider import GeminiProvider


@patch("server.llm.gemini_provider.requests.post")
def test_gemini_chat(mock_post):
    mock_post.return_value = _mock_response(200, {
        "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}]
    })
    provider = GeminiProvider("test-gemini", "https://generativelanguage.googleapis.com", "gemini-2.0-flash", "AIza-test")
    result = provider.chat([{"role": "user", "content": "Hi"}])
    assert result == "Gemini response"
    call_url = mock_post.call_args[0][0]
    assert "gemini-2.0-flash:generateContent" in call_url


def test_gemini_provider_type():
    provider = GeminiProvider("test", "https://generativelanguage.googleapis.com", "gemini-2.0-flash", "key")
    assert provider.provider_type == "gemini"


def test_gemini_get_config():
    provider = GeminiProvider("my-gemini", "https://generativelanguage.googleapis.com", "gemini-2.0-flash", "AIza-12345678")
    config = provider.get_config()
    assert config["type"] == "gemini"
    assert config["api_key_set"] is True
```

- [ ] **Step 2: Implement Gemini provider**

```python
# server/llm/gemini_provider.py
import requests
import json
import time
import logging
from typing import Generator
from server.llm.base import LLMProvider
from server.utils.validation import mask_api_key

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0
CONNECT_TIMEOUT = 10
STREAM_TOTAL_TIMEOUT = 300


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API (/v1beta/models/{model}:generateContent)."""

    def __init__(self, name: str, endpoint: str, model: str, api_key: str = ""):
        super().__init__(name, model)
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert OpenAI-format messages to Gemini 'contents' format."""
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                # Gemini uses systemInstruction at top level, skip here
                continue
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return contents

    def _extract_system(self, messages: list[dict]) -> str:
        parts = [m["content"] for m in messages if m["role"] == "system"]
        return "\n".join(parts)

    def chat(self, messages: list[dict], temperature: float = 0.7, timeout: int = 120) -> str:
        url = f"{self.endpoint}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        system = self._extract_system(messages)
        contents = self._convert_messages(messages)
        payload = {"contents": contents, "generationConfig": {"temperature": temperature}}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        log.info(f"[LLM:{self.name}] POST {url.split('?')[0]}, model='{self.model}'")

        last_exc = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                                     json=payload, timeout=(CONNECT_TIMEOUT, timeout))
                if resp.status_code != 200:
                    body = resp.text[:1000]
                    if resp.status_code >= 500 and attempt < MAX_RETRIES:
                        time.sleep(RETRY_BACKOFF * (2 ** attempt))
                        continue
                    raise ValueError(f"Gemini API {resp.status_code}: {body}")
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                else:
                    break
            except ValueError:
                raise
        raise ValueError(f"Gemini request failed after {MAX_RETRIES + 1} attempts: {last_exc}") from last_exc

    def chat_stream(self, messages: list[dict], temperature: float = 0.7) -> Generator[str, None, None]:
        url = f"{self.endpoint}/v1beta/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        system = self._extract_system(messages)
        contents = self._convert_messages(messages)
        payload = {"contents": contents, "generationConfig": {"temperature": temperature}}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        resp = requests.post(url, headers={"Content-Type": "application/json"},
                             json=payload, timeout=30, stream=True)
        resp.raise_for_status()

        start = time.monotonic()
        try:
            for line in resp.iter_lines():
                if time.monotonic() - start > STREAM_TOTAL_TIMEOUT:
                    break
                if line:
                    text = line.decode("utf-8")
                    if text.startswith("data: "):
                        try:
                            data = json.loads(text[6:])
                            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                            for p in parts:
                                if "text" in p:
                                    yield p["text"]
                        except json.JSONDecodeError:
                            pass
        except requests.exceptions.Timeout:
            log.error(f"[LLM:{self.name}] Stream timed out")

    def list_models(self) -> list[str]:
        url = f"{self.endpoint}/v1beta/models?key={self.api_key}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return [m.get("name", "").replace("models/", "") for m in data.get("models", [])]
        except Exception:
            return ["gemini-2.0-flash", "gemini-2.0-pro"]

    def test_connection(self) -> str:
        return self.chat(
            [{"role": "user", "content": "Reply with 'Connection OK'"}],
            temperature=0.1, timeout=60,
        )

    def get_config(self) -> dict:
        base = super().get_config()
        base["endpoint"] = self.endpoint
        base["api_key_set"] = bool(self.api_key)
        base["api_key_masked"] = mask_api_key(self.api_key)
        return base
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_llm_providers.py -v`
Expected: 18 passed

- [ ] **Step 4: Commit**

```bash
git add server/llm/gemini_provider.py tests/test_llm_providers.py
git commit -m "feat(llm): add Google Gemini provider"
```

---

### Task 5: LLM Registry

**Files:**
- Create: `server/llm/registry.py`
- Modify: `tests/test_llm_providers.py`

- [ ] **Step 1: Write tests for registry**

Append to `tests/test_llm_providers.py`:

```python
from server.llm.registry import LLMRegistry


def _make_stub(name="stub", **kw):
    return StubProvider(name, **kw)


def test_registry_register_and_get():
    reg = LLMRegistry()
    p = _make_stub("test-p")
    reg.register("test-p", p)
    assert reg.get_active() is p


def test_registry_first_registered_is_active():
    reg = LLMRegistry()
    reg.register("a", _make_stub("a"))
    reg.register("b", _make_stub("b"))
    assert reg.get_active().name == "a"


def test_registry_set_active():
    reg = LLMRegistry()
    reg.register("a", _make_stub("a"))
    reg.register("b", _make_stub("b"))
    reg.set_active("b")
    assert reg.get_active().name == "b"


def test_registry_set_active_not_found():
    reg = LLMRegistry()
    with pytest.raises(ValueError, match="not registered"):
        reg.set_active("nonexistent")


def test_registry_get_active_empty():
    reg = LLMRegistry()
    with pytest.raises(ValueError, match="No providers"):
        reg.get_active()


def test_registry_remove():
    reg = LLMRegistry()
    reg.register("a", _make_stub("a"))
    reg.register("b", _make_stub("b"))
    reg.set_active("b")
    reg.remove("b")
    # Active was removed, should fall back to first remaining
    assert reg.get_active().name == "a"


def test_registry_remove_active_no_fallback():
    reg = LLMRegistry()
    reg.register("a", _make_stub("a"))
    reg.remove("a")
    with pytest.raises(ValueError, match="No providers"):
        reg.get_active()


def test_registry_list_providers():
    reg = LLMRegistry()
    reg.register("local", _make_stub("local"))
    reg.register("cloud", _make_stub("cloud"))
    reg.set_active("cloud")
    result = reg.list_providers()
    assert len(result) == 2
    cloud = next(p for p in result if p["name"] == "cloud")
    assert cloud["is_active"] is True
    local = next(p for p in result if p["name"] == "local")
    assert local["is_active"] is False


def test_registry_create_provider_openai():
    reg = LLMRegistry()
    p = reg.create_provider("openai", "test", endpoint="http://localhost:12340", model="gpt-4", api_key="sk-test")
    assert isinstance(p, OpenAIProvider)
    assert p.name == "test"


def test_registry_create_provider_anthropic():
    reg = LLMRegistry()
    p = reg.create_provider("anthropic", "claude", endpoint="https://api.anthropic.com", model="claude-sonnet-4-6", api_key="sk-ant")
    assert isinstance(p, AnthropicProvider)


def test_registry_create_provider_gemini():
    reg = LLMRegistry()
    p = reg.create_provider("gemini", "gemini", endpoint="https://generativelanguage.googleapis.com", model="gemini-2.0-flash", api_key="AIza-test")
    assert isinstance(p, GeminiProvider)


def test_registry_create_provider_unknown():
    reg = LLMRegistry()
    with pytest.raises(ValueError, match="Unknown provider type"):
        reg.create_provider("unknown", "x", endpoint="", model="")
```

- [ ] **Step 2: Implement registry**

```python
# server/llm/registry.py
import logging
from server.llm.base import LLMProvider

log = logging.getLogger(__name__)


class LLMRegistry:
    """Manages multiple LLM providers with active selection."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._active_name: str | None = None

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider
        if self._active_name is None:
            self._active_name = name
            log.info(f"[LLMRegistry] Registered '{name}' as active provider ({provider.provider_type})")
        else:
            log.info(f"[LLMRegistry] Registered '{name}' ({provider.provider_type})")

    def remove(self, name: str) -> None:
        if name not in self._providers:
            return
        del self._providers[name]
        if self._active_name == name:
            self._active_name = next(iter(self._providers), None)
        log.info(f"[LLMRegistry] Removed provider '{name}'")

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        self._active_name = name
        log.info(f"[LLMRegistry] Active provider set to '{name}'")

    def get_active(self) -> LLMProvider:
        if not self._active_name or self._active_name not in self._providers:
            raise ValueError("No providers registered")
        return self._providers[self._active_name]

    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        return self._providers[name]

    def list_providers(self) -> list[dict]:
        result = []
        for name, provider in self._providers.items():
            config = provider.get_config()
            config["is_active"] = (name == self._active_name)
            result.append(config)
        return result

    def create_provider(self, provider_type: str, name: str, **kwargs) -> LLMProvider:
        """Factory: create a provider by type string."""
        endpoint = kwargs.get("endpoint", "")
        model = kwargs.get("model", "")
        api_key = kwargs.get("api_key", "")

        if provider_type == "openai":
            from server.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(name, endpoint, model, api_key)
        elif provider_type == "anthropic":
            from server.llm.anthropic_provider import AnthropicProvider
            return AnthropicProvider(name, endpoint, model, api_key)
        elif provider_type == "gemini":
            from server.llm.gemini_provider import GeminiProvider
            return GeminiProvider(name, endpoint, model, api_key)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
```

- [ ] **Step 3: Update `__init__.py` exports**

```python
# server/llm/__init__.py
from server.llm.base import LLMProvider
from server.llm.registry import LLMRegistry

__all__ = ["LLMProvider", "LLMRegistry"]
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_llm_providers.py -v`
Expected: 30 passed

- [ ] **Step 5: Commit**

```bash
git add server/llm/registry.py server/llm/__init__.py tests/test_llm_providers.py
git commit -m "feat(llm): add LLMRegistry multi-provider management"
```

---

### Task 6: Update DI Container and Startup

**Files:**
- Modify: `server/di/container.py`
- Modify: `server/main.py`

- [ ] **Step 1: Update DI container to register LLMRegistry**

```python
# server/di/container.py — replace entire register_services function

def register_services(container):
    from server.game_manager import GameManager
    from server.websocket_hub import WebSocketHub
    from server.host_dm import HostDM
    from server.script_repository import ScriptRepository
    from server.script_service import ScriptService
    from server.llm.registry import LLMRegistry
    from server.llm.openai_provider import OpenAIProvider
    from server.config import config as app_config

    def _create_registry():
        registry = LLMRegistry()
        # Create default provider from .env config
        default = OpenAIProvider(
            name="default",
            endpoint=app_config.LLM_ENDPOINT,
            model=app_config.LLM_MODEL,
            api_key=app_config.LLM_API_KEY,
        )
        registry.register("default", default)
        return registry

    container.register("llm_registry", _create_registry, singleton=True)
    container.register("game_manager", GameManager, singleton=True)
    container.register("websocket_hub", WebSocketHub, singleton=True)
    container.register("host_dm", HostDM, singleton=True)
    container.register("script_repository", ScriptRepository, singleton=True)
    container.register("script_service", lambda: ScriptService(container.resolve("script_repository")), singleton=True)
```

- [ ] **Step 2: Run existing tests**

Run: `pytest tests/test_game_manager.py tests/test_api_rooms.py -v`
Expected: 49 passed (DI change should be transparent to existing tests)

- [ ] **Step 3: Commit**

```bash
git add server/di/container.py
git commit -m "feat(di): register LLMRegistry as default LLM service"
```

---

### Task 7: Migrate HostDM to Use Registry

**Files:**
- Modify: `server/host_dm.py`

- [ ] **Step 1: Update HostDM to accept registry**

Replace `server/host_dm.py` constructor and all LLM call sites:

```python
# server/host_dm.py — update __init__ and LLM calls only

class HostDM:
    def __init__(self):
        from server.di import container
        self._registry = None

    @property
    def registry(self):
        if self._registry is None:
            from server.di import container
            self._registry = container.resolve("llm_registry")
        return self._registry

    # Remove: self.llm = LLMClient()
```

Then replace every `self.llm.xxx()` call with `self.registry.get_active().xxx()`:
- `self.llm.host_event(...)` → `self.registry.get_active().chat(messages, ...)`
- `self.llm.chat_stream(...)` → `self.registry.get_active().chat_stream(messages, ...)`
- `self.llm.generate_script_stream(...)` → `self.registry.get_active().chat_stream(messages, ...)`
- `self.llm.generate_script(...)` → `self.registry.get_active().chat(messages, ...)`

The key change: `host_event()` used to construct messages with system/assistant/user roles and call `self.llm.host_event(system_prompt, history)`. Now we call `self.registry.get_active().chat(messages, temperature=0.8, timeout=300)` directly.

Full replacement file:

```python
# server/host_dm.py — complete replacement
import json
import logging
from typing import Generator, Tuple

from server.models import GameState

log = logging.getLogger(__name__)


class HostDM:
    def __init__(self):
        self._registry = None

    @property
    def registry(self):
        if self._registry is None:
            from server.di import container
            self._registry = container.resolve("llm_registry")
        return self._registry

    # Keep backward compat alias
    @property
    def llm(self):
        return self.registry.get_active()

    @staticmethod
    def parse_event_response(raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            log.warning(f"[DM] JSON parse failed, using raw text as public_event: {e}")
            return {"public_event": raw, "private_clues": [], "dm_instruction": ""}
        return {
            "public_event": data.get("public_event", ""),
            "private_clues": data.get("private_clues", []),
            "dm_instruction": data.get("dm_instruction", ""),
        }

    def generate_event(self, game_state: GameState) -> dict:
        history = game_state.host_message_history[-10:]
        player_info = []
        role_names = []
        for pid, p in game_state.players.items():
            role_name = p.role.name if p.role else "未分配"
            player_info.append(f"{p.name}({role_name})")
            role_names.append(role_name)

        chat_summary = []
        for msg in game_state.public_messages[-20:]:
            sender = next(
                (p.name for pid, p in game_state.players.items() if pid == msg.from_player_id),
                msg.from_player_id,
            )
            chat_summary.append(f"{sender}: {msg.content}")

        user_input = f"""当前是第{game_state.current_round}轮，阶段: 第{game_state.act}幕
玩家状态：{', '.join(player_info)}
在场角色名：{', '.join(role_names)}
最近聊天：
{''.join(chat_summary) if chat_summary else '暂无聊天记录'}

请根据以上信息生成下一个游戏事件。严格按JSON格式返回，包含 public_event、private_clues、dm_instruction 三个字段。"""

        messages = [{"role": "system", "content": self.SYSTEM_EVENT_PROMPT}]
        for msg in history[:-1]:
            messages.append({"role": "assistant", "content": msg})
        if history:
            messages.append({"role": "user", "content": user_input})
        else:
            messages.append({"role": "user", "content": user_input})

        raw = self.registry.get_active().chat(messages, temperature=0.8, timeout=300)
        return self.parse_event_response(raw)

    def generate_script(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.registry.get_active().chat(messages, temperature=0.7, timeout=300)

    DM_CHAT_SYSTEM_PROMPT = """你是一名专业的剧本杀主持人（DM）。玩家正在通过私信与你对话。

你的职责：
1. 根据当前游戏阶段和剧本设定，给玩家合适的回应
2. 如果玩家询问线索，根据阶段决定是否透露
3. 保持DM身份，不要直接透露凶手或关键剧情
4. 回复使用中文，语气亲切但保持神秘感
5. 回复长度控制在 50-200 字
6. 只回复纯文本，不要JSON格式"""

    def _build_chat_messages(self, game_state: GameState, player_id: str, player_message: str) -> list[dict]:
        player = game_state.players.get(player_id)
        role_name = player.role.name if player and player.role else "未分配"

        chat_summary = []
        for msg in game_state.private_messages[-10:]:
            if msg.from_player_id == "__dm__":
                sender = "🎭 DM"
            elif msg.from_player_id in game_state.players:
                sender = game_state.players[msg.from_player_id].name
            else:
                sender = msg.from_player_id
            chat_summary.append(f"{sender}: {msg.content}")

        user_input = f"""你正在与一名玩家私信对话。
当前是第{game_state.current_round}轮，第{game_state.act}幕。
玩家角色：{role_name}
玩家消息：{player_message}
私信历史：
{''.join(chat_summary) if chat_summary else '暂无私信记录'}

请给玩家一个符合DM身份的回复。"""

        return [
            {"role": "system", "content": self.DM_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

    def respond_to_chat(self, game_state: GameState, player_id: str, player_message: str) -> str:
        messages = self._build_chat_messages(game_state, player_id, player_message)
        full_reply = ""
        for chunk in self.registry.get_active().chat_stream(messages, temperature=0.8):
            full_reply += chunk
        return full_reply

    def respond_to_chat_stream(self, game_state: GameState, player_id: str, player_message: str) -> Generator[str, None, None]:
        messages = self._build_chat_messages(game_state, player_id, player_message)
        yield from self.registry.get_active().chat_stream(messages, temperature=0.8)

    SYSTEM_EVENT_PROMPT = """你是一名专业的剧本杀主持人（DM）。你的职责：
1. 动态发布事件 — 每轮给玩家一个情境或发现
2. 投放线索 — 根据游戏进度和玩家行为决定何时放出什么线索
3. 维持剧情一致性 — 所有事件和线索必须符合剧本设定
4. 引导节奏 — 玩家卡住时给提示，讨论热烈时推进剧情

=== 输出格式（严格遵守）===
你必须返回一个 JSON 对象，包含以下字段：
{
  "public_event": "面向所有玩家公开的叙事/事件/线索。",
  "private_clues": [
    {"role": "角色名", "content": "该角色专属的线索内容"},
    ...
  ],
  "dm_instruction": "仅DM可见的行动指引。"
}
只返回JSON，不要添加任何解释文字"""


host = HostDM()
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_game_manager.py tests/test_api_rooms.py -v`
Expected: 49 passed

- [ ] **Step 3: Commit**

```bash
git add server/host_dm.py
git commit -m "refactor(host_dm): migrate from LLMClient to LLMRegistry"
```

---

### Task 8: New Provider Management API

**Files:**
- Create: `server/api/llm.py`
- Modify: `server/api/__init__.py` (replace config router with llm router)
- Modify: `tests/conftest.py`

- [ ] **Step 1: Create new LLM management API**

```python
# server/api/llm.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from starlette.concurrency import run_in_threadpool
from server.di import container

router = APIRouter()


def _get_registry():
    return container.resolve("llm_registry")


def _get_manager():
    return container.resolve("game_manager")


class ProviderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., pattern=r"^(openai|anthropic|gemini)$")
    endpoint: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    api_key: str = ""


class ActiveProviderRequest(BaseModel):
    name: str = Field(..., min_length=1)


@router.get("/llm/providers")
async def list_providers():
    return {"providers": _get_registry().list_providers()}


@router.post("/llm/providers")
async def add_provider(req: ProviderCreateRequest):
    registry = _get_registry()
    try:
        provider = registry.create_provider(req.type, req.name,
                                            endpoint=req.endpoint,
                                            model=req.model,
                                            api_key=req.api_key)
        registry.register(req.name, provider)
        return {"status": "added", "name": req.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/llm/providers/{name}")
async def remove_provider(name: str):
    registry = _get_registry()
    providers = {p["name"] for p in registry.list_providers()}
    if name not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    registry.remove(name)
    return {"status": "removed"}


@router.post("/llm/providers/active")
async def set_active_provider(req: ActiveProviderRequest):
    registry = _get_registry()
    try:
        registry.set_active(req.name)
        return {"status": "active", "name": req.name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/llm/providers/{name}/test")
async def test_provider(name: str):
    registry = _get_registry()
    try:
        provider = registry.get(name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")

    import time
    try:
        start = time.time()
        result = await run_in_threadpool(provider.test_connection)
        elapsed = time.time() - start
        return {
            "status": "connected",
            "response_time_ms": round(elapsed * 1000),
            "model": provider.model,
            "sample_response": result[:200],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/llm/providers/{name}/models")
async def list_provider_models(name: str):
    registry = _get_registry()
    try:
        provider = registry.get(name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")
    try:
        models = await run_in_threadpool(provider.list_models)
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


# Backward-compatible endpoints
@router.get("/llm-config")
async def get_llm_config():
    return _get_registry().get_active().get_config()


@router.get("/health")
async def health_check():
    return {"status": "ok", "games_count": len(_get_manager().games)}
```

- [ ] **Step 2: Update API router imports**

```python
# server/api/__init__.py
from fastapi import APIRouter
from server.api.rooms import router as rooms_router
from server.api.script import router as script_router
from server.api.game import router as game_router
from server.api.dm import router as dm_router
from server.api.voting import router as voting_router
from server.api.chat import router as chat_router
from server.api.llm import router as llm_router
from server.api.scripts import router as scripts_router

router = APIRouter()

router.include_router(rooms_router)
router.include_router(script_router)
router.include_router(game_router)
router.include_router(dm_router)
router.include_router(voting_router)
router.include_router(chat_router)
router.include_router(llm_router)
router.include_router(scripts_router)
```

- [ ] **Step 3: Run all tests**

Run: `pytest tests/test_game_manager.py tests/test_api_rooms.py tests/test_llm_providers.py -v`
Expected: 79 passed

- [ ] **Step 4: Commit**

```bash
git add server/api/llm.py server/api/__init__.py
git commit -m "feat(api): add multi-provider LLM management API"
```

---

### Task 9: Delete Old LLMClient and Config Router

**Files:**
- Delete: `server/llm_client.py`
- Delete: `server/api/config.py`
- Modify: any remaining imports of `llm_client`

- [ ] **Step 1: Search for remaining LLMClient references**

Run: `grep -r "llm_client" server/ --include="*.py"`
Expected: No references (all migrated to registry)

If references found, update them to use `container.resolve("llm_registry").get_active()`.

- [ ] **Step 2: Delete old files**

```bash
rm server/llm_client.py
rm server/api/config.py
```

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/test_game_manager.py tests/test_api_rooms.py tests/test_llm_providers.py -v`
Expected: 79 passed

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove old LLMClient, replaced by provider layer"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- 1.1 Abstract interface → Task 1 ✅
- 1.2 Providers (OpenAI, Anthropic, Gemini) → Tasks 2, 3, 4 ✅
- 1.3 Registry → Task 5 ✅
- 1.4 Admin API → Task 8 ✅
- 1.5 Migration → Tasks 6, 7, 9 ✅

**2. Placeholder scan:** No TBDs, TODOs, or "implement later" patterns. All code blocks are complete.

**3. Type consistency:**
- `chat(messages, temperature, timeout) -> str` — consistent across all providers ✅
- `chat_stream(messages, temperature) -> Generator[str]` — consistent ✅
- Registry `create_provider(type, name, **kwargs)` matches all test calls ✅
- `get_config() -> dict` includes `is_active` only from `list_providers()`, not individual `get_config()` ✅
