# 完整实验流程与数据检查清单

**目标**: 确保所有数据和实验流程符合顶会高标准  
**更新日期**: 2025-11-23  
**状态**: ✅ Brief质量已提升，准备进行实验

---

## 📊 数据质量检查清单

### 1. Brief数据（15个）✅

#### 检查项

- [x] **结构完整性**: 所有Brief包含必需字段（title, domain, goal）
- [x] **内容完整性**: 所有Brief包含推荐字段（problem_statement, solution_approach）
- [x] **用户画像**: 每个Brief至少2个用户画像
- [x] **约束条件**: 每个Brief至少2个约束条件
- [x] **业务指标**: 每个Brief至少2个业务指标
- [x] **Goal描述**: 每个Brief的Goal描述≥50字符
- [x] **领域覆盖**: 覆盖5个领域（General, Ecommerce, Financial, Medical, Education）

#### 验证结果

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 平均质量分 | ≥8.0/10 | 9.2/10 | ✅ 优秀 |
| 高质量Brief | ≥80% | 93% (14/15) | ✅ 优秀 |
| 低质量Brief | 0% | 0% | ✅ 完美 |
| 结构完整性 | 100% | 100% | ✅ 完美 |
| 领域覆盖 | ≥4个 | 5个 | ✅ 优秀 |

#### 验证命令

```bash
python scripts/validate_briefs.py
```

---

### 2. 专家PRD数据（参考数据）

#### 检查项

- [ ] **中文PRD映射**: `data/chinese_prds/processed/brief_to_expert_mapping.json`
  - [ ] 15个Brief都有对应的专家PRD
  - [ ] 专家PRD文件存在且可访问
  - [ ] 映射关系正确

- [ ] **英文PRD映射**: `data/expert_prds/mapping.json`（备选）
  - [ ] 映射文件存在
  - [ ] 专家PRD文件存在

#### 验证命令

```bash
# 检查映射文件
python -c "import json; from pathlib import Path; m = json.loads(Path('data/chinese_prds/processed/brief_to_expert_mapping.json').read_text()); print(f'映射数: {len(m.get(\"mappings\", {}))}')"
```

---

### 3. 基线系统数据（45个PRD）

#### 检查项

- [ ] **Baseline-TXT**: `results/baseline_text_only/`
  - [ ] 15个PRD文件存在
  - [ ] 所有PRD格式正确（JSON）
  - [ ] 指标已计算（metrics_summary.json）

- [ ] **Baseline-TPL**: `results/baseline_template/`
  - [ ] 15个PRD文件存在
  - [ ] 所有PRD格式正确

- [ ] **Baseline-RET**: `results/baseline_retrieval/`
  - [ ] 15个PRD文件存在
  - [ ] 所有PRD格式正确

#### 验证命令

```bash
# 检查基线系统PRD数量
ls results/baseline_text_only/prd_*.json | wc -l  # 应该=15
ls results/baseline_template/prd_*.json | wc -l   # 应该=15
ls results/baseline_retrieval/prd_*.json | wc -l  # 应该=15
```

---

### 4. 完整系统数据（15个PRD）

#### 检查项

- [ ] **Full System**: `results/full_system/`
  - [ ] 15个PRD文件存在（100%成功率）
  - [ ] 所有PRD格式正确
  - [ ] 指标已计算（metrics_summary.json）
  - [ ] 所有PRD质量指标合理

#### 验证命令

```bash
# 检查完整系统PRD数量
ls results/full_system/prd_*.json | wc -l  # 应该=15

# 检查指标汇总
cat results/full_system/metrics_summary.json | grep -c "prd_id"  # 应该=15
```

---

## 🔬 实验流程检查清单

### Phase 1: 数据准备 ✅

- [x] **Brief质量提升**
  - [x] 所有Brief结构完整
  - [x] 所有Brief内容质量≥8.0/10
  - [x] 所有Brief包含problem_statement和solution_approach
  - [x] 所有Brief至少2个用户画像
  - [x] 所有Brief至少2个约束条件

- [ ] **专家PRD验证**
  - [ ] 检查15个Brief的专家PRD映射
  - [ ] 验证专家PRD文件存在
  - [ ] 测试S_expert指标计算

- [ ] **基线系统验证**
  - [ ] 确认45个基线PRD存在
  - [ ] 验证基线系统指标已计算
  - [ ] 检查基线系统质量

---

### Phase 2: 完整系统实验 ✅

- [x] **实验脚本**: `scripts/run_full_system_experiment.py`
  - [x] 脚本已创建
  - [x] 支持Few-shot学习
  - [x] 支持S_expert指标
  - [x] 错误处理和重试机制

- [ ] **实验执行**
  - [ ] 运行完整系统实验（15个PRD）
  - [ ] 验证100%成功率
  - [ ] 检查生成时间合理（~15分钟/PRD）

- [ ] **结果验证**
  - [ ] 所有PRD格式正确
  - [ ] 所有指标已计算
  - [ ] 质量指标符合预期

---

### Phase 3: 消融实验 ⏳

- [x] **实验脚本**: `scripts/run_ablation_experiment.py`
  - [x] 脚本已创建
  - [x] 支持7个消融配置
  - [x] 自动检测已有结果
  - [x] 动态延迟避免限流

- [ ] **实验执行**
  - [ ] 运行消融实验（90个PRD）
  - [ ] 监控进度和错误
  - [ ] 验证所有配置完成

- [ ] **结果验证**
  - [ ] 所有90个PRD生成成功
  - [ ] 所有配置的指标已计算
  - [ ] 数据完整性检查

---

### Phase 4: 结果分析 ⏳

- [x] **分析脚本**: `scripts/analyze_ablation_results.py`
  - [x] 脚本已创建
  - [x] 支持统计检验
  - [x] 生成对比报告

- [ ] **分析执行**
  - [ ] 运行消融结果分析
  - [ ] 验证统计显著性
  - [ ] 检查对比表格

- [ ] **可视化生成**
  - [ ] 运行可视化脚本
  - [ ] 生成所有图表
  - [ ] 验证图表质量

---

### Phase 5: 错误分析与案例研究 ⏳

- [x] **分析脚本**: `scripts/error_analysis_and_case_study.py`
  - [x] 脚本已创建

- [ ] **分析执行**
  - [ ] 运行错误分析
  - [ ] 选择典型案例
  - [ ] 生成分析报告

---

### Phase 6: 人工评估（可选）⏳

- [x] **评估框架**: `scripts/human_evaluation_framework.py`
  - [x] 脚本已创建
  - [x] 评估问卷已生成

- [ ] **评估执行**
  - [ ] 联系评估人员
  - [ ] 分发评估问卷
  - [ ] 收集评估结果
  - [ ] 计算一致性指标

---

## 📋 数据完整性验证

### 必需数据文件

```
data/
├── benchmark/
│   ├── benchmark_index.json                    ✅ 已存在
│   ├── *_brief.json (15个)                    ✅ 已改进
│
├── chinese_prds/
│   └── processed/
│       └── brief_to_expert_mapping.json       ⚠️ 需验证
│
└── expert_prds/
    └── mapping.json                            ⚠️ 需验证

results/
├── baseline_text_only/
│   ├── prd_*.json (15个)                       ⚠️ 需验证
│   └── metrics_summary.json                   ⚠️ 需验证
│
├── baseline_template/
│   └── prd_*.json (15个)                       ⚠️ 需验证
│
├── baseline_retrieval/
│   └── prd_*.json (15个)                       ⚠️ 需验证
│
├── full_system/
│   ├── prd_*.json (15个)                       ⚠️ 需验证
│   └── metrics_summary.json                   ⚠️ 需验证
│
└── ablation/
    ├── no_alignment/
    ├── no_vision/
    ├── no_table/
    ├── no_consistency/
    ├── async_queue/
    └── mock_model/
```

---

## 🔍 质量指标验证

### 自动指标（13个）

- [ ] **S_comp**: 结构完整度
- [ ] **S_mm**: 多模态一致性
- [ ] **S_tab**: 表格一致性
- [ ] **S_bi**: 双语一致性
- [ ] **S_var**: 变量一致性
- [ ] **S_sem**: 语义质量
- [ ] **S_biz**: 业务对齐度
- [ ] **S_tech**: 技术可行性
- [ ] **S_risk**: 风险识别
- [ ] **S_expert**: 专家对齐度
- [ ] **S_ps**: 问题-解决方案分离
- [ ] **S_uj**: 用户旅程完整性
- [ ] **S_hyp**: 假设验证度

### 验证命令

```bash
# 检查指标计算
python -c "from src.metrics.quality import compute_all_metrics; from src.metrics.extended_quality import compute_all_extended_metrics; import json; prd = json.loads(open('results/full_system/prd_*.json').read()); print(compute_all_metrics(prd))"
```

---

## 📊 统计检验验证

### 必需统计方法

- [ ] **Wilcoxon检验**: 配对样本显著性检验
- [ ] **Cliff's δ**: 效应量分析
- [ ] **Bootstrap CI**: 置信区间

### 验证命令

```bash
# 运行对比分析
python scripts/compare_full_vs_baseline.py

# 检查统计结果
cat results/comparison_full_vs_baseline.json | grep "p_value"
```

---

## 🎯 实验执行标准

### 成功率要求

- **完整系统**: ≥95% (15/15 PRD)
- **消融实验**: ≥90% (81/90 PRD)
- **基线系统**: ≥95% (43/45 PRD)

### 质量要求

- **平均质量分**: ≥0.8 (所有指标平均)
- **S_expert**: ≥0.9 (专家对齐度)
- **S_sem**: ≥0.8 (语义质量)

### 时间要求

- **完整系统**: ~15分钟/PRD
- **消融实验**: ~15分钟/PRD
- **总实验时间**: ~27小时（消融实验）

---

## ✅ 最终检查清单

### 实验前检查

- [x] Brief质量验证通过（平均≥8.0/10）
- [ ] 专家PRD映射验证通过
- [ ] 基线系统数据完整（45个PRD）
- [ ] 完整系统数据完整（15个PRD）
- [ ] 所有脚本已测试

### 实验后检查

- [ ] 消融实验完成（90个PRD）
- [ ] 所有指标已计算
- [ ] 统计检验完成
- [ ] 可视化图表生成
- [ ] 分析报告完成

### 论文准备检查

- [ ] 所有数据完整
- [ ] 所有图表清晰
- [ ] 统计结果显著
- [ ] 案例研究完成
- [ ] 人工评估完成（可选）

---

## 🚀 执行顺序

1. **数据准备** ✅
   - Brief质量提升 ✅
   - 专家PRD验证 ⏳
   - 基线系统验证 ⏳

2. **完整系统实验** ⏳
   - 运行实验
   - 验证结果

3. **消融实验** ⏳
   - 运行实验（90个PRD）
   - 监控进度

4. **结果分析** ⏳
   - 统计分析
   - 可视化生成

5. **报告生成** ⏳
   - 错误分析
   - 案例研究
   - 完整报告

---

## 📝 验证脚本

### 完整验证脚本

```bash
#!/bin/bash
# 完整数据验证脚本

echo "=== Brief质量验证 ==="
python scripts/validate_briefs.py

echo "=== 基线系统验证 ==="
echo "Baseline-TXT: $(ls results/baseline_text_only/prd_*.json 2>/dev/null | wc -l)/15"
echo "Baseline-TPL: $(ls results/baseline_template/prd_*.json 2>/dev/null | wc -l)/15"
echo "Baseline-RET: $(ls results/baseline_retrieval/prd_*.json 2>/dev/null | wc -l)/15"

echo "=== 完整系统验证 ==="
echo "Full System: $(ls results/full_system/prd_*.json 2>/dev/null | wc -l)/15"

echo "=== 消融实验验证 ==="
echo "No Alignment: $(ls results/ablation/no_alignment/prd_*.json 2>/dev/null | wc -l)/15"
echo "No Vision: $(ls results/ablation/no_vision/prd_*.json 2>/dev/null | wc -l)/15"
echo "No Table: $(ls results/ablation/no_table/prd_*.json 2>/dev/null | wc -l)/15"
echo "No Consistency: $(ls results/ablation/no_consistency/prd_*.json 2>/dev/null | wc -l)/15"
echo "Async Queue: $(ls results/ablation/async_queue/prd_*.json 2>/dev/null | wc -l)/15"
echo "Mock Model: $(ls results/ablation/mock_model/prd_*.json 2>/dev/null | wc -l)/15"
```

---

## 📈 质量标准总结

### Brief质量标准 ✅

- ✅ 平均质量分: 9.2/10 (目标: ≥8.0)
- ✅ 高质量Brief: 93% (目标: ≥80%)
- ✅ 结构完整性: 100%
- ✅ 领域覆盖: 5个领域

### 实验质量标准

- ⏳ 成功率: ≥95%
- ⏳ 平均质量分: ≥0.8
- ⏳ 统计显著性: p < 0.05

---

**结论**: Brief数据质量已提升至高标准（9.2/10），可以开始实验。建议先验证专家PRD映射和基线系统数据，然后开始完整系统实验和消融实验。






