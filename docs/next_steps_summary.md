# 下一步运行步骤总结

## 🎯 当前情况

根据检查，**进度检查显示105/105完成**，但**分析脚本发现部分配置只有1个PRD**。

这说明：
- 进度检查可能基于其他标准（如metrics_summary.json）
- 实际目录中的PRD文件可能不完整
- 需要重新运行这些配置的实验

---

## 📋 需要执行的步骤

### **步骤1：检查实际文件情况**

```bash
# 检查每个配置目录的实际PRD文件数量
python scripts/diagnose_ablation_analysis.py
```

这将显示每个配置目录实际有多少个PRD文件。

---

### **步骤2：根据检查结果补全缺失的PRD**

如果确认某些配置缺少PRD，运行：

#### 如果缺少多个PRD（推荐顺序执行）：

```bash
# 1. 补全no_alignment（14个PRD）
python scripts/run_ablation_single_config.py --config no_alignment

# 2. 补全no_consistency（14个PRD）
python scripts/run_ablation_single_config.py --config no_consistency

# 3. 补全no_table（14个PRD）
python scripts/run_ablation_single_config.py --config no_table

# 4. 补全no_vision（14个PRD）
python scripts/run_ablation_single_config.py --config no_vision

# 5. 补全async_queue缺失的1个
python scripts/run_ablation_single_config.py --config async_queue --brief general_ai_powered_prd_assistant

# 6. 补全mock_model缺失的1个
python scripts/run_ablation_single_config.py --config mock_model --brief general_ai_powered_prd_assistant
```

**预计时间**：
- 步骤1-4：每个约3.5小时（14个PRD × 15分钟），总共约14小时（顺序）或3.5小时（并行4个终端）
- 步骤5-6：每个约15分钟，总共30分钟

---

#### 如果选择并行执行（需要4个终端窗口）：

**终端1**：
```bash
python scripts/run_ablation_single_config.py --config no_alignment
```

**终端2**：
```bash
python scripts/run_ablation_single_config.py --config no_consistency
```

**终端3**：
```bash
python scripts/run_ablation_single_config.py --config no_table
```

**终端4**：
```bash
python scripts/run_ablation_single_config.py --config no_vision
```

等这4个完成后，再运行步骤5-6。

---

### **步骤3：验证所有PRD已生成**

```bash
# 重新运行诊断脚本
python scripts/diagnose_ablation_analysis.py

# 确认每个配置都有15个benchmark PRD
```

---

### **步骤4：重新运行分析**

```bash
# 1. 分析消融实验结果
python scripts/analyze_ablation_results.py

# 2. 生成可视化图表
python scripts/generate_visualizations.py

# 3. 错误分析和案例研究
python scripts/error_analysis_and_case_study.py
```

---

## ⏱️ 预计总时间

### 顺序执行：
- 补全实验：约14.5小时
- 分析：约10分钟
- **总计**：约14.5小时

### 并行执行：
- 补全实验：约3.75小时（并行4个配置）
- 分析：约10分钟
- **总计**：约4小时

---

## ✅ 检查清单

完成后确认：

- [ ] 所有配置目录都有15个PRD文件（通过`diagnose_ablation_analysis.py`确认）
- [ ] 所有配置都是15/15 benchmark PRD（通过`analyze_ablation_results.py`确认）
- [ ] 分析结果正常（没有样本数为0或异常值）
- [ ] 可视化图表已生成

---

## 🔍 故障排查

如果遇到问题：

1. **PRD文件存在但分析脚本找不到**
   - 检查文件命名：应该是`prd_<brief_id>.json`格式
   - 确认brief_id在benchmark列表中

2. **进度显示完成但文件不完整**
   - 检查`metrics_summary.json`可能记录了已完成，但实际文件缺失
   - 重新运行对应配置的脚本会跳过已存在的PRD

3. **分析结果异常**
   - 确保所有配置都有15个benchmark PRD
   - 检查指标计算是否正常

---

## 📝 建议

1. **优先并行执行**：如果有4个终端可用，并行执行可以节省约10小时
2. **定期检查**：每完成一个配置就运行`diagnose_ablation_analysis.py`检查
3. **保存中间结果**：每次分析后保存结果，避免重复计算

