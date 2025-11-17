from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import requests

try:  # pragma: no cover - optional dependency
    import dashscope
    from dashscope import MultiModalConversation

    HAS_DASHSCOPE = True
except Exception:  # pragma: no cover - optional dependency
    dashscope = None
    MultiModalConversation = None
    HAS_DASHSCOPE = False

from src.models.model_client import ModelClient


class QwenTextClient(ModelClient):
    """OpenAI-compatible client for Qwen text/chat模型."""

    CHAT_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str = "qwen2.5-32b-instruct",
        timeout: int = 60,
    ) -> None:
        super().__init__(name=f"qwen-text:{model_name}")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout

    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        stop: Optional[Iterable[str]] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
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
        if stop:
            payload["stop"] = list(stop)

        response = requests.post(
            self.CHAT_URL,
            headers=self._headers,
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Qwen text generation failed: {response.status_code} {response.text}"
            )
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Qwen response: {data}") from exc

    def generate_image(self, prompt: str, *, size: str = "1024x768") -> Dict[str, Any]:
        raise NotImplementedError("Use QwenVisionClient for image generation.")

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }


class QwenVisionClient(ModelClient):
    """Image generation client supporting dashscope SDK with compatible fallback."""

    IMAGE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/images/generations"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str = "wanx-v1",
        assets_dir: Path | None = None,
        timeout: int = 120,
        compatible_api_key: Optional[str] = None,
    ) -> None:
        super().__init__(name=f"qwen-vision:{model_name}")
        self.model_name = model_name
        self.assets_dir = (assets_dir or Path("assets/output/qwen_images")).resolve()
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.dashscope_api_key = api_key
        self.compatible_api_key = compatible_api_key or api_key
        self._use_dashscope = HAS_DASHSCOPE and self.model_name.lower() not in {"none", ""}
        self.default_size = os.getenv("QWEN_VISION_SIZE", "1328x1328" if "image-plus" in self.model_name else "1024x1024")
        if self._use_dashscope:
            dashscope.api_key = self.dashscope_api_key
            base_url = os.getenv("DASHSCOPE_BASE_URL")
            if base_url:
                dashscope.base_http_api_url = base_url  # type: ignore[attr-defined]

    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        stop: Optional[Iterable[str]] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        raise NotImplementedError("Vision client does not support text generation.")

    def generate_image(self, prompt: str, *, size: str | None = None) -> Dict[str, Any]:
        if self.model_name.lower() in {"none", ""}:
            raise RuntimeError("Vision model disabled.")
        size_to_use = size or self.default_size
        if self._use_dashscope:
            return self._generate_via_dashscope(prompt, size_to_use)
        return self._generate_via_compatible(prompt, size_to_use)

    def _generate_via_dashscope(self, prompt: str, size: str) -> Dict[str, Any]:
        if not HAS_DASHSCOPE or MultiModalConversation is None or dashscope is None:
            raise RuntimeError("dashscope SDK not available.")

        messages = [{"role": "user", "content": [{"text": prompt}]}]
        size_param = size.replace("x", "*")
        response = MultiModalConversation.call(  # type: ignore[call-arg]
            api_key=self.dashscope_api_key,
            model=self.model_name,
            messages=messages,
            result_format="message",
            stream=False,
            watermark=False,
            prompt_extend=True,
            size=size_param,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Qwen image generation failed: {response.status_code} {response.code} {response.message}"
            )
        choices = response.output.get("choices", [])
        if not choices:
            raise RuntimeError(f"Missing choices in response: {response.output}")
        message = choices[0].get("message", {})
        content = message.get("content", [])
        image_url: Optional[str] = None
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "image" in item:
                    image = item.get("image")
                    if isinstance(image, dict):
                        image_url = image.get("url")
                    elif isinstance(image, str):
                        image_url = image
                    if image_url:
                        break
                elif isinstance(item, dict) and "url" in item:
                    image_url = item.get("url")
                    if image_url:
                        break
        elif isinstance(content, dict):
            image_url = content.get("url") or content.get("image", {}).get("url") if isinstance(content.get("image"), dict) else None
        elif isinstance(content, str):
            # 有些模型会直接返回 base64 字符串
            if content.startswith("data:image"):
                header, b64_data = content.split(",", 1)
                image_bytes = base64.b64decode(b64_data)
                return self._save_image(image_bytes, prompt, size)

        if not image_url:
            raise RuntimeError(f"Missing image url in response: {content}")

        image_bytes = requests.get(image_url, timeout=self.timeout).content
        return self._save_image(image_bytes, prompt, size)

    def _generate_via_compatible(self, prompt: str, size: str) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "size": size,
        }
        response = requests.post(
            self.IMAGE_URL,
            headers=self._headers,
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Qwen image generation failed: {response.status_code} {response.text}"
            )
        data = response.json()
        try:
            image_info = data["data"][0]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Qwen image response: {data}") from exc

        if "b64_json" in image_info:
            image_bytes = base64.b64decode(image_info["b64_json"])
        elif "url" in image_info:
            image_bytes = requests.get(image_info["url"], timeout=self.timeout).content
        else:
            raise RuntimeError(f"Missing image payload in response: {image_info}")

        return self._save_image(image_bytes, prompt, size)

    def _save_image(self, image_bytes: bytes, prompt: str, size: str) -> Dict[str, Any]:
        filename = self._filename(prompt, size)
        path = self.assets_dir / filename
        path.write_bytes(image_bytes)
        return {
            "path": str(path),
            "prompt": prompt,
            "size": size,
            "provider": self.name,
        }

    def _filename(self, prompt: str, size: str) -> str:
        digest = hashlib.sha256(f"{prompt}:{size}".encode("utf-8")).hexdigest()[:16]
        return f"qwen_{digest}.png"

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.compatible_api_key}",
        }


def create_qwen_clients_from_env() -> Tuple[Optional[ModelClient], Optional[ModelClient], Optional[ModelClient]]:
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        return None, None, None

    text_model_cn = os.getenv("QWEN_TEXT_MODEL_CN", "qwen2.5-32b-instruct")
    text_model_en = os.getenv("QWEN_TEXT_MODEL_EN", text_model_cn)
    vision_model = os.getenv("QWEN_VISION_MODEL", "wanx-v1")

    if vision_model.lower() in {"none", ""}:
        vision = None
    else:
        vision_api_key = os.getenv("DASHSCOPE_API_KEY", api_key)
        vision = QwenVisionClient(
            api_key=vision_api_key,
            model_name=vision_model,
            compatible_api_key=api_key,
        )

    text_cn = QwenTextClient(api_key=api_key, model_name=text_model_cn)
    text_en = QwenTextClient(api_key=api_key, model_name=text_model_en)

    return text_cn, text_en, vision

