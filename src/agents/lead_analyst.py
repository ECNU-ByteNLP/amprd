from __future__ import annotations

import uuid
from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard


class LeadAnalystAgent(Agent):
    """
    Parses the initial brief and expands it into a structured plan.
    
    创新点：实现问题空间和解决方案空间分离（参考Intercom, Airbnb, Asana, Miro, Basecamp最佳实践）
    参考：https://pmprompt.com/blog/prd-templates
    """

    def __init__(self) -> None:
        super().__init__(role="LeadAnalyst")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "init":
            return None

        brief = message.payload.get("brief", {})
        template = message.payload.get("template")
        
        plan = self._draft_plan(brief, template)
        blackboard.update_state(["planning", "structure"], plan)

        response_payload: Dict[str, Dict] = {"plan": plan, "brief": brief}
        return self.emit(
            receiver="TextGen_CN",
            intent="draft_section",
            payload=response_payload,
            dependencies=[message.message_id],
        )

    def _draft_plan(self, brief: Dict, template: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        创建结构化计划，明确分离问题空间和解决方案空间
        
        问题空间（Problem Space）：
        - 问题陈述（problem_statement）
        - 用户痛点（pain_points）
        - 问题影响量化（problem_impact）
        
        解决方案空间（Solution Space）：
        - 解决方案概述（solution_approach）
        - 功能需求（functional_requirements）
        - 技术规格（technical_specs）
        """
        domain = brief.get("domain", "general")
        constraints = brief.get("key_constraints", [])
        
        # 提取问题空间信息
        problem_statement = brief.get("problem_statement", "")
        pain_points = []
        for persona in brief.get("target_users", []):
            if "pain_points" in persona:
                pain_points.append(persona["pain_points"])
        
        # 提取解决方案空间信息
        solution_approach = brief.get("solution_approach", "")
        
        # 根据模板调整章节结构
        sections = self._build_sections(brief, template)
        
        plan = {
            "prd_id": brief.get("prd_id") or str(uuid.uuid4()),
            "domain": domain,
            "goal": brief.get("goal", "提升用户体验"),
            "personas": [
                {
                    "persona": persona.get("persona", "Primary User"),
                    "needs": persona.get("needs", ""),
                    "pain_points": persona.get("pain_points", ""),
                }
                for persona in brief.get("target_users", [])
            ],
            "sections": sections,
            "constraints": constraints,
            # 问题空间
            "problem_space": {
                "problem_statement": problem_statement,
                "pain_points": pain_points,
                "problem_impact": brief.get("problem_impact", ""),
            },
            # 解决方案空间
            "solution_space": {
                "solution_approach": solution_approach,
                "solution_alternatives": brief.get("solution_alternatives", []),
            },
            # 模板信息
            "template_style": template.get("id") if template else None,
        }
        
        return plan
    
    def _build_sections(self, brief: Dict, template: Optional[Dict] = None) -> list:
        """根据模板和Brief构建章节结构"""
        # 标准章节（问题空间优先）
        standard_sections = [
            {"section_id": "overview", "required": True, "focus": "problem"},  # 问题陈述
            {"section_id": "user_persona", "required": True, "focus": "problem"},  # 用户画像和痛点
            {"section_id": "user_stories", "required": True, "focus": "problem"},  # 用户故事（问题导向）
            {"section_id": "user_flows", "required": True, "focus": "solution"},  # 用户流程（解决方案）
            {"section_id": "functional_requirements", "required": True, "focus": "solution"},  # 功能需求
            {"section_id": "non_functional_requirements", "required": True, "focus": "solution"},  # 非功能需求
            {"section_id": "key_interfaces", "required": True, "focus": "solution"},  # 关键界面
            {"section_id": "kpi_and_milestones", "required": True, "focus": "both"},  # KPI和里程碑
            {"section_id": "risks_and_mitigations", "required": False, "focus": "both"},  # 风险和缓解
            {"section_id": "data_and_tracking", "required": True, "focus": "solution"},  # 数据埋点
            {"section_id": "release_plan", "required": True, "focus": "solution"},  # 发布计划
        ]
        
        # 如果提供了模板，可以根据模板调整
        if template:
            # 可以添加模板特定的章节
            pass
        
        return standard_sections


