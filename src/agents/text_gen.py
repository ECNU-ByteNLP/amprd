from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard
from src.models.model_client import ModelClient


class TextGenerationAgent(Agent):
    """Generates localized textual sections for the PRD."""

    def __init__(self, role: str, language: str, model: ModelClient) -> None:
        super().__init__(role=role)
        self._language = language
        self._model = model

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent not in {"draft_section", "revise_section"}:
            return None

        plan: Dict = message.payload["plan"]
        brief: Dict = message.payload.get("brief", {})

        sections = plan["sections"]
        generated_sections = {}
        for section in sections:
            section_id = section["section_id"]
            prompt = self._build_prompt(section_id, plan, brief)
            generated_sections[section_id] = self._model.generate_text(prompt)
            blackboard.update_state(
                ["sections", section_id, "content", self._language],
                generated_sections[section_id],
            )

        if self._language == "zh-CN":
            return self.emit(
                receiver="TextGen_EN",
                intent="draft_section",
                payload={
                    "plan": plan,
                    "brief": brief,
                    "dependencies": list(generated_sections.keys()),
                },
                dependencies=[message.message_id],
            )
        else:
            return self.emit(
                receiver="AlignmentAgent",
                intent="align",
                payload={"plan": plan},
                dependencies=[message.message_id],
            )

    def _build_prompt(self, section_id: str, plan: Dict, brief: Dict) -> str:
        goal = brief.get("goal", "一个创新功能")
        domain = plan.get("domain", "通用领域")
        persona = ", ".join(plan.get("personas", ["核心用户"]))
        constraints = "; ".join(
            c.get("description", "") for c in plan.get("constraints", [])
        )
        return (
            f"领域: {domain}\n"
            f"目标: {goal}\n"
            f"用户画像: {persona}\n"
            f"约束: {constraints or '无'}\n"
            f"当前小节: {section_id}\n"
            f"请用 {self._language} 输出结构化PRD段落。"
        )


def build_text_agents(model_cn: ModelClient, model_en: ModelClient) -> Dict[str, Agent]:
    cn_agent = TextGenerationAgent("TextGen_CN", "zh-CN", model_cn)
    en_agent = TextGenerationAgent("TextGen_EN", "en-US", model_en)
    return {
        cn_agent.role: cn_agent,
        en_agent.role: en_agent,
    }


