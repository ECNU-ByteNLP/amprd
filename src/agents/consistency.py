from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard


class ConsistencyAgent(Agent):
    """Runs structural and cross-modal consistency checks."""

    def __init__(self) -> None:
        super().__init__(role="ConsistencyAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "verify":
            return None

        plan = message.payload["plan"]
        state = blackboard.get_state()

        issues = []
        sections_state = state.get("sections", {})
        for section in plan["sections"]:
            section_id = section["section_id"]
            if section_id not in sections_state:
                issues.append({"section": section_id, "issue": "missing_section"})
                continue
            content = sections_state[section_id].get("content", {})
            if not content.get("zh-CN"):
                issues.append({"section": section_id, "issue": "missing_zh"})
            if not content.get("en-US"):
                issues.append({"section": section_id, "issue": "missing_en"})

        blackboard.update_state(["review", "consistency"], issues)

        return self.emit(
            receiver="QualityAgent",
            intent="aggregate",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )


