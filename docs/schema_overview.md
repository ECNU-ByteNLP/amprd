# PRD Schema v0.9 概览

本文档补充说明 `schemas/prd_schema_v0_9.json` 的关键结构，便于数据生成、校验与评测脚本实现。

## 元数据 (`metadata`)

- `prd_id`：UUID，唯一标识。
- `domain` / `platform`：领域与平台列表（移动/Web/小程序等）。
- `agent_trace`：记录多智能体角色、模型版本、迭代次数、随机种子和采样参数，支持复现与协同分析。
- `source_refs`：所有外部参考的 URI、时间戳与许可声明。

## 输入 (`inputs`)

- `brief`：任务种子，包含目标（goal）、用户画像、关键约束（合规、性能等）、业务指标与竞品参考。
- `optional_assets`：可选多模态提示，如草图、思维导图、操作日志。

## 输出 (`outputs`)

- `languages`：当前支持 `zh-CN` 与 `en-US`。
- `sections`：PRD 主体，依据 `section_id` 分为概述、用户画像、用户故事、功能/非功能需求、流程、界面、KPI、风险、数据埋点、发布计划等模块。
  - `content`：按语言存储文本段落。
  - `tables`/`stories`/`requirements`/`flows` 等子结构在各自 section 下定义。
  - `anchors` 与 `linked_*` 字段用于跨模态引用（文本 ↔ 图像/流程/表格）。
- `glossary`：术语表，确保双语一致。
- `citations`：每个外部引用的来源索引与置信度。
- `assets_manifest`：所有生成或引用的图像与流程文件的路径、哈希、生成器及许可。
- `quality_report`：自动指标结果、重写标记、人评占位。

## 质量指标字段

- `S_comp`：结构完整度。
- `S_sem`：语义充分性子指标（overall/coverage/nli_score）。
- `S_mm`：跨模态一致性。
- `S_tab`：表格一致性。
- `S_bi`：双语一致性。
- `S_var`：生成稳定性（std / max_dev）。

## JSON Schema 校验

使用示例：

```bash
pip install jsonschema
python - <<'PY'
import json, jsonschema
from pathlib import Path

schema = json.loads(Path("schemas/prd_schema_v0_9.json").read_text(encoding="utf-8"))
payload = json.loads(Path("artifacts/prd_example.json").read_text(encoding="utf-8"))
jsonschema.validate(payload, schema)
print("validate ok")
PY
```

该结构为后续指标计算、数据集构建与发布提供统一标准，可与多智能体黑板状态无缝对接。随后若新增多模态字段（如音频或交互模拟），只需在 `sections` 子结构扩展相应模式并同步更新文档与 Schema。 

