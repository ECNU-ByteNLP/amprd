# 多模态双语 PRD 多智能体原型系统 (AMPRD)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)

**AMPRD** (Automated Multimodal PRD) 是一个基于多智能体协作的**双语（中文/英文）多模态产品需求文档（PRD）自动生成系统**。系统通过多个专业化智能体协同工作，从业务概要自动生成包含文本、表格、流程图和界面示意图的结构化 PRD 文档。

## ✨ 核心特性

- 🤖 **多智能体协同架构**：需求分析、文本生成（中/英）、双语对齐、视觉生成、表格生成、一致性校验与质量汇总等角色通过黑板消息系统协作
- 📝 **双语一致性保证**：中英文生成链路完全对等，并由 Alignment Agent 对段落缺失、长度差异做检查
- 🎨 **多模态内容生成**：自动生成流程图、界面示意图、KPI 表格、里程碑计划等
- 📊 **结构化输出**：符合 `schemas/prd_schema_v0_9.json` 的结构化 JSON，支持导出为 Markdown/DOCX
- 🔄 **可复现实验管线**：所有状态写入统一黑板，支持完整追溯与审计
- 🔌 **纯开源模型支持**：默认使用 Mock 客户端，可替换为 Qwen/Doubao 等开源模型

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 依赖包见 `requirements.txt`

### 安装

```bash
# 克隆仓库
git clone https://github.com/ECNU-ByteNLP/amprd.git
cd amprd

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选，用于真实模型）
cp env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 使用方式

#### 方式一：自然语言输入（推荐）

1. 准备配置文件 `run_config.json`：
```json
{
  "brief_text": "我们要做一个面向中小商家的对账平台，目标是缩短对账周期至T+1...",
  "template_id": "figma",
  "output": "artifacts",
  "verbose": true
}
```

2. 运行脚本：
```bash
python scripts/run_prd.py --config run_config.json
```

#### 方式二：结构化 Brief JSON

1. 准备 Brief JSON（示例见 `examples/brief_sample.json`）：
```json
{
  "title": "产品名称",
  "domain": "financial",
  "goal": "核心目标描述",
  "target_users": [{"persona": "目标用户"}],
  "key_constraints": [{"type": "技术约束", "description": "描述"}],
  "business_metrics": [{"name": "KPI", "target": "目标值"}]
}
```

2. 运行 CLI：
```bash
python -m src.cli --brief examples/brief_sample.json --output artifacts --verbose
```

#### 导出文档

生成完成后，导出为可读文档：

```bash
# 导出中文 DOCX
python -m src.cli_export --input artifacts/<prd>.json --output exports/<prd>_zh.docx --format docx --language zh

# 导出英文 DOCX
python -m src.cli_export --input artifacts/<prd>.json --output exports/<prd>_en.docx --format docx --language en

# 导出 Markdown
python -m src.cli_export --input artifacts/<prd>.json --output exports/<prd>.md --format markdown --language auto
```

## 📁 项目结构

```
amprd/
├── src/
│   ├── agents/          # 多智能体实现
│   │   ├── lead_analyst.py      # 需求分析 Agent
│   │   ├── text_gen.py          # 文本生成 Agent（中/英）
│   │   ├── alignment.py         # 双语对齐 Agent
│   │   ├── vision.py            # 视觉生成 Agent
│   │   ├── table_agent.py       # 表格生成 Agent
│   │   ├── consistency.py       # 一致性校验 Agent
│   │   ├── quality.py           # 质量汇总 Agent
│   │   └── assembler.py         # 组装输出 Agent
│   ├── pipeline/        # 编排器
│   │   └── orchestrator.py     # 多智能体调度器
│   ├── shared/          # 共享组件
│   │   └── blackboard.py       # 线程安全黑板实现
│   ├── models/          # 模型客户端
│   │   ├── model_client.py     # 模型接口
│   │   └── qwen_client.py      # Qwen 模型实现
│   ├── exporters/       # 导出器
│   │   └── prd_renderer.py     # DOCX/Markdown 渲染
│   ├── templates/       # 模板管理
│   │   └── manager.py          # 模板加载器
│   └── utils/           # 工具函数
│       └── brief_parser.py     # 自然语言解析
├── templates/            # PRD 模板库
│   ├── template_index.yaml     # 模板索引
│   ├── figma_prd.md            # Figma 模板
│   └── ...
├── schemas/             # Schema 定义
│   └── prd_schema_v0_9.json   # PRD JSON Schema
├── docs/                # 文档
│   ├── system_guide.md         # 系统详细讲解与图解
│   ├── system_overview.md      # 系统总览
│   └── ...
├── scripts/             # 脚本
│   └── run_prd.py              # 一键运行脚本
└── examples/            # 示例
    └── brief_sample.json        # Brief 示例
```

## 🏗️ 系统架构

系统采用**黑板模式（Blackboard Pattern）**实现多智能体协作：

```
[CLI/脚本] → [编排器 Orchestrator] → [黑板 Blackboard]
                                              ↓
    ┌─────────────────────────────────────────┐
    │  多智能体协作流程（按顺序执行）          │
    ├─────────────────────────────────────────┤
    │ 1. LeadAnalyst     需求分析与计划生成    │
    │ 2. TextGen_CN      中文文本生成          │
    │ 3. TextGen_EN      英文文本生成          │
    │ 4. AlignmentAgent  双语对齐检查          │
    │ 5. VisionAgent    流程图/界面图生成     │
    │ 6. TableAgent      KPI/里程碑表格生成    │
    │ 7. ConsistencyAgent 一致性校验           │
    │ 8. QualityAgent   质量指标汇总           │
    │ 9. Assembler      输出 PRD JSON          │
    └─────────────────────────────────────────┘
                      ↓
            [artifacts/prd_*.json]
                      ↓
            [导出器 → DOCX/Markdown]
```

详细流程图与逐步方法说明请参考：[`docs/system_guide.md`](docs/system_guide.md)

## 🔧 配置说明

### 环境变量

创建 `.env` 文件（参考 `env.example`）：

```bash
# Qwen 文本模型（中文）
QWEN_TEXT_CN_API_KEY=your_key_here
QWEN_TEXT_CN_MODEL=qwen-plus

# Qwen 文本模型（英文）
QWEN_TEXT_EN_API_KEY=your_key_here
QWEN_TEXT_EN_MODEL=qwen-plus

# Qwen 视觉模型
DASHSCOPE_API_KEY=your_key_here
QWEN_VISION_MODEL=qwen-image-plus
QWEN_VISION_SIZE=1328x1328
```

### 模板选择

系统支持多种 PRD 模板，可在 `templates/template_index.yaml` 查看可用模板：

- `figma` - Figma PRD 模板
- `asana` - Asana 规范模板
- `jira` - Jira PRD 模板
- 更多模板见 `templates/` 目录

## 📊 质量指标

系统自动计算以下质量指标：

- **S_comp** - 结构完整度
- **S_mm** - 跨模态一致性（图/表/文本锚点）
- **S_tab** - 表格质量
- **S_bi** - 双语一致性
- **S_var** - 稳定性（多次运行方差）

指标详情见 `src/metrics/quality.py`

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 📚 相关文档

- [系统详细讲解与图解](docs/system_guide.md)
- [系统总览](docs/system_overview.md)
- [多智能体架构](docs/multi_agent_architecture.md)
- [Schema 说明](docs/schema_overview.md)

## 🙏 致谢

本项目由 ECNU-ByteNLP 团队开发，采用纯开源模型栈，支持 Qwen/Doubao 等开源模型。

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/ECNU-ByteNLP/amprd/issues)
- 邮箱：740847470@qq.com

---

**注意**：本项目为研究原型，生产环境使用请自行评估风险。
