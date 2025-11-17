from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard
from src.models.model_client import ModelClient


class TableAgent(Agent):
    """Generates KPI tables and milestone plans."""

    def __init__(self, model: ModelClient) -> None:
        super().__init__(role="TableAgent")
        self._model = model

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "supply_tables":
            return None

        plan = message.payload["plan"]
        kpi_prompt = self._build_prompt(plan, "kpi_and_milestones")
        table_text = self._model.generate_text(kpi_prompt)

        table_rows = self._parse_table(table_text)
        table_payload = {
            "table_id": "tbl-kpi",
            "title": {"zh-CN": "关键指标", "en-US": "Key Metrics"},
            "headers": [
                {"zh-CN": "指标", "en-US": "Metric"},
                {"zh-CN": "目标", "en-US": "Target"},
                {"zh-CN": "时间范围", "en-US": "Timeframe"},
            ],
            "rows": table_rows,
        }

        blackboard.update_state(["sections", "kpi_and_milestones", "tables"], [table_payload])

        return self.emit(
            receiver="ConsistencyAgent",
            intent="verify",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )

    def _build_prompt(self, plan: Dict, section: str) -> str:
        goal = plan.get("goal", "提高用户体验")
        domain = plan.get("domain", "通用领域")
        return (
            f"领域: {domain}\n"
            f"目标: {goal}\n"
            f"任务: 为 {section} 生成结构化KPI表，包含指标、目标值、时间范围。"
        )

    def _parse_table(self, value: str) -> list:
        rows = []
        for line in value.splitlines():
            if "|" not in line:
                continue
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 3:
                rows.append(
                    [
                        {"zh-CN": parts[0], "en-US": parts[0]},
                        {"value": parts[1], "unit": "", "timeframe": ""},
                        {"zh-CN": parts[2], "en-US": parts[2]},
                    ]
                )
        if not rows:
            rows.append(
                [
                    {"zh-CN": "月活用户", "en-US": "Monthly Active Users"},
                    {"value": "100k", "unit": "", "timeframe": "Q3"},
                    {"zh-CN": "三个月", "en-US": "3 months"},
                ]
            )
        return rows


