# 顶刊实验标准优化方案 v2.0

## 概述

基于 [pmprompt.com PRD Templates](https://pmprompt.com/blog/prd-templates) 的最佳实践，对系统进行全面优化，提升PRD生成质量至顶刊实验标准。

## 一、基准数据集扩展

### 1.1 数据集规模

**从3个扩展到15个PRD样例**，覆盖：
- **6个领域**：general, ecommerce, financial, medical, education, enterprise
- **14种PRD模板风格**：参考顶级公司的PRD模板

### 1.2 覆盖的PRD模板风格

| 模板风格 | 来源公司 | 样例数量 | 特点 |
|---------|---------|---------|------|
| Google Data-Driven PRD | Google | 1 | 数据驱动，强调指标 |
| Amazon-Style PRD | Amazon | 1 | 客户中心，用户旅程 |
| Intercom Job Story | Intercom | 1 | 用户工作导向 |
| Figma Design-First | Figma | 1 | 设计优先 |
| Miro Product Alignment | Miro | 1 | 视觉对齐，协作 |
| ShapeUp Pitch | Basecamp | 1 | 时间约束，边界清晰 |
| Dropbox One-Page | Dropbox | 1 | 简洁一页 |
| Notion PRD System | Notion | 1 | 结构化系统 |
| Microsoft Feature Doc | Microsoft | 2 | 技术文档风格 |
| Atlassian Agile | Atlassian | 1 | 敏捷流程 |
| Lean UX Canvas | - | 1 | 假设验证 |
| Product School | Product School | 1 | 教育导向 |
| Startup-Focused | - | 1 | 创业公司风格 |
| AI-Enhanced | - | 1 | AI增强 |

### 1.3 新增样例列表

1. **Google Search Algorithm Update** (google_data_driven)
2. **Dropbox Real-time Collaboration** (dropbox_one_page)
3. **Notion AI Writing Assistant** (notion_prd)
4. **Amazon Prime Video Personalization** (amazon_style)
5. **Shopify Mobile Store Management** (startup_focused)
6. **Smart Financial Advisor** (intercom_job_story)
7. **Payment Security Enhancement** (microsoft_feature)
8. **Figma Real-time Collaboration** (figma_design_first)
9. **Miro Template Marketplace** (miro_alignment)
10. **Linear Priority Micro-Adjustments** (shapeup_pitch)
11. **Jira Automated Workflow** (atlassian_agile)
12. **Telemedicine Consultation Platform** (lean_ux_canvas)
13. **Personalized Learning Path** (product_school)
14. **AI-Powered PRD Assistant** (ai_enhanced)
15. **Enterprise SSO Integration** (microsoft_feature)

### 1.4 Brief结构增强

每个Brief现在包含：
- `problem_statement`: 问题陈述（问题空间）
- `solution_approach`: 解决方案方向（解决方案空间）
- `pain_points`: 用户痛点列表
- `problem_impact`: 问题影响量化（可选）

## 二、问题空间和解决方案空间分离

### 2.1 核心创新

**参考最佳实践**：Intercom, Airbnb, Asana, Miro, Basecamp 都遵循的关键实践

> "I firmly believe that nailing the problem statement is the single most important step in solving any problem. It's deceptively easy to get wrong, and when done well it's a superpower of the best leaders."
> — Lenny Rachitsky, former Airbnb PM

### 2.2 LeadAnalyst优化

**新增功能**：
- 明确分离问题空间（Problem Space）和解决方案空间（Solution Space）
- 在Plan中单独存储问题空间和解决方案空间信息
- 章节标记为问题导向或解决方案导向

**问题空间包含**：
- `problem_statement`: 问题陈述
- `pain_points`: 用户痛点列表
- `problem_impact`: 问题影响量化

**解决方案空间包含**：
- `solution_approach`: 解决方案方向
- `solution_alternatives`: 备选方案（可选）

### 2.3 章节分类

每个章节现在标记为：
- `focus: "problem"`: 问题空间章节（overview, user_persona, user_stories）
- `focus: "solution"`: 解决方案空间章节（functional_requirements, user_flows, key_interfaces）
- `focus: "both"`: 两者兼顾（kpi_and_milestones, risks_and_mitigations）

## 三、TextGen Agent Prompt优化

### 3.1 优化策略

参考14种顶级PRD模板的最佳实践，为每个章节设计专门的prompt。

### 3.2 章节特定Prompt

#### Overview章节
- **参考**：Kevin Yien PRD Template, Google Data-Driven PRD
- **强调**：问题空间和解决方案空间分离
- **要求**：
  1. 问题陈述（1-2句话，包含证据和影响）
  2. 解决方案概述（高层次，不过于详细）
  3. 目标和成功指标

#### User Persona章节
- **参考**：Intercom Job Story, Miro Product Alignment Document
- **要求**：
  1. 用户基本信息（角色、背景、场景）
  2. 用户需求（User Needs）
  3. 用户痛点（Pain Points）
  4. 用户目标（User Goals）

#### User Stories章节
- **参考**：Intercom Job Story格式
- **格式**：
  - Job Story格式：当[情况]时，我想要[目标]，以便[价值]
  - 传统格式：作为[角色]，我想要[功能]，以便[价值]
- **要求**：包含验收标准（Acceptance Criteria）

#### Functional Requirements章节
- **参考**：Google Data-Driven PRD, Microsoft Feature Doc
- **要求**：
  1. 核心功能（优先级、依赖关系）
  2. 功能规格（输入/输出、行为、边界条件）
  3. 验收标准

#### Non-Functional Requirements章节
- **参考**：Figma, Microsoft技术文档
- **要求**：
  1. 性能要求（响应时间、吞吐量、可扩展性）
  2. 安全要求（数据安全、隐私、合规）
  3. 可用性要求（系统可用性、容错）
  4. 技术约束

#### User Flows章节
- **参考**：Miro Product Alignment Document
- **要求**：
  1. 主要用户流程（步骤、决策点、异常处理）
  2. 用户旅程地图（接触点、情感变化、痛点）
  3. 流程优化点

#### KPI and Milestones章节
- **参考**：Google Data-Driven PRD, Amazon-Style PRD
- **要求**：
  1. 成功指标（KPIs）：定义、基线、目标、测量方法
  2. 里程碑计划：时间点、交付物、依赖关系
  3. **假设验证**（参考Lean UX Canvas）：假设、验证方法、成功标准

#### Risks and Mitigations章节
- **参考**：Linear Priority Micro-Adjust, ShapeUp Rabbit Holes
- **要求**：
  1. 关键风险（技术、业务、用户采用、合规）
  2. 风险影响评估（严重程度、概率、影响）
  3. 缓解策略（具体措施、责任人、时间计划）

### 3.3 Prompt设计原则

1. **具体性**：避免空泛描述，要求具体、可执行
2. **结构化**：使用列表、段落、关键信息突出
3. **对齐性**：确保内容与问题陈述和解决方案方向一致
4. **参考性**：明确参考的顶级公司PRD模板

## 四、新增质量指标

### 4.1 S_ps: 问题-解决方案分离度

**参考**：Intercom, Airbnb, Asana, Miro, Basecamp最佳实践

**维度**：
- `problem_clarity`: 问题陈述清晰度
- `solution_clarity`: 解决方案清晰度
- `separation_quality`: 分离质量

**计算方法**：
- 检查Overview章节是否包含问题关键词和解决方案关键词
- 检查是否有结构化的问题陈述和解决方案概述
- 评估两者是否清晰分离

### 4.2 S_uj: 用户旅程完整性

**参考**：Miro Product Alignment Document, Intercom Job Story

**维度**：
- `persona_completeness`: 用户画像完整性（需求、痛点、目标、场景）
- `journey_map_quality`: 用户旅程地图质量（流程、步骤、接触点）
- `touchpoint_coverage`: 接触点覆盖度（开始、中间、结束阶段）

**计算方法**：
- 检查User Persona章节是否包含用户画像的关键要素
- 检查User Flows章节是否包含用户旅程的关键要素
- 评估接触点和阶段的覆盖度

### 4.3 S_hyp: 假设验证度

**参考**：Lean UX Canvas的假设验证方法

**检查项**：
- 是否包含假设陈述
- 是否定义了验证方法
- 是否明确了成功标准

**计算方法**：
- 检查KPI章节是否包含假设验证的关键要素
- 评估假设、验证方法、成功标准的完整性

### 4.4 指标汇总

现在系统支持**13个质量指标**：

**基础指标（5个）**：
- S_comp: 结构完整度
- S_mm: 跨模态一致性
- S_tab: 表格一致性
- S_bi: 双语一致性
- S_var: 生成稳定性

**扩展指标（8个）**：
- S_sem: 语义质量
- S_biz: 业务对齐度
- S_tech: 技术可行性
- S_risk: 风险识别
- S_expert: 专家对齐度
- **S_ps: 问题-解决方案分离度**（新增）
- **S_uj: 用户旅程完整性**（新增）
- **S_hyp: 假设验证度**（新增）

## 五、模板系统增强

### 5.1 模板风格支持

系统现在可以识别和应用14种PRD模板风格：
- 根据Brief中的`template_style`字段自动适配
- 在Plan中记录模板风格信息
- 根据模板风格调整章节结构和内容要求

### 5.2 模板特定优化

不同模板风格会触发不同的生成策略：
- **ShapeUp**: 强调时间约束（appetite）和边界（no-gos）
- **Miro**: 强调视觉对齐和协作
- **Intercom**: 强调用户工作和动机
- **Google**: 强调数据驱动和指标
- **Amazon**: 强调客户中心和用户旅程

## 六、使用建议

### 6.1 生成高质量PRD

1. **使用扩展的基准数据集**：
   ```bash
   python -c "from src.data.benchmark_builder import create_sample_benchmark_prds; create_sample_benchmark_prds(Path('data/benchmark'))"
   ```

2. **指定模板风格**（可选）：
   ```json
   {
     "brief_text": "...",
     "template_id": "figma"  // 或其他模板
   }
   ```

3. **查看完整指标**：
   ```python
   from src.metrics.extended_quality import compute_all_extended_metrics
   metrics = compute_all_extended_metrics(prd)
   # 现在包含 S_ps, S_uj, S_hyp
   ```

### 6.2 实验设置

1. **基准数据集**：使用15个PRD样例
2. **质量指标**：计算13个指标
3. **消融实验**：可以测试不同模板风格的影响

## 七、创新点总结

### 7.1 方法论创新

1. **问题-解决方案空间分离**：
   - 首次在多智能体PRD生成系统中实现
   - 参考顶级产品团队的最佳实践
   - 提升PRD的逻辑清晰度和可执行性

2. **多模板风格支持**：
   - 支持14种PRD模板风格
   - 自动适配不同模板要求
   - 提升PRD的适用性和专业性

3. **增强的质量评估**：
   - 新增3个顶刊标准指标
   - 全面评估PRD质量
   - 符合顶级期刊的实验标准

### 7.2 技术创新

1. **章节特定Prompt**：
   - 每个章节有专门的prompt设计
   - 参考顶级公司的最佳实践
   - 提升生成内容的质量和相关性

2. **结构化Brief**：
   - 明确的问题陈述和解决方案方向
   - 用户痛点和需求分离
   - 支持更精准的PRD生成

## 八、下一步优化方向

### 8.1 短期（1-2周）

1. **模板特定章节生成**：
   - 为不同模板风格生成特定章节
   - 如ShapeUp的Rabbit Holes、No-Gos

2. **用户旅程可视化**：
   - 自动生成用户旅程地图
   - 集成到VisionAgent

3. **假设验证框架**：
   - 自动生成假设陈述
   - 提供验证方法建议

### 8.2 中期（1-2月）

1. **更大规模数据集**：
   - 扩展到50+个PRD样例
   - 覆盖更多领域和场景

2. **人工标注**：
   - 邀请产品经理标注PRD质量
   - 建立人工评估基准

3. **模板自动选择**：
   - 根据Brief自动推荐最佳模板
   - 基于领域和项目类型

### 8.3 长期（3-6月）

1. **交互式PRD生成**：
   - 支持多轮对话优化
   - 实时质量反馈

2. **PRD质量预测**：
   - 基于Brief预测PRD质量
   - 提前识别潜在问题

3. **多语言扩展**：
   - 支持更多语言
   - 跨语言质量对齐

## 九、参考资源

- [PRD Templates from Top Tech Companies](https://pmprompt.com/blog/prd-templates)
- [PRD Examples](https://pmprompt.com/blog/prd-examples)
- [Shape Up Methodology](https://basecamp.com/shapeup)
- [Intercom Job Stories](https://www.intercom.com/blog/job-stories/)
- [Miro Product Alignment](https://miro.com/templates/product-alignment/)

---

**版本**: v2.0  
**更新日期**: 2025-01-20  
**作者**: AMPRD Team

