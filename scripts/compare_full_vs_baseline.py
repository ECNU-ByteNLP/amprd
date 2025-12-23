"""
对比完整系统 vs 基线系统

计算完整系统（Full System）与基线系统（Baseline-TXT）的质量指标对比，使用统计检验验证显著性。

统计检验：
- Wilcoxon检验（配对样本）
- Cliff's δ（效应量）
- Bootstrap CI（置信区间）
"""

import sys
import io
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name)
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            try:
                setattr(sys, _stream_name, io.TextIOWrapper(_stream.detach(), encoding="utf-8", line_buffering=True))
            except Exception:
                pass

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics
from src.experiments.statistics import wilcoxon_test, cliffs_delta, bootstrap_ci

# 加载环境变量
load_dotenv()

def holm_bonferroni(p_values: List[float], *, alpha: float = 0.05) -> List[float]:
    """Holm-Bonferroni adjusted p-values (FWER control)."""
    m = len(p_values)
    if m == 0:
        return []
    pv = []
    for p in p_values:
        try:
            pp = float(p)
        except Exception:
            pp = 1.0
        if not math.isfinite(pp):
            pp = 1.0
        pp = min(max(pp, 0.0), 1.0)
        pv.append(pp)
    order = sorted(range(m), key=lambda i: pv[i])
    adj = [1.0] * m
    running_max = 0.0
    for rank, idx in enumerate(order):
        q = pv[idx] * (m - rank)
        if q > running_max:
            running_max = q
        adj[idx] = min(running_max, 1.0)
    return adj


def load_prd_metrics(prd_path: Path, expert_prd_path: Path = None) -> Dict:
    """
    加载PRD并计算所有质量指标
    
    Args:
        prd_path: PRD JSON文件路径
        expert_prd_path: 专家PRD路径（可选，用于S_expert计算）
    
    Returns:
        Dict: 所有质量指标字典
    """
    prd = json.loads(prd_path.read_text(encoding="utf-8"))
    
    # 基础指标
    basic_metrics = compute_all_metrics(prd)
    
    # 扩展指标
    extended_metrics = compute_all_extended_metrics(prd, expert_prd_path=expert_prd_path)
    
    # 合并所有指标
    all_metrics = {**basic_metrics, **extended_metrics}
    
    return all_metrics


def extract_single_value(metric_value) -> float:
    """
    从指标值中提取单个数值（处理嵌套结构）
    
    Args:
        metric_value: 指标值（可能是float、dict等）
    
    Returns:
        float: 单个数值
    """
    if isinstance(metric_value, (int, float)):
        return float(metric_value)
    elif isinstance(metric_value, dict):
        # 优先使用overall，否则使用第一个数值
        if "overall" in metric_value:
            return float(metric_value["overall"])
        # 如果是S_var这样的字典，尝试提取有意义的数值
        elif "std" in metric_value:
            return float(metric_value["std"])
        else:
            # 返回第一个数值类型的值
            for value in metric_value.values():
                if isinstance(value, (int, float)):
                    return float(value)
    return 0.0


def compare_systems(
    full_system_dir: Path,
    baseline_dir: Path,
    output_path: Path,
    full_system_metrics_summary: Path = None,
) -> Dict:
    """
    对比完整系统与基线系统
    
    Args:
        full_system_dir: 完整系统PRD目录
        baseline_dir: 基线系统PRD目录
        output_path: 对比结果输出路径
        full_system_metrics_summary: 完整系统指标汇总文件（可选，用于获取成功列表）
    
    Returns:
        Dict: 对比结果
    """
    # 获取完整系统成功的PRD列表
    successful_prd_ids = []
    if full_system_metrics_summary and full_system_metrics_summary.exists():
        summary_data = json.loads(full_system_metrics_summary.read_text(encoding="utf-8"))
        successful_prd_ids = [r["prd_id"] for r in summary_data.get("detailed_results", [])]
    
    # 如果成功列表为空，尝试从文件名提取
    if not successful_prd_ids:
        full_system_files = list(full_system_dir.glob("prd_*.json"))
        # 过滤掉UUID格式的文件名，只保留有意义的ID
        successful_prd_ids = [
            f.stem.replace("prd_", "") for f in full_system_files
            if "_" in f.stem and not f.stem.replace("prd_", "").startswith("0")
        ]
    
    print(f"📋 找到 {len(successful_prd_ids)} 个完整系统成功的PRD")
    
    # 收集所有PRD的指标
    full_system_metrics: Dict[str, Dict[str, float]] = {}
    baseline_metrics: Dict[str, Dict[str, float]] = {}
    
    # 所有需要对比的指标
    metric_names = [
        "S_comp", "S_mm", "S_tab", "S_bi", "S_var",
        "S_sem", "S_biz", "S_tech", "S_risk", "S_expert",
        "S_ps", "S_uj", "S_hyp"
    ]
    
    print("\n🔄 加载PRD并计算指标...")
    
    for prd_id in successful_prd_ids:
        # 完整系统PRD
        full_prd_path = full_system_dir / f"prd_{prd_id}.json"
        if not full_prd_path.exists():
            # 尝试查找UUID格式的文件
            full_prd_files = list(full_system_dir.glob(f"prd_{prd_id}*.json"))
            if not full_prd_files:
                print(f"  ⚠️  跳过 {prd_id}：未找到完整系统PRD文件")
                continue
            full_prd_path = full_prd_files[0]
        
        # 基线系统PRD
        baseline_prd_path = baseline_dir / f"prd_{prd_id}.json"
        if not baseline_prd_path.exists():
            print(f"  ⚠️  跳过 {prd_id}：未找到基线系统PRD文件")
            continue
        
        try:
            # 加载完整系统指标（如果需要专家PRD，可以从metrics_summary中获取）
            expert_prd_path = None
            if full_system_metrics_summary and full_system_metrics_summary.exists():
                summary_data = json.loads(full_system_metrics_summary.read_text(encoding="utf-8"))
                for r in summary_data.get("detailed_results", []):
                    if r["prd_id"] == prd_id and r.get("expert_prd_path"):
                        expert_prd_path = Path(r["expert_prd_path"])
                        break
            
            full_metrics = load_prd_metrics(full_prd_path, expert_prd_path=expert_prd_path)
            baseline_metrics_dict = load_prd_metrics(baseline_prd_path)
            
            # 提取每个指标的单个数值
            full_system_metrics[prd_id] = {
                metric: extract_single_value(full_metrics.get(metric, 0.0))
                for metric in metric_names
            }
            baseline_metrics[prd_id] = {
                metric: extract_single_value(baseline_metrics_dict.get(metric, 0.0))
                for metric in metric_names
            }
            
            print(f"  ✅ {prd_id}")
            
        except Exception as e:
            print(f"  ❌ {prd_id}: {e}")
            continue
    
    if not full_system_metrics or not baseline_metrics:
        print("❌ 未找到足够的PRD进行对比")
        return {}
    
    print(f"\n✅ 成功加载 {len(full_system_metrics)} 个PRD的指标")
    
    # 对每个指标进行统计检验
    print("\n📊 进行统计检验...")
    
    comparison_results = {}
    
    for metric_name in metric_names:
        # 提取完整系统和基线系统的该指标值
        full_values = [full_system_metrics[prd_id][metric_name] for prd_id in full_system_metrics.keys()]
        baseline_values = [baseline_metrics[prd_id][metric_name] for prd_id in baseline_metrics.keys()]
        
        # 确保配对（按PRD ID顺序）
        paired_full = []
        paired_baseline = []
        for prd_id in sorted(full_system_metrics.keys()):
            if prd_id in baseline_metrics:
                paired_full.append(full_system_metrics[prd_id][metric_name])
                paired_baseline.append(baseline_metrics[prd_id][metric_name])
        
        if len(paired_full) < 2:
            print(f"  ⚠️  {metric_name}: 样本数不足，跳过统计检验")
            continue
        
        # 计算均值
        full_mean = sum(paired_full) / len(paired_full)
        baseline_mean = sum(paired_baseline) / len(paired_baseline)
        
        # Wilcoxon检验（配对样本）
        try:
            wilcoxon_result = wilcoxon_test(paired_full, paired_baseline)
        except Exception as e:
            print(f"  ⚠️  {metric_name}: Wilcoxon检验失败 - {e}")
            wilcoxon_result = {"statistic": 0.0, "p_value": 1.0}

        # 关键：wilcoxon在“全零差异/完全相同”时可能返回NaN（不抛异常），这会污染JSON输出
        try:
            p = float(wilcoxon_result.get("p_value", 1.0))
        except Exception:
            p = 1.0
        if not math.isfinite(p):
            p = 1.0
        try:
            stat = float(wilcoxon_result.get("statistic", 0.0))
        except Exception:
            stat = 0.0
        if not math.isfinite(stat):
            stat = 0.0
        wilcoxon_result = {"statistic": stat, "p_value": p}
        
        # Cliff's δ（效应量）
        delta = cliffs_delta(paired_full, paired_baseline)
        
        # Bootstrap CI（差异的置信区间）
        differences = [f - b for f, b in zip(paired_full, paired_baseline)]
        ci = bootstrap_ci(differences)
        
        comparison_results[metric_name] = {
            "full_system_mean": round(full_mean, 4),
            "baseline_mean": round(baseline_mean, 4),
            "improvement": round(full_mean - baseline_mean, 4),
            "improvement_percent": round((full_mean - baseline_mean) / baseline_mean * 100, 2) if baseline_mean > 0 else 0.0,
            "wilcoxon": {
                "statistic": round(wilcoxon_result["statistic"], 4),
                "p_value": round(wilcoxon_result["p_value"], 4),
                "significant": wilcoxon_result["p_value"] < 0.05,
            },
            "cliffs_delta": round(delta, 4),
            "bootstrap_ci": [round(ci[0], 4), round(ci[1], 4)],
            "sample_size": len(paired_full),
        }
        
        # 显示结果
        significance = "***" if wilcoxon_result["p_value"] < 0.001 else ("**" if wilcoxon_result["p_value"] < 0.01 else ("*" if wilcoxon_result["p_value"] < 0.05 else ""))
        print(f"  {metric_name}: 完整系统={full_mean:.3f} vs 基线={baseline_mean:.3f} (提升{comparison_results[metric_name]['improvement_percent']:+.1f}%) {significance}")

    # 多重比较校正（Holm-Bonferroni）：覆盖所有指标
    metrics_for_corr = list(comparison_results.keys())
    pvals = [comparison_results[m]["wilcoxon"]["p_value"] for m in metrics_for_corr]
    qvals = holm_bonferroni(pvals, alpha=0.05)
    for m, q in zip(metrics_for_corr, qvals):
        comparison_results[m]["wilcoxon_corrected"] = {
            "method": "holm-bonferroni",
            "q_value": round(float(q), 4),
            "significant": float(q) < 0.05,
        }
    
    # 保存对比结果
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_data = {
        "comparison_date": "2025-11-21",
        "full_system_prd_count": len(full_system_metrics),
        "baseline_prd_count": len(baseline_metrics),
        "comparison_results": comparison_results,
        "multiple_comparison_correction": {
            "method": "holm-bonferroni",
            "alpha": 0.05,
            "num_tests": len(metrics_for_corr),
        },
        "notes": {
            "wilcoxon_significance": "p < 0.05 indicates significant difference",
            "holm_bonferroni": "wilcoxon_corrected.q_value controls family-wise error rate (FWER) across all metrics",
            "cliffs_delta_interpretation": "|delta| > 0.147 = small, > 0.33 = medium, > 0.474 = large effect",
            "bootstrap_ci": "95% confidence interval for the difference (full - baseline)",
        }
    }
    
    output_path.write_text(
        # ensure strict JSON (no NaN/Infinity)
        json.dumps(comparison_data, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ 对比结果已保存: {output_path}")
    
    return comparison_data


def main():
    print("=" * 70)
    print("完整系统 vs 基线系统对比分析")
    print("=" * 70)
    print()
    
    import argparse

    parser = argparse.ArgumentParser(description="系统A vs 系统B 对比分析（Wilcoxon + Holm校正）")
    parser.add_argument("--full-dir", type=str, default="results/full_system", help="系统A PRD目录（包含prd_*.json）")
    parser.add_argument("--baseline-dir", type=str, default="results/baseline_text_only", help="基线PRD目录（包含prd_*.json）")
    parser.add_argument("--output", type=str, default="results/comparison_full_vs_baseline.json", help="输出JSON路径")
    args = parser.parse_args()

    full_system_dir = Path(args.full_dir)
    baseline_dir = Path(args.baseline_dir)
    full_system_metrics_summary = full_system_dir / "metrics_summary.json"
    output_path = Path(args.output)
    
    if not full_system_dir.exists():
        print(f"❌ 完整系统目录不存在: {full_system_dir}")
        return
    
    if not baseline_dir.exists():
        print(f"❌ 基线系统目录不存在: {baseline_dir}")
        return
    
    print(f"完整系统目录: {full_system_dir}")
    print(f"基线系统目录: {baseline_dir}")
    print(f"输出路径: {output_path}")
    print()
    
    # 执行对比
    comparison_data = compare_systems(
        full_system_dir=full_system_dir,
        baseline_dir=baseline_dir,
        output_path=output_path,
        full_system_metrics_summary=full_system_metrics_summary,
    )
    
    if comparison_data:
        print("\n" + "=" * 70)
        print("对比分析完成！")
        print("=" * 70)
        print(f"\n📊 统计显著性说明:")
        print(f"  - *: p < 0.05 (显著)")
        print(f"  - **: p < 0.01 (非常显著)")
        print(f"  - ***: p < 0.001 (极其显著)")
        print(f"\n📈 效应量说明 (Cliff's δ):")
        print(f"  - |δ| > 0.147: 小效应")
        print(f"  - |δ| > 0.33: 中效应")
        print(f"  - |δ| > 0.474: 大效应")
        print()


if __name__ == "__main__":
    main()

