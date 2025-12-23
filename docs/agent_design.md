# Agent 设计说明

本文档详细说明系统中各个 Agent 的设计思路、职责分工与协作机制。

## 一、设计原则

### 1.1 基础架构

所有 Agent 继承自 `Agent` 基类，遵循统一的接口规范：

```python
class Agent(abc.ABC):
    role: str  # Agent 角色标识
    
    @abc.abstractmethod
    def handle(self, message: AgentMessage, blackboard: Blackboard) -> Optional[AgentMessage]:
        """处理消息并可选地发出响应"""
```

### 1.2 消息机制

Agent 之间通过 `AgentMessage` 进行通信，消息包含：

- `message_id`: 唯一标识
- `sender/receiver`: 发送者/接收者
- `intent`: 意图（如 "init", "draft_section", "align"）
- `payload`: 消息载荷（包含 plan、brief 等）
- `dependencies`: 依赖的消息 ID（用于追溯）
- `status`: 状态（"open", "completed"）

### 1.3 黑板模式

所有 Agent 通过 `Blackboard` 共享状态：

- **状态读取**：`blackboard.get_state()` 获取完整状态快照
- **状态更新**：`blackboard.update_state(path, value)` 按路径更新嵌套状态
- **消息投递**：`blackboard.post_message()` 投递消息到队列
- **消息拉取**：`blackboard.fetch_pending(receiver)` 按接收者拉取待处理消息

## 二、各 Agent 详细设计

### 2.1 LeadAnalyst（需求分析 Agent）

**职责**：解析初始 Brief，生成结构化计划

**设计要点**：

1. **输入处理**：
   - 接收 `intent="init"` 消息
   - 从 `payload.brief` 提取业务需求

2. **计划生成**（`_draft_plan`）：
   - 生成 PRD ID（UUID）
   - 提取领域、目标、用户画像、约束
   - **固定章节结构**：11 个标准章节（overview、user_persona、user_stories 等）
   - 标记必填/可选章节

3. **输出**：
   - 将计划写入黑板：`blackboard.update_state(["planning", "structure"], plan)`
   - 向 `TextGen_CN` 发送 `draft_section` 消息，启动文本生成流程

**代码位置**：`src/agents/lead_analyst.py`

**设计亮点**：
- 章节结构标准化，确保所有 PRD 都有完整结构
- 支持从模板扩展（未来可接入 `TemplateManager` 的约束）

---

### 2.2 TextGen_CN / TextGen_EN（文本生成 Agent）

**职责**：按章节生成中英文文本内容

**设计要点**：

1. **双 Agent 设计**：
   - `TextGen_CN`：生成中文（zh-CN）
   - `TextGen_EN`：生成英文（en-US）
   - 通过 `build_text_agents()` 工厂函数创建

2. **生成流程**：
   - 接收 `draft_section` 或 `revise_section` 消息
   - 遍历计划中的所有章节
   - 为每个章节构建 Prompt（包含领域、目标、用户画像、约束）
   - 调用模型生成文本：`self._model.generate_text(prompt)`
   - 写入黑板：`blackboard.update_state(["sections", section_id, "content", language], text)`

3. **链式触发**：
   - `TextGen_CN` 完成后 → 触发 `TextGen_EN`
   - `TextGen_EN` 完成后 → 触发 `AlignmentAgent`

**代码位置**：`src/agents/text_gen.py`

**设计亮点**：
- 中英文生成链路完全对等，保证结构一致性
- 支持 `revise_section` 意图，便于回溯修复
- Prompt 模板化，易于优化生成质量

---

### 2.3 AlignmentAgent（双语对齐 Agent）

**职责**：检查中英文段落的结构对齐情况

**设计要点**：

1. **对齐检查**：
   - 遍历所有章节
   - 检查每个章节是否同时有中文和英文内容
   - 检查内容是否为空
   - 记录问题：`{"section": section_id, "issue": "missing_language"}`

2. **问题记录**：
   - 将检查结果写入黑板：`blackboard.update_state(["review", "alignment"], flags)`
   - 供后续 `QualityAgent` 计算 `S_bi`（双语一致性）指标

3. **流程继续**：
   - 无论是否有问题，都继续流程（不阻塞）
   - 向 `VisionAgent` 发送 `supply_visuals` 消息

**代码位置**：`src/agents/alignment.py`

**设计亮点**：
- 轻量级检查，不阻塞主流程
- 问题记录为后续质量指标提供数据
- 未来可扩展为自动修复（触发 `revise_section`）

---

### 2.4 VisionAgent（视觉生成 Agent）

**职责**：生成流程图、界面示意图等视觉资产

**设计要点**：

1. **触发条件**：
   - 接收 `supply_visuals` 消息
   - 针对特定章节生成：`user_flows`、`key_interfaces`

2. **双语视觉生成**：
   - 从黑板读取章节的中英文内容
   - 为中文内容生成中文图，为英文内容生成英文图
   - 构建结构化 Prompt（包含领域、章节、角色、布局建议）

3. **生成与回退**：
   - 调用 `self._model.generate_image(prompt)` 生成图片
   - 失败时自动重试一次
   - 连续失败则写入占位元数据（保留 prompt、错误信息）

4. **资产管理**：
   - 将图片元数据写入黑板：`blackboard.update_state(["sections", section_id, "figures"], figures)`
   - 同时写入 `artifacts` 命名空间，供 `Assembler` 汇总

**代码位置**：`src/agents/vision.py`

**设计亮点**：
- 结构化 Prompt 提升生成质量
- 自动重试机制提高成功率
- 占位策略保证流程不中断
- 支持双语视觉资产（中英文各一套图）

---

### 2.5 TableAgent（表格生成 Agent）

**职责**：生成 KPI 表格、里程碑计划等结构化表格

**设计要点**：

1. **表格生成**：
   - 接收 `supply_tables` 消息
   - 针对 `kpi_and_milestones` 章节生成表格
   - 构建 Prompt（包含领域、目标）
   - 调用模型生成表格文本，解析为结构化行数据

2. **表格结构**：
   - 固定表头：指标、目标、时间范围（中英双语）
   - 解析模型输出为行数据
   - 失败时使用默认示例行

3. **写入黑板**：
   - `blackboard.update_state(["sections", "kpi_and_milestones", "tables"], [table_payload])`

**代码位置**：`src/agents/table_agent.py`

**设计亮点**：
- 表格结构标准化，便于导出渲染
- 支持从 Brief 的 `business_metrics` 字段读取用户自定义指标（未来扩展）

---

### 2.6 ConsistencyAgent（一致性校验 Agent）

**职责**：检查结构完整度、跨模态一致性

**设计要点**：

1. **结构检查**：
   - 检查计划中的所有章节是否都已生成
   - 检查每个章节是否同时有中英文内容
   - 记录缺失：`{"section": section_id, "issue": "missing_section"}`

2. **问题记录**：
   - 写入黑板：`blackboard.update_state(["review", "consistency"], issues)`
   - 供 `QualityAgent` 计算 `S_comp`（结构完整度）指标

3. **流程继续**：
   - 向 `QualityAgent` 发送 `aggregate` 消息

**代码位置**：`src/agents/consistency.py`

**设计亮点**：
- 结构完整性检查，确保 PRD 不缺失关键章节
- 问题记录为质量指标提供数据
- 未来可扩展为自动修复（触发对应 Agent 重新生成）

---

### 2.7 QualityAgent（质量汇总 Agent）

**职责**：聚合自动指标，准备最终质量报告

**设计要点**：

1. **指标计算**（`_compute_metrics`）：
   - **S_comp**（结构完整度）：已生成章节数 / 计划章节总数
   - **S_bi**（双语一致性）：基于 `AlignmentAgent` 的问题数量
   - **S_mm**（跨模态一致性）：基于 `ConsistencyAgent` 的问题数量
   - **S_tab**（表格质量）：固定值 0.8（未来可扩展为实际计算）

2. **写入黑板**：
   - `blackboard.update_state(["quality", "auto_metrics"], metrics)`

3. **流程继续**：
   - 向 `Assembler` 发送 `assemble` 消息

**代码位置**：`src/agents/quality.py`

**设计亮点**：
- 指标计算逻辑清晰，易于扩展
- 与 `src/metrics/quality.py` 的计算函数保持一致（未来可统一）

---

### 2.8 Assembler（组装输出 Agent）

**职责**：将黑板状态组装为最终 PRD JSON 并持久化

**设计要点**：

1. **数据组装**（`_build_bundle`）：
   - 从黑板读取计划与所有章节状态
   - 组装为符合 Schema 的结构：
     ```python
     {
       "metadata": {...},
       "sections": [
         {
           "section_id": "...",
           "content": {"zh-CN": "...", "en-US": "..."},
           "tables": [...],
           "figures": [...]
         }
       ],
       "quality": {...}
     }
     ```

2. **资产清单**：
   - 汇总所有图片为 `assets_manifest`
   - 计算 SHA-256 校验值（如果图片存在）

3. **持久化**（`_persist`）：
   - 保存为 `artifacts/prd_<id>.json`
   - 将路径写入黑板：`blackboard.update_state(["quality", "artifact_path"], path)`

**代码位置**：`src/agents/assembler.py`

**设计亮点**：
- 严格遵循 `schemas/prd_schema_v0_9.json` 规范
- 资产清单便于审计与导出检查
- 版本化输出（每个 PRD 有唯一 ID）

## 三、协作流程

### 3.1 消息流转图

```
[System] init
    ↓
[LeadAnalyst] draft_plan → 写入黑板
    ↓
[TextGen_CN] draft_section → 写入中文内容
    ↓
[TextGen_EN] draft_section → 写入英文内容
    ↓
[AlignmentAgent] align → 检查对齐，记录问题
    ↓
[VisionAgent] supply_visuals → 生成图片，写入 figures
    ↓
[TableAgent] supply_tables → 生成表格，写入 tables
    ↓
[ConsistencyAgent] verify → 检查一致性，记录问题
    ↓
[QualityAgent] aggregate → 计算指标，写入 quality
    ↓
[Assembler] assemble → 组装 JSON，持久化文件
    ↓
[完成]
```

### 3.2 回溯机制（未来扩展）

当 `AlignmentAgent` 或 `ConsistencyAgent` 发现问题时，可触发回溯：

```python
# 示例：发现问题后触发修复
if alignment_flags:
    return self.emit(
        receiver="TextGen_CN",
        intent="revise_section",
        payload={"plan": plan, "issues": alignment_flags},
        dependencies=[message.message_id],
    )
```

`TextGen_CN` 收到 `revise_section` 时，只重新生成有问题的章节。

## 四、设计优势

1. **职责单一**：每个 Agent 只负责一个明确的任务
2. **松耦合**：通过消息和黑板通信，易于扩展和替换
3. **可追溯**：消息依赖链完整，便于调试和审计
4. **可扩展**：新增 Agent 只需实现 `handle()` 方法
5. **可测试**：每个 Agent 可独立测试（Mock Blackboard）
6. **可复现**：所有状态写入黑板，支持完整追溯

## 五、未来扩展方向

1. **自动修复**：`AlignmentAgent` 发现问题后自动触发 `revise_section`
2. **模板约束**：`LeadAnalyst` 读取模板要求，强制生成特定章节/资产
3. **质量门控**：`QualityAgent` 计算指标后，低于阈值时触发修复流程
4. **并行生成**：部分 Agent（如 Vision/Table）可并行执行
5. **Agent 插件化**：支持动态加载自定义 Agent

---

**相关文档**：
- [系统总览](system_overview.md)
- [多智能体架构](multi_agent_architecture.md)
- [系统详细讲解](system_guide.md)

