"""
运行基准实验的完整脚本

用法：
    python scripts/run_benchmark_experiment.py --benchmark-dir data/benchmark --output-dir results
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.benchmark_builder import BenchmarkBuilder, create_sample_benchmark_prds
from src.experiments.ablation_suite import AblationSuite
from src.experiments.report_generator import ExperimentReportGenerator
from src.experiments.auto_eval import evaluate_system_outputs
from src.pipeline import MultiAgentOrchestrator


def main():
    parser = argparse.ArgumentParser(description="运行完整的基准实验流程")
    parser.add_argument("--benchmark-dir", type=Path, default=Path("data/benchmark"), help="基准数据集目录")
    parser.add_argument("--output-dir", type=Path, default=Path("results"), help="结果输出目录")
    parser.add_argument("--create-samples", action="store_true", help="创建示例基准PRD")
    parser.add_argument("--run-full-system", action="store_true", help="运行完整系统生成")
    parser.add_argument("--run-ablation", action="store_true", help="运行消融实验")
    parser.add_argument("--generate-report", action="store_true", help="生成实验报告")
    args = parser.parse_args()
    
    # 1. 创建基准数据集（如果需要）
    if args.create_samples:
        print("创建示例基准PRD...")
        samples = create_sample_benchmark_prds(args.benchmark_dir)
        print(f"✅ 创建了 {len(samples)} 个基准PRD样例")
    
    # 2. 运行完整系统生成
    if args.run_full_system:
        print("运行完整系统生成...")
        builder = BenchmarkBuilder(args.benchmark_dir)
        prds = builder.list_prds()
        
        output_dir = args.output_dir / "full_system"
        orchestrator = MultiAgentOrchestrator(persist_dir=output_dir)
        
        for prd_info in prds:
            prd_id = prd_info["prd_id"]
            print(f"  处理: {prd_id}")
            brief = builder.load_brief(prd_id)
            state = orchestrator.run({"brief": brief})
            print(f"  ✅ 完成: {prd_id}")
        
        print("✅ 完整系统生成完成")
    
    # 3. 运行消融实验
    if args.run_ablation:
        print("运行消融实验...")
        builder = BenchmarkBuilder(args.benchmark_dir)
        prds = builder.list_prds()
        brief_paths = [args.benchmark_dir / prd["brief_path"] for prd in prds if prd.get("brief_path")]
        
        ablation_dir = args.output_dir / "ablation"
        suite = AblationSuite(ablation_dir)
        configs = suite.define_ablation_configs()
        
        def create_orchestrator(config):
            return MultiAgentOrchestrator(
                persist_dir=ablation_dir / config.name,
                disabled_agents=config.disabled_agents,
                communication_mode=config.communication_mode,
            )
        
        for config in configs:
            print(f"  运行: {config.name}")
            suite.run_ablation_experiment(config, brief_paths, create_orchestrator)
            print(f"  ✅ 完成: {config.name}")
        
        # 对比结果
        comparison = suite.compare_ablation_results()
        print("✅ 消融实验完成，对比结果已保存")
    
    # 4. 生成报告
    if args.generate_report:
        print("生成实验报告...")
        report_dir = args.output_dir / "reports"
        generator = ExperimentReportGenerator(report_dir)
        
        # 加载结果（简化版，实际应加载所有PRD文件）
        full_system_dir = args.output_dir / "full_system"
        if full_system_dir.exists():
            prd_files = list(full_system_dir.glob("prd_*.json"))
            if prd_files:
                results = evaluate_system_outputs("ours", prd_files)
                report = generator.generate_comparison_report(
                    baseline_results=[],  # 需要基线结果
                    ours_results=[{"metrics": r.metrics, "prd_path": r.prd_path} for r in results],
                )
                print(f"✅ 报告已保存至: {report_dir}")
    
    print("实验流程完成！")


if __name__ == "__main__":
    main()

