"""
Baseline-TXT：使用单一 LLM 生成纯文本 PRD

特点：
- 单一模型，无多智能体协作
- 无多模态生成（无图像、表格）
- 无双语对齐（仅中文）
- 一次性生成，无迭代优化

用途：对照多智能体系统在结构完整度、跨模态一致性、双语对齐上的提升。
"""

from __future__ import annotations

import uuid
from typing import Dict, Optional

from src.models.model_client import ModelClient, MockModelClient


def generate_prd_text_only(brief: Dict, model: Optional[ModelClient] = None) -> Dict:
    """
    Baseline-TXT：使用单一 LLM 生成纯文本 PRD，不涉及多模态或双语对齐。
    
    Args:
        brief: Brief字典，包含goal、domain、target_users等信息
        model: 模型客户端（可选，默认使用MockModelClient）
    
    Returns:
        Dict: 结构化PRD字典，格式与主系统兼容
    """
    client = model or MockModelClient()
    
    goal = brief.get("goal", "提升核心指标")
    domain = brief.get("domain", "general")
    title = brief.get("title", goal)
    
    # 提取用户画像信息
    target_users = brief.get("target_users", [])
    personas_text = "\n".join([
        f"- {p.get('persona', '用户')}: {p.get('needs', '')} (痛点: {p.get('pain_points', '')})"
        if isinstance(p, dict) else f"- {p}"
        for p in target_users
    ])
    
    # 提取约束信息
    constraints = brief.get("key_constraints", [])
    constraints_text = "\n".join([
        f"- {c.get('type', '约束')}: {c.get('description', '')}"
        for c in constraints
    ])
    
    # 提取业务指标
    business_metrics = brief.get("business_metrics", [])
    metrics_text = "\n".join([
        f"- {m.get('name', '指标')}: 目标={m.get('target', '')}, 时间={m.get('timeframe', '')}"
        for m in business_metrics
    ])
    
    # 构建详细的prompt
    prompt = (
        f"你是一位资深产品经理，请为以下产品需求生成完整的PRD文档。\n\n"
        f"## 产品信息\n"
        f"- 产品名称: {title}\n"
        f"- 领域: {domain}\n"
        f"- 产品目标: {goal}\n\n"
        f"## 目标用户\n"
        f"{personas_text or '未指定'}\n\n"
        f"## 关键约束\n"
        f"{constraints_text or '无'}\n\n"
        f"## 业务指标\n"
        f"{metrics_text or '待定义'}\n\n"
        f"## 任务\n"
        f"请生成完整的PRD文档，包含以下章节：\n"
        f"1. 产品概述（Overview）：包含问题陈述、解决方案概述、目标和成功指标\n"
        f"2. 用户画像（User Persona）：详细描述每个用户画像的背景、需求、痛点和目标\n"
        f"3. 用户故事（User Stories）：使用Job Story或User Story格式描述用户需求\n"
        f"4. 功能需求（Functional Requirements）：详细的功能描述、优先级、验收标准\n"
        f"5. 非功能需求（Non-Functional Requirements）：性能、安全、可用性、技术约束\n"
        f"6. 用户流程（User Flows）：主要用户流程、用户旅程地图、流程优化点\n"
        f"7. KPI与里程碑（KPI and Milestones）：成功指标、里程碑计划、假设验证\n"
        f"8. 风险与缓解（Risks and Mitigations）：关键风险、影响评估、缓解策略\n"
        f"9. 数据与追踪（Data and Tracking）：数据埋点、追踪指标\n"
        f"10. 发布计划（Release Plan）：发布阶段、交付物、依赖关系\n\n"
        f"请使用中文输出，内容要具体、可执行，避免空泛描述。"
    )
    
    # 生成完整PRD文本
    full_text = client.generate_text(prompt)
    
    # 构建结构化输出（与主系统格式兼容）
    prd_id = brief.get("prd_id") or str(uuid.uuid4())
    
    return {
        "metadata": {
            "prd_id": prd_id,
            "generator": client.name,
            "domain": domain,
            "baseline_type": "text_only",
            "languages": ["zh-CN"],  # 仅中文
        },
        "outputs": {
            "languages": ["zh-CN"],
            "sections": [
                {
                    "section_id": "overview",
                    "content": {
                        "zh-CN": full_text,  # 完整文本作为overview
                    },
                },
            ],
            "assets_manifest": [],  # 无多模态资产
            "glossary": {},
        },
    }


