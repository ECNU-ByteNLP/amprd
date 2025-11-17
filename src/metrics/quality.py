from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

import json


def load_prd(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_structure_completeness(prd: Dict) -> float:
    sections = prd.get("outputs", {}).get("sections", [])
    if not sections:
        return 0.0
    covered = 0
    for section in sections:
        content = section.get("content", {})
        if any(value and value.strip() for value in content.values()):
            covered += 1
    return round(covered / len(sections), 4)


def compute_cross_modal_consistency(prd: Dict) -> float:
    sections = prd.get("outputs", {}).get("sections", [])
    anchors = 0
    matched = 0
    manifest = {asset["asset_id"]: asset for asset in prd.get("outputs", {}).get("assets_manifest", [])}

    for section in sections:
        for anchor in section.get("anchors", []):
            anchors += 1
            ref_id = anchor.get("ref_id")
            if ref_id and ref_id in manifest:
                matched += 1
    if anchors == 0:
        return 1.0
    return round(matched / anchors, 4)


def compute_table_consistency(prd: Dict) -> float:
    sections = prd.get("outputs", {}).get("sections", [])
    metrics_section = next((s for s in sections if s.get("section_id") == "kpi_and_milestones"), None)
    if not metrics_section:
        return 0.0
    tables = metrics_section.get("tables", [])
    if not tables:
        return 0.0
    score = 0.0
    for table in tables:
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        if len(headers) < 2 or not rows:
            continue
        valid_rows = [row for row in rows if any(row)]
        score += len(valid_rows) / max(len(rows), 1)
    return round(min(score, 1.0), 4)


def compute_bilingual_consistency(prd: Dict) -> float:
    sections = prd.get("outputs", {}).get("sections", [])
    if not sections:
        return 0.0
    diffs = []
    for section in sections:
        content = section.get("content", {})
        zh = len((content.get("zh-CN") or "").split())
        en = len((content.get("en-US") or "").split())
        if zh == 0 or en == 0:
            diffs.append(1.0)
        else:
            diffs.append(abs(zh - en) / max(zh, en))
    avg_diff = sum(diffs) / len(diffs)
    return round(max(0.0, 1.0 - avg_diff), 4)


def compute_stability(run_scores: List[Dict[str, float]]) -> Dict[str, float]:
    if not run_scores:
        return {"std": 0.0, "max_dev": 0.0}
    metrics = run_scores[0].keys()
    deviations: List[float] = []
    for metric in metrics:
        values = [score[metric] for score in run_scores if metric in score]
        if not values:
            continue
        mean_v = sum(values) / len(values)
        variance = sum((v - mean_v) ** 2 for v in values) / max(len(values) - 1, 1)
        deviations.append(math.sqrt(variance))
    if not deviations:
        return {"std": 0.0, "max_dev": 0.0}
    return {
        "std": round(sum(deviations) / len(deviations), 4),
        "max_dev": round(max(deviations), 4),
    }


def compute_all_metrics(prd: Dict, stability_runs: List[Dict[str, float]] | None = None) -> Dict[str, Dict]:
    return {
        "S_comp": compute_structure_completeness(prd),
        "S_mm": compute_cross_modal_consistency(prd),
        "S_tab": compute_table_consistency(prd),
        "S_bi": compute_bilingual_consistency(prd),
        "S_var": compute_stability(stability_runs or []),
    }


