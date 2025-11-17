from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    persist_root: Path = Path("artifacts")
    communication_mode: str = "blackboard"
    disabled_agents: list[str] | None = None


DEFAULT_CONFIG = PipelineConfig()


