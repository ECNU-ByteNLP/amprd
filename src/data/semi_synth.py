from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List

from src.pipeline import MultiAgentOrchestrator
from src.data.seed_builder import SeedRecord


@dataclass
class SemiSynthConfig:
    runs_per_seed: int = 2
    output_dir: Path = Path("data/generated")


def load_seed_file(path: Path) -> List[SeedRecord]:
    seeds: List[SeedRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        seeds.append(SeedRecord(**payload))
    return seeds


def seed_to_brief(seed: SeedRecord) -> Dict:
    return {
        "prd_id": seed.seed_id,
        "domain": seed.domain,
        "goal": seed.goal,
        "target_users": [{"persona": user, "needs": ""} for user in seed.target_users],
        "key_constraints": [
            {"type": "business", "description": constraint, "priority": "P1"}
            for constraint in seed.constraints
        ],
        "platform": seed.platform,
        "pain_points": seed.pain_points,
    }


def generate_from_seeds(
    seeds: Iterable[SeedRecord],
    config: SemiSynthConfig,
) -> List[Dict]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for seed in seeds:
        for run_idx in range(config.runs_per_seed):
            orchestrator = MultiAgentOrchestrator(persist_dir=config.output_dir / seed.domain)
            state = orchestrator.run({"brief": seed_to_brief(seed)})
            outputs.append(state)
            artifact = state.get("quality", {}).get("artifact_path")
            if artifact:
                continue
    index_path = config.output_dir / "index.json"
    index_path.write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    return outputs


