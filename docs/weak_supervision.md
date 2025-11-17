# 弱监督质量门控流程

目的：对批量生成的多模态 PRD 进行自动筛选，确保进入数据集或评测流水线的样本满足结构与一致性标准。

## 模块

- `src/data/quality_gate.py`
  - `GateConfig`：指定 Schema、阈值。
  - `gate_prd`：对单个 PRD 进行 Schema 校验 + 指标打分。
  - `gate_directory`：批量处理目录，输出 `gate_report.json`。
- 依赖指标：
  - `S_comp`、`S_mm`、`S_bi`：来自 `src/metrics/quality.py`。

## 示例

```python
from pathlib import Path
from src.data.quality_gate import GateConfig, gate_directory

config = GateConfig(schema_path=Path("schemas/prd_schema_v0_9.json"), threshold_comp=0.75)
reports = gate_directory(Path("data/generated/financial"), config)
passed = [r for r in reports if r["passed"]]
print(f"通过样本 {len(passed)} / {len(reports)}")
```

## 扩展计划

- 引入 `S_sem`（语义覆盖）、`S_tab`（表格一致），并支持自定义权重。
- 将 `schema_errors` 分类映射为回溯指令，自动触发多智能体重生成。
- 汇总历史分数，动态调整阈值与再生成次数。 

