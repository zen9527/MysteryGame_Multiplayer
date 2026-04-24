import requests
import json
from typing import Optional
from server.config import config


def _normalize_endpoint(url: str) -> str:
    """Ensure endpoint has http:// scheme and strip trailing slash."""
    url = url.strip().rstrip("/")
    if not url:
        return url
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url


class LLMClient:
    def __init__(self):
        self.endpoint = _normalize_endpoint(config.LLM_ENDPOINT)
        self.model = config.LLM_MODEL
        self.api_key = config.LLM_API_KEY

    def set_runtime_config(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Runtime override of LLM config (per-session, not persisted to .env).

        Passing empty string "" for api_key will clear the key.
        Passing null/None means "don't change this field".
        """
        if endpoint is not None:
            self.endpoint = _normalize_endpoint(endpoint)
        if model is not None:
            self.model = model
        if api_key is not None:
            self.api_key = api_key.strip()

    def get_config(self) -> dict:
        """Return current config with masked api_key."""
        has_key = bool(self.api_key and self.api_key.strip())
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "api_key_set": has_key,
            "api_key_masked": (self.api_key[:8] + "...") if has_key and len(self.api_key) > 8 else "",
        }

    def _chat_url(self) -> str:
        """Standard OpenAI-compatible chat endpoint."""
        return f"{self.endpoint}/v1/chat/completions"

    def _models_url(self) -> str:
        """Standard OpenAI-compatible models endpoint."""
        return f"{self.endpoint}/v1/models"

    def _build_request(self, messages: list, temperature: float = 0.7, timeout: int = 120) -> dict:
        """Build and send an OpenAI-compatible chat request. Returns parsed response dict."""
        url = self._chat_url()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if not data.get("choices"):
            raw = json.dumps(data, ensure_ascii=False)[:500]
            raise ValueError(f"Unexpected response format (missing 'choices'): {raw}")
        return data

    def generate_script(self, system_prompt: str, user_prompt: str) -> str:
        """生成剧本，返回 JSON 字符串"""
        resp = self._build_request([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ], temperature=0.7, timeout=120)
        return resp["choices"][0]["message"]["content"]

    def host_event(self, system_prompt: str, message_history: list[str]) -> str:
        """LLM 主持人发布事件"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([{"role": "assistant", "content": msg} for msg in message_history])
        resp = self._build_request(messages, temperature=0.8, timeout=120)
        return resp["choices"][0]["message"]["content"]

    def test_connection(self) -> str:
        """Quick connection test, returns short response text."""
        resp = self._build_request([
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": "Reply with 'Connection OK'"},
        ], temperature=0.1, timeout=60)
        return resp["choices"][0]["message"]["content"]

    def list_models(self) -> list[str]:
        """Fetch available models from the LLM provider."""
        url = self._models_url()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        models = data.get("data", [])
        return [m.get("id", "") for m in models if isinstance(m, dict)]
