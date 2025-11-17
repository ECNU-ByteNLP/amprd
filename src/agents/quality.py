from __future__ import annotations

from statistics import mean
from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard


class QualityAgent(Agent):
    """Aggregates automatic metrics and prepares the final dossier."""

    def __init__(self) -> None:
        super().__init__(role="QualityAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "aggregate":
            return None

        plan = message.payload["plan"]
        state = blackboard.get_state()
        metrics = self._compute_metrics(plan, state)
        blackboard.update_state(["quality", "auto_metrics"], metrics)

        return self.emit(
            receiver="Assembler",
            intent="assemble",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )

    def _compute_metrics(self, plan: Dict, state: Dict) -> Dict[str, float]:
        sections = plan["sections"]
        sections_state = state.get("sections", {})

        completeness_scores = []
        for meta in sections:
            section = sections_state.get(meta["section_id"], {})
            content = section.get("content", {})
            completeness_scores.append(1.0 if content else 0.0)
        completeness = mean(completeness_scores) if completeness_scores else 0.0

        alignment_flags = state.get("review", {}).get("alignment", [])
        consistency_flags = state.get("review", {}).get("consistency", [])
        alignment_score = max(0.0, 1.0 - 0.1 * len(alignment_flags))
        consistency_score = max(0.0, 1.0 - 0.1 * len(consistency_flags))

        return {
            "S_comp": round(completeness, 3),
            "S_mm": round(alignment_score, 3),
            "S_tab": 0.8,
            "S_bi": round(consistency_score, 3),
        }


