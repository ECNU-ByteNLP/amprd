# 自动实验与显著性检验流水线

## 组成

- `src/experiments/auto_eval.py`
  - `evaluate_system_outputs`：计算系统产物的指标。
  - `compare_systems`：对比多智能体与基线的指标，输出 Wilcoxon、Cliff's δ、Bootstrap CI。
- `src/cli_auto_eval.py`：命令行入口。
- `src/experiments/statistics.py`：统计工具（Wilcoxon、Cliff's δ、Bootstrap）。

## 使用示例

```bash
python -m src.cli_auto_eval \
  --baseline-dir results/baseline_txt \
  --ours-dir results/ours_multiagent \
  --output reports/auto_eval.json
```

输出 JSON 结构示例：

```json
{
  "S_comp": {
    "ours_mean": 0.88,
    "baseline_mean": 0.63,
    "wilcoxon": {"statistic": 2.0, "p_value": 0.031},
    "cliffs_delta": 0.42,
    "bootstrap_ci": [0.15, 0.29]
  }
}
```

## 后续扩展

- 支持 FDR 校正、方差分析及多指标融合。
- 自动拉取多轮生成稳定性并加入 `S_var` 分析。
- 与可视化面板对接（Plotly/Altair），生成论文级别的图表。 

