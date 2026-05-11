import requests
import json
import time
import logging
from typing import Generator
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
