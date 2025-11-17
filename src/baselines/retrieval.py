from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np  # type: ignore[import]
from sentence_transformers import SentenceTransformer  # type: ignore[import]


class RetrievalBaseline:
    """
    Baseline-MIX：通过语义检索找到相似界面/流程图，结合文本生成。
    在无多模态模型时提供弱多模态对照。
    """

    def __init__(self, corpus_dir: Path, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.corpus_dir = corpus_dir
        self.model = SentenceTransformer(model_name)
        self.index: List[Tuple[str, np.ndarray]] = []
        self._load_corpus()

    def _load_corpus(self) -> None:
        for path in self.corpus_dir.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            caption = payload.get("caption", "")
            embedding = self.model.encode(caption, normalize_embeddings=True)
            self.index.append((str(path), embedding))

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        if not self.index:
            return []
        query_emb = self.model.encode(query, normalize_embeddings=True)
        scored = [
            (path, float(np.dot(query_emb, emb)))
            for path, emb in self.index
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [path for path, _ in scored[:top_k]]

    def generate(self, brief: Dict) -> Dict:
        goal = brief.get("goal", "")
        retrieved = self.retrieve(goal)
        return {
            "metadata": {"strategy": "retrieval", "retrieved_assets": retrieved},
            "sections": [
                {"section_id": "overview", "content": f"目标：{goal}", "anchors": retrieved},
            ],
        }


