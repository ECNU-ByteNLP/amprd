from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import requests

from src.models.model_client import ModelClient


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout_s: int = 120
    max_retries: int = 3


class OpenAITextClient(ModelClient):
    """
    OpenAI-compatible Chat Completions client.

    Works with OpenAI and any OpenAI-compatible providers (DeepSeek, etc.)
    by changing base_url and model_name.
    """

    def __init__(self, *, config: OpenAIConfig, model_name: str) -> None:
        super().__init__(name=f"openai:{model_name}")
        self._cfg = config
        self.model_name = model_name

    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        stop: Optional[Iterable[str]] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        url = self._cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._cfg.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }
        if stop is not None:
            payload["stop"] = list(stop)

        last_exc: Exception | None = None
        for attempt in range(1, self._cfg.max_retries + 1):
            try:
                resp = requests.post(
                    url, headers=headers, data=json.dumps(payload), timeout=self._cfg.timeout_s
                )
                if resp.status_code >= 400:
                    raise RuntimeError(f"OpenAI-compatible error {resp.status_code}: {resp.text}")
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                last_exc = e
                if attempt < self._cfg.max_retries:
                    time.sleep(1.0 * attempt)
                    continue
                break
        raise RuntimeError(f"OpenAI-compatible request failed: {last_exc}") from last_exc

    def generate_image(self, prompt: str, *, size: str = "1024x768") -> Dict[str, Any]:
        raise NotImplementedError("Use a vision/image client for image generation.")


def create_openai_clients_from_env() -> tuple[Optional[ModelClient], Optional[ModelClient], Optional[ModelClient]]:
    """
    Create OpenAI-compatible clients from env vars.

    Env:
    - OPENAI_API_KEY
    - OPENAI_BASE_URL (optional, default https://api.openai.com/v1)
    - OPENAI_TEXT_MODEL_CN / OPENAI_TEXT_MODEL_EN (optional, defaults to OPENAI_TEXT_MODEL)
    - OPENAI_TEXT_MODEL (optional)

    Returns: (text_cn, text_en, vision) where vision is None for now.
    """
    import os

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, None, None

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    model_default = os.getenv("OPENAI_TEXT_MODEL", "").strip()
    model_cn = os.getenv("OPENAI_TEXT_MODEL_CN", model_default).strip()
    model_en = os.getenv("OPENAI_TEXT_MODEL_EN", model_default).strip()
    if not model_cn and not model_en:
        return None, None, None

    cfg = OpenAIConfig(api_key=api_key, base_url=base_url)
    text_cn = OpenAITextClient(config=cfg, model_name=model_cn) if model_cn else None
    text_en = OpenAITextClient(config=cfg, model_name=model_en) if model_en else None
    return text_cn, text_en, None



