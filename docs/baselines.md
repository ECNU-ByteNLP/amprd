# 基线系统实现说明

## Baseline-TXT（强 LLM 纯文本）

- 模块：`src/baselines/text_only.py::generate_prd_text_only`
- 特点：单模型输出结构化文本 PRD，无多模态/双语逻辑。
- 用途：对照多智能体在结构完整度、跨模态一致性上的提升。

## Baseline-TPL（规则模板）

- 模块：`src/baselines/template.py::generate_prd_template`
- 特点：固定章节模板 + 简单插值，代表传统流程文档工具。
- 用途：评估规则系统在复杂场景下的局限。

## Baseline-MIX（检索增强弱多模态）

- 模块：`src/baselines/retrieval.py::RetrievalBaseline`
- 特点：使用 `sentence-transformers` 检索相似界面/流程，作为弱多模态补充。
- 用途：比较检索式多模态与生成式多模态的差异。

## 示例

```python
from pathlib import Path
from src.baselines.text_only import generate_prd_text_only
from src.baselines.template import generate_prd_template
from src.baselines.retrieval import RetrievalBaseline

brief = {...}

txt = generate_prd_text_only(brief)
tpl = generate_prd_template(brief)
retr = RetrievalBaseline(Path("corpus/ui")).generate(brief)
```

后续实验中将统一使用上述三个基线，与多智能体系统进行定量/定性对比。 

