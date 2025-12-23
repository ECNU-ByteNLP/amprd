"""
Baseline-RET：检索增强生成

特点：
- 使用sentence-transformers进行语义检索
- 从真实PRD语料库中检索相似内容
- 结合检索结果生成PRD
- 弱多模态（检索到的内容可能包含图像/表格引用）

用途：比较检索式多模态与生成式多模态的差异。
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.model_client import ModelClient

import numpy as np  # type: ignore[import]

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import]
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class RetrievalBaseline:
    """
    Baseline-RET：通过语义检索找到相似PRD内容，结合文本生成。
    在无多模态模型时提供弱多模态对照。
    """

    def __init__(
        self,
        corpus_dir: Optional[Path] = None,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ) -> None:
        """
        Args:
            corpus_dir: PRD语料库目录（包含JSON格式的PRD文件）
            model_name: sentence-transformers模型名称（默认使用多语言模型）
        """
        self.corpus_dir = corpus_dir or Path("data/chinese_prds/processed")
        self.model_name = model_name
        
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers is required for RetrievalBaseline. "
                "Install it with: pip install sentence-transformers"
            )
        
        self.model = SentenceTransformer(model_name)
        self.index: List[Tuple[str, Dict, np.ndarray]] = []  # (path, metadata, embedding)
        self._load_corpus()

    def _load_corpus(self) -> None:
        """加载PRD语料库并构建索引"""
        if not self.corpus_dir.exists():
            return
        
        # 加载所有JSON格式的PRD文件
        for path in self.corpus_dir.rglob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                
                # 提取文本内容用于检索
                sections = payload.get("outputs", {}).get("sections", payload.get("sections", []))
                text_parts = []
                
                for section in sections:
                    content = section.get("content", {})
                    # 优先使用中文，如果没有则使用英文
                    text = content.get("zh-CN") or content.get("en-US") or ""
                    if text and len(text) > 50:  # 只索引有足够内容的章节
                        text_parts.append(text[:500])  # 限制长度
                
                if not text_parts:
                    continue
                
                # 合并文本并生成embedding
                combined_text = " ".join(text_parts)
                embedding = self.model.encode(combined_text, normalize_embeddings=True)
                
                # 保存元数据
                metadata = {
                    "path": str(path),
                    "domain": payload.get("metadata", {}).get("domain", "unknown"),
                    "title": payload.get("metadata", {}).get("title", path.stem),
                    "sections_count": len(sections),
                }
                
                self.index.append((str(path), metadata, embedding))
            except Exception:
                continue  # 跳过无法解析的文件

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        检索相似的PRD内容
        
        Args:
            query: 查询文本（通常是Brief的goal或problem_statement）
            top_k: 返回的相似PRD数量
        
        Returns:
            List[Dict]: 相似PRD列表，每个包含path、metadata、similarity_score
        """
        if not self.index:
            return []
        
        query_emb = self.model.encode(query, normalize_embeddings=True)
        scored = [
            (metadata, float(np.dot(query_emb, emb)))
            for _, metadata, emb in self.index
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        
        return [
            {
                "path": metadata["path"],
                "domain": metadata["domain"],
                "title": metadata["title"],
                "similarity_score": score,
            }
            for metadata, score in scored[:top_k]
        ]

    def generate(self, brief: Dict, model: Optional["ModelClient"] = None) -> Dict:
        """
        基于检索结果生成PRD
        
        Args:
            brief: Brief字典
            model: 可选的LLM模型（用于生成文本，如果为None则仅使用检索结果）
        
        Returns:
            Dict: 结构化PRD字典，格式与主系统兼容
        """
        goal = brief.get("goal", "")
        domain = brief.get("domain", "general")
        title = brief.get("title", goal)
        prd_id = brief.get("prd_id") or str(uuid.uuid4())
        
        # 构建查询（结合goal和problem_statement）
        problem_statement = brief.get("problem_statement", "")
        query = f"{goal} {problem_statement}".strip()
        
        # 检索相似PRD
        retrieved = self.retrieve(query, top_k=3)
        
        # 构建检索结果摘要
        retrieved_summary = []
        for item in retrieved:
            retrieved_summary.append(
                f"- {item['title']} (领域: {item['domain']}, 相似度: {item['similarity_score']:.3f})"
            )
        retrieved_text = "\n".join(retrieved_summary) if retrieved_summary else "未找到相似PRD"
        
        # 如果提供了模型，使用模型生成内容；否则仅使用检索结果
        if model:
            prompt = (
                f"你是一位资深产品经理，请基于以下检索到的相似PRD示例，生成新的PRD文档。\n\n"
                f"## 产品信息\n"
                f"- 产品名称: {title}\n"
                f"- 领域: {domain}\n"
                f"- 产品目标: {goal}\n\n"
                f"## 检索到的相似PRD示例\n"
                f"{retrieved_text}\n\n"
                f"## 任务\n"
                f"请参考上述相似PRD示例的风格和结构，生成完整的PRD文档。"
            )
            generated_text = model.generate_text(prompt)
        else:
            generated_text = (
                f"产品名称: {title}\n"
                f"领域: {domain}\n"
                f"产品目标: {goal}\n\n"
                f"## 检索到的相似PRD示例\n"
                f"{retrieved_text}\n\n"
                f"（注：此基线系统仅检索相似内容，未使用LLM生成详细内容）"
            )
        
        return {
            "metadata": {
                "prd_id": prd_id,
                "strategy": "retrieval",
                "domain": domain,
                "baseline_type": "retrieval",
                "languages": ["zh-CN"],
                "retrieved_count": len(retrieved),
            },
            "outputs": {
                "languages": ["zh-CN"],
                "sections": [
                    {
                        "section_id": "overview",
                        "content": {
                            "zh-CN": generated_text,
                        },
                        "retrieved_references": retrieved,  # 保存检索到的参考
                    },
                ],
                "assets_manifest": [],  # 检索基线不生成新资产
                "glossary": {},
            },
        }


