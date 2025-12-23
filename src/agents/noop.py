from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard


class NoOpAlignmentAgent(Agent):
    """
    消融用：替代 AlignmentAgent，但不做任何对齐检查，保持流水线继续向下游推进。
    """

    def __init__(self) -> None:
        super().__init__(role="AlignmentAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "align":
            return None
        plan = message.payload["plan"]
        blackboard.update_state(["review", "alignment"], [])
        return self.emit(
            receiver="VisionAgent",
            intent="supply_visuals",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )


class NoOpVisionAgent(Agent):
    """
    消融用：替代 VisionAgent，不生成任何图片/图示，但继续触发 TableAgent。
    """

    def __init__(self) -> None:
        super().__init__(role="VisionAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "supply_visuals":
            return None
        plan = message.payload["plan"]
        # 不写入任何artifacts/figures
        return self.emit(
            receiver="TableAgent",
            intent="supply_tables",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )


class NoOpTableAgent(Agent):
    """
    消融用：替代 TableAgent，不生成任何表格，但继续触发 ConsistencyAgent。
    """

    def __init__(self) -> None:
        super().__init__(role="TableAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "supply_tables":
            return None
        plan = message.payload["plan"]
        # 不写入 tables
        return self.emit(
            receiver="ConsistencyAgent",
            intent="verify",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )


class NoOpConsistencyAgent(Agent):
    """
    消融用：替代 ConsistencyAgent，不做一致性检查，但继续触发 QualityAgent。
    """

    def __init__(self) -> None:
        super().__init__(role="ConsistencyAgent")

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "verify":
            return None
        plan = message.payload["plan"]
        blackboard.update_state(["review", "consistency"], [])
        return self.emit(
            receiver="QualityAgent",
            intent="aggregate",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )


