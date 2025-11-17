from __future__ import annotations

from typing import Dict, List


TEMPLATE_SECTIONS: List[str] = [
    "产品概述",
    "目标用户与场景",
    "核心功能",
    "非功能需求",
    "数据与埋点",
    "KPI 与里程碑",
    "风险与缓解",
]


def generate_prd_template(brief: Dict) -> Dict:
    """
    Baseline-TPL：根据固定模板填充概要信息，适合作为规则系统对照。
    """

    goal = brief.get("goal", "")
    domain = brief.get("domain", "")
    target_users = ", ".join(persona.get("persona", "") for persona in brief.get("target_users", []))
    constraints = "; ".join(c.get("description", "") for c in brief.get("key_constraints", []))

    sections = []
    for section in TEMPLATE_SECTIONS:
        if section == "产品概述":
            content = f"{domain} 领域，目标：{goal}"
        elif section == "目标用户与场景":
            content = f"目标用户：{target_users or '未指定'}"
        elif section == "风险与缓解":
            content = f"当前约束：{constraints or '暂无'}"
        else:
            content = "待完善"
        sections.append({"section_id": section, "content": content})

    return {
        "metadata": {"strategy": "rule_template", "domain": domain},
        "sections": sections,
    }


