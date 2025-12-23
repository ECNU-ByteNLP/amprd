# 顶刊实验标准实施指南

本文档说明如何使用优化后的实验框架，进行符合顶刊标准的实验。

## 一、扩展评测指标使用

### 1.1 基础指标（已有）

```python
from src.metrics.quality import compute_all_metrics

prd = json.loads(prd_path.read_text(encoding="utf-8"))
basic_metrics = compute_all_metrics(prd)
# 返回: {"S_comp": 0.85, "S_mm": 0.72, "S_tab": 0.80, "S_bi": 0.91, "S_var": {...}}
```

### 1.2 扩展指标（新增）

```python
from src.metrics.extended_quality import compute_all_extended_metrics

# 基础使用
extended_metrics = compute_all_extended_metrics(prd)
# 返回: {
#   "S_sem": {"overall": 0.82, "problem_clarity": 0.85, ...},
#   "S_biz": 0.78,
#   "S_tech": 0.75,
#   "S_risk": 1.0,
#   "S_expert": {"overall": 0.88, "structure_similarity": 0.90, ...}
# }

# 与专家PRD对比（可选）
expert_prd_path = Path("benchmark/google_search_prd.json")
expert_metrics = compute_all_extended_metrics(prd, expert_prd_path=expert_prd_path)
```

**新增指标说明**：

- **S_sem（语义质量）**：
  - `problem_clarity`: 问题陈述清晰度（基于关键词检测）
  - `requirement_executability`: 需求可执行性（是否包含验收标准）
  - `terminology_consistency`: 术语一致性（领域术语使用准确性）

- **S_biz（业务对齐度）**：
  - Goal与KPI的一致性
  - 用户需求覆盖度

- **S_tech（技术可行性）**：
  - 技术要求的合理性（架构、性能指标）
  - 约束完整性

- **S_risk（风险识别）**：
  - 风险识别完整性
  - 缓解策略有效性

- **S_expert（专家对齐度）**：
  - 结构相似度（与标准PRD结构对比）
  - 内容相似度（基于语义相似度，需要sentence-transformers）

## 二、基准数据集构建

### 2.1 创建基准数据集

```python
from pathlib import Path
from src.data.benchmark_builder import BenchmarkBuilder, create_sample_benchmark_prds

# 创建基准数据集目录
benchmark_dir = Path("data/benchmark")
benchmark_dir.mkdir(parents=True, exist_ok=True)

# 创建示例基准PRD（基于顶级公司PRD样例）
samples = create_sample_benchmark_prds(benchmark_dir)
print(f"创建了 {len(samples)} 个基准PRD样例")

# 或手动添加
builder = BenchmarkBuilder(benchmark_dir)
builder.add_prd_sample(
    title="Your PRD Title",
    domain="financial",
    source="Your Company",
    brief={
        "title": "...",
        "domain": "financial",
        "goal": "...",
        # ... 其他字段
    },
    prd_json=prd_data,  # 可选
    annotations={  # 可选
        "quality_scores": {"usability": 6, "clarity": 7, "completeness": 6},
        "annotator": "expert_pm_1",
    }
)
```

### 2.2 使用基准数据集

```python
# 列出所有PRD样例
prds = builder.list_prds(domain="financial")  # 可按领域过滤

# 加载Brief用于实验
brief = builder.load_brief("financial_smart_financial_advisor")

# 加载PRD用于对比
expert_prd = builder.load_prd("financial_smart_financial_advisor")
```

## 三、系统化消融实验

### 3.1 定义消融实验配置

```python
from pathlib import Path
from src.experiments.ablation_suite import AblationSuite, AblationConfig
from src.pipeline import MultiAgentOrchestrator

# 创建消融实验套件
ablation_dir = Path("experiments/ablation")
suite = AblationSuite(ablation_dir)

# 获取预定义的消融配置
configs = suite.define_ablation_configs()
# 包括：
# - full_system: 完整系统（基线）
# - no_alignment: 无AlignmentAgent
# - no_vision: 无VisionAgent
# - no_table: 无TableAgent
# - no_consistency: 无ConsistencyAgent
# - async_queue: 异步队列通信模式
# - mock_model: 使用Mock模型
```

### 3.2 运行消融实验

```python
# 准备Brief文件列表
brief_paths = [Path("data/benchmark") / f"{prd_id}_brief.json" for prd_id in prd_ids]

# 定义orchestrator工厂函数
def create_orchestrator(config: AblationConfig):
    disabled = config.disabled_agents
    comm_mode = config.communication_mode
    
    # 根据model_variant选择模型
    if config.model_variant == "mock":
        from src.models.model_client import MockModelClient
        text_cn = MockModelClient()
        text_en = MockModelClient()
        vision = MockModelClient()
    else:
        # 使用真实模型（从环境变量读取）
        text_cn = text_en = vision = None
    
    return MultiAgentOrchestrator(
        persist_dir=Path(f"experiments/ablation/{config.name}"),
        disabled_agents=disabled,
        communication_mode=comm_mode,
        text_model_cn=text_cn,
        text_model_en=text_en,
        vision_model=vision,
    )

# 运行所有消融实验
for config in configs:
    print(f"运行消融实验: {config.name}")
    result = suite.run_ablation_experiment(
        config=config,
        brief_paths=brief_paths,
        orchestrator_factory=create_orchestrator,
    )
    print(f"结果保存至: {result['result_path']}")

# 对比所有消融实验结果
comparison = suite.compare_ablation_results()
print("消融实验对比结果:", comparison)
```

## 四、实验报告生成

### 4.1 生成对比实验报告

```python
from src.experiments.report_generator import ExperimentReportGenerator
from src.experiments.auto_eval import evaluate_system_outputs

# 准备结果
baseline_prds = list(Path("results/baseline").glob("prd_*.json"))
ours_prds = list(Path("results/ours").glob("prd_*.json"))

baseline_results = evaluate_system_outputs("baseline", baseline_prds)
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

print(f"报告已保存至: {report_dir}/experiment_report.json")
print(f"Markdown报告: {report_dir}/experiment_report.md")
```

## 五、完整实验流程示例

### 5.1 端到端实验流程

```python
from pathlib import Path
import json

# 1. 构建基准数据集
from src.data.benchmark_builder import create_sample_benchmark_prds
benchmark_dir = Path("data/benchmark")
samples = create_sample_benchmark_prds(benchmark_dir)

# 2. 运行完整系统生成
from src.pipeline import MultiAgentOrchestrator
orchestrator = MultiAgentOrchestrator(persist_dir=Path("results/ours"))

for sample in samples:
    brief = json.loads(sample.brief_path.read_text(encoding="utf-8"))
    state = orchestrator.run({"brief": brief})

# 3. 运行消融实验
from src.experiments.ablation_suite import AblationSuite
suite = AblationSuite(Path("experiments/ablation"))
configs = suite.define_ablation_configs()

brief_paths = [s.brief_path for s in samples]
for config in configs:
    suite.run_ablation_experiment(config, brief_paths, create_orchestrator)

# 4. 计算指标
from src.metrics.extended_quality import compute_all_extended_metrics
ours_prds = list(Path("results/ours").glob("prd_*.json"))
for prd_path in ours_prds:
    prd = json.loads(prd_path.read_text(encoding="utf-8"))
    metrics = compute_all_extended_metrics(prd)
    print(f"{prd_path.name}: {metrics}")

# 5. 生成报告
from src.experiments.report_generator import ExperimentReportGenerator
generator = ExperimentReportGenerator(Path("reports"))
report = generator.generate_comparison_report(...)
```

## 六、论文撰写建议

### 6.1 实验设置部分

- **数据集**：说明基准数据集的来源（参考顶级公司PRD样例）、领域分布、样本数量
- **基线系统**：列出对比的基线系统（如text-only、template-based等）
- **评估指标**：说明10+个自动指标和人工评测维度

### 6.2 结果分析部分

- **主实验**：展示完整系统 vs 基线的对比结果（表格+统计检验）
- **消融实验**：展示各组件（Agent、通信模式、Prompt）的贡献度
- **专家对比**：展示与人类专家PRD的对比结果（S_expert指标）

### 6.3 统计检验

- 使用Wilcoxon符号秩检验（非参数，适合小样本）
- 报告Cliff's δ效应量（解释实际差异大小）
- 提供Bootstrap置信区间（展示不确定性）

---

**参考资源**：
- [PRD Examples from Top Tech Companies](https://pmprompt.com/blog/prd-examples)
- 扩展指标实现：`src/metrics/extended_quality.py`
- 基准数据集工具：`src/data/benchmark_builder.py`
- 消融实验框架：`src/experiments/ablation_suite.py`
- 报告生成器：`src/experiments/report_generator.py`

