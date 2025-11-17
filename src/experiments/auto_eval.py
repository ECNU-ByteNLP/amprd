from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from src.metrics.quality import compute_all_metrics
from src.experiments.statistics import bootstrap_ci, cliffs_delta, wilcoxon_test


@dataclass
class ExperimentResult:
    system: str
    prd_path: str
    metrics: Dict[str, float]


def evaluate_system_outputs(system: str, prd_files: List[Path]) -> List[ExperimentResult]:
    results = []
    for path in prd_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics = compute_all_metrics(payload)
        results.append(
            ExperimentResult(system=system, prd_path=str(path), metrics=metrics)
        )
    return results


def aggregate_metrics(results: List[ExperimentResult]) -> Dict[str, List[float]]:
    aggregated: Dict[str, List[float]] = {}
    for result in results:
        for key, value in result.metrics.items():
            if isinstance(value, dict):
                continue
            aggregated.setdefault(key, []).append(value)
    return aggregated


def compare_systems(
    baseline_results: List[ExperimentResult],
    ours_results: List[ExperimentResult],
) -> Dict[str, Dict]:
    baseline_metrics = aggregate_metrics(baseline_results)
    ours_metrics = aggregate_metrics(ours_results)

    report: Dict[str, Dict] = {}
    for metric in ours_metrics:
        ours_values = ours_metrics.get(metric, [])
        base_values = baseline_metrics.get(metric, [])
        if not ours_values or not base_values:
            continue
        wilcoxon = wilcoxon_test(ours_values, base_values)
        delta = cliffs_delta(ours_values, base_values)
        ci = bootstrap_ci([o - b for o, b in zip(ours_values, base_values)])
        report[metric] = {
            "ours_mean": float(sum(ours_values) / len(ours_values)),
            "baseline_mean": float(sum(base_values) / len(base_values)),
            "wilcoxon": wilcoxon,
            "cliffs_delta": delta,
            "bootstrap_ci": ci,
        }
    return report


def save_experiment_report(results: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


