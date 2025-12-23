"""
基线系统实现

包含三个基线系统：
1. Baseline-TXT（TextOnly）：单一LLM生成纯文本PRD
2. Baseline-TPL（Template）：基于固定模板的规则系统
3. Baseline-RET（Retrieval）：检索增强生成
4. Baseline-SP（StrongPrompt）：单一LLM + 强提示词约束，直接输出可交付结构化PRD（双语/表格/风险/追踪/图示引用）
"""

from src.baselines.text_only import generate_prd_text_only
from src.baselines.template import generate_prd_template
from src.baselines.retrieval import RetrievalBaseline
from src.baselines.strong_prompt import generate_prd_strong_prompt

__all__ = [
    "generate_prd_text_only",
    "generate_prd_template",
    "RetrievalBaseline",
    "generate_prd_strong_prompt",
]

