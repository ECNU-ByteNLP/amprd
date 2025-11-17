from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard


class AlignmentAgent(Agent):
    """Ensures bilingual sections align structurally."""

    def __init__(self) -> None:
        super().__init__(role="AlignmentAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "align":
            return None

        plan = message.payload["plan"]
        state = blackboard.get_state()
        sections = plan["sections"]

        alignment_flags = []
        for meta in sections:
            section_id = meta["section_id"]
            content = state.get("sections", {}).get(section_id, {}).get("content", {})
            zh = (content.get("zh-CN") or "").strip()
            en = (content.get("en-US") or "").strip()
            if not zh or not en:
                alignment_flags.append({"section": section_id, "issue": "missing_language"})
            elif len(zh.split()) == 0 or len(en.split()) == 0:
                alignment_flags.append({"section": section_id, "issue": "empty_content"})

        blackboard.update_state(["review", "alignment"], alignment_flags)

        return self.emit(
            receiver="VisionAgent",
            intent="supply_visuals",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )


