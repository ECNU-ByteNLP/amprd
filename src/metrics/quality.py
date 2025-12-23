from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

import json


def load_prd(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_structure_completeness(prd: Dict) -> float:
    # 兼容两种结构：schema结构（outputs.sections）和扁平化结构（sections）
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    covered = 0
    for section in sections:
        content = section.get("content", {})
        if any(value and value.strip() and not value.strip().startswith("[mock") for value in content.values()):
            covered += 1
    return round(covered / len(sections), 4)


def compute_cross_modal_consistency(prd: Dict) -> float:
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    assets_manifest = prd.get("outputs", {}).get("assets_manifest", prd.get("assets_manifest", []))
    
    anchors = 0
    matched = 0
    manifest = {asset["asset_id"]: asset for asset in assets_manifest}

    for section in sections:
        for anchor in section.get("anchors", []):
            anchors += 1
            ref_id = anchor.get("ref_id")
            if ref_id and ref_id in manifest:
                matched += 1
    
    # 如果没有anchors，但有figures，检查figures是否在manifest中
    if anchors == 0:
        has_figures = False
        for section in sections:
            figures = section.get("figures", [])
            if figures:
                has_figures = True
                # 检查是否有有效的图片路径
                for fig in figures:
                    if fig.get("path") or fig.get("image_path"):
                        matched += 1
        if has_figures:
            return 1.0 if matched > 0 else 0.0
        return 1.0
    return round(matched / anchors, 4)


def compute_table_consistency(prd: Dict) -> float:
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
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
    """
    计算双语一致性 S_bi
    
    优化方案（符合顶会标准）：
    1. 使用jieba进行中文分词（准确的中文词数统计）
    2. 使用字符数对比作为备选方案（更公平的对比方式）
    3. 综合考虑词数和字符数差异
    
    返回：0.0-1.0，值越大表示双语一致性越好
    """
    # 兼容两种结构
    sections = prd.get("outputs", {}).get("sections", prd.get("sections", []))
    if not sections:
        return 0.0
    
    # 尝试导入jieba（如果可用）
    try:
        import jieba
        HAS_JIEBA = True
    except ImportError:
        HAS_JIEBA = False
    
    diffs = []
    for section in sections:
        content = section.get("content", {})
        zh_text = content.get("zh-CN") or ""
        en_text = content.get("en-US") or ""
        
        # 忽略mock内容
        if "[mock" in zh_text.lower() or "[mock" in en_text.lower():
            continue
        
        # 方法1：使用jieba进行中文分词（如果可用）
        if HAS_JIEBA:
            zh_words = list(jieba.cut(zh_text))
            zh_word_count = len([w for w in zh_words if w.strip()])  # 过滤空白
            en_word_count = len(en_text.split())
            
            if zh_word_count == 0 or en_word_count == 0:
                diffs.append(1.0)
            else:
                # 计算词数比例差异
                word_diff = abs(zh_word_count - en_word_count) / max(zh_word_count, en_word_count)
                
                # 方法2：字符数对比（作为补充）
                zh_char_count = len(zh_text.replace(" ", "").replace("\n", ""))
                en_char_count = len(en_text.replace(" ", "").replace("\n", ""))
                
                if zh_char_count == 0 or en_char_count == 0:
                    char_diff = 1.0
                else:
                    char_diff = abs(zh_char_count - en_char_count) / max(zh_char_count, en_char_count)
                
                # 综合词数和字符数差异（加权平均）
                combined_diff = 0.6 * word_diff + 0.4 * char_diff
                diffs.append(combined_diff)
        else:
            # 备选方案：使用字符数对比（不需要jieba）
            zh_char_count = len(zh_text.replace(" ", "").replace("\n", ""))
            en_char_count = len(en_text.replace(" ", "").replace("\n", ""))
            
            if zh_char_count == 0 or en_char_count == 0:
                diffs.append(1.0)
            else:
                char_diff = abs(zh_char_count - en_char_count) / max(zh_char_count, en_char_count)
                diffs.append(char_diff)
    
    if not diffs:
        return 0.0
    
    avg_diff = sum(diffs) / len(diffs)
    # 转换为一致性分数（差异越小，一致性越高）
    consistency_score = max(0.0, 1.0 - avg_diff)
    return round(consistency_score, 4)


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
    """
    计算所有基础质量指标
    
    注意：扩展指标（S_sem, S_biz, S_tech, S_risk, S_expert）请使用
    src.metrics.extended_quality.compute_all_extended_metrics()
    """
    return {
        "S_comp": compute_structure_completeness(prd),
        "S_mm": compute_cross_modal_consistency(prd),
        "S_tab": compute_table_consistency(prd),
        "S_bi": compute_bilingual_consistency(prd),
        "S_var": compute_stability(stability_runs or []),
    }


