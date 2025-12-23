# 完整实验执行指南

**目标**: 完成所有符合顶会标准的实验  
**预计时间**: Week 4-5（约2周）  
**完成度**: 脚本已就绪，等待执行

---

## 📋 实验流程概览

```
Week 4: 消融实验
├─ 运行消融实验（90个PRD，约27小时）
├─ 分析消融实验结果
└─ 生成可视化图表

Week 5: 报告与评估
├─ 错误分析与案例研究
├─ 人工评估（可选）
└─ 生成完整实验报告
```

---

## 🚀 执行步骤

### Step 1: 运行消融实验（P0 - 必须）

**脚本**: `scripts/run_ablation_experiment.py`

**命令**:
```bash
python scripts/run_ablation_experiment.py
```

**预计时间**: 约27小时（90个PRD × 15.4分钟/PRD）

**输出**:
- `results/ablation/` - 各配置的PRD文件
- `results/ablation/ablation_summary.json` - 实验汇总

**注意事项**:
- 确保网络稳定
- 建议在服务器上运行
- 可以分批运行（按配置）
- 定期检查进度

**监控**:
```bash
# 查看日志
tail -f results/logs/ablation_experiment_*.log

# 检查进度
ls results/ablation/*/prd_*.json | wc -l
```

---

### Step 2: 分析消融实验结果（P0 - 必须）

**脚本**: `scripts/analyze_ablation_results.py`

**命令**:
```bash
python scripts/analyze_ablation_results.py
```

**预计时间**: 5-10分钟

**输出**:
- `results/ablation/ablation_analysis.json` - 详细分析结果
- `results/ablation/ablation_comparison_table.json` - 对比表格

**检查点**:
- ✅ 所有配置都有结果
- ✅ 统计显著性检验完成
- ✅ 对比表格生成成功

---

### Step 3: 生成可视化图表（P0 - 必须）

**脚本**: `scripts/generate_visualizations.py`

**前置条件**:
```bash
pip install matplotlib seaborn pandas numpy
```

**命令**:
```bash
python scripts/generate_visualizations.py
```

**预计时间**: 2-3分钟

**输出**:
- `results/visualizations/full_vs_baseline_comparison.png` - 完整系统vs基线系统对比图
- `results/visualizations/ablation_heatmap.png` - 消融实验热力图
- `results/visualizations/ablation_comparison.png` - 消融实验对比图
- `results/visualizations/statistical_significance.png` - 统计显著性可视化

**检查点**:
- ✅ 所有图表生成成功
- ✅ 图表清晰可读
- ✅ 符合论文要求

---

### Step 4: 错误分析与案例研究（P1 - 强烈推荐）

**脚本**: `scripts/error_analysis_and_case_study.py`

**命令**:
```bash
python scripts/error_analysis_and_case_study.py
```

**预计时间**: 5-10分钟

**输出**:
- `results/analysis/error_analysis_report.json` - 错误分析报告
- `results/analysis/case_study_report.json` - 案例研究报告

**用途**:
- 识别系统失败原因
- 选择典型案例用于论文
- 提供改进建议

---

### Step 5: 人工评估（P1 - 强烈推荐）

**脚本**: `scripts/human_evaluation_framework.py`

**命令**:
```bash
python scripts/human_evaluation_framework.py
```

**预计时间**: 准备5分钟，评估需要协调人员（3-5天）

**输出**:
- `results/human_evaluation/questionnaire.html` - 评估问卷
- `results/human_evaluation/samples.json` - 评估样本
- `results/human_evaluation/results_template.json` - 结果模板

**执行流程**:
1. 运行脚本生成问卷
2. 联系评估人员（PM、研发、QA各≥5人）
3. 分发问卷进行评估
4. 收集评估结果
5. 计算评分者间一致性（Krippendorff's α）

**评估人员要求**:
- PM（产品经理）: ≥5人
- 研发（开发工程师）: ≥5人
- QA（测试工程师）: ≥5人
- 每个领域至少5-10个样本

---

### Step 6: 生成完整实验报告（P0 - 必须）

**脚本**: 待创建（或手动整理）

**内容**:
1. 实验设置
2. 基线系统对比结果
3. 消融实验结果
4. 统计分析
5. 可视化图表
6. 错误分析
7. 案例研究
8. 人工评估结果（如果有）

**输出**:
- `docs/final_experiment_report.md` - 完整实验报告
- `results/final_report/` - 所有报告材料

---

## 📊 实验检查清单

### Week 4 检查清单

- [ ] 消融实验运行完成（90个PRD）
- [ ] 所有配置都有结果
- [ ] 消融实验结果分析完成
- [ ] 可视化图表生成完成
- [ ] 统计显著性检验完成

### Week 5 检查清单

- [ ] 错误分析完成
- [ ] 案例研究完成
- [ ] 人工评估完成（可选）
- [ ] 完整实验报告生成
- [ ] 所有材料整理完成

---

## ⚠️ 常见问题

### Q1: 消融实验运行时间太长怎么办？

**A**: 
- 可以分批运行（按配置）
- 使用多进程并行（需要修改脚本）
- 在服务器上后台运行
- 使用screen或tmux保持会话

### Q2: API限流怎么办？

**A**:
- 增加延迟时间（脚本中已实现动态延迟）
- 使用多个API密钥
- 联系API提供商提高限流

### Q3: 可视化图表中文显示乱码？

**A**:
- 确保系统安装了中文字体（Microsoft YaHei）
- 脚本会自动尝试设置字体
- 如果仍有问题，可以修改脚本中的字体设置

### Q4: 人工评估找不到足够的人？

**A**:
- 可以降低要求（至少3人/角色）
- 可以只评估部分样本（每个领域3-5个）
- 可以分阶段进行（先小规模测试）

---

## 📈 进度跟踪

### 当前状态

- ✅ 实验脚本已创建
- ✅ 分析脚本已创建
- ✅ 可视化脚本已创建
- ✅ 错误分析脚本已创建
- ✅ 人工评估框架已创建
- ⏳ 等待执行消融实验

### 下一步行动

1. **立即执行**: 运行消融实验（`scripts/run_ablation_experiment.py`）
2. **并行准备**: 准备人工评估（联系评估人员）
3. **等待数据**: 消融实验完成后，运行分析和可视化

---

## 🎯 成功标准

### 必须完成（P0）

- ✅ 消融实验完成（90个PRD）
- ✅ 消融实验结果分析完成
- ✅ 可视化图表生成完成
- ✅ 统计显著性检验完成

### 强烈推荐（P1）

- ✅ 错误分析完成
- ✅ 案例研究完成
- ✅ 人工评估完成（至少小规模）

### 可选（P2）

- ⚠️ 样本量扩展（增加到30个Brief）
- ⚠️ 理论分析加强

---

## 📝 实验记录

### 实验日期记录

- **Week 4开始**: [填写日期]
- **消融实验开始**: [填写日期]
- **消融实验完成**: [填写日期]
- **Week 5开始**: [填写日期]
- **报告完成**: [填写日期]

### 实验结果记录

- **消融实验成功率**: [填写百分比]
- **平均生成时间**: [填写时间]
- **统计显著性**: [填写显著指标数]
- **人工评估一致性**: [填写Krippendorff's α]

---

**最后更新**: 2025-11-23  
**状态**: ✅ 脚本就绪，等待执行

