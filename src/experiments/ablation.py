from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.pipeline import MultiAgentOrchestrator
from src.models.model_client import MockModelClient, ModelClient


@dataclass
class AblationConfig:
    """Configuration entry describing a single ablation scenario."""

    name: str
    disabled_agents: List[str]
    communication_mode: str
    text_model_cn: Optional[ModelClient] = None
    text_model_en: Optional[ModelClient] = None
    vision_model: Optional[ModelClient] = None

    def to_dict(self) -> Dict:
        payload = asdict(self)
        payload.update(
            {
                "text_model_cn": getattr(self.text_model_cn, "name", None),
                "text_model_en": getattr(self.text_model_en, "name", None),
                "vision_model": getattr(self.vision_model, "name", None),
            }
        )
        return payload


def run_ablation_suite(
    brief: Dict,
    configs: Iterable[AblationConfig],
    *,
    output_dir: Path,
) -> List[Dict]:
    """
    Execute a series of ablation experiments.

    Returns:
        List of result dictionaries (one per experiment).
    """

    results = []
    for config in configs:
        orchestrator = MultiAgentOrchestrator(
            text_model_cn=config.text_model_cn or MockModelClient(),
            text_model_en=config.text_model_en or MockModelClient(),
            vision_model=config.vision_model or MockModelClient(),
            persist_dir=output_dir / config.name,
        )
        state = orchestrator.run({"brief": brief, "config": config.to_dict()})

        result = {
            "config": config.to_dict(),
            "quality": state.get("quality", {}),
            "review": state.get("review", {}),
            "artifact_path": state.get("quality", {}).get("artifact_path"),
        }
        results.append(result)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ablation_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return results


def predefined_configs() -> List[AblationConfig]:
    """Default set of ablation scenarios mirroring论文实验设置。"""

    return [
        AblationConfig(name="full_system", disabled_agents=[], communication_mode="blackboard"),
        AblationConfig(
            name="no_alignment",
            disabled_agents=["AlignmentAgent"],
            communication_mode="blackboard",
        ),
        AblationConfig(
            name="no_visuals",
            disabled_agents=["VisionAgent"],
            communication_mode="blackboard",
        ),
        AblationConfig(
            name="queue_communication",
            disabled_agents=[],
            communication_mode="async_queue",
        ),
    ]


