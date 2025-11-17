from __future__ import annotations

import uuid
from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard


class LeadAnalystAgent(Agent):
    """Parses the initial brief and expands it into a structured plan."""

    def __init__(self) -> None:
        super().__init__(role="LeadAnalyst")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "init":
            return None

        brief = message.payload.get("brief", {})
        plan = self._draft_plan(brief)
        blackboard.update_state(["planning", "structure"], plan)

        response_payload: Dict[str, Dict] = {"plan": plan, "brief": brief}
        return self.emit(
            receiver="TextGen_CN",
            intent="draft_section",
            payload=response_payload,
            dependencies=[message.message_id],
        )

    def _draft_plan(self, brief: Dict) -> Dict[str, Dict]:
        domain = brief.get("domain", "general")
        constraints = brief.get("key_constraints", [])
        return {
            "prd_id": brief.get("prd_id") or str(uuid.uuid4()),
            "domain": domain,
            "goal": brief.get("goal", "提升用户体验"),
            "personas": [persona.get("persona", "Primary User") for persona in brief.get("target_users", [])],
            "sections": [
                {"section_id": "overview", "required": True},
                {"section_id": "user_persona", "required": True},
                {"section_id": "user_stories", "required": True},
                {"section_id": "functional_requirements", "required": True},
                {"section_id": "non_functional_requirements", "required": True},
                {"section_id": "user_flows", "required": True},
                {"section_id": "key_interfaces", "required": True},
                {"section_id": "kpi_and_milestones", "required": True},
                {"section_id": "risks_and_mitigations", "required": False},
                {"section_id": "data_and_tracking", "required": True},
                {"section_id": "release_plan", "required": True},
            ],
            "constraints": constraints,
        }


