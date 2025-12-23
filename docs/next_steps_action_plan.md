# 下一步运行步骤安排

## 当前状态分析

根据诊断结果，需要完成以下工作：

### ✅ 已完成的配置
- `full_system`: 15/15 ✅
- `async_queue`: 14/15（缺少1个）
- `mock_model`: 14/15（缺少1个）

### ⚠️ 未完成的配置（各只有1个测试PRD）
- `no_alignment`: 1/15
- `no_consistency`: 1/15  
- `no_table`: 1/15
- `no_vision`: 1/15

---

## 运行步骤（按优先级）

### 步骤1：补全缺失的PRD（高优先级）

**目标**：为`async_queue`和`mock_model`各补全1个缺失的PRD

```bash
# 检查缺失的PRD ID
python -c "from pathlib import Path; benchmark_dir = Path('data/benchmark'); briefs = set(f.stem.replace('_brief', '') for f in benchmark_dir.glob('*_brief.json')); async_dir = Path('results/ablation/async_queue'); async_prds = set(f.stem.replace('prd_', '') for f in async_dir.glob('prd_*.json')); missing = briefs - async_prds; print(f'async_queue缺失: {missing}')"
```

如果确认缺失`general_ai_powered_prd_assistant`：

```bash
# 为async_queue生成缺失的PRD
python scripts/run_ablation_single_config.py --config async_queue --brief general_ai_powered_prd_assistant

# 为mock_model生成缺失的PRD
python scripts/run_ablation_single_config.py --config mock_model --brief general_ai_powered_prd_assistant
```

**预计时间**：约30分钟（2个PRD × 15分钟/个）

---

### 步骤2：完成未完成的消融配置（高优先级）

**目标**：完成`no_alignment`、`no_consistency`、`no_table`、`no_vision`的所有15个benchmark PRD

**推荐执行方式**：按顺序执行（稳定）或并行执行（快速）

#### 方式1：顺序执行（推荐，稳定）

```bash
# 按顺序逐个完成
python scripts/run_ablation_single_config.py --config no_alignment
python scripts/run_ablation_single_config.py --config no_consistency
python scripts/run_ablation_single_config.py --config no_table
python scripts/run_ablation_single_config.py --config no_vision
```

**预计时间**：约15小时（4个配置 × 15个PRD × 15分钟/个 ÷ 60分钟）

#### 方式2：并行执行（更快，需要4个终端）

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

**预计时间**：约3.75小时（4个配置并行，最慢的配置完成时间）

---

### 步骤3：验证所有实验完成

```bash
# 检查进度
python scripts/check_ablation_progress.py

# 预期结果：所有配置都显示 15/15 (100.0%)
```

---

### 步骤4：重新运行分析（实验完成后）

```bash
# 1. 分析消融实验结果
python scripts/analyze_ablation_results.py

# 2. 生成可视化图表
python scripts/generate_visualizations.py

# 3. 错误分析和案例研究（如果之前没运行过）
python scripts/error_analysis_and_case_study.py
```

---

## 推荐执行顺序

### 快速方案（如果您有时间监控）

1. **立即执行步骤1**：补全2个缺失的PRD（约30分钟）
2. **然后并行执行步骤2**：4个终端同时运行（约3.75小时）
3. **完成后执行步骤3-4**：验证和分析（约10分钟）

**总时间**：约4.5小时

### 稳定方案（如果希望稳定运行）

1. **立即执行步骤1**：补全2个缺失的PRD（约30分钟）
2. **然后顺序执行步骤2**：一个一个配置完成（约15小时）
3. **完成后执行步骤3-4**：验证和分析（约10分钟）

**总时间**：约15.5小时

---

## 注意事项

1. **脚本会自动跳过已完成的PRD**：重新运行命令不会重复生成
2. **如果中断**：重新运行相同命令即可继续，已完成的会被跳过
3. **定期检查进度**：运行`python scripts/check_ablation_progress.py`查看进度
4. **监控资源使用**：并行运行会占用更多CPU/内存，确保系统资源充足

---

## 检查清单

完成后确认：

- [ ] `async_queue`: 15/15 PRD
- [ ] `mock_model`: 15/15 PRD
- [ ] `no_alignment`: 15/15 PRD
- [ ] `no_consistency`: 15/15 PRD
- [ ] `no_table`: 15/15 PRD
- [ ] `no_vision`: 15/15 PRD
- [ ] 重新运行分析脚本得到正确结果
- [ ] 生成所有可视化图表

---

## 如果遇到问题

1. **PRD生成失败**：检查日志，确认API连接和模型可用性
2. **进度检查异常**：确认PRD文件命名格式正确（`prd_<brief_id>.json`）
3. **分析结果异常**：确认所有配置都有15个benchmark PRD

---

## 最终目标

完成所有消融实验后：
- ✅ 105个PRD（7个配置 × 15个benchmark）
- ✅ 完整的统计分析报告
- ✅ 可视化图表
- ✅ 可用于论文的实验数据

