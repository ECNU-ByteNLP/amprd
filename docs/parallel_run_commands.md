# 并行运行命令（真实数据）

## ✅ 确认：所有命令都会生成真实PRD数据

脚本会：
- 从 `data/benchmark/` 加载真实的15个Brief
- 使用真实的模型API（Qwen等）生成PRD
- 只有在 `mock_model` 配置时才使用Mock模型（这是实验的一部分）

---

## 🚀 并行运行命令（4个终端窗口）

### **终端窗口1 - no_alignment**

```bash
cd D:\2025pos\2026paper\amprd
python scripts/run_ablation_single_config.py --config no_alignment
```

**功能**：为所有15个benchmark brief生成"去掉双语对齐Agent"配置的PRD  
**预计时间**：约3.75小时  
**生成数据**：15个真实PRD文件 → `results/ablation/no_alignment/prd_*.json`

---

### **终端窗口2 - no_consistency**

```bash
cd D:\2025pos\2026paper\amprd
python scripts/run_ablation_single_config.py --config no_consistency
```

**功能**：为所有15个benchmark brief生成"去掉一致性检查Agent"配置的PRD  
**预计时间**：约3.75小时  
**生成数据**：15个真实PRD文件 → `results/ablation/no_consistency/prd_*.json`

---

### **终端窗口3 - no_table**

```bash
cd D:\2025pos\2026paper\amprd
python scripts/run_ablation_single_config.py --config no_table
```

**功能**：为所有15个benchmark brief生成"去掉表格生成Agent"配置的PRD  
**预计时间**：约3.75小时  
**生成数据**：15个真实PRD文件 → `results/ablation/no_table/prd_*.json`

---

### **终端窗口4 - no_vision**

```bash
cd D:\2025pos\2026paper\amprd
python scripts/run_ablation_single_config.py --config no_vision
```

**功能**：为所有15个benchmark brief生成"去掉视觉生成Agent"配置的PRD  
**预计时间**：约3.75小时  
**生成数据**：15个真实PRD文件 → `results/ablation/no_vision/prd_*.json`

---

## 📝 等上面4个完成后，运行以下命令补全缺失的PRD

### **补全 async_queue 缺失的1个PRD**

```bash
cd D:\2025pos\2026paper\amprd
python scripts/run_ablation_single_config.py --config async_queue --brief-id general_ai_powered_prd_assistant
```

**功能**：为`general_ai_powered_prd_assistant` brief生成"异步队列通信模式"配置的PRD  
**预计时间**：约15分钟  
**生成数据**：1个真实PRD文件 → `results/ablation/async_queue/prd_general_ai_powered_prd_assistant.json`

---

### **补全 mock_model 缺失的1个PRD**

```bash
cd D:\2025pos\2026paper\amprd
python scripts/run_ablation_single_config.py --config mock_model --brief-id general_ai_powered_prd_assistant
```

**功能**：为`general_ai_powered_prd_assistant` brief生成"使用Mock模型"配置的PRD  
**预计时间**：约15分钟  
**生成数据**：1个真实PRD文件 → `results/ablation/mock_model/prd_general_ai_powered_prd_assistant.json`

**注意**：`mock_model`配置会使用Mock模型（这是实验设计的一部分，用于对比真实模型的重要性）

---

## ✅ 验证完成

等所有命令完成后，运行：

```bash
cd D:\2025pos\2026paper\amprd
python scripts/check_ablation_progress.py
```

**预期结果**：所有配置显示 15/15 (100.0%)

---

## 📊 生成最终分析报告

```bash
cd D:\2025pos\2026paper\amprd

# 1. 分析消融实验结果（真实数据对比）
python scripts/analyze_ablation_results.py

# 2. 生成可视化图表（基于真实分析结果）
python scripts/generate_visualizations.py

# 3. 错误分析和案例研究（基于真实PRD数据）
python scripts/error_analysis_and_case_study.py
```

---

## 📁 生成的文件位置

所有真实PRD数据会保存在：
- `results/ablation/no_alignment/prd_*.json` (15个)
- `results/ablation/no_consistency/prd_*.json` (15个)
- `results/ablation/no_table/prd_*.json` (15个)
- `results/ablation/no_vision/prd_*.json` (15个)
- `results/ablation/async_queue/prd_*.json` (15个，包含补全的1个)
- `results/ablation/mock_model/prd_*.json` (15个，包含补全的1个)

分析结果会保存在：
- `results/ablation/ablation_analysis.json` - 完整统计分析
- `results/ablation/ablation_comparison_table.json` - 对比表格
- `results/visualizations/*.png` - 可视化图表
- `results/analysis/*.json` - 错误分析和案例研究

---

## ⚠️ 重要说明

1. **所有数据都是真实的**：
   - 从真实Brief文件生成
   - 使用真实模型API（除了mock_model配置）
   - 生成真实的PRD文档

2. **自动跳过已存在的PRD**：
   - 如果PRD文件已存在，脚本会跳过
   - 可以安全地重新运行命令

3. **API调用**：
   - 每个PRD生成会调用真实的模型API
   - 需要确保API密钥已配置（.env文件）
   - 脚本会自动处理API限流（5秒延迟）

4. **进度监控**：
   - 每个终端窗口会显示当前进度
   - 日志保存在 `results/logs/` 目录

---

## 🎯 预计总时间

- **并行运行4个配置**：约3.75小时（最慢的那个）
- **补全2个缺失PRD**：约30分钟
- **生成分析报告**：约10分钟

**总计**：约4-4.5小时

