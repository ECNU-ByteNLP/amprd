from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import logging

from src.agents.assembler import AssemblerAgent
from src.agents.base import Agent, AgentMessage
from src.agents.consistency import ConsistencyAgent
from src.agents.lead_analyst import LeadAnalystAgent
from src.agents.quality import QualityAgent
from src.agents.table_agent import TableAgent
from src.agents.text_gen import build_text_agents
from src.agents.vision import VisionAgent
from src.agents.alignment import AlignmentAgent
from src.agents.noop import (
    NoOpAlignmentAgent,
    NoOpConsistencyAgent,
    NoOpTableAgent,
    NoOpVisionAgent,
)
from src.models.model_client import MockModelClient, ModelClient
from src.models.qwen_client import create_qwen_clients_from_env
from src.models.openai_client import create_openai_clients_from_env
from src.shared.blackboard import InMemoryBlackboard


class MultiAgentOrchestrator:
    """Coordinates the multi-agent PRD generation pipeline."""

    _logger = logging.getLogger("MultiAgentOrchestrator")

    def __init__(
        self,
        *,
        text_model_cn: ModelClient | None = None,
        text_model_en: ModelClient | None = None,
        vision_model: ModelClient | None = None,
        persist_dir: Path | None = None,
        disabled_agents: list[str] | None = None,
        communication_mode: str = "blackboard",
        model_provider: str = "qwen",
    ) -> None:
        self.blackboard = InMemoryBlackboard(
            persist_path=(persist_dir / "blackboard.json") if persist_dir else None
        )

        # Support multiple providers via env vars.
        # Priority:
        # 1) explicit injected clients (text_model_cn/en/vision_model)
        # 2) provider-specific env clients (qwen/openai)
        # 3) Mock fallback (keeps pipeline executable without keys)
        provider = (model_provider or "qwen").lower()
        if provider == "openai":
            env_text_cn, env_text_en, env_vision = create_openai_clients_from_env()
        else:
            env_text_cn, env_text_en, env_vision = create_qwen_clients_from_env()

        text_cn = text_model_cn or env_text_cn or MockModelClient()
        text_en = text_model_en or env_text_en or MockModelClient()
        vision = vision_model or env_vision or MockModelClient()

        disabled = set(disabled_agents or [])
        self.communication_mode = communication_mode

        self.agents: Dict[str, Agent] = {
            "LeadAnalyst": LeadAnalystAgent(),
            **build_text_agents(text_cn, text_en),
            "AlignmentAgent": AlignmentAgent(),
            "VisionAgent": VisionAgent(vision),
            "TableAgent": TableAgent(text_cn),
            "ConsistencyAgent": ConsistencyAgent(),
            "QualityAgent": QualityAgent(),
            "Assembler": AssemblerAgent((persist_dir or Path("artifacts")).resolve()),
        }

        # 消融实验关键修复：
        # 不能简单移除中间Agent，否则消息链会断裂，导致没有artifact_path/PRD落盘。
        # 对于被禁用的中间Agent，用No-Op替身保持链路继续，但不产生该Agent贡献。
        noop_map: Dict[str, Agent] = {
            "AlignmentAgent": NoOpAlignmentAgent(),
            "VisionAgent": NoOpVisionAgent(),
            "TableAgent": NoOpTableAgent(),
            "ConsistencyAgent": NoOpConsistencyAgent(),
        }
        for name in list(self.agents.keys()):
            if name in disabled and name in noop_map:
                self.agents[name] = noop_map[name]
            elif name in disabled:
                # 其它Agent若被禁用，按原策略移除（当前消融配置不应禁用Quality/Assembler/TextGen等）
                self.agents.pop(name, None)

    def run(self, payload: Dict) -> Dict:
        self._logger.info("流水线启动：初始化黑板并下发初始消息给 LeadAnalyst")
        init = AgentMessage.create(
            sender="System",
            receiver="LeadAnalyst",
            intent="init",
            payload=payload,
        )
        self.blackboard.post_message(init)
        self._drive()
        self._logger.info("流水线完成：返回最终黑板状态")
        return self.blackboard.get_state()

    def _drive(self) -> None:
        self._logger.info("开始驱动各 Agent（通信模式=%s）", self.communication_mode)
        pending = True
        visited: set[str] = set()

        while pending:
            pending = False
            for role, agent in self.agents.items():
                messages = self.blackboard.fetch_pending(role)
                if not messages:
                    continue
                self._logger.info("Agent %s 拉取到 %d 条待处理消息", role, len(messages))
                pending = True
                if self.communication_mode == "async_queue" and len(messages) > 1:
                    for leftover in messages[1:]:
                        self.blackboard.post_message(leftover)
                    processing_batch = [messages[0]]
                    self._logger.debug("异步队列模式：本轮处理 1 条，其余 %d 条回队列", len(messages) - 1)
                else:
                    processing_batch = messages

                for message in processing_batch:
                    visited.add(message.message_id)
                    self._logger.info(
                        "处理中：role=%s intent=%s msg_id=%s 依赖=%s",
                        role,
                        message.intent,
                        message.message_id,
                        getattr(message, "dependencies", None),
                    )
                    response = agent.handle(message, self.blackboard)
                    self.blackboard.update_status(message.message_id, "completed")
                    self._logger.info("完成：role=%s intent=%s msg_id=%s", role, message.intent, message.message_id)
                    if response:
                        self._logger.info("Agent %s 产生响应 → %s intent=%s", role, response.receiver, response.intent)
                        self.blackboard.post_message(response)
            if not pending:
                break


