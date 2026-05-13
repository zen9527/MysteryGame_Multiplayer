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
        contents = []
        for msg in messages:
            if msg["role"] == "system":
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
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "api_key": self.api_key,
            "name": self.name,
            "type": self.provider_type,
        }
