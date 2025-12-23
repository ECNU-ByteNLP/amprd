# 实验步骤指南（Step-by-Step）

本文档提供完整的实验流程，从环境准备到结果分析，确保实验可复现且符合顶刊标准。

## 前置准备

### 1. 环境检查

```bash
# 检查Python版本（需要3.8+）
python --version

# 检查依赖是否安装
pip install -r requirements.txt

# 检查环境变量（可选，用于真实模型）
# 如果使用Mock模型，可跳过此步
cat .env  # 或检查环境变量
```

### 2. 目录结构准备

```bash
# 创建必要的目录
mkdir -p data/benchmark
mkdir -p results/full_system
mkdir -p results/baseline
mkdir -p experiments/ablation
mkdir -p reports
```

## 实验步骤

### 步骤1：创建基准数据集（5分钟）

**目标**：构建标准化的测试数据集，用于可复现实验。

```bash
# 方式1：使用脚本自动创建示例数据集
python -c "
from pathlib import Path
from src.data.benchmark_builder import create_sample_benchmark_prds

benchmark_dir = Path('data/benchmark')
samples = create_sample_benchmark_prds(benchmark_dir)
print(f'✅ 创建了 {len(samples)} 个基准PRD样例')
for s in samples:
    print(f'  - {s.prd_id}: {s.title} ({s.domain})')
"
```

**验证**：
```bash
# 检查创建的文件
ls -la data/benchmark/
# 应该看到：
# - benchmark_index.json
# - general_google_search_algorithm_update_brief.json
# - ecommerce_amazon_prime_video_personalization_brief.json
# - financial_smart_financial_advisor_brief.json
```

**或手动添加自己的Brief**：
```python
from pathlib import Path
from src.data.benchmark_builder import BenchmarkBuilder

builder = BenchmarkBuilder(Path("data/benchmark"))
builder.add_prd_sample(
    title="Your PRD Title",
    domain="financial",  # 或 ecommerce/medical/general
    source="Your Source",
    brief={
        "title": "产品名称",
        "domain": "financial",
        "goal": "核心目标描述",
        "target_users": [
            {"persona": "用户画像", "needs": "具体需求"}
        ],
        "key_constraints": [
            {"type": "performance", "description": "约束描述", "priority": "P0"}
        ],
        "business_metrics": [
            {"name": "KPI名称", "target": "目标值", "timeframe": "时间范围"}
        ],
    }
)
```

---

### 步骤2：运行完整系统生成（10-30分钟，取决于模型）

**目标**：使用完整多智能体系统生成PRD。

```bash
# 方式1：使用一键脚本（推荐）
python scripts/run_benchmark_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results \
    --run-full-system \
    --verbose
```

**或方式2：手动运行**：

```python
from pathlib import Path
import json
from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder

# 加载基准数据集
builder = BenchmarkBuilder(Path("data/benchmark"))
prds = builder.list_prds()

# 创建orchestrator
orchestrator = MultiAgentOrchestrator(
    persist_dir=Path("results/full_system")
)

# 为每个Brief生成PRD
for prd_info in prds:
    prd_id = prd_info["prd_id"]
    print(f"处理: {prd_id}")
    
    # 加载Brief
    brief = builder.load_brief(prd_id)
    
    # 运行生成
    state = orchestrator.run({"brief": brief})
    
    # 检查结果
    prd_path = state.get("quality", {}).get("artifact_path")
    if prd_path:
        print(f"  ✅ PRD已生成: {prd_path}")
    else:
        print(f"  ⚠️  未找到PRD文件")
```

**验证**：
```bash
# 检查生成的文件
ls -la results/full_system/
# 应该看到：
# - prd_*.json（生成的PRD文件）
# - blackboard.json（黑板状态）
# - state_summary.json（状态快照）
```

---

### 步骤3：运行基线系统对比（可选，10-30分钟）

**目标**：生成基线系统的PRD，用于对比。

```python
from pathlib import Path
from src.baselines.text_only import TextOnlyBaseline
from src.data.benchmark_builder import BenchmarkBuilder

builder = BenchmarkBuilder(Path("data/benchmark"))
prds = builder.list_prds()

baseline = TextOnlyBaseline()
output_dir = Path("results/baseline")

for prd_info in prds:
    brief = builder.load_brief(prd_info["prd_id"])
    
    # 运行基线生成
    prd_json = baseline.generate(brief)
    
    # 保存结果
    prd_path = output_dir / f"prd_{prd_info['prd_id']}.json"
    prd_path.write_text(
        json.dumps(prd_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 基线PRD已生成: {prd_path}")
```

---

### 步骤4：计算质量指标（2分钟）

**目标**：计算所有PRD的质量指标。

```python
from pathlib import Path
import json
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics

# 计算完整系统的指标
full_system_dir = Path("results/full_system")
prd_files = list(full_system_dir.glob("prd_*.json"))

results = []
for prd_path in prd_files:
    prd = json.loads(prd_path.read_text(encoding="utf-8"))
    
    # 基础指标
    basic_metrics = compute_all_metrics(prd)
    
    # 扩展指标
    extended_metrics = compute_all_extended_metrics(prd)
    
    # 合并
    all_metrics = {**basic_metrics, **extended_metrics}
    
    results.append({
        "prd_id": prd_path.stem,
        "metrics": all_metrics,
    })
    
    print(f"{prd_path.name}:")
    print(f"  S_comp: {all_metrics.get('S_comp', 0):.3f}")
    print(f"  S_sem: {all_metrics.get('S_sem', {}).get('overall', 0):.3f}")
    print(f"  S_biz: {all_metrics.get('S_biz', 0):.3f}")

# 保存结果
results_path = Path("results/full_system_metrics.json")
results_path.write_text(
    json.dumps(results, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"\n✅ 指标已保存至: {results_path}")
```

---

### 步骤5：运行消融实验（30-60分钟）

**目标**：验证各组件（Agent、通信模式等）的必要性。

```bash
# 使用一键脚本
python scripts/run_benchmark_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results \
    --run-ablation \
    --verbose
```

**或手动运行**：

```python
from pathlib import Path
from src.experiments.ablation_suite import AblationSuite
from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder

# 准备Brief文件
builder = BenchmarkBuilder(Path("data/benchmark"))
prds = builder.list_prds()
brief_paths = [Path(builder.benchmark_dir / prd["brief_path"]) 
               for prd in prds if prd.get("brief_path")]

# 创建消融实验套件
ablation_dir = Path("experiments/ablation")
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
    result = suite.run_ablation_experiment(
        config=config,
        brief_paths=brief_paths,
        orchestrator_factory=create_orchestrator,
    )
    print(f"  ✅ 结果已保存: {result['result_path']}")

# 对比所有结果
print("\n对比消融实验结果...")
comparison = suite.compare_ablation_results()
print("✅ 对比结果已保存至: experiments/ablation/ablation_comparison.json")
```

**验证**：
```bash
# 检查消融实验结果
ls -la experiments/ablation/
# 应该看到：
# - ablation_full_system.json
# - ablation_no_alignment.json
# - ablation_no_vision.json
# - ablation_no_table.json
# - ablation_no_consistency.json
# - ablation_async_queue.json
# - ablation_mock_model.json
# - ablation_comparison.json
```

---

### 步骤6：生成实验报告（1分钟）

**目标**：生成符合论文要求的实验报告。

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
baseline_prds = list(Path("results/baseline").glob("prd_*.json"))
ours_prds = list(Path("results/full_system").glob("prd_*.json"))

# 计算指标
baseline_results = evaluate_system_outputs("baseline", baseline_prds) if baseline_prds else []
ours_results = evaluate_system_outputs("ours", ours_prds)

# 加载消融实验结果（可选）
ablation_path = Path("experiments/ablation/ablation_comparison.json")
ablation_results = None
if ablation_path.exists():
    ablation_results = json.loads(ablation_path.read_text(encoding="utf-8"))

# 生成报告
report_dir = Path("reports")
generator = ExperimentReportGenerator(report_dir)

report = generator.generate_comparison_report(
    baseline_results=[{"metrics": r.metrics, "prd_path": r.prd_path} for r in baseline_results],
    ours_results=[{"metrics": r.metrics, "prd_path": r.prd_path} for r in ours_results],
    ablation_results=ablation_results,
)

print(f"✅ 报告已保存至:")
print(f"  - {report_dir}/experiment_report.json")
print(f"  - {report_dir}/experiment_report.md")
```

**查看报告**：
```bash
# 查看Markdown报告
cat reports/experiment_report.md
```

---

### 步骤7：统计分析（可选，5分钟）

**目标**：进行统计检验，验证结果显著性。

```python
from pathlib import Path
import json
from src.experiments.statistics import wilcoxon_test, cliffs_delta, bootstrap_ci

# 加载指标结果
full_system_metrics = json.loads(
    Path("results/full_system_metrics.json").read_text(encoding="utf-8")
)

# 如果有基线结果
baseline_metrics = json.loads(
    Path("results/baseline_metrics.json").read_text(encoding="utf-8")
)

# 对比每个指标
for metric_name in ["S_comp", "S_sem", "S_biz", "S_tech", "S_risk"]:
    # 提取指标值
    ours_values = [
        r["metrics"].get(metric_name, {}).get("overall", 0) 
        if isinstance(r["metrics"].get(metric_name), dict)
        else r["metrics"].get(metric_name, 0)
        for r in full_system_metrics
    ]
    
    baseline_values = [
        r["metrics"].get(metric_name, {}).get("overall", 0)
        if isinstance(r["metrics"].get(metric_name), dict)
        else r["metrics"].get(metric_name, 0)
        for r in baseline_metrics
    ] if baseline_metrics else []
    
    if baseline_values:
        # 统计检验
        wilcoxon = wilcoxon_test(ours_values, baseline_values)
        delta = cliffs_delta(ours_values, baseline_values)
        ci = bootstrap_ci([o - b for o, b in zip(ours_values, baseline_values)])
        
        print(f"\n{metric_name}:")
        print(f"  我们的系统: {sum(ours_values)/len(ours_values):.3f}")
        print(f"  基线系统: {sum(baseline_values)/len(baseline_values):.3f}")
        print(f"  Wilcoxon p值: {wilcoxon.get('p_value', 0):.4f}")
        print(f"  Cliff's δ: {delta:.3f}")
        print(f"  Bootstrap CI: [{ci[0]:.3f}, {ci[1]:.3f}]")
```

---

## 完整实验流程（一键运行）

如果你想一次性运行所有步骤：

```bash
# 创建完整的实验流程脚本
python scripts/run_benchmark_experiment.py \
    --benchmark-dir data/benchmark \
    --output-dir results \
    --create-samples \
    --run-full-system \
    --run-ablation \
    --generate-report \
    --verbose
```

**预计时间**：
- 创建数据集：1分钟
- 完整系统生成：10-30分钟（取决于模型和样本数）
- 消融实验：30-60分钟（7个配置 × 样本数）
- 生成报告：1分钟

**总计**：约1-2小时（使用Mock模型）或2-4小时（使用真实模型）

---

## 结果检查清单

实验完成后，检查以下文件：

- [ ] `data/benchmark/benchmark_index.json` - 基准数据集索引
- [ ] `results/full_system/prd_*.json` - 完整系统生成的PRD
- [ ] `results/full_system/blackboard.json` - 黑板状态（可追溯）
- [ ] `experiments/ablation/ablation_*.json` - 各消融实验结果
- [ ] `experiments/ablation/ablation_comparison.json` - 消融实验对比
- [ ] `reports/experiment_report.json` - JSON格式报告
- [ ] `reports/experiment_report.md` - Markdown格式报告（适合论文）

---

## 常见问题

### Q1: 如果模型API不可用怎么办？

**A**: 系统会自动使用Mock模型，可以正常生成PRD（质量较低，但可用于测试流程）。

### Q2: 如何添加自己的Brief？

**A**: 使用 `BenchmarkBuilder.add_prd_sample()` 方法，或直接编辑 `data/benchmark/` 下的JSON文件。

### Q3: 消融实验太慢怎么办？

**A**: 可以减少样本数量，或只运行关键的消融配置（如 `no_alignment`, `no_vision`）。

### Q4: 如何查看某个PRD的详细指标？

**A**: 
```python
from src.metrics.extended_quality import compute_all_extended_metrics
import json

prd = json.loads(Path("results/full_system/prd_xxx.json").read_text(encoding="utf-8"))
metrics = compute_all_extended_metrics(prd)
print(json.dumps(metrics, ensure_ascii=False, indent=2))
```

---

## 下一步

实验完成后，你可以：

1. **分析结果**：查看 `reports/experiment_report.md`
2. **撰写论文**：使用报告中的表格和统计结果
3. **扩展实验**：添加更多Brief、调整配置、尝试不同模型

---

**参考文档**：
- [实验实施指南](experiment_guide.md) - 详细API说明
- [顶刊实验标准优化方案](top_tier_optimization.md) - 优化背景
- [优化总结](optimization_summary.md) - 已完成功能总结

