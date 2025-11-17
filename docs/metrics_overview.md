# 自动评测指标原型（v0.1）

本节描述 `metric-proto` 任务交付的指标实现与使用方式。

## 指标一览

- `S_comp`：结构完整度。计算已生成 section 的比例。
- `S_mm`：跨模态一致性。统计文本锚点引用的资产是否存在。
- `S_tab`：表格一致性。检查 KPI/里程碑表格是否具备有效行。
- `S_bi`：双语一致性。基于中英文词数差异的轻量近似。
- `S_var`：生成稳定性。可接受多个 run 的质量得分，输出总体标准差与最大偏差。

## 代码入口

- `src/metrics/quality.py`：指标核心实现。
- `src/metrics/report.py`：报告渲染与保存。
- `src/cli_metrics.py`：命令行工具。

## 使用示例

```bash
python -m src.cli_metrics --prd artifacts/prd_<id>.json --output reports/prd_<id>_metrics.json
```

输出示例：

```
PRD 文件: artifacts/prd_demo.json
  S_comp: 0.73
  S_mm: 0.67
  S_tab: 0.8
  S_bi: 0.91
  S_var: {'std': 0.05, 'max_dev': 0.09}
```

后续计划：

- `S_sem` 将在弱监督与信息抽取模块完成后接入（依赖 NLI/信息覆盖计算）。
- `S_mm` 将引入 CLIP/VLM 相似度，而不仅仅是锚点命中率。
- `S_bi` 将替换为 COMETKiwi/术语表一致性检验。

当前版本旨在支撑快速迭代与单元测试，便于后续与实际模型、评测脚本整合。 

