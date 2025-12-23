# AMPRD 项目总体总结

## 一、实验实现的核心功能

### 1.1 多智能体协同PRD生成系统

**核心架构**：基于黑板模式（Blackboard Pattern）的多智能体协作系统，包含9个专业化Agent：

1. **LeadAnalyst**：需求分析与规划
   - 解析Brief（自然语言或结构化JSON）
   - 生成章节计划、术语表、用户画像、约束条件
   - 输出结构化执行计划

2. **TextGen_CN/EN**：双语文本生成
   - 独立的中文和英文生成链路
   - 调用LLM（Qwen/Doubao等）生成各章节内容
   - 支持11个标准章节（overview, user_persona, user_stories, functional_requirements等）

3. **AlignmentAgent**：双语对齐检查
   - 检测中英文段落缺失
   - 检查段落长度差异
   - 确保双语内容对等

4. **VisionAgent**：多模态视觉生成
   - 生成流程图（user_flows）
   - 生成界面示意图（key_interfaces）
   - 支持中英文双语视觉内容
   - 自动重试机制和占位策略

5. **TableAgent**：结构化表格生成
   - KPI指标表格
   - 里程碑计划表格
   - 数据埋点表格

6. **ConsistencyAgent**：一致性校验
   - 结构完整性检查
   - 跨模态引用一致性
   - 术语一致性验证

7. **QualityAgent**：质量指标汇总
   - 自动计算10个质量指标
   - 实时质量监控

8. **Assembler**：最终PRD组装
   - 收集所有生成内容
   - 生成符合Schema的结构化JSON
   - 计算资源清单和校验和

### 1.2 输入方式支持

**方式一：自然语言输入（推荐）**
- 支持用户提供一段自然语言描述
- LLM驱动的结构化提取（优先使用Qwen模型）
- 启发式解析回退（当LLM不可用时）
- 自动识别领域（financial/ecommerce/medical/general）

**方式二：结构化Brief JSON**
- 支持完整的Brief JSON格式
- 包含goal、target_users、key_constraints、business_metrics等字段

**方式三：模板驱动生成**
- 支持预定义PRD模板（如figma、kevin_prd等）
- 模板可包含表格、多模态要求
- 自动应用模板结构到生成过程

### 1.3 多模态内容生成

**文本内容**：
- 11个标准PRD章节的中英文双语内容
- 结构化段落、列表、关键信息提取

**视觉内容**：
- 流程图（user_flows）：展示用户操作流程
- 界面示意图（key_interfaces）：关键界面设计示意
- 支持中英文双语视觉内容生成

**表格内容**：
- KPI指标表格：业务指标与目标值
- 里程碑计划表格：时间线与交付物
- 数据埋点表格：追踪指标定义

### 1.4 质量评估体系

**基础指标（5个）**：
- **S_comp**：结构完整度（章节覆盖度）
- **S_mm**：跨模态一致性（文本-图片引用一致性）
- **S_tab**：表格一致性（表格结构完整性）
- **S_bi**：双语一致性（中英文内容对等性）
- **S_var**：生成稳定性（多次运行的一致性）

**扩展指标（8个）**：
- **S_sem**：语义质量（问题清晰度、需求可执行性、术语一致性）
- **S_biz**：业务对齐度（Goal与KPI一致性、用户需求覆盖度）
- **S_tech**：技术可行性（技术要求合理性、约束完整性）
- **S_risk**：风险识别（风险识别完整性、缓解策略有效性）
- **S_expert**：专家对齐度（与人类专家PRD的结构/内容相似度）
- **S_ps**：问题-解决方案分离度（问题空间和解决方案空间清晰分离）✨ 新增
- **S_uj**：用户旅程完整性（用户画像、旅程地图、接触点覆盖）✨ 新增
- **S_hyp**：假设验证度（假设陈述、验证方法、成功标准）✨ 新增

**参考**：基于 [pmprompt.com PRD Templates](https://pmprompt.com/blog/prd-templates) 的14种顶级PRD模板最佳实践

### 1.5 实验框架

**基准数据集构建**：
- **15个PRD样例**，覆盖6个领域（general/ecommerce/financial/medical/education/enterprise）
- **14种PRD模板风格**：Google Data-Driven, Amazon-Style, Intercom Job Story, Figma Design-First, Miro Product Alignment, ShapeUp Pitch, Dropbox One-Page, Notion PRD System, Microsoft Feature Doc, Atlassian Agile, Lean UX Canvas, Product School, Startup-Focused, AI-Enhanced
- 每个样例包含问题陈述和解决方案方向，支持问题-解决方案空间分离
- 参考：[pmprompt.com PRD Templates](https://pmprompt.com/blog/prd-templates)

**消融实验框架**：
- Agent消融：无AlignmentAgent、无VisionAgent、无TableAgent、无ConsistencyAgent
- 通信模式消融：同步批量 vs 异步队列
- 模型消融：不同Qwen模型版本对比（如qwen2.5-32b vs qwen2.5-7b）

**自动化实验报告**：
- 指标对比表格自动生成
- 消融实验结果分析
- 统计检验（Wilcoxon、Cliff's δ、Bootstrap CI）
- Markdown格式报告（适合论文撰写）

### 1.6 输出与导出

**结构化JSON输出**：
- 符合 `schemas/prd_schema_v0_9.json` 标准
- 包含metadata、sections、assets_manifest、quality等完整信息
- 支持完整追溯与审计

**文档导出**：
- **DOCX导出**：支持中英文版本，专业格式（表格、图片、段落样式）
- **Markdown导出**：支持中英文版本，适合版本控制

**可复现性保障**：
- 黑板状态持久化（blackboard.json）
- 完整消息历史记录
- Agent执行轨迹（agent_trace）
- 随机种子和超参数记录

## 二、系统支持的能力

### 2.1 多领域支持

- **金融领域（financial）**：智能理财助手、支付系统等
- **电商领域（ecommerce）**：个性化推荐、订单系统等
- **医疗领域（medical）**：健康管理、诊断辅助等
- **通用领域（general）**：搜索引擎、协作工具等

### 2.2 模型支持

**文本生成模型**：
- **Qwen2/3系列**（默认：qwen2.5-32b-instruct）
  - 系统自动从环境变量 `QWEN_API_KEY` 读取配置
  - 支持自定义模型：`QWEN_TEXT_MODEL_CN`、`QWEN_TEXT_MODEL_EN`
  - 中英文可独立配置不同模型
- Doubao等开源LLM（通过统一接口接入）
- Mock模型（仅用于测试，当未配置API密钥时自动回退）

**视觉生成模型**：
- **DashScope图像生成API**（默认：wanx-v1）
  - 通过 `QWEN_VISION_MODEL` 环境变量配置
  - 支持中英文双语视觉内容生成
- 兼容模式（自动匹配分辨率）
- 占位策略（仅当API不可用时的降级处理）

### 2.3 通信模式

- **同步批量模式**：所有Agent按顺序执行，适合调试
- **异步队列模式**：Agent并行处理消息，适合生产环境

### 2.4 实验工具

- **一键快速实验**：`scripts/quick_start_experiment.py`
- **完整基准实验**：`scripts/run_benchmark_experiment.py`
- **消融实验套件**：`src/experiments/ablation_suite.py`
- **报告生成器**：`src/experiments/report_generator.py`

### 2.5 配置与扩展

- **环境变量配置**：支持`.env`文件配置API密钥
- **模板系统**：支持自定义PRD模板
- **指标扩展**：易于添加新的质量指标
- **Agent扩展**：基于统一接口，易于添加新Agent

## 三、下一步优化方向

### 3.1 PRD生成质量优化（v2.0已完成）

**问题-解决方案空间分离**：
- LeadAnalyst现在明确分离问题空间和解决方案空间
- 参考Intercom, Airbnb, Asana, Miro, Basecamp的最佳实践
- 章节标记为问题导向或解决方案导向

**章节特定Prompt优化**：
- 每个章节有专门的prompt设计
- 参考14种顶级PRD模板的最佳实践
- 提升生成内容的质量和相关性

**新增质量指标**：
- S_ps: 问题-解决方案分离度
- S_uj: 用户旅程完整性
- S_hyp: 假设验证度

详细说明：见 `docs/top_tier_optimization_v2.md`

### 3.2 交互式增强（Phase 3）

**交互式Brief补全**：
- 当Brief缺失关键字段时，系统主动提示用户补充
- 支持多轮对话式Brief收集
- 智能推荐缺失字段的示例

**多轮对话式PRD生成**：
- 支持用户对生成的PRD进行反馈和修改
- 迭代优化PRD内容
- 基于用户反馈调整生成策略

**实时质量监控与反馈**：
- 生成过程中实时显示质量指标
- 低质量内容自动标记和重生成
- 用户可实时查看生成进度和质量

### 3.2 质量提升

**视觉生成质量优化**：
- 更精细的Prompt工程
- 支持更多视觉风格（流程图、架构图、时序图等）
- 视觉内容与文本内容的语义对齐

**内容质量优化**：
- 更智能的章节内容生成
- 更好的中英文对齐算法
- 术语一致性自动修复

**指标计算优化**：
- 更准确的语义相似度计算（使用更好的embedding模型）
- 更细粒度的质量维度
- 支持领域特定的质量指标

### 3.3 实验与评估

**更大规模基准数据集**：
- 扩展到50+个PRD样例
- 覆盖更多领域和场景
- 人工标注的质量评分

**更严格的统计检验**：
- 更大样本量的实验
- 更全面的基线对比
- 人类专家评估（Human Evaluation）

**消融实验扩展**：
- 更多Agent组合的消融
- Prompt策略的消融
- 模型选择的消融

### 3.4 系统性能

**生成速度优化**：
- Agent并行化优化
- 缓存机制（相似Brief的复用）
- 批量处理优化

**资源消耗优化**：
- 模型调用次数减少
- 视觉生成成本控制
- 存储空间优化

### 3.5 用户体验

**更友好的CLI**：
- 交互式命令行界面
- 进度条和实时反馈
- 错误提示和恢复建议

**Web界面（可选）**：
- 可视化Brief输入界面
- 实时PRD预览
- 在线编辑和导出

**文档与教程**：
- 更详细的用户指南
- 视频教程
- 最佳实践案例

### 3.6 技术架构

**分布式支持**：
- 支持多机部署
- Agent分布式执行
- 状态同步机制

**可观测性**：
- 详细的日志系统
- 性能监控
- 错误追踪

**API服务化**：
- RESTful API接口
- 微服务架构
- 容器化部署

## 四、项目价值与贡献

### 4.1 学术价值

- **多智能体协作**：证明了多智能体架构在复杂文档生成任务中的有效性
- **双语多模态**：首次实现了双语多模态PRD的自动生成
- **质量评估体系**：建立了全面的PRD质量评估指标体系
- **可复现实验**：提供了完整的实验框架和基准数据集

### 4.2 实用价值

- **提升效率**：将PRD生成时间从数天缩短到数分钟
- **保证质量**：通过多Agent协作和质量检查，确保PRD的完整性和一致性
- **降低门槛**：非专业人员也能生成专业级PRD
- **标准化**：统一的PRD格式和结构，便于团队协作

### 4.3 技术贡献

- **黑板模式应用**：在多智能体文档生成中的成功实践
- **双语对齐算法**：创新的中英文内容对齐方法
- **多模态融合**：文本、表格、视觉内容的统一生成框架
- **质量指标设计**：10个维度的PRD质量评估体系

## 五、使用建议

### 5.1 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置Qwen API密钥（推荐，系统会自动使用Qwen模型）
export QWEN_API_KEY="your-api-key"
# 可选：自定义模型
export QWEN_TEXT_MODEL_CN="qwen2.5-32b-instruct"
export QWEN_VISION_MODEL="wanx-v1"

# 3. 运行快速实验
python scripts/quick_start_experiment.py
```

### 5.2 生成PRD

```bash
# 方式一：自然语言输入
python scripts/run_prd.py --config run_config.json

# 方式二：结构化Brief
python -m src.cli --brief examples/brief_sample.json --output artifacts
```

### 5.3 运行完整实验

```bash
python scripts/run_benchmark_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results \
    --create-samples \
    --run-full-system \
    --run-ablation \
    --generate-report
```

### 5.4 导出文档

```bash
python -m src.cli_export \
    --input artifacts/prd_xxx.json \
    --output exports/prd_zh.docx \
    --format docx \
    --language zh
```

## 六、相关文档

- **系统详细讲解**：`docs/system_guide.md`
- **多智能体架构**：`docs/multi_agent_architecture.md`
- **Agent设计说明**：`docs/agent_design.md`
- **实验实施指南**：`docs/experiment_guide.md`
- **实验步骤详解**：`docs/experiment_steps.md`
- **优化总结**：`docs/optimization_summary.md`
- **实验分析报告**：`docs/experiment_analysis.md`

---

**项目状态**：✅ 核心功能已完成，实验框架已建立，可进行论文实验

**下一步重点**：交互式增强、质量提升、更大规模实验

