## 多模态双语 PRD 多智能体原型（纯开源栈）

本仓库实现计划中的 `Ours-MOD v1` 多智能体系统原型，以支持双语（中文/英文）多模态 PRD 的自动生成实验。核心特点：

- **多智能体协同**：需求分析、文本生成（中/英）、对齐、视觉生成、表格生成、一致性校验与质量汇总等角色通过黑板消息系统协作。
- **可复现实验管线**：所有状态写入统一黑板，最终由组装 Agent 输出符合 `schemas/prd_schema_v0_9.json` 的结构化草稿。
- **纯开源依赖**：当前默认使用 `MockModelClient`，可替换为 Qwen/Doubao 等开源模型客户端，便于后续实验扩展。

### 快速开始

1. 准备输入概要（示例见 `examples/brief_sample.json`）。
2. 运行：
   ```bash
   python -m src.cli --brief examples/brief_sample.json --output artifacts
   ```
3. 系统将依次驱动多智能体协作，并在 `artifacts/` 下输出最新的 PRD 草稿与状态快照。
4. 导出可阅读版本（示例）：
   ```bash
   python -m src.cli_export --input artifacts/<prd>.json --output exports/<prd>_zh.docx --format docx --language zh
   python -m src.cli_export --input artifacts/<prd>.json --output exports/<prd>_en.docx --format docx --language en
   ```

### 代码结构

- `schemas/prd_schema_v0_9.json`：双语多模态 PRD JSON Schema。
- `src/agents/`：各类智能体实现。
- `src/shared/blackboard.py`：线程安全黑板实现。
- `src/models/model_client.py`：模型客户端接口与 Mock 实现。
- `src/exporters/prd_renderer.py`：将结构化 PRD 渲染为 Markdown/DOCX。
- `src/pipeline/orchestrator.py`：多智能体调度器。
- `src/cli.py`：命令行入口。
- `src/cli_export.py`：PRD 导出工具（Markdown/DOCX）。

### 一键脚本运行（免命令行记忆）

- 准备 `run_config.json`（示例）：
  ```json
  {
    "brief_text": "我们要做一个面向中小商家的对账平台，目标是缩短对账周期至T+1...",
    "template_id": "figma",
    "output": "artifacts",
    "verbose": true
  }
  ```
- 运行：
  ```bash
  python scripts/run_prd.py --config run_config.json
  ```
  
- 更多配置用法与带注释示例：见 `run_config.examples.jsonc`（JSONC 带注释；如需严格 JSON，请去掉注释复制到单独文件）。

### 下一步

- 替换 Mock 客户端为真实开源 LLM/VLM。
- 扩展视觉 Agent 接入程序化流程图与控制网络。
- 补充自动指标脚本、消融实验与人评工具链。


