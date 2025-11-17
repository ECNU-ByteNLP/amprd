from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

from src.data.quality_gate import GateConfig, gate_prd


@dataclass
class AnnotationTask:
    prd_path: str
    domain: str
    platform: str
    priority: str
    issues_detected: List[str]


def sample_for_annotation(
    prd_paths: Iterable[Path],
    *,
    schema_path: Path,
    limit: int = 50,
) -> List[AnnotationTask]:
    config = GateConfig(schema_path=schema_path)
    tasks = []
    for path in prd_paths:
        gate_result = gate_prd(path, config)
        domain = "unknown"
        platform = "unknown"
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            domain = payload.get("metadata", {}).get("domain", "unknown")
            platform = ",".join(payload.get("metadata", {}).get("platform", []))
        except json.JSONDecodeError:
            pass
        priority = "high" if not gate_result["passed"] else "medium"
        tasks.append(
            AnnotationTask(
                prd_path=str(path),
                domain=domain,
                platform=platform,
                priority=priority,
                issues_detected=gate_result["schema_errors"],
            )
        )
        if len(tasks) >= limit:
            break

    return tasks


def export_annotation_tasks(tasks: List[AnnotationTask], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        for task in tasks:
            fp.write(json.dumps(asdict(task), ensure_ascii=False) + "\n")


