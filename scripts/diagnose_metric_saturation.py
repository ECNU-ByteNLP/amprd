"""
诊断“弱基线导致指标+1.0饱和”的根因：对比 baseline_text_only vs full_system 的结构事实。

输出：
- 每个系统：PRD数量、章节数均值/范围、出现关键章节的数量、是否有表格/图示、overview是否双语
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any


def load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sections(prd: Dict[str, Any]) -> List[Dict[str, Any]]:
    secs = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if isinstance(secs, dict):
        return [v for v in secs.values() if isinstance(v, dict)]
    if isinstance(secs, list):
        return [s for s in secs if isinstance(s, dict)]
    return []


def section_ids(prd: Dict[str, Any]) -> List[str]:
    return [s.get("section_id") for s in sections(prd) if s.get("section_id")]


def has_tables(prd: Dict[str, Any]) -> bool:
    for s in sections(prd):
        if s.get("tables"):
            return True
    return bool(prd.get("tables") or prd.get("outputs", {}).get("tables"))


def has_figures(prd: Dict[str, Any]) -> bool:
    for s in sections(prd):
        if s.get("figures"):
            return True
    return bool(prd.get("figures") or prd.get("outputs", {}).get("assets_manifest"))


def overview_bilingual(prd: Dict[str, Any]) -> bool:
    for s in sections(prd):
        if s.get("section_id") == "overview":
            c = s.get("content", {})
            return isinstance(c, dict) and bool(c.get("zh-CN") and c.get("en-US"))
    return False


def summarize(dir_path: Path) -> Dict[str, Any]:
    files = sorted(dir_path.glob("prd_*.json"))
    n = len(files)
    sec_counts: List[int] = []
    ids_set = set()
    kpi = risk = nfr = stories = 0
    tables = figures = bi = 0

    for f in files:
        prd = load(f)
        ids = section_ids(prd)
        sec_counts.append(len(ids))
        ids_set.update(ids)
        if "kpi_and_milestones" in ids:
            kpi += 1
        if "risks_and_mitigations" in ids:
            risk += 1
        if "non_functional_requirements" in ids:
            nfr += 1
        if "user_stories" in ids:
            stories += 1
        if has_tables(prd):
            tables += 1
        if has_figures(prd):
            figures += 1
        if overview_bilingual(prd):
            bi += 1

    if sec_counts:
        sec_mean = sum(sec_counts) / len(sec_counts)
        sec_min = min(sec_counts)
        sec_max = max(sec_counts)
    else:
        sec_mean = sec_min = sec_max = 0

    return {
        "n": n,
        "sections_mean": round(sec_mean, 2),
        "sections_min": sec_min,
        "sections_max": sec_max,
        "unique_section_ids": len(ids_set),
        "has_kpi_section": kpi,
        "has_risk_section": risk,
        "has_nfr_section": nfr,
        "has_user_stories": stories,
        "has_any_tables": tables,
        "has_any_figures": figures,
        "overview_bilingual": bi,
    }


def main():
    base = Path("results/baseline_text_only")
    full = Path("results/full_system")
    if not base.exists() or not full.exists():
        print("❌ 缺少 results 目录，先跑完实验再诊断。")
        return
    print("baseline_text_only:", summarize(base))
    print("full_system:", summarize(full))


if __name__ == "__main__":
    main()






