from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import json
import hashlib

from src.agents.base import Agent, AgentMessage, Blackboard


class AssemblerAgent(Agent):
    """Materializes the final PRD package on disk."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__(role="Assembler")
        self._output_dir = output_dir

    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        if message.intent != "assemble":
            return None

        plan = message.payload["plan"]
        state = blackboard.get_state()

        bundle = self._build_bundle(plan, state)
        path = self._persist(bundle)
        blackboard.update_state(["quality", "artifact_path"], str(path))

        return None

    def _build_bundle(self, plan: Dict, state: Dict) -> Dict:
        metadata = {
            "prd_id": plan.get("prd_id"),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "domain": plan.get("domain"),
        }
        sections = []
        assets_manifest = []
        for meta in plan["sections"]:
            section_state = state.get("sections", {}).get(meta["section_id"], {})
            figures = section_state.get("figures", [])
            # 收集图片清单为资产清单
            for fig in figures:
                image_path = fig.get("image_path") or fig.get("path")
                if not image_path:
                    continue
                checksum = ""
                try:
                    p = Path(image_path)
                    if p.exists() and p.is_file():
                        checksum = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                except Exception:
                    checksum = ""
                assets_manifest.append(
                    {
                        "asset_id": f"fig-{meta['section_id']}-{len(assets_manifest)+1}",
                        "path": str(image_path),
                        "checksum": checksum,
                        "generator": "VisionAgent",
                        "license": "",
                    }
                )
            sections.append(
                {
                  "section_id": meta["section_id"],
                  "content": section_state.get("content", {}),
                  "tables": section_state.get("tables", []),
                  "figures": figures,
                }
            )
        return {
            "metadata": metadata,
            "sections": sections,
            "assets_manifest": assets_manifest,
            "quality": state.get("quality", {}),
        }

    def _persist(self, payload: Dict) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"prd_{payload['metadata'].get('prd_id', 'draft')}.json"
        path = self._output_dir / filename
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


