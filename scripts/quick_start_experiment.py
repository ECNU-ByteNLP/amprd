"""
快速开始实验脚本

一键运行完整的实验流程，适合首次使用。
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from src.data.benchmark_builder import create_sample_benchmark_prds
from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics
import json
from pathlib import Path
from typing import Optional

# 加载环境变量（包括Qwen API密钥）
load_dotenv()


def find_expert_prd(prd_id: str) -> Optional[Path]:
    """
    根据PRD ID查找对应的专家PRD（真实PRD参考）
    
    优先级：
    1. 中文PRD映射（data/chinese_prds/processed/brief_to_expert_mapping.json）- 优先使用
    2. 英文PRD映射（data/expert_prds/mapping.json）- 备选
    
    参考来源：
    - 中文PRD：300份真实中文PRD案例（倒推案例、大厂案例）
    - 英文PRD：https://pmprompt.com/blog/prd-examples (12个真实PRD示例)
    """
    # 优先使用中文PRD映射
    chinese_mapping_path = Path("data/chinese_prds/processed/brief_to_expert_mapping.json")
    if chinese_mapping_path.exists():
        try:
            mapping_data = json.loads(chinese_mapping_path.read_text(encoding="utf-8"))
            mappings = mapping_data.get("mappings", {})
            expert_info = mappings.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                expert_path = Path(expert_info["expert_prd_path"])
                if expert_path.exists():
                    return expert_path
                # 如果JSON不存在，尝试使用PDF路径（用于后续转换）
                pdf_path = Path(expert_info.get("source_pdf_path", ""))
                if pdf_path.exists():
                    # 返回PDF路径（虽然不能直接用于计算，但可以标记为需要转换）
                    return pdf_path
        except Exception as e:
            print(f"  ⚠️  读取中文PRD映射文件失败: {e}")
    
    # 备选：英文PRD映射
    english_mapping_path = Path("data/expert_prds/mapping.json")
    if english_mapping_path.exists():
        try:
            mapping = json.loads(english_mapping_path.read_text(encoding="utf-8"))
            expert_info = mapping.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                expert_path = Path(expert_info["expert_prd_path"])
                if expert_path.exists():
                    return expert_path
        except Exception as e:
            print(f"  ⚠️  读取英文PRD映射文件失败: {e}")
    
    # 如果没有映射文件，尝试默认路径
    expert_dir = Path("data/expert_prds")
    if expert_dir.exists():
        expert_path = expert_dir / f"{prd_id}.json"
        if expert_path.exists():
            return expert_path
    
    return None


def main():
    print("=" * 60)
    print("多模态双语PRD生成系统 - 快速实验")
    print("=" * 60)
    print()
    
    # 步骤1：创建基准数据集
    print("步骤1/4: 创建基准数据集...")
    benchmark_dir = Path("data/benchmark")
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        samples = create_sample_benchmark_prds(benchmark_dir)
        print(f"  ✅ 创建了 {len(samples)} 个基准PRD样例（覆盖14种PRD模板风格）")
        for s in samples:
            template_info = f" [{s.template_style}]" if s.template_style else ""
            print(f"     - {s.title} ({s.domain}){template_info}")
    except Exception as e:
        print(f"  ⚠️  创建数据集时出错: {e}")
        import traceback
        traceback.print_exc()
        print("  继续使用现有数据集...")
    
    print()
    
    # 步骤2：运行完整系统生成
    print("步骤2/4: 运行完整系统生成...")
    builder = BenchmarkBuilder(benchmark_dir)
    prds = builder.list_prds()
    
    if not prds:
        print("  ❌ 未找到基准PRD，请先运行步骤1")
        return
    
    print(f"  找到 {len(prds)} 个Brief，开始生成...")
    
    output_dir = Path("results/full_system")
    orchestrator = MultiAgentOrchestrator(persist_dir=output_dir)
    
    generated_count = 0
    failed_count = 0
    import time
    
    for idx, prd_info in enumerate(prds, 1):
        prd_id = prd_info["prd_id"]
        print(f"  处理 [{idx}/{len(prds)}]: {prd_id}...", end=" ", flush=True)
        
        # 在批量处理时添加延迟，避免API限流
        # 根据处理进度动态调整延迟：前面可以快一点，后面慢一点
        if idx > 1:
            if idx <= 5:
                delay = 3.0  # 前5个：3秒延迟
            elif idx <= 10:
                delay = 8.0  # 6-10个：8秒延迟（避免限流）
            else:
                delay = 12.0  # 11个以后：12秒延迟（更保守，避免连续失败）
            print(f"    [等待 {delay:.1f}秒以避免API限流...]", flush=True)
            time.sleep(delay)
        
        try:
            brief = builder.load_brief(prd_id)
            state = orchestrator.run({"brief": brief})
            
            prd_path = state.get("quality", {}).get("artifact_path")
            if prd_path and Path(prd_path).exists():
                print("✅")
                generated_count += 1
            else:
                print("⚠️  (未找到PRD文件)")
                failed_count += 1
        except Exception as e:
            print(f"❌ 错误: {str(e)[:100]}")  # 只显示前100个字符
            failed_count += 1
            # 继续处理下一个，不中断整个流程
            continue
    
    print(f"  ✅ 成功生成 {generated_count}/{len(prds)} 个PRD")
    if failed_count > 0:
        print(f"  ⚠️  失败 {failed_count} 个PRD（可能是网络超时，请检查网络连接或稍后重试）")
    print()
    
    # 步骤3：计算质量指标
    print("步骤3/4: 计算质量指标...")
    prd_files = list(output_dir.glob("prd_*.json"))
    
    if not prd_files:
        print("  ⚠️  未找到生成的PRD文件")
        return
    
    results = []
    for prd_path in prd_files:
        try:
            prd = json.loads(prd_path.read_text(encoding="utf-8"))
            
            # 查找对应的专家PRD（如果存在）
            prd_id = prd.get("metadata", {}).get("prd_id", prd_path.stem.replace("prd_", ""))
            expert_prd_path = find_expert_prd(prd_id)
            
            # 基础指标
            basic_metrics = compute_all_metrics(prd)
            
            # 扩展指标（提供expert_prd_path用于S_expert计算）
            extended_metrics = compute_all_extended_metrics(prd, expert_prd_path=expert_prd_path)
            
            # 合并
            all_metrics = {**basic_metrics, **extended_metrics}
            
            results.append({
                "prd_id": prd_path.stem,
                "metrics": all_metrics,
            })
        except Exception as e:
            print(f"  ⚠️  计算 {prd_path.name} 指标时出错: {e}")
    
    # 保存结果
    results_path = output_dir / "metrics_summary.json"
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # 显示平均指标
    if results:
        print("  平均指标:")
        metric_names = ["S_comp", "S_mm", "S_tab", "S_bi", "S_sem", "S_biz", "S_tech", "S_risk"]
        for metric_name in metric_names:
            values = []
            for r in results:
                metric_value = r["metrics"].get(metric_name)
                if isinstance(metric_value, dict):
                    metric_value = metric_value.get("overall", 0)
                if isinstance(metric_value, (int, float)):
                    values.append(metric_value)
            
            if values:
                avg = sum(values) / len(values)
                print(f"    {metric_name}: {avg:.3f}")
    
    print(f"  ✅ 指标已保存至: {results_path}")
    print()
    
    # 步骤4：生成简要报告
    print("步骤4/4: 生成简要报告...")
    report_lines = [
        "# 实验简要报告",
        "",
        f"## 实验设置",
        f"- 基准数据集: {len(prds)} 个Brief",
        f"- 成功生成: {generated_count} 个PRD",
        "",
        "## 平均指标",
        "",
        "| 指标 | 平均值 |",
        "|------|--------|",
    ]
    
    for metric_name in metric_names:
        values = []
        for r in results:
            metric_value = r["metrics"].get(metric_name)
            if isinstance(metric_value, dict):
                metric_value = metric_value.get("overall", 0)
            if isinstance(metric_value, (int, float)):
                values.append(metric_value)
        
        if values:
            avg = sum(values) / len(values)
            report_lines.append(f"| {metric_name} | {avg:.3f} |")
    
    report_path = Path("reports/quick_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    
    print(f"  ✅ 报告已保存至: {report_path}")
    print()
    
    print("=" * 60)
    print("实验完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("  1. 查看报告: cat reports/quick_report.md")
    print("  2. 查看详细指标: cat results/full_system/metrics_summary.json")
    print("  3. 运行消融实验: python scripts/run_benchmark_experiment.py --run-ablation")
    print("  4. 查看完整实验步骤: docs/experiment_steps.md")


if __name__ == "__main__":
    main()

