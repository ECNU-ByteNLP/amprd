# 消融实验运行指南

## 实验概述

消融实验用于验证各个Agent的必要性，共7个配置：
1. **full_system**: 完整系统（对照组，已有15个PRD）
2. **no_alignment**: 去掉双语对齐Agent
3. **no_vision**: 去掉视觉生成Agent
4. **no_table**: 去掉表格生成Agent
5. **no_consistency**: 去掉一致性检查Agent
6. **async_queue**: 异步队列通信模式
7. **mock_model**: 使用Mock模型

**总工作量**: 6个配置 × 15个Brief = 90个PRD（full_system已有，无需重新生成）

**预计时间**: 约27小时（每个PRD平均15分钟）

## 运行方式

### 方式1: 分批运行（推荐）

由于实验时间较长，建议分批运行各个配置：

```bash
# 运行单个配置（所有15个Brief）
python scripts/run_ablation_single_config.py --config no_alignment
python scripts/run_ablation_single_config.py --config no_vision
python scripts/run_ablation_single_config.py --config no_table
python scripts/run_ablation_single_config.py --config no_consistency
python scripts/run_ablation_single_config.py --config async_queue
python scripts/run_ablation_single_config.py --config mock_model
```

### 方式2: 运行单个Brief（用于测试）

```bash
# 运行单个配置的单个Brief
python scripts/run_ablation_single_config.py --config no_alignment --brief-id general_google_search_algorithm_update
```

### 方式3: 完整运行（一次性运行所有配置）

```bash
# 运行所有配置（约27小时）
python scripts/run_ablation_experiment.py
```

## 检查进度

随时检查实验进度：

```bash
python scripts/check_ablation_progress.py
```

输出示例：
```
配置                   状态           进度              描述
----------------------------------------------------------------------
full_system          ✅ completed   15/15 (100.0%)  完整系统
no_alignment         🔄 in_progress 1/15 (6.7%)     去掉双语对齐Agent
no_vision            ⏳ not_started 0/15 (0.0%)      去掉视觉生成Agent
...
```

## 后台运行

在Windows PowerShell中，可以使用后台任务运行：

```powershell
# 启动后台任务
Start-Job -ScriptBlock { cd D:\2025pos\2026paper\amprd ; python scripts/run_ablation_single_config.py --config no_vision }

# 查看后台任务
Get-Job

# 查看任务输出
Receive-Job -Id <JobId>

# 等待任务完成
Wait-Job -Id <JobId>
```

在Linux/Mac中，可以使用nohup或screen：

```bash
# 使用nohup
nohup python scripts/run_ablation_single_config.py --config no_vision > no_vision.log 2>&1 &

# 使用screen
screen -S ablation_no_vision
python scripts/run_ablation_single_config.py --config no_vision
# 按Ctrl+A然后D退出screen
# 重新连接: screen -r ablation_no_vision
```

## 结果位置

每个配置的结果保存在：
- `results/ablation/<config_name>/`
  - `prd_<brief_id>.json`: 生成的PRD文件
  - `metrics_summary.json`: 指标汇总
  - `blackboard.json`: 黑板状态（用于调试）

## 注意事项

1. **API限流**: 脚本已内置延迟机制，避免API限流。如果遇到限流错误，可以增加延迟时间。

2. **中断恢复**: 如果实验中断，可以重新运行脚本，已完成的Brief会被跳过（通过检查PRD文件是否存在）。

3. **资源消耗**: 每个PRD生成需要调用多次API，注意API配额和费用。

4. **日志查看**: 详细日志保存在 `results/logs/` 目录。

## 完成后的下一步

所有实验完成后，运行分析脚本：

```bash
# 分析消融实验结果
python scripts/analyze_ablation_results.py

# 生成可视化图表
python scripts/generate_visualizations.py

# 错误分析和案例研究
python scripts/error_analysis_and_case_study.py
```






