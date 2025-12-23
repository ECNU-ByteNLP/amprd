"""
Baseline-TPL：基于固定模板的规则系统

特点：
- 固定章节模板
- 简单插值填充
- 无LLM生成
- 无多模态、无双语

用途：评估规则系统在复杂场景下的局限，作为最基础的对照。
"""

from __future__ import annotations

import uuid
from typing import Dict, List


# 标准PRD章节列表（与主系统对齐）
TEMPLATE_SECTIONS: List[str] = [
    "overview",
    "user_persona",
    "user_stories",
    "functional_requirements",
    "non_functional_requirements",
    "user_flows",
    "kpi_and_milestones",
    "risks_and_mitigations",
    "data_and_tracking",
    "release_plan",
]


def generate_prd_template(brief: Dict) -> Dict:
    """
    Baseline-TPL：根据固定模板填充概要信息，适合作为规则系统对照。
    
    Args:
        brief: Brief字典，包含goal、domain、target_users等信息
    
    Returns:
        Dict: 结构化PRD字典，格式与主系统兼容
    """
    goal = brief.get("goal", "")
    domain = brief.get("domain", "general")
    title = brief.get("title", goal)
    prd_id = brief.get("prd_id") or str(uuid.uuid4())
    
    # 提取用户画像
    target_users = brief.get("target_users", [])
    personas_list = []
    for persona in target_users:
        if isinstance(persona, dict):
            personas_list.append(
                f"{persona.get('persona', '用户')}: "
                f"需求={persona.get('needs', '')}, "
                f"痛点={persona.get('pain_points', '')}"
            )
        else:
            personas_list.append(str(persona))
    personas_text = "\n".join(f"- {p}" for p in personas_list) if personas_list else "未指定"
    
    # 提取约束
    constraints = brief.get("key_constraints", [])
    constraints_list = []
    for constraint in constraints:
        if isinstance(constraint, dict):
            constraints_list.append(
                f"{constraint.get('type', '约束')}: {constraint.get('description', '')}"
            )
        else:
            constraints_list.append(str(constraint))
    constraints_text = "\n".join(f"- {c}" for c in constraints_list) if constraints_list else "暂无"
    
    # 提取业务指标
    business_metrics = brief.get("business_metrics", [])
    metrics_list = []
    for metric in business_metrics:
        if isinstance(metric, dict):
            metrics_list.append(
                f"{metric.get('name', '指标')}: "
                f"目标={metric.get('target', '')}, "
                f"时间={metric.get('timeframe', '')}"
            )
        else:
            metrics_list.append(str(metric))
    metrics_text = "\n".join(f"- {m}" for m in metrics_list) if metrics_list else "待定义"
    
    # 问题陈述和解决方案（如果存在）
    problem_statement = brief.get("problem_statement", "")
    solution_approach = brief.get("solution_approach", "")
    
    # 构建章节内容
    sections = []
    for section_id in TEMPLATE_SECTIONS:
        if section_id == "overview":
            content = (
                f"产品名称: {title}\n"
                f"领域: {domain}\n"
                f"产品目标: {goal}\n"
            )
            if problem_statement:
                content += f"\n问题陈述: {problem_statement}\n"
            if solution_approach:
                content += f"解决方案: {solution_approach}\n"
        elif section_id == "user_persona":
            content = f"目标用户:\n{personas_text}"
        elif section_id == "user_stories":
            content = f"基于目标用户的需求，生成用户故事。\n目标用户:\n{personas_text}"
        elif section_id == "functional_requirements":
            content = f"基于产品目标 '{goal}' 的功能需求。\n解决方案方向: {solution_approach or '待设计'}"
        elif section_id == "non_functional_requirements":
            content = f"领域: {domain}\n关键约束:\n{constraints_text}"
        elif section_id == "user_flows":
            content = f"基于解决方案 '{solution_approach or goal}' 的用户流程。"
        elif section_id == "kpi_and_milestones":
            content = f"业务指标:\n{metrics_text}\n\n产品目标: {goal}"
        elif section_id == "risks_and_mitigations":
            content = f"领域: {domain}\n关键约束:\n{constraints_text}"
        elif section_id == "data_and_tracking":
            content = f"数据埋点和追踪指标（待完善）"
        elif section_id == "release_plan":
            content = f"发布计划（待完善）"
        else:
            content = "待完善"
        
        sections.append({
            "section_id": section_id,
            "content": {
                "zh-CN": content,
            },
        })
    
    return {
        "metadata": {
            "prd_id": prd_id,
            "strategy": "rule_template",
            "domain": domain,
            "baseline_type": "template",
            "languages": ["zh-CN"],
        },
        "outputs": {
            "languages": ["zh-CN"],
            "sections": sections,
            "assets_manifest": [],  # 无多模态资产
            "glossary": {},
        },
    }


