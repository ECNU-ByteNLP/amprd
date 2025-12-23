# 后续实验计划（基于快速实验结果）

## 实验状态概览

### ✅ 已完成：快速实验（步骤1）
- **数据集**：已创建15个基准PRD样例（覆盖14种模板风格）
- **生成结果**：成功生成12个PRD（80%成功率）
- **质量指标**：已计算13个质量指标
- **简要报告**：已生成 `reports/quick_report.md`

### 📋 当前发现
- **成功指标**：S_mm=0.942, S_tab=1.000（表现优秀）
- **问题指标**：S_bi=0.106（双语一致性严重不足）
- **网络问题**：3个PRD因网络超时失败（第8-10个）

---

## 下一步实验计划

### 阶段一：完善基础实验（优先级：高）

#### 1.1 修复失败的PRD生成（可选，10-15分钟）

**目的**：补全失败的3个PRD，确保完整数据集

**执行步骤**：
```bash
# 单独重试失败的3个PRD
python scripts/retry_failed_prds.py \
    --benchmark-dir data/benchmark \
    --output-dir results/full_system \
    --failed-prds general_figma_real_time_collaboration,general_miro_template_marketplace,general_linear_priority_micro_adjustments
```

**预计结果**：
- 补全3个失败的PRD
- 数据集完整度：15/15（100%）

**是否需要**：取决于后续实验是否需要完整数据集

---

#### 1.2 运行基线系统对比（优先级：高，15-30分钟）

**目的**：生成基线系统的PRD，用于定量对比

**基线系统**：
1. **Baseline-TXT**：单一LLM纯文本生成（无多模态、无双语对齐）
2. **Baseline-TPL**：规则模板+简单插值（传统文档工具）
3. **Baseline-MIX**：检索增强弱多模态（可选）

**执行步骤**：
```bash
# 运行基线系统生成
python scripts/run_baseline_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results/baseline \
    --baseline-type text_only  # 或 template, retrieval
```

**或手动运行**：
```python
from pathlib import Path
from src.baselines.text_only import generate_prd_text_only
from src.data.benchmark_builder import BenchmarkBuilder
import json

builder = BenchmarkBuilder(Path("data/benchmark"))
prds = builder.list_prds()
output_dir = Path("results/baseline_text_only")
output_dir.mkdir(parents=True, exist_ok=True)

for prd_info in prds:
    brief = builder.load_brief(prd_info["prd_id"])
    prd_json = generate_prd_text_only(brief)
    
    prd_path = output_dir / f"prd_{prd_info['prd_id']}.json"
    prd_path.write_text(
        json.dumps(prd_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 基线PRD已生成: {prd_path}")
```

**预计输出**：
- `results/baseline_text_only/prd_*.json`：基线系统生成的PRD
- 与完整系统的指标对比

**时间预估**：15-30分钟（取决于模型和样本数）

---

#### 1.3 重新计算质量指标（仅新生成的PRD）

**目的**：只统计本次新生成的12个PRD的指标，避免历史数据干扰

**执行步骤**：
```python
from pathlib import Path
import json
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics
from datetime import datetime

# 只统计最近生成的PRD（例如：今天生成的）
output_dir = Path("results/full_system")
prd_files = list(output_dir.glob("prd_*.json"))

# 筛选新生成的PRD（根据修改时间）
cutoff_time = datetime(2025, 11, 20, 22, 0, 0)  # 根据实际情况调整
new_prds = [
    f for f in prd_files 
    if datetime.fromtimestamp(f.stat().st_mtime) > cutoff_time
]

print(f"筛选出 {len(new_prds)} 个新生成的PRD")

results = []
for prd_path in new_prds:
    try:
        prd = json.loads(prd_path.read_text(encoding="utf-8"))
        basic_metrics = compute_all_metrics(prd)
        extended_metrics = compute_all_extended_metrics(prd)
        all_metrics = {**basic_metrics, **extended_metrics}
        
        results.append({
            "prd_id": prd_path.stem,
            "metrics": all_metrics,
        })
    except Exception as e:
        print(f"⚠️  计算 {prd_path.name} 指标时出错: {e}")

# 保存结果
results_path = Path("results/new_prds_metrics.json")
results_path.write_text(
    json.dumps(results, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"✅ 指标已保存至: {results_path}")
```

**预计输出**：
- `results/new_prds_metrics.json`：仅新生成PRD的指标
- 更准确的指标平均值

---

### 阶段二：消融实验（优先级：高，1-2小时）

#### 2.1 定义消融实验配置

**已定义的消融配置**（共7个）：
1. **full_system**：完整多智能体系统（基线）
2. **no_alignment**：无AlignmentAgent（验证双语对齐的必要性）
3. **no_vision**：无VisionAgent（验证多模态的必要性）
4. **no_table**：无TableAgent（验证结构化表格的必要性）
5. **no_consistency**：无ConsistencyAgent（验证一致性检查的必要性）
6. **async_queue**：异步队列通信模式（验证通信模式的影响）
7. **mock_model**：使用Mock模型（验证真实模型的重要性）

#### 2.2 运行消融实验

**执行步骤**：
```bash
# 方式1：使用一键脚本（推荐）
python scripts/run_benchmark_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results \
    --run-ablation \
    --verbose
```

**或方式2：手动运行**：
```python
from pathlib import Path
from src.experiments.ablation_suite import AblationSuite
from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder
import json

# 准备Brief文件
builder = BenchmarkBuilder(Path("data/benchmark"))
prds = builder.list_prds()

# 创建消融实验套件
ablation_dir = Path("results/ablation")
suite = AblationSuite(ablation_dir)

# 获取所有消融配置
configs = suite.define_ablation_configs()
print(f"共 {len(configs)} 个消融实验配置")

# 定义orchestrator工厂函数
def create_orchestrator(config):
    return MultiAgentOrchestrator(
        persist_dir=ablation_dir / config.name,
        disabled_agents=config.disabled_agents,
        communication_mode=config.communication_mode,
    )

# 运行所有消融实验
for config in configs:
    print(f"\n运行消融实验: {config.name}")
    print(f"  描述: {config.description}")
    
    # 只使用成功生成的12个PRD（节省时间）
    brief_paths = []
    for prd_info in prds[:12]:  # 只使用前12个成功的
        brief_path = builder.benchmark_dir / prd_info.get("brief_path", "")
        if brief_path.exists():
            brief_paths.append(brief_path)
    
    result = suite.run_ablation_experiment(
        config=config,
        brief_paths=brief_paths,
        orchestrator_factory=create_orchestrator,
    )
    print(f"  ✅ 结果已保存: {result['result_path']}")

# 对比所有结果
print("\n对比消融实验结果...")
comparison = suite.compare_ablation_results()
print("✅ 对比结果已保存至: results/ablation/ablation_comparison.json")
```

**预计输出**：
- `results/ablation/ablation_full_system.json`
- `results/ablation/ablation_no_alignment.json`
- `results/ablation/ablation_no_vision.json`
- `results/ablation/ablation_no_table.json`
- `results/ablation/ablation_no_consistency.json`
- `results/ablation/ablation_async_queue.json`
- `results/ablation/ablation_mock_model.json`
- `results/ablation/ablation_comparison.json`

**时间预估**：1-2小时（7个配置 × 12个样本）

**注意事项**：
- 消融实验时间较长，建议分批运行
- 可以优先运行关键的消融配置（no_alignment, no_vision）
- 如果网络不稳定，可以增加延迟时间

---

### 阶段三：统计分析（优先级：中，10-20分钟）

#### 3.1 基线系统对比统计

**目的**：使用统计检验验证完整系统相对于基线的提升

**执行步骤**：
```python
from pathlib import Path
import json
from src.experiments.statistics import wilcoxon_test, cliffs_delta, bootstrap_ci

# 加载指标结果
baseline_metrics = json.loads(
    Path("results/baseline_text_only_metrics.json").read_text(encoding="utf-8")
)
ours_metrics = json.loads(
    Path("results/new_prds_metrics.json").read_text(encoding="utf-8")
)

# 对比每个指标
statistical_report = {}
for metric_name in ["S_comp", "S_mm", "S_tab", "S_bi", "S_sem", "S_biz", "S_tech", "S_risk"]:
    # 提取指标值
    ours_values = [
        r["metrics"].get(metric_name, {}).get("overall", 0) 
        if isinstance(r["metrics"].get(metric_name), dict)
        else r["metrics"].get(metric_name, 0)
        for r in ours_metrics
    ]
    
    baseline_values = [
        r["metrics"].get(metric_name, {}).get("overall", 0)
        if isinstance(r["metrics"].get(metric_name), dict)
        else r["metrics"].get(metric_name, 0)
        for r in baseline_metrics
    ]
    
    if not baseline_values or not ours_values:
        continue
    
    # 统计检验
    wilcoxon = wilcoxon_test(ours_values, baseline_values)
    delta = cliffs_delta(ours_values, baseline_values)
    ci = bootstrap_ci([o - b for o, b in zip(ours_values, baseline_values)])
    
    statistical_report[metric_name] = {
        "ours_mean": sum(ours_values) / len(ours_values),
        "baseline_mean": sum(baseline_values) / len(baseline_values),
        "wilcoxon_p_value": wilcoxon.get("p_value", 0),
        "cliffs_delta": delta,
        "bootstrap_ci": ci,
        "significant": wilcoxon.get("p_value", 1) < 0.05,
    }
    
    print(f"\n{metric_name}:")
    print(f"  我们的系统: {statistical_report[metric_name]['ours_mean']:.3f}")
    print(f"  基线系统: {statistical_report[metric_name]['baseline_mean']:.3f}")
    print(f"  Wilcoxon p值: {statistical_report[metric_name]['wilcoxon_p_value']:.4f}")
    print(f"  Cliff's δ: {statistical_report[metric_name]['cliffs_delta']:.3f}")
    print(f"  显著性: {'是' if statistical_report[metric_name]['significant'] else '否'}")

# 保存统计报告
stats_path = Path("results/statistical_comparison.json")
stats_path.write_text(
    json.dumps(statistical_report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"\n✅ 统计报告已保存至: {stats_path}")
```

#### 3.2 消融实验结果统计

**目的**：分析各组件对系统性能的贡献

**执行步骤**：
```python
from pathlib import Path
import json

# 加载消融对比结果
ablation_path = Path("results/ablation/ablation_comparison.json")
ablation_comparison = json.loads(ablation_path.read_text(encoding="utf-8"))

# 生成统计摘要
print("=" * 60)
print("消融实验结果统计摘要")
print("=" * 60)

for config_name, data in ablation_comparison.items():
    print(f"\n{config_name}: {data.get('description', '')}")
    metrics_diff = data.get("metrics_diff", {})
    
    # 找出影响最大的指标
    max_impact = max(
        metrics_diff.items(),
        key=lambda x: abs(x[1].get("delta", 0)),
        default=None
    )
    
    if max_impact:
        metric, diff_data = max_impact
        print(f"  最大影响指标: {metric}")
        print(f"    基线: {diff_data.get('baseline', 0):.3f}")
        print(f"    消融: {diff_data.get('ablation', 0):.3f}")
        print(f"    差异: {diff_data.get('delta', 0):+.3f} ({diff_data.get('relative_change', 0)*100:+.1f}%)")
```

---

### 阶段四：生成完整实验报告（优先级：高，5-10分钟）

#### 4.1 生成对比报告

**执行步骤**：
```bash
# 使用一键脚本
python scripts/run_benchmark_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results \
    --generate-report
```

**或手动生成**：
```python
from pathlib import Path
import json
from src.experiments.report_generator import ExperimentReportGenerator
from src.experiments.auto_eval import evaluate_system_outputs

# 准备结果
baseline_prds = list(Path("results/baseline_text_only").glob("prd_*.json"))
ours_prds = list(Path("results/full_system").glob("prd_*.json"))

# 计算指标
baseline_results = evaluate_system_outputs("baseline", baseline_prds) if baseline_prds else []
ours_results = evaluate_system_outputs("ours", ours_prds)

# 加载消融实验结果
ablation_path = Path("results/ablation/ablation_comparison.json")
ablation_results = None
if ablation_path.exists():
    ablation_results = json.loads(ablation_path.read_text(encoding="utf-8"))

# 加载统计检验结果
stats_path = Path("results/statistical_comparison.json")
stats_results = None
if stats_path.exists():
    stats_results = json.loads(stats_path.read_text(encoding="utf-8"))

# 生成报告
report_dir = Path("reports")
generator = ExperimentReportGenerator(report_dir)

report = generator.generate_comparison_report(
    baseline_results=[{"metrics": r.metrics, "prd_path": r.prd_path} for r in baseline_results],
    ours_results=[{"metrics": r.metrics, "prd_path": r.prd_path} for r in ours_results],
    ablation_results=ablation_results,
)

# 添加统计检验结果
if stats_results:
    report["statistical_tests"] = stats_results

# 保存完整报告
full_report_path = report_dir / "full_experiment_report.json"
full_report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"✅ 完整报告已保存至:")
print(f"  - {report_dir}/experiment_report.json")
print(f"  - {report_dir}/experiment_report.md")
print(f"  - {full_report_path}")
```

---

## 实验执行顺序建议

### 方案A：完整实验（推荐用于论文）

```
步骤1：运行基线系统对比（15-30分钟）
  ↓
步骤2：重新计算质量指标（仅新生成的PRD）（5分钟）
  ↓
步骤3：运行消融实验（1-2小时）
  ├─ 先运行关键配置（no_alignment, no_vision）
  └─ 再运行其他配置
  ↓
步骤4：统计分析（10-20分钟）
  ├─ 基线对比统计
  └─ 消融结果统计
  ↓
步骤5：生成完整实验报告（5-10分钟）
```

**总时间**：约2-3小时

---

### 方案B：快速实验（验证核心功能）

```
步骤1：运行基线系统对比（仅前5个样本）（10-15分钟）
  ↓
步骤2：运行关键消融实验（no_alignment, no_vision）（20-30分钟）
  ↓
步骤3：生成简要报告（5分钟）
```

**总时间**：约35-50分钟

---

### 方案C：分阶段执行（适合时间有限的情况）

**阶段一（今天）**：
1. 运行基线系统对比（15-30分钟）
2. 重新计算质量指标（5分钟）

**阶段二（明天）**：
3. 运行消融实验（分批运行，每次1小时）
   - 第一批：full_system, no_alignment, no_vision
   - 第二批：no_table, no_consistency, async_queue

**阶段三（后天）**：
4. 统计分析（10-20分钟）
5. 生成完整报告（5-10分钟）

---

## 预期输出文件

### 目录结构
```
results/
├── full_system/              # 完整系统生成的PRD（已有）
│   ├── prd_*.json
│   └── metrics_summary.json
├── baseline_text_only/       # 基线系统生成的PRD（待生成）
│   ├── prd_*.json
│   └── baseline_metrics.json
├── ablation/                 # 消融实验结果（待生成）
│   ├── ablation_full_system.json
│   ├── ablation_no_alignment.json
│   ├── ablation_no_vision.json
│   ├── ablation_no_table.json
│   ├── ablation_no_consistency.json
│   ├── ablation_async_queue.json
│   ├── ablation_mock_model.json
│   └── ablation_comparison.json
└── statistical_comparison.json  # 统计检验结果（待生成）

reports/
├── quick_report.md           # 快速实验报告（已有）
├── experiment_report.json    # 对比实验报告（待生成）
├── experiment_report.md      # Markdown格式报告（待生成）
└── full_experiment_report.json  # 完整报告（包含统计检验）（待生成）
```

---

## 关键决策点

### 1. 是否需要补全失败的3个PRD？
- **如果不需要**：跳过步骤1.1，直接使用12个PRD进行实验
- **如果需要**：先运行步骤1.1，确保数据集完整

### 2. 消融实验的样本数？
- **完整样本**：使用15个样本（更严格，但时间更长）
- **成功样本**：使用12个成功的样本（推荐，节省时间）
- **子集样本**：使用前5个样本（快速验证）

### 3. 基线系统的选择？
- **最少配置**：仅Baseline-TXT（文本生成基线）
- **完整配置**：Baseline-TXT + Baseline-TPL + Baseline-MIX（更全面）

---

## 优先级排序

### 🔴 高优先级（必须完成）
1. **运行基线系统对比**（步骤1.2）
   - 用于论文的核心对比数据
   - 时间：15-30分钟

2. **运行关键消融实验**（步骤2.2）
   - no_alignment（验证双语对齐）
   - no_vision（验证多模态）
   - 时间：40-60分钟

3. **生成完整实验报告**（步骤4.1）
   - 论文撰写的核心数据
   - 时间：5-10分钟

### 🟡 中优先级（建议完成）
4. **统计分析**（步骤3）
   - Wilcoxon检验、Cliff's δ
   - 增强论文的严谨性
   - 时间：10-20分钟

5. **完整消融实验**（步骤2.2全部配置）
   - 更全面的组件贡献分析
   - 时间：1-2小时

### 🟢 低优先级（可选）
6. **补全失败的PRD**（步骤1.1）
   - 取决于是否需要完整数据集
   - 时间：10-15分钟

---

## 下一步行动

### 立即执行（今天）

1. **选择实验方案**：
   - 方案A（完整实验）：如果时间充足（2-3小时）
   - 方案B（快速实验）：如果时间有限（35-50分钟）
   - 方案C（分阶段）：如果时间分散

2. **执行第一步**：
   ```bash
   # 推荐：先运行基线系统对比
   python scripts/run_baseline_experiment.py \
       --benchmark-dir data/benchmark \
       --output-dir results/baseline \
       --baseline-type text_only
   ```

3. **验证结果**：
   - 检查基线PRD是否生成成功
   - 计算基线系统的指标

### 后续执行

根据选择的方案，按照顺序执行后续步骤。

---

## 注意事项

1. **网络稳定性**：
   - 消融实验时间长，建议在网络稳定时运行
   - 已优化的延迟策略（3秒→8秒→12秒）

2. **数据备份**：
   - 实验前备份 `results/` 目录
   - 消融实验结果可重复使用

3. **资源消耗**：
   - 消融实验会产生大量PRD文件
   - 确保有足够的磁盘空间

4. **时间管理**：
   - 完整实验需要2-3小时
   - 建议分批运行，避免一次性运行所有实验

---

## 参考文档

- [实验步骤详解](experiment_steps.md)
- [实验目的说明](experiment_purpose.md)
- [实验结果分析](experiment_result_analysis.md)
- [网络优化指南](network_optimization.md)

