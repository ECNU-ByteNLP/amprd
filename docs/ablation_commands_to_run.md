# 消融实验运行命令

## 当前状态（最新）
- ✅ full_system: 15/15 (已完成)
- ✅ no_alignment: 15/15 (已完成)
- ✅ no_vision: 15/15 (已完成)
- ✅ no_table: 15/15 (已完成)
- ✅ no_consistency: 15/15 (已完成)
- ✅ async_queue: 15/15 (已完成)
- ⏳ mock_model: 0/15 (未开始) - **最后一步**

**总体进度**: 90/105 PRD (85.7%)  
**剩余**: 15个PRD（全部为mock_model）  
**预计剩余时间**: 3.8小时

## 运行命令（最后一步）

### 完成所有实验 - 运行mock_model配置

```bash
# mock_model - 运行所有15个Brief（约3.8小时）
python scripts/run_ablation_single_config.py --config mock_model
```

**说明**: mock_model配置用于验证真实模型（LLM/视觉模型）的重要性，对比使用Mock模型时的性能下降。

## 检查进度命令

```bash
# 检查所有配置的进度
python scripts/check_ablation_progress.py
```

## 后台运行（Windows PowerShell）

如果需要后台运行，可以使用：

```powershell
# 启动后台任务
Start-Job -ScriptBlock { cd D:\2025pos\2026paper\amprd ; python scripts/run_ablation_single_config.py --config no_alignment }

# 查看所有后台任务
Get-Job

# 查看任务输出
Receive-Job -Id <JobId>

# 等待任务完成
Wait-Job -Id <JobId>
```

## 推荐执行顺序

### 方案1：顺序执行（稳定，推荐）

```bash
# 步骤1: 完成已开始的配置
python scripts/run_ablation_single_config.py --config no_alignment
python scripts/run_ablation_single_config.py --config no_table
python scripts/run_ablation_single_config.py --config no_consistency

# 步骤2: 运行未开始的配置
python scripts/run_ablation_single_config.py --config no_vision
python scripts/run_ablation_single_config.py --config async_queue
python scripts/run_ablation_single_config.py --config mock_model
```

### 方案2：并行执行（更快，需要更多资源）

在多个终端窗口同时运行：

```bash
# 终端1
python scripts/run_ablation_single_config.py --config no_alignment

# 终端2
python scripts/run_ablation_single_config.py --config no_table

# 终端3
python scripts/run_ablation_single_config.py --config no_consistency

# 终端4
python scripts/run_ablation_single_config.py --config no_vision

# 终端5
python scripts/run_ablation_single_config.py --config async_queue

# 终端6
python scripts/run_ablation_single_config.py --config mock_model
```

## 预计时间

- 每个配置：约3.75小时（15个Brief × 15分钟/个）
- 剩余6个配置：约22.5小时

## 注意事项

1. 每个命令会运行对应配置的所有15个Brief
2. 脚本会自动跳过已完成的Brief（通过检查PRD文件是否存在）
3. 如果中断，可以重新运行命令，已完成的不会重复
4. 建议定期运行 `python scripts/check_ablation_progress.py` 检查进度

## 实验完成后的分析命令

```bash
# 分析消融实验结果
python scripts/analyze_ablation_results.py

# 生成可视化图表
python scripts/generate_visualizations.py

# 错误分析和案例研究
python scripts/error_analysis_and_case_study.py
```

