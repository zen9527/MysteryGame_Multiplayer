import requests
import json
from typing import Optional
from server.config import config


class LLMClient:
    def __init__(self):
        self.endpoint = config.LLM_ENDPOINT
        self.model = config.LLM_MODEL
        self.api_key = config.LLM_API_KEY

    def set_runtime_config(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Runtime override of LLM config (per-session, not persisted to .env)."""
        if endpoint is not None:
            self.endpoint = endpoint
        if model is not None:
            self.model = model
        if api_key is not None:
            self.api_key = api_key

    def get_config(self) -> dict:
        """Return current config with masked api_key."""
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "api_key_set": bool(self.api_key),
            "api_key_masked": self.api_key[:8] + "..." if len(self.api_key) > 8 else "",
        }

    def _build_request(self, messages: list, temperature: float = 0.7, timeout: int = 120) -> dict:
        """Build and send an OpenAI-compatible chat request. Returns parsed response dict."""
        url = f"{self.endpoint}/v1/chat/completions"
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
        return response.json()

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
        resp = self._build_request(messages, temperature=0.8, timeout=60)
        return resp["choices"][0]["message"]["content"]

    def test_connection(self) -> str:
        """Quick connection test, returns short response text."""
        resp = self._build_request([
            {"role": "system", "content": "你是一个助手。"},
            {"role": "user", "content": "请用一句话回复'连接正常'"},
        ], temperature=0.1, timeout=30)
        return resp["choices"][0]["message"]["content"]
