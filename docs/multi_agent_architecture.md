# 多智能体协作原型（MAS-proto）

## Agent 角色

| Role | 职责 | 关键输入 | 关键输出 |
| ---- | ---- | -------- | -------- |
| `LeadAnalyst` | 解析概要、生成章节计划与约束列表 | Brief | Plan JSON、任务分派 |
| `TextGen_CN` / `TextGen_EN` | 按章节生成中英文文本 | Plan、Brief | 双语段落、术语锚点 |
| `AlignmentAgent` | 校验中英对齐、触发修订 | 状态黑板 | 对齐标记、下一步指令 |
| `VisionAgent` | 生成流程图/界面示意 | Plan、黑板状态 | 视觉资产元数据 |
| `TableAgent` | 输出 KPI/里程碑等表格 | Plan、Brief | 表格 JSON |
| `ConsistencyAgent` | 结构/双语/跨模态一致性检查 | 黑板状态 | 问题列表、回溯指令 |
| `QualityAgent` | 聚合指标、准备装配 | 黑板状态、计划 | 自动指标 |
| `Assembler` | 输出最终 PRD 包并记录路径 | 黑板状态、计划 | JSON 产物、资产路径 |

## 通信机制

- **黑板模型**：`src/shared/blackboard.py::InMemoryBlackboard` 储存状态与消息队列。
- **消息格式**：`AgentMessage`（含 `intent`、`payload`、`dependencies`、`status`）。
- **回溯策略**：`ConsistencyAgent` / `AlignmentAgent` 发现问题时，发布 `intent="revise_section"` 的消息重新触发生成。
- **通信模式**：支持 `blackboard`（同步批量）与 `async_queue`（异步逐条）。
- **禁用 Agent**：`MultiAgentOrchestrator` 构造时可通过 `disabled_agents` 参数进行 ablation。

## 配置

```python
from pathlib import Path
from src.pipeline import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator(
    persist_dir=Path("artifacts/run1"),
    communication_mode="blackboard",
    disabled_agents=[],
)
state = orchestrator.run({"brief": {...}})
```

## 扩展点

- 将 `ModelClient` 替换为真实 Qwen/Doubao 客户端。
- 将视觉 Agent 扩展为“程序化渲染 + 生成模型”双通路，并记录来源。
- 通过事件订阅机制引入新的评审 Agent（如安全/隐私审查）。

## 消融实验支持

- `src/experiments/ablation.py` 提供预设配置：
  - `no_alignment`：关闭对齐 Agent；
  - `no_visuals`：关闭视觉 Agent；
  - `queue_communication`：切换异步消息模式。
- 实验结果写入 `experiments/ablation/ablation_results.json`，可与自动评测脚本联动。

该文档即为 MAS 原型说明，可用于论文附录与开源 README 的相关章节。 

