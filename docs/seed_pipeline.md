# 任务种子抽取与聚类流程

目标：从抓取并清洗后的网页文本中，构建多领域 PRD 生成所需的任务种子（五元组），并进行去重与聚类，为半合成生成提供高质量输入。

## 抽取

- 使用 `src/data/seed_builder.py::SeedBuilder` 从文本中抽取：
  - `goal`：产品目标或核心改进方向；
  - `pain_points`：用户痛点或业务挑战；
  - `target_users`：目标用户群；
  - `platform`：默认由配置提供（web/mobile/miniapp 等）；
  - `constraints`：合规、性能、资源等限制。
- 输出：`SeedRecord` JSONL 文件，每行一个种子，带有 `source_hash` 便于追踪。

## 聚类与去重（未代码化部分）

后续步骤建议使用 `sentence-transformers` / `faiss`：

1. 对 `goal + pain_points + constraints` 进行嵌入编码；
2. 使用 HDBSCAN 或 K-means 聚类，过滤重复或相似度高的种子；
3. 每个簇保留代表性种子，并记录来源领域与平台。

## 用法示例

```python
from pathlib import Path
from src.data.seed_builder import build_seed_corpus

text_files = Path("data/clean").glob("*.txt")
seeds = build_seed_corpus(
    text_files,
    domain="financial",
    platform="mobile",
    output_path=Path("data/seeds/financial_mobile.jsonl"),
)
print(f"共生成 {len(seeds)} 条任务种子")
```

生成的种子可直接输入多智能体系统，用于半合成多模态 PRD 草稿的生成。 

