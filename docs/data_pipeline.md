# 数据抓取与清洗流水线（v0.1）

目标：构建可复现、合规的公开网页抓取 → 清洗 → 归档流程，为金融/电商/医疗三领域的数据集准备基础素材。

## 组件

1. `src/data/crawler.py::CrawlPipeline`
   - 输入：`CrawlTask(url, domain, tags)` 列表。
   - 输出：HTML 快照（`snapshots/`）、元数据（`metadata/`）以及 JSONL 日志。
   - 记录：状态码、时间戳、SHA-256 哈希、领域标签、许可占位。
2. `src/data/cleaner.py`
   - 利用 `beautifulsoup4` 剥离脚本/样式，输出整洁文本与摘要。
   - 支持批量处理（`clean_bulk`）。

## 使用示例

```python
from pathlib import Path
from src.data.crawler import CrawlPipeline, CrawlTask
from src.data.cleaner import clean_bulk

pipeline = CrawlPipeline(Path("data/raw"))
records = pipeline.run([
    CrawlTask(url="https://example.com/finance", domain="financial", tags=["finance", "regulation"]),
])

html_files = [Path(record.content_path) for record in records if record.status == 200]
clean_results = clean_bulk(html_files, Path("data/clean"))
```

## 合规要点

- 仅抓取公开访问页面，并尊重 robots.txt（后续版本将新增自动校验）。
- 保存原始快照以便审计，同时在元数据文件中记录来源与许可信息。
- 清洗阶段执行去标识化（可接入 `presidio` 等工具，留待后续实现）。

## 下一步

- 接入速率限制与自定义 Header。
- 集成 `trafilatura` / `readability-lxml` 获得更高质量文本。
- 加入 URL 去重、相似度聚类与违规条款自动识别。

