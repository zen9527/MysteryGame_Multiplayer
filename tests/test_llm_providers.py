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


# --- OpenAI Provider tests ---

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
    assert config["api_key_masked"] == "sk-1...cdef"


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


# --- Anthropic Provider tests ---

from server.llm.anthropic_provider import AnthropicProvider


@patch("server.llm.anthropic_provider.requests.post")
def test_anthropic_chat(mock_post):
    mock_post.return_value = _mock_response(200, {
        "content": [{"type": "text", "text": "Claude says hi"}]
    })
    provider = AnthropicProvider("test-claude", "https://api.anthropic.com", "claude-sonnet-4-6", "sk-ant-test")
    result = provider.chat([{"role": "user", "content": "Hi"}])
    assert result == "Claude says hi"
    call_url = mock_post.call_args[0][0]
    assert "/v1/messages" in call_url


@patch("server.llm.anthropic_provider.requests.post")
def test_anthropic_chat_stream(mock_post):
    lines = [
        b'event: content_block_delta',
        b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}',
        b'',
        b'event: content_block_delta',
        b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" world"}}',
        b'',
        b'event: message_stop',
        b'data: {"type":"message_stop"}',
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


# --- Gemini Provider tests ---

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
