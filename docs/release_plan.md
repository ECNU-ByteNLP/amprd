# 开源发布与复现计划

## 目录结构

- `schemas/`：PRD JSON Schema。
- `src/`：多智能体系统、数据流程、评测脚本。
- `docs/`：实验说明、评测方案、数据处理指南。
- `examples/`：输入样例。
- `scripts/build_release.py`：打包脚本。

## 复现步骤

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 生成多智能体 PRD：
   ```bash
   python -m src.cli --brief examples/brief_sample.json --output artifacts
   ```
3. 运行基线与自动评测：
   ```bash
   python -m src.cli_ablation --brief examples/brief_sample.json --output experiments/ablation
   python -m src.cli_auto_eval --baseline-dir results/baseline --ours-dir artifacts --output reports/auto_eval.json
   ```
4. 组织人工评测：参考 `docs/human_eval.md`。

## 合规与脱敏

- 抓取数据仅限公开网页，并保留来源与许可记录。
- 发布数据前执行去标识化（参见 `docs/data_pipeline.md`）。
- 提供 `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` 模板（后续补充）。

## 打包

```bash
python scripts/build_release.py --output release/v0.1
```

生成的 `manifest.json` 列出所有包含的目录，便于校验。

## 后续工作

- 增补模型配置示例（Qwen/Doubao API）。
- 添加 Dockerfile 与 CI 流程。
- 发布数据许可文件（CC-BY-SA 或定制许可）。 

