# Week 4 消融实验计划

**目标**: 验证完整系统中各个Agent的必要性  
**预计时间**: Week 4（约27小时实验时间）

---

## 📋 实验目标

### 核心问题

1. **哪些Agent是必需的？**
   - 去掉哪个Agent会显著降低PRD质量？
   - 哪个Agent的贡献最大？

2. **通信模式的影响？**
   - Blackboard模式 vs Async Queue模式，哪个更好？

3. **模型的重要性？**
   - 真实模型 vs Mock模型，差异有多大？

---

## 🔬 消融实验配置

### 配置列表（7个）

| 配置名称 | 说明 | 去掉/修改的组件 | 预期影响 |
|---------|------|---------------|---------|
| **full_system** | 完整系统（对照组） | 无 | 基准 |
| **no_alignment** | 去掉双语对齐 | AlignmentAgent | S_bi下降 |
| **no_vision** | 去掉视觉生成 | VisionAgent | S_mm可能不变（有其他模态） |
| **no_table** | 去掉表格生成 | TableAgent | S_tab=0 |
| **no_consistency** | 去掉一致性检查 | ConsistencyAgent | S_var可能下降 |
| **async_queue** | 异步队列通信 | 通信模式改变 | 性能变化？ |
| **mock_model** | 使用Mock模型 | 所有AI模型 | 质量大幅下降 |

### 详细配置说明

#### 1. full_system（完整系统）
- **状态**: ✅ 已完成（15个PRD）
- **用途**: 作为对照组，其他配置与之对比
- **无需重新生成**: 直接使用 `results/full_system/` 的结果

#### 2. no_alignment（去掉双语对齐）
- **配置**:
  ```python
  disabled_agents = ["AlignmentAgent"]
  ```
- **预期影响**:
  - S_bi 从 0.507 降到 0.0（最直接的影响）
  - 其他指标可能不受影响
- **验证假设**: 双语对齐对双语一致性至关重要

#### 3. no_vision（去掉视觉生成）
- **配置**:
  ```python
  disabled_agents = ["VisionAgent"]
  ```
- **预期影响**:
  - S_mm 可能不变（因为还有其他模态如表格）
  - 但如果PRD中只有图片作为多模态内容，S_mm可能下降
- **验证假设**: 视觉生成对多模态一致性有影响吗？

#### 4. no_table（去掉表格生成）
- **配置**:
  ```python
  disabled_agents = ["TableAgent"]
  ```
- **预期影响**:
  - S_tab 从 1.0 降到 0.0（直接的影响）
  - S_mm 可能不变（因为还有其他模态如图片）
- **验证假设**: 表格生成是必需的吗？

#### 5. no_consistency（去掉一致性检查）
- **配置**:
  ```python
  disabled_agents = ["ConsistencyAgent"]
  ```
- **预期影响**:
  - S_var 可能不变（当前就是0）
  - 但实际的一致性可能下降（虽然没有指标测量）
- **验证假设**: 一致性检查Agent有作用吗？

#### 6. async_queue（异步队列通信）
- **配置**:
  ```python
  communication_mode = "async_queue"
  disabled_agents = []
  ```
- **预期影响**:
  - 性能可能有变化（更快或更慢）
  - 质量指标可能不变（只是通信方式改变）
- **验证假设**: 通信模式对系统性能有影响吗？

#### 7. mock_model（使用Mock模型）
- **配置**:
  ```python
  text_model_cn = MockModelClient()
  text_model_en = MockModelClient()
  vision_model = MockModelClient()
  ```
- **预期影响**:
  - 所有质量指标大幅下降
  - 但可以验证系统的架构是否完整
- **验证假设**: 真实模型vsMock模型，质量差异有多大？

---

## 🗂️ 实验文件组织

### 目录结构

```
results/
├── full_system/              # ✅ 已完成（15个PRD）
│   ├── prd_*.json
│   └── metrics_summary.json
│
├── ablation/
│   ├── no_alignment/        # 去掉双语对齐（15个PRD）
│   ├── no_vision/           # 去掉视觉生成（15个PRD）
│   ├── no_table/            # 去掉表格生成（15个PRD）
│   ├── no_consistency/      # 去掉一致性检查（15个PRD）
│   ├── async_queue/         # 异步队列通信（15个PRD）
│   ├── mock_model/          # Mock模型（15个PRD）
│   │
│   └── ablation_summary.json  # 消融实验汇总结果
```

### 文件命名规则

- PRD文件: `prd_{brief_id}.json`
- 指标汇总: `metrics_summary.json`
- 对比结果: `ablation_summary.json`

---

## 📊 实验规模

### 数据规模

- **Brief数量**: 15个
- **消融配置数**: 7个（包括full_system）
- **总PRD数量**: 7 × 15 = **105个PRD**
- **需要新生成的PRD**: 6 × 15 = **90个PRD**（full_system已有）

### 时间估算

- **平均生成时间**: 15.4分钟/PRD（基于full_system数据）
- **总实验时间**: 90 × 15.4 = **1386分钟**（约23小时）
- **考虑延迟和重试**: **约27小时**（1.2倍安全系数）

### 资源需求

- **API调用次数**: 约90个PRD × 多个Agent = 约500-1000次API调用
- **存储空间**: 约90个PRD × 50KB/PRD = 约4.5MB
- **网络稳定性**: 需要稳定的网络连接（避免超时）

---

## 🔧 实验脚本

### 需要创建的脚本

#### 脚本1: `scripts/run_ablation_experiment.py`

**功能**: 批量运行消融实验

**参数**:
- `--config`: 消融配置名称（如 `no_alignment`）
- `--benchmark-dir`: Brief目录
- `--output-dir`: 输出目录
- `--parallel`: 是否并行运行（可选）

**流程**:
1. 加载15个Brief
2. 为每个Brief运行指定配置的消融实验
3. 计算质量指标
4. 生成指标汇总文件

#### 脚本2: `scripts/analyze_ablation_results.py`

**功能**: 分析消融实验结果

**输出**:
- 每个配置的质量指标对比
- 统计显著性检验（Wilcoxon检验）
- 效应量分析（Cliff's δ）
- 可视化图表

---

## 📈 预期结果分析

### 假设验证表

| 配置 | 验证假设 | 预期结果 | 成功标准 |
|------|---------|---------|---------|
| **no_alignment** | 双语对齐是必需的 | S_bi显著下降 | S_bi < 0.3 |
| **no_vision** | 视觉生成影响质量 | S_mm可能下降 | S_mm < 0.9 |
| **no_table** | 表格生成是必需的 | S_tab=0 | S_tab = 0.0 |
| **no_consistency** | 一致性检查有作用 | 质量可能下降 | 需要人工评估 |
| **async_queue** | 通信模式影响性能 | 性能或质量变化 | 记录变化 |
| **mock_model** | 真实模型重要 | 所有指标下降 | 大部分指标 < 0.5 |

### 预期发现

1. **关键Agent**:
   - AlignmentAgent: 对S_bi至关重要
   - TableAgent: 对S_tab至关重要
   - 其他Agent: 需要实验验证

2. **非关键Agent**:
   - 某些Agent可能影响较小
   - 可以通过简化系统架构来减少复杂度

---

## ⚠️ 注意事项

### 实验执行注意事项

1. **网络稳定性**:
   - 90个PRD生成需要约27小时
   - 建议在稳定的网络环境下运行
   - 使用动态延迟避免API限流

2. **资源管理**:
   - 监控API调用次数
   - 监控存储空间使用
   - 定期备份实验结果

3. **错误处理**:
   - 实现智能重试机制
   - 记录所有失败案例
   - 失败后可以单独重试

4. **进度跟踪**:
   - 实时显示实验进度
   - 记录每个PRD的生成时间
   - 生成进度报告

---

## 📋 执行步骤

### Step 1: 准备实验脚本 ⏳
- [ ] 创建 `scripts/run_ablation_experiment.py`
- [ ] 创建 `scripts/analyze_ablation_results.py`
- [ ] 测试脚本功能

### Step 2: 运行消融实验 ⏳
- [ ] 运行 `no_alignment` 配置（15个PRD）
- [ ] 运行 `no_vision` 配置（15个PRD）
- [ ] 运行 `no_table` 配置（15个PRD）
- [ ] 运行 `no_consistency` 配置（15个PRD）
- [ ] 运行 `async_queue` 配置（15个PRD）
- [ ] 运行 `mock_model` 配置（15个PRD）

### Step 3: 分析实验结果 ⏳
- [ ] 计算各配置的质量指标
- [ ] 进行统计显著性检验
- [ ] 生成对比报告

### Step 4: 生成可视化 ⏳
- [ ] 生成对比图表
- [ ] 生成热力图
- [ ] 生成详细数据表格

---

## 🎯 成功标准

### 实验成功的标准

1. **数据完整性**: 所有90个PRD成功生成
2. **统计显著性**: 各配置之间有显著差异（p < 0.05）
3. **可解释性**: 能够解释每个Agent的作用
4. **可复现性**: 实验结果可以复现

### 预期产出

1. **消融实验报告**: 详细的分析报告
2. **可视化图表**: 对比图、热力图等
3. **数据文件**: 所有实验数据（JSON格式）
4. **论文素材**: 实验结果可用于论文写作

---

## 📝 总结

### 实验价值

1. **验证架构设计**: 证明哪些Agent是必需的
2. **优化系统性能**: 去掉不必要的Agent，减少复杂度
3. **学术贡献**: 为论文提供消融实验数据

### 关键里程碑

- ✅ **Week 3**: 完整系统实验完成（15/15 PRD）
- ⏳ **Week 4**: 消融实验（90个PRD，约27小时）
- ⏳ **Week 5**: 实验报告生成

---

**状态**: ⏳ 准备开始  
**预计开始时间**: Week 4  
**预计完成时间**: Week 4 结束前

