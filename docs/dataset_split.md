# 数据集划分与泄漏防护

## 分割策略

- 默认比例：Train 70%、Dev 10%、Test 20%，外加 OOD-Test（跨域）。
- OOD 域：金融/电商/医疗之间交叉，可根据实验配置选择某一域作为 OOD。
- 随机种子：统一使用 `SplitConfig.seed`，确保可复现。

## 工具

- `src/data/splitter.py`
  - `split_dataset`：读取 PRD JSON 元数据，按领域拆分。
  - `save_split`：写出分割方案。

示例：

```python
from pathlib import Path
from src.data.splitter import SplitConfig, split_dataset, save_split

config = SplitConfig(ood_domains=["medical"])
splits = split_dataset(Path("data/generated/all"), config)
save_split(splits, Path("data/splits/split_v1.json"))
```

## 泄漏防护建议

- 保证同一 `prd_id` 或同源数据仅出现在一个集合中。
- 针对多模态资产（界面图/流程图），可在生成阶段记录哈希，分割时避免重复。
- 若使用真实项目文档，应在抓取阶段对相同域名/URL 聚类并切分。

## 后续扩展

- 纳入平台（mobile/web/miniapp）维度的 OOD 划分。
- 引入嵌入相似度阈值，过滤语义重复。 

