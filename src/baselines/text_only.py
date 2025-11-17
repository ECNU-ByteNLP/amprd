from __future__ import annotations

from typing import Dict

from src.models.model_client import ModelClient, MockModelClient


def generate_prd_text_only(brief: Dict, model: ModelClient | None = None) -> Dict:
    """
    Baseline-TXT：使用单一 LLM 生成纯文本 PRD，不涉及多模态或双语对齐。
    返回结构化字典，方便与主系统对比。
    """

    client = model or MockModelClient()
    goal = brief.get("goal", "提升核心指标")
    domain = brief.get("domain", "general")
    prompt = (
        f"领域: {domain}\n"
        f"目标: {goal}\n"
        "请输出 PRD 结构，包含概述、用户画像、需求列表、KPI 与风险。"
    )
    body = client.generate_text(prompt)
    return {
        "metadata": {"generator": client.name, "domain": domain},
        "sections": [
            {"section_id": "overview", "text": body},
        ],
    }


