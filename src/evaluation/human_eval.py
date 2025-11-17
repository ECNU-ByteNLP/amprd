from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


@dataclass
class HumanEvalTask:
    prd_path: str
    system: str
    domain: str
    dimensions: List[str]


@dataclass
class HumanEvalResult:
    prd_path: str
    rater_id: str
    dimension: str
    score: float


def create_eval_tasks(
    prd_pairs: Iterable[Dict],
    *,
    dimensions: Sequence[str],
    output_path: Path,
) -> List[HumanEvalTask]:
    tasks = []
    for pair in prd_pairs:
        for system in ("ours", "baseline"):
            tasks.append(
                HumanEvalTask(
                    prd_path=pair[f"{system}_path"],
                    system=system,
                    domain=pair.get("domain", "unknown"),
                    dimensions=list(dimensions),
                )
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(task) for task in tasks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return tasks


def load_results(path: Path) -> List[HumanEvalResult]:
    results = []
    with path.open("r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            results.append(
                HumanEvalResult(
                    prd_path=row["prd_path"],
                    rater_id=row["rater_id"],
                    dimension=row["dimension"],
                    score=float(row["score"]),
                )
            )
    return results


def krippendorff_alpha(
    scores: List[HumanEvalResult],
    *,
    dimension: str,
    min_score: float = 1.0,
    max_score: float = 7.0,
) -> float:
    """
    计算 Krippendorff α（序顺尺度）。
    实现参考：Krippendorff, 2011. 适用于评分型 Likert 数据。
    """

    filtered = [s for s in scores if s.dimension == dimension]
    if not filtered:
        return 0.0

    items: Dict[str, Dict[str, float]] = {}
    for score in filtered:
        items.setdefault(score.prd_path, {})[score.rater_id] = score.score

    # 构造频数矩阵
    values = sorted(set(score.score for score in filtered))
    if len(values) == 1:
        return 1.0

    value_range = max_score - min_score
    coincidence = 0.0
    total_pairs = 0.0
    for ratings in items.values():
        raters = list(ratings.values())
        n = len(raters)
        if n < 2:
            continue
        total_pairs += n * (n - 1)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                coincidence += ((raters[i] - raters[j]) / value_range) ** 2

    if total_pairs == 0:
        return 0.0

    observed_disagreement = coincidence / total_pairs

    # 预期分歧
    distribution: Dict[float, int] = {}
    for score in filtered:
        distribution[score.score] = distribution.get(score.score, 0) + 1
    total = sum(distribution.values())
    expected = 0.0
    for v_i, n_i in distribution.items():
        for v_j, n_j in distribution.items():
            expected += (n_i * n_j) * ((v_i - v_j) / value_range) ** 2
    expected_disagreement = expected / (total * (total - 1))
    if expected_disagreement == 0:
        return 1.0
    alpha = 1 - observed_disagreement / expected_disagreement
    return max(min(alpha, 1.0), -1.0)


def summarize_results(results: List[HumanEvalResult]) -> Dict[str, Dict[str, float]]:
    summary: Dict[str, Dict[str, float]] = {}
    by_dimension: Dict[str, List[float]] = {}
    for result in results:
        key = f"{result.dimension}:{result.prd_path}"
        summary.setdefault(key, {})
        summary[key][result.rater_id] = result.score
        by_dimension.setdefault(result.dimension, []).append(result.score)
    stats = {"dimensions": {}}
    for dimension, scores in by_dimension.items():
        stats["dimensions"][dimension] = sum(scores) / len(scores)
    return stats


