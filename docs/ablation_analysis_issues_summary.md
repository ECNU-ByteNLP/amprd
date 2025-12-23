# 消融实验分析问题总结

## 发现的问题

### 1. ✅ 已修复：完整系统PRD过滤问题

**问题**：full_system目录下有66个PRD文件，但只有15个是benchmark PRD，其余是UUID命名的测试文件。

**修复**：
- 添加了`get_benchmark_brief_ids()`函数识别benchmark brief
- 在加载时过滤出benchmark PRD，忽略UUID命名的文件
- 现在正确加载15个benchmark PRD

### 2. ⚠️ 部分配置缺失PRD

**现状**：
- `async_queue`: 14/15 PRD（缺少`general_ai_powered_prd_assistant`）
- `mock_model`: 14/15 PRD（缺少`general_ai_powered_prd_assistant`）
- `no_alignment`: 1/15 PRD（只有`general_google_search_algorithm_update`）
- `no_consistency`: 1/15 PRD（只有`general_google_search_algorithm_update`）
- `no_table`: 1/15 PRD（只有`general_google_search_algorithm_update`）
- `no_vision`: 1/15 PRD（只有`general_google_search_algorithm_update`）

**原因**：
- `async_queue`和`mock_model`：可能某个PRD生成失败或被跳过
- 其他配置：实验未完成，只有测试运行时的1个PRD

**建议**：
- 检查`async_queue`和`mock_model`目录，确认是否真的缺少该PRD
- 继续运行未完成的配置实验

### 3. ⚠️ 指标值为0的问题

**问题**：对于未完成配置（只有1个PRD），所有指标对比都是0.000。

**原因**：
- 样本数太少（只有1个），无法进行有效统计
- 完整的Wilcoxon检验等统计方法需要至少2个样本

**处理**：
- 对于样本数<2的配置，输出警告并跳过统计分析
- 建议等实验完成后再进行对比分析

### 4. ✅ 已修复：完整系统指标提取

**问题**：完整系统的config_name显示为"unknown"。

**修复**：
- 改进了配置识别逻辑
- 优先查找包含"full"或样本数最多的配置
- 现在正确识别为"full_system"配置

## 当前分析结果

### 已完成的配置对比（14-15个样本）

- **async_queue vs full_system**:
  - S_comp, S_mm, S_tab: 无显著差异（都是1.000）
  - S_bi: async_queue略高（0.564 vs 0.504，+11.8%）***
  - S_sem, S_biz, S_tech, S_risk, S_expert, S_ps, S_uj, S_hyp: async_queue均为0（可能计算问题或缺失字段）

- **mock_model vs full_system**:
  - S_comp: mock_model显著更低（0.000 vs 1.000，-100%）***
  - S_bi: mock_model显著更低（0.000 vs 0.504，-100%）**
  - 其他指标：mock_model均为0（符合预期，使用Mock模型）

### 未完成配置

以下配置只有1个PRD，无法进行有效统计分析：
- no_alignment
- no_consistency  
- no_table
- no_vision

## 建议

1. **完成缺失实验**：
   - 运行缺失的`general_ai_powered_prd_assistant` PRD（对async_queue和mock_model）
   - 完成其他配置的实验（至少完成所有15个benchmark brief）

2. **重新运行分析**：
   - 等所有实验完成后，重新运行`analyze_ablation_results.py`
   - 确保所有配置都有15个benchmark PRD

3. **检查指标计算**：
   - 检查为什么async_queue和mock_model的某些指标（S_sem等）都是0
   - 可能是这些指标的计算逻辑有问题，或者PRD中确实缺少相关字段

## 下一步

1. 检查并补全缺失的PRD
2. 完成所有消融配置的实验（15个benchmark PRD）
3. 重新运行分析脚本生成最终报告

