from __future__ import annotations

import logging
from typing import Dict, Optional

from src.agents.base import Agent, AgentMessage, Blackboard
from src.models.model_client import ModelClient


class VisionAgent(Agent):
    """Produces flow diagrams and interface mockups."""

    def __init__(self, model: ModelClient) -> None:
        super().__init__(role="VisionAgent")
        self._model = model
        self._logger = logging.getLogger(__name__)

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "supply_visuals":
            return None

        plan = message.payload["plan"]
        domain = plan.get("domain", "general")
        artifacts = {}
        state_snapshot = blackboard.get_state()
        sections_state = state_snapshot.get("sections", {})
        personas = plan.get("personas", [])

        for section in plan["sections"]:
            if section["section_id"] in {"user_flows", "key_interfaces"}:
                section_id = section["section_id"]
                section_state = sections_state.get(section_id, {})
                content = section_state.get("content", {})

                # 中文内容驱动中文图
                zh_text = (content.get("zh-CN") or "").strip()
                if zh_text:
                    prompt_zh = self._build_prompt_zh(domain, section_id, zh_text, personas)
                    artifacts.setdefault(section_id, []).append(
                        self._generate_figure(
                            prompt_zh,
                            language="zh",
                            caption_cn=f"{section_id} 视觉示意图",
                            caption_en=f"{section_id} visualization (CN)",
                        )
                    )

                # 英文内容驱动英文图
                en_text = (content.get("en-US") or "").strip()
                if en_text:
                    prompt_en = self._build_prompt_en(domain, section_id, en_text, personas)
                    artifacts.setdefault(section_id, []).append(
                        self._generate_figure(
                            prompt_en,
                            language="en",
                            caption_cn=f"{section_id} 英文示意图",
                            caption_en=f"{section_id} visualization",
                        )
                    )

        for section_id, figures in artifacts.items():
            blackboard.update_state(["artifacts", section_id], figures)
            blackboard.update_state(["sections", section_id, "figures"], figures)

        return self.emit(
            receiver="TableAgent",
            intent="supply_tables",
            payload={"plan": plan},
            dependencies=[message.message_id],
        )

    def _generate_figure(
        self,
        prompt: str,
        *,
        language: str,
        caption_cn: str,
        caption_en: str,
    ) -> Dict:
        attempts = 2
        last_exc: Exception | None = None
        for _ in range(attempts):
            try:
                image_meta = self._model.generate_image(prompt)
                image_meta.update(
                    {
                        "language": language,
                        "caption": {"zh-CN": caption_cn, "en-US": caption_en},
                    }
                )
                return image_meta
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                self._logger.warning(
                    "VisionAgent 第一次生成失败，准备重试。provider=%s err=%s",
                    getattr(self._model, "name", "unknown-model"),
                    exc,
                )
        # fallback
        self._logger.warning(
            "VisionAgent 连续失败，使用占位。provider=%s err=%s",
            getattr(self._model, "name", "unknown-model"),
            last_exc,
        )
        return {
            "path": None,
            "prompt": prompt,
            "size": "unavailable",
            "provider": getattr(self._model, "name", "unknown"),
            "error": str(last_exc) if last_exc else "unknown error",
            "language": language,
            "caption": {"zh-CN": caption_cn, "en-US": caption_en},
        }

    def _build_prompt_zh(self, domain: str, section_id: str, text: str, personas: list[str]) -> str:
        key_points = self._extract_key_points_zh(text, max_points=6)
        personas_str = "、".join(personas) if personas else "用户"
        return (
            f"任务：生成高信息密度的{section_id}示意图，用于 PRD 文档插图；"
            f"领域：{domain}；主要角色：{personas_str}；"
            f"风格：简洁、对比度高、结构化、适合报告内嵌；"
            f"请突出以下要点（顺序即布局建议）：\n- " + "\n- ".join(key_points)
        )

    def _build_prompt_en(self, domain: str, section_id: str, text: str, personas: list[str]) -> str:
        key_points = self._extract_key_points_en(text, max_points=6)
        personas_str = ", ".join(personas) if personas else "users"
        return (
            f"Task: Produce a high-information {section_id} visual for PRD embedding; "
            f"Domain: {domain}; Key actors: {personas_str}; "
            f"Style: clean, high-contrast, structured, report-friendly. "
            f"Emphasize the following points in order (suggested layout):\n- " + "\n- ".join(key_points)
        )

    def _extract_key_points_zh(self, text: str, max_points: int = 6) -> list[str]:
        # 简易要点提取：按句号/分号/顿号切分，取非空片段
        seps = ["。", "；", ";", "，", ",", "\n"]
        tmp = text
        for s in seps:
            tmp = tmp.replace(s, "\n")
        points = [p.strip() for p in tmp.split("\n") if p.strip()]
        return points[:max_points] or [text[:80]]

    def _extract_key_points_en(self, text: str, max_points: int = 6) -> list[str]:
        seps = [". ", "; ", ", ", "\n"]
        tmp = text
        for s in seps:
            tmp = tmp.replace(s, "\n")
        points = [p.strip("- ").strip() for p in tmp.split("\n") if p.strip()]
        return points[:max_points] or [text[:120]]


