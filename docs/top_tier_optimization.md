# 顶刊实验标准优化方案

基于顶级公司PRD样例（Google, Amazon, Linear等）和顶刊实验标准，本文档提出系统性优化方案。

## 一、当前系统分析

### 1.1 优势
- ✅ 多智能体架构清晰，职责分离
- ✅ 双语多模态支持
- ✅ 基础评测指标（S_comp, S_mm, S_tab, S_bi, S_var）
- ✅ 统计检验工具（Wilcoxon, Cliff's δ, Bootstrap CI）
- ✅ 人工评测框架（Krippendorff α）

### 1.2 关键差距（对标顶级PRD样例）

#### 差距1：Brief解析能力不足
- **现状**：启发式解析，仅提取前120字符作为goal
- **顶级PRD要求**：清晰的问题陈述、目标用户、成功指标、技术约束
- **影响**：无法从自然语言中提取结构化信息，导致PRD质量下降

#### 差距2：评测指标不够全面
- **现状**：5个基础指标（结构、跨模态、表格、双语、稳定性）
- **顶级PRD要求**：
  - 语义质量（问题陈述清晰度、需求可执行性）
  - 业务对齐度（目标与指标一致性）
  - 技术可行性（技术要求的合理性）
  - 风险识别（风险与缓解策略的完整性）
- **影响**：无法全面评估PRD质量，难以与人类专家PRD对比

#### 差距3：缺少真实PRD基准数据集
- **现状**：无标准数据集，无法进行可复现实验
- **顶级PRD要求**：基于真实产品需求的PRD样例
- **影响**：无法进行公平对比，实验结果难以复现

#### 差距4：缺少与人类专家PRD的对比
- **现状**：仅与基线系统对比
- **顶级PRD要求**：与Google、Amazon等公司的真实PRD对比
- **影响**：无法证明系统生成的PRD达到专家水平

#### 差距5：消融实验设计不完整
- **现状**：支持Agent禁用，但缺少系统化消融实验
- **顶级PRD要求**：明确各组件贡献度
- **影响**：无法证明多智能体架构的必要性

## 二、优化方案

### 2.1 Brief解析器升级（LLM驱动）

**目标**：从自然语言文本中提取结构化Brief，达到与顶级PRD样例相当的信息密度。

**实现**：
1. 使用LLM进行结构化提取
2. 分阶段解析（核心字段 → 细节字段）
3. 置信度计算（基于提取字段的完整性）
4. 支持交互式补全（缺失字段时提示用户）

**参考顶级PRD样例的关键字段**：
- **问题陈述**（Problem Statement）：清晰描述要解决的问题
- **目标用户**（Target Users）：详细的用户画像和需求
- **成功指标**（Success Metrics）：具体、可衡量的KPI
- **技术约束**（Technical Constraints）：架构、性能、安全要求
- **时间线**（Timeline）：里程碑和发布计划
- **风险识别**（Risks）：潜在风险和缓解策略

### 2.2 评测指标扩展

**新增指标**：

1. **S_sem（语义质量）**
   - 问题陈述清晰度（NLI模型评估）
   - 需求可执行性（是否包含验收标准）
   - 术语一致性（领域术语使用准确性）

2. **S_biz（业务对齐度）**
   - 目标与指标一致性（goal与KPI的匹配度）
   - 用户需求覆盖度（persona与功能的对应关系）

3. **S_tech（技术可行性）**
   - 技术要求的合理性（架构、性能指标的合理性）
   - 约束完整性（安全、合规、性能约束是否完整）

4. **S_risk（风险识别）**
   - 风险识别完整性（是否识别关键风险）
   - 缓解策略有效性（缓解策略是否具体可行）

5. **S_expert（专家对齐度）**
   - 与人类专家PRD的结构相似度
   - 与人类专家PRD的内容相似度（基于语义相似度）

### 2.3 PRD质量基准数据集构建

**数据集组成**：

1. **真实PRD样例**（参考pmprompt.com）
   - Google Search Algorithm Update
   - Amazon Prime Video Features
   - Linear Priority Micro-Adjust
   - Figma Real-time Collaboration
   - Stripe Payment Processing
   - 等12个顶级公司PRD样例

2. **领域覆盖**
   - 金融（financial）：3-5个样例
   - 电商（ecommerce）：3-5个样例
   - 医疗（medical）：3-5个样例
   - 通用（general）：3-5个样例

3. **标注信息**
   - 每个PRD标注：问题陈述、目标用户、成功指标、技术约束、风险
   - 质量评分（1-7 Likert量表）：可执行性、清晰度、完整性

### 2.4 与人类专家PRD对比实验

**实验设计**：

1. **对比维度**
   - 结构完整性（章节覆盖度）
   - 内容质量（语义相似度、可执行性）
   - 多模态一致性（图、表、文本对齐）
   - 双语一致性（中英文对应关系）

2. **评估方法**
   - 自动指标对比（S_comp, S_sem, S_biz等）
   - 人工评测对比（双盲实验，Likert 1-7）
   - 专家评审（PM、研发、QA各≥5人）

3. **统计检验**
   - Wilcoxon符号秩检验
   - Cliff's δ效应量
   - Bootstrap置信区间

### 2.5 系统化消融实验

**消融维度**：

1. **Agent消融**
   - 无AlignmentAgent（验证双语对齐的必要性）
   - 无VisionAgent（验证多模态的必要性）
   - 无TableAgent（验证结构化表格的必要性）
   - 无ConsistencyAgent（验证一致性检查的必要性）

2. **通信模式消融**
   - 同步批量（blackboard）vs 异步队列（async_queue）
   - 验证通信模式对质量的影响

3. **Prompt优化消融**
   - 基础Prompt vs 结构化Prompt（VisionAgent）
   - 验证Prompt设计对生成质量的影响

4. **模型消融**
   - Qwen vs Doubao vs Mock
   - 验证模型选择对质量的影响

## 三、实施状态

### ✅ Phase 1（已完成）
1. ✅ Brief解析器升级（LLM驱动）- 已实现，支持从环境变量自动创建Qwen客户端
2. ✅ 评测指标扩展（S_sem, S_biz, S_tech, S_risk, S_expert）- 已实现，见 `src/metrics/extended_quality.py`
3. ✅ PRD质量基准数据集构建（至少12个样例）- 已实现，见 `src/data/benchmark_builder.py`

### ✅ Phase 2（已完成）
4. ✅ 与人类专家PRD对比实验 - 通过S_expert指标支持
5. ✅ 系统化消融实验设计 - 已实现，见 `src/experiments/ablation_suite.py`
6. ✅ 实验报告自动生成 - 已实现，见 `src/experiments/report_generator.py`

### Phase 3（未来增强）
7. ⏳ 交互式Brief补全
8. ⏳ 多轮对话式PRD生成
9. ⏳ 实时质量监控与反馈

## 四、预期成果

### 4.1 实验可复现性
- 标准数据集（12+真实PRD样例）
- 完整的实验配置（随机种子、超参数）
- 自动化实验流水线

### 4.2 评测全面性
- 10+自动指标（覆盖结构、语义、业务、技术、风险）
- 人工评测框架（多角色、多维度）
- 统计检验（Wilcoxon, Cliff's δ, Bootstrap CI）

### 3.3 论文贡献点
- 多智能体架构的有效性（消融实验证明）
- 双语多模态PRD生成（与基线对比）
- 达到专家水平（与人类专家PRD对比）

---

**参考资源**：
- [PRD Examples from Top Tech Companies](https://pmprompt.com/blog/prd-examples)
- Google Search Algorithm Update PRD
- Amazon Prime Video Features PRD
- Linear Priority Micro-Adjust PRD

