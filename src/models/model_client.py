from __future__ import annotations

import abc
from typing import Any, Dict, Iterable, Optional


class ModelClient(abc.ABC):
    """Abstract client used by agents to call underlying language or vision models."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        stop: Optional[Iterable[str]] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Return generated text."""

    @abc.abstractmethod
    def generate_image(self, prompt: str, *, size: str = "1024x768") -> Dict[str, Any]:
        """Return metadata about a generated image; implementation defined."""


class MockModelClient(ModelClient):
    """
    Fallback mock client for local development.

    Generates deterministic template outputs to keep the pipeline executable
    without external dependencies. Replace with real clients in production.
    """

    def __init__(self) -> None:
        super().__init__(name="mock-model")

    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        stop: Optional[Iterable[str]] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        sanitized = prompt.split("\n")[-1][:400]
        return f"[mock-text-response] {sanitized}"

    def generate_image(self, prompt: str, *, size: str = "1024x768") -> Dict[str, Any]:
        return {
            "path": f"assets/output/mock/{abs(hash(prompt)) % 10_000}.png",
            "size": size,
            "prompt": prompt[:200],
        }


