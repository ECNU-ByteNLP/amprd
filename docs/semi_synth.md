# 半合成数据生成流程

目的：利用任务种子驱动多智能体系统，批量生成双语多模态 PRD 草稿，形成高质量训练/评测样本。

## 模块

- `src/data/semi_synth.py`
  - `SemiSynthConfig`：控制每个种子的生成次数、输出目录等。
  - `seed_to_brief`：将 `SeedRecord` 转换为多智能体系统的输入概要。
  - `generate_from_seeds`：遍历种子，调用 `MultiAgentOrchestrator` 生成并写出产物（自动记录 `artifact_path` 与状态快照）。

## 示例

```python
from pathlib import Path
from src.data.semi_synth import load_seed_file, generate_from_seeds, SemiSynthConfig

seeds = load_seed_file(Path("data/seeds/financial_mobile.jsonl"))
config = SemiSynthConfig(runs_per_seed=2, output_dir=Path("data/generated/financial"))
generate_from_seeds(seeds, config)
```

## 注意事项

- 需在运行前为多智能体系统配置真实 LLM/VLM 客户端，以提升生成质量。
- 建议将每次生成的状态快照与指标报告同步保存，供弱监督门控与误差分析使用。
- 对于跨域/OOD 实验，可按领域分别生成并在后续划分中混合使用。 

