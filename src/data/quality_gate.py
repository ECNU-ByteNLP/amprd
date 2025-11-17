from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import jsonschema  # type: ignore[import]

from src.metrics.quality import compute_all_metrics


@dataclass
class GateConfig:
    schema_path: Path
    threshold_comp: float = 0.7
    threshold_mm: float = 0.6
    threshold_bi: float = 0.6


def load_schema(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(payload: Dict, schema: Dict) -> List[str]:
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{error.message} @ {list(error.path)}" for error in validator.iter_errors(payload)]


def gate_prd(prd_path: Path, config: GateConfig) -> Dict:
    payload = json.loads(prd_path.read_text(encoding="utf-8"))
    schema = load_schema(config.schema_path)
    schema_errors = validate_schema(payload, schema)
    metrics = compute_all_metrics(payload)

    passed = (
        not schema_errors
        and metrics["S_comp"] >= config.threshold_comp
        and metrics["S_mm"] >= config.threshold_mm
        and metrics["S_bi"] >= config.threshold_bi
    )

    return {
        "path": str(prd_path),
        "passed": passed,
        "schema_errors": schema_errors,
        "metrics": metrics,
    }


def gate_directory(prd_dir: Path, config: GateConfig) -> List[Dict]:
    reports = []
    for path in prd_dir.glob("*.json"):
        reports.append(gate_prd(path, config))
    output_path = prd_dir / "gate_report.json"
    output_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    return reports


