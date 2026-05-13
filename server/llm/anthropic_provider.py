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
        return ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5"]

    def test_connection(self) -> str:
        return self.chat(
            [{"role": "user", "content": "Reply with 'Connection OK'"}],
            temperature=0.1, timeout=60,
        )

    def get_config(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "api_key": self.api_key,
            "name": self.name,
            "type": self.provider_type,
        }
