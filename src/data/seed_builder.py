from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List


@dataclass
class SeedRecord:
    seed_id: str
    domain: str
    goal: str
    pain_points: List[str]
    target_users: List[str]
    platform: str
    constraints: List[str]
    source_hash: str


class SeedBuilder:
    """
    从清洗文本中抽取“问题—目标—约束—用户—平台”五元组的弱监督工具。
    模块化设计，便于后续替换为 LLM 或信息抽取模型。
    """

    def __init__(self, domain: str, platform: str) -> None:
        self.domain = domain
        self.platform = platform

    def build(self, text_path: Path) -> SeedRecord:
        text = text_path.read_text(encoding="utf-8")
        goal = self._extract_goal(text)
        pains = self._extract_pain_points(text)
        users = self._extract_users(text)
        constraints = self._extract_constraints(text)

        return SeedRecord(
            seed_id=text_path.stem,
            domain=self.domain,
            goal=goal,
            pain_points=pains,
            target_users=users,
            platform=self.platform,
            constraints=constraints,
            source_hash=text_path.stem,
        )

    def _extract_goal(self, text: str) -> str:
        match = re.search(r"(目标|purpose|aim)\D{0,20}[:：]\s*([^\n。]+)", text, re.IGNORECASE)
        if match:
            return match.group(2).strip()
        sentences = re.split(r"[。.!?]", text)
        return sentences[0].strip() if sentences else "提升用户价值"

    def _extract_pain_points(self, text: str) -> List[str]:
        matches = re.findall(r"(痛点|challenge|问题)[:：]\s*([^\n。]+)", text, re.IGNORECASE)
        return [m[1].strip() for m in matches][:5] or ["流程复杂", "缺乏实时反馈"]

    def _extract_users(self, text: str) -> List[str]:
        candidates = re.findall(r"(用户|customer|personas?)[:：]\s*([^\n。]+)", text, re.IGNORECASE)
        users = []
        for _, segment in candidates:
            users.extend(part.strip() for part in re.split(r"[，,;/]", segment))
        counter = Counter(filter(None, users))
        return [item for item, _ in counter.most_common(5)] or ["核心用户"]

    def _extract_constraints(self, text: str) -> List[str]:
        matches = re.findall(r"(约束|constraint|compliance)[:：]\s*([^\n。]+)", text, re.IGNORECASE)
        return [m[1].strip() for m in matches][:5]


def build_seed_corpus(
    text_files: Iterable[Path],
    *,
    domain: str,
    platform: str,
    output_path: Path,
) -> List[SeedRecord]:
    builder = SeedBuilder(domain=domain, platform=platform)
    seeds = [builder.build(path) for path in text_files]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        for seed in seeds:
            fp.write(json.dumps(asdict(seed), ensure_ascii=False) + "\n")
    return seeds


