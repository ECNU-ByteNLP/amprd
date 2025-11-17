from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from src.metrics.quality import compute_all_metrics, load_prd


def render_report(prd_path: Path) -> Dict:
    prd = load_prd(prd_path)
    metrics = compute_all_metrics(prd)
    return {"path": str(prd_path), "metrics": metrics}


def save_report(report: Dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def pretty_print(report: Dict) -> str:
    lines = [f"PRD 文件: {report['path']}"]
    for key, value in report["metrics"].items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


