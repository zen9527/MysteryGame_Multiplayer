import requests
import json
from server.config import config


class LLMClient:
    def __init__(self):
        self.endpoint = config.LLM_ENDPOINT
        self.model = config.LLM_MODEL
        self.api_key = config.LLM_API_KEY

    def generate_script(self, system_prompt: str, user_prompt: str) -> str:
        """生成剧本，返回 JSON 字符串"""
        url = f"{self.endpoint}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def host_event(self, system_prompt: str, message_history: list[str]) -> str:
        """LLM 主持人发布事件"""
        url = f"{self.endpoint}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([{"role": "assistant", "content": msg} for msg in message_history])
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
