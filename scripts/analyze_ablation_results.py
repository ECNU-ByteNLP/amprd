"""
分析消融实验结果

对比所有消融配置与完整系统，进行统计分析。

统计检验：
- Wilcoxon检验（配对样本）
- Cliff's δ（效应量）
- Bootstrap CI（置信区间）

输出：
- results/ablation/ablation_analysis.json: 详细分析结果
- results/ablation/ablation_comparison_table.json: 对比表格
"""

import sys
import io
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
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

from src.experiments.statistics import wilcoxon_test, cliffs_delta, bootstrap_ci

# 加载环境变量
load_dotenv()


def holm_bonferroni(p_values: List[float], *, alpha: float = 0.05) -> List[float]:
    """
    Holm-Bonferroni adjusted p-values (FWER control).
    Returns q-values aligned with original order.
    """
    m = len(p_values)
    if m == 0:
        return []

    # clamp to [0,1] and handle non-finite
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
    # step-down: q_i = max_{j<=i} ( (m-j)*p_(j) )
    running_max = 0.0
    for rank, idx in enumerate(order):
        factor = m - rank
        q = pv[idx] * factor
        if q > running_max:
            running_max = q
        adj[idx] = min(running_max, 1.0)
    return adj


def get_benchmark_brief_ids() -> set:
    """获取所有benchmark brief的ID列表"""
    benchmark_dir = Path("data/benchmark")
    brief_files = list(benchmark_dir.glob("*_brief.json"))
    brief_ids = set()
    for brief_file in brief_files:
        # 从brief文件名提取ID：xxx_brief.json -> xxx
        brief_id = brief_file.stem.replace("_brief", "")
        brief_ids.add(brief_id)
    return brief_ids


def prd_id_from_filename(prd_file: Path) -> str:
    """
    从文件名提取PRD ID：只移除前缀 prd_
    注意：不能用 str.replace("prd_", "")，否则会误删ID内部的 "prd_" 子串，
    例如 prd_general_ai_powered_prd_assistant.json 会被错误提取为 general_ai_powered_assistant。
    """
    stem = prd_file.stem
    return stem[4:] if stem.startswith("prd_") else stem


def find_expert_prd(prd_id: str) -> Path | None:
    """根据PRD ID查找对应的专家PRD（用于S_expert等扩展指标）"""
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
        except Exception:
            pass

    english_mapping_path = Path("data/expert_prds/mapping.json")
    if english_mapping_path.exists():
        try:
            mapping = json.loads(english_mapping_path.read_text(encoding="utf-8"))
            expert_info = mapping.get(prd_id)
            if expert_info and expert_info.get("expert_prd_path"):
                expert_path = Path(expert_info["expert_prd_path"])
                if expert_path.exists():
                    return expert_path
        except Exception:
            pass

    return None


def extract_single_value(metric_value) -> float:
    """从指标值中提取单个数值（处理嵌套结构）"""
    if isinstance(metric_value, (int, float)):
        return float(metric_value)
    elif isinstance(metric_value, dict):
        if "overall" in metric_value:
            return float(metric_value["overall"])
        elif "std" in metric_value:
            return float(metric_value["std"])
        else:
            for value in metric_value.values():
                if isinstance(value, (int, float)):
                    return float(value)
    return 0.0


def load_ablation_results(ablation_dir: Path) -> Dict:
    """加载消融实验结果"""
    summary_path = ablation_dir / "ablation_summary.json"
    
    if summary_path.exists():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        return data
    
    # 如果汇总文件不存在，从PRD文件直接加载
    print(f"⚠️  未找到消融实验汇总文件: {summary_path}")
    print("   正在从PRD文件直接加载...")
    
    try:
        from src.metrics.quality import compute_all_metrics, load_prd
        from src.metrics.extended_quality import compute_all_extended_metrics
    except ImportError:
        print("❌ 无法导入质量指标计算模块")
        return {}
    
    results = []
    benchmark_ids = get_benchmark_brief_ids()
    config_dirs = [d for d in ablation_dir.iterdir() if d.is_dir() and d.name != "ablation_summary"]
    
    print(f"   识别到 {len(benchmark_ids)} 个benchmark brief")
    
    for config_dir in config_dirs:
        config_name = config_dir.name
        prd_files = list(config_dir.glob("prd_*.json"))
        
        # 按benchmark id固定顺序读取，确保配对检验有效；并避免replace误删"prd_"子串
        file_map = {prd_id_from_filename(f): f for f in prd_files}
        benchmark_prds = [(file_map[bid], bid) for bid in sorted(benchmark_ids) if bid in file_map]
        
        print(f"   配置 {config_name}: {len(prd_files)} 个PRD文件, {len(benchmark_prds)} 个benchmark PRD")
        
        for prd_file, prd_id in benchmark_prds:
            try:
                prd_data = load_prd(prd_file)
                basic = compute_all_metrics(prd_data)
                expert_prd_path = find_expert_prd(prd_id)
                extended = compute_all_extended_metrics(prd_data, expert_prd_path=expert_prd_path)
                metrics = {**basic, **extended}
                
                results.append({
                    "config_name": config_name,
                    "prd_id": prd_id,
                    "prd_path": str(prd_file),
                    "metrics": metrics,
                })
            except Exception as e:
                print(f"  ⚠️  处理 {prd_file} 失败: {e}")
    
    return {"results": results}


def load_full_system_results(full_system_dir: Path) -> Dict:
    """加载完整系统结果"""
    summary_path = full_system_dir / "metrics_summary.json"
    
    if summary_path.exists():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        # 如果data有detailed_results，直接返回；否则转换为统一格式
        if "detailed_results" in data:
            benchmark_ids = get_benchmark_brief_ids()
            by_id: Dict[str, Dict] = {}
            for r in data.get("detailed_results", []):
                rid = r.get("prd_id")
                if rid and rid in benchmark_ids:
                    rr = dict(r)
                    rr["config_name"] = "full_system"
                    by_id[rid] = rr
            ordered = [by_id[bid] for bid in sorted(benchmark_ids) if bid in by_id]
            return {"detailed_results": ordered}
        elif "results" in data:
            # 兼容另一种格式：补齐config_name，并过滤到benchmark集合，且固定顺序
            benchmark_ids = get_benchmark_brief_ids()
            by_id: Dict[str, Dict] = {}
            for r in data["results"]:
                rid = r.get("prd_id")
                if rid and rid in benchmark_ids:
                    rr = dict(r)
                    rr["config_name"] = "full_system"
                    by_id[rid] = rr
            ordered = [by_id[bid] for bid in sorted(benchmark_ids) if bid in by_id]
            return {"detailed_results": ordered}
    
    # 尝试从PRD文件重建
    print(f"⚠️  未找到完整系统汇总文件: {summary_path}")
    print("   正在从PRD文件直接加载并计算指标...")
    
    prd_files = list(full_system_dir.glob("prd_*.json"))
    if not prd_files:
        print("  ❌ 未找到PRD文件")
        return {}
    
    try:
        from src.metrics.quality import compute_all_metrics, load_prd
        from src.metrics.extended_quality import compute_all_extended_metrics
    except ImportError:
        print("  ❌ 无法导入质量指标计算模块")
        return {}
    
    # 过滤出benchmark PRD（只移除前缀 prd_），并固定顺序
    benchmark_ids = get_benchmark_brief_ids()
    file_map = {prd_id_from_filename(f): f for f in prd_files}
    benchmark_prds = [(file_map[bid], bid) for bid in sorted(benchmark_ids) if bid in file_map]
    
    print(f"   找到 {len(prd_files)} 个PRD文件，过滤出 {len(benchmark_prds)} 个benchmark PRD")
    
    results = []
    for prd_file, prd_id in benchmark_prds:
        try:
            prd_data = load_prd(prd_file)
            basic = compute_all_metrics(prd_data)
            expert_prd_path = find_expert_prd(prd_id)
            extended = compute_all_extended_metrics(prd_data, expert_prd_path=expert_prd_path)
            metrics = {**basic, **extended}
            results.append({
                "config_name": "full_system",
                "prd_id": prd_id,
                "prd_path": str(prd_file),
                "metrics": metrics,
            })
        except Exception as e:
            print(f"  ⚠️  加载 {prd_file} 失败: {e}")
    
    return {"detailed_results": results}


def extract_metrics_by_config(results: List[Dict]) -> Dict[str, Dict[str, List[float]]]:
    """按配置提取指标值"""
    metric_names = [
        "S_comp", "S_mm", "S_tab", "S_bi", "S_var",
        "S_sem", "S_biz", "S_tech", "S_risk", "S_expert",
        "S_ps", "S_uj", "S_hyp"
    ]
    
    config_metrics: Dict[str, Dict[str, List[float]]] = {}
    
    for result in results:
        config_name = result.get("config_name", "unknown")
        prd_id = result.get("prd_id", "unknown")
        metrics = result.get("metrics", {})
        
        if config_name not in config_metrics:
            config_metrics[config_name] = {metric: [] for metric in metric_names}
        
        for metric_name in metric_names:
            metric_value = metrics.get(metric_name, 0.0)
            single_value = extract_single_value(metric_value)
            config_metrics[config_name][metric_name].append(single_value)
    
    return config_metrics


def compare_configs(
    full_system_metrics: Dict[str, List[float]],
    ablation_metrics: Dict[str, List[float]],
    metric_name: str,
) -> Dict:
    """对比完整系统与消融配置"""
    # 确保配对（按索引顺序）
    if len(full_system_metrics) != len(ablation_metrics):
        # 尝试按PRD ID配对
        print(f"  ⚠️  {metric_name}: 样本数不匹配 ({len(full_system_metrics)} vs {len(ablation_metrics)})")
        min_len = min(len(full_system_metrics), len(ablation_metrics))
        full_values = full_system_metrics[:min_len]
        ablation_values = ablation_metrics[:min_len]
    else:
        full_values = full_system_metrics
        ablation_values = ablation_metrics
    
    if len(full_values) < 2:
        return {
            "full_system_mean": 0.0,
            "ablation_mean": 0.0,
            "difference": 0.0,
            "difference_percent": 0.0,
            "wilcoxon": {"statistic": 0.0, "p_value": 1.0, "significant": False},
            "cliffs_delta": 0.0,
            "bootstrap_ci": [0.0, 0.0],
            "sample_size": len(full_values),
        }
    
    # 计算均值
    full_mean = sum(full_values) / len(full_values)
    ablation_mean = sum(ablation_values) / len(ablation_values)
    
    # Wilcoxon检验
    try:
        wilcoxon_result = wilcoxon_test(full_values, ablation_values)
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
    
    # Cliff's δ
    delta = cliffs_delta(full_values, ablation_values)
    
    # Bootstrap CI（差异的置信区间）
    differences = [f - a for f, a in zip(full_values, ablation_values)]
    ci = bootstrap_ci(differences)
    
    return {
        "full_system_mean": round(full_mean, 4),
        "ablation_mean": round(ablation_mean, 4),
        "difference": round(full_mean - ablation_mean, 4),
        "difference_percent": round((full_mean - ablation_mean) / full_mean * 100, 2) if full_mean > 0 else 0.0,
        "wilcoxon": {
            "statistic": round(wilcoxon_result["statistic"], 4),
            "p_value": round(wilcoxon_result["p_value"], 4),
            "significant": wilcoxon_result["p_value"] < 0.05,
        },
        "cliffs_delta": round(delta, 4),
        "bootstrap_ci": [round(ci[0], 4), round(ci[1], 4)],
        "sample_size": len(full_values),
    }


def analyze_ablation_results(
    ablation_dir: Path,
    full_system_dir: Path,
    output_path: Path,
) -> Dict:
    """分析消融实验结果"""
    print("=" * 70)
    print("消融实验结果分析")
    print("=" * 70)
    print()
    
    # 加载数据
    print("📂 加载实验结果...")
    ablation_data = load_ablation_results(ablation_dir)
    full_system_data = load_full_system_results(full_system_dir)
    
    if not ablation_data or not ablation_data.get("results"):
        print("❌ 未找到消融实验结果")
        return {}
    
    if not full_system_data or not full_system_data.get("detailed_results"):
        print("❌ 未找到完整系统结果")
        return {}
    
    ablation_results = ablation_data["results"]
    full_system_results = full_system_data["detailed_results"]
    
    print(f"✅ 加载了 {len(ablation_results)} 个消融实验结果")
    print(f"✅ 加载了 {len(full_system_results)} 个完整系统结果")
    print()
    
    # 提取指标
    print("📊 提取质量指标...")
    ablation_metrics_by_config = extract_metrics_by_config(ablation_results)
    full_system_metrics_by_config = extract_metrics_by_config(full_system_results)
    
    # 获取完整系统的指标（作为对照组）
    full_system_metrics = full_system_metrics_by_config.get("full_system", {})
    if not full_system_metrics:
        # 尝试从full_system_results中提取（可能config_name不是"full_system"）
        # 检查是否有其他名称的配置（可能是"unknown"或其他）
        if full_system_metrics_by_config:
            # 优先查找包含"full"或样本数最多的配置
            best_config = None
            max_samples = 0
            for config_name, metrics in full_system_metrics_by_config.items():
                sample_count = len(metrics.get("S_comp", []))
                if "full" in config_name.lower() or sample_count > max_samples:
                    best_config = config_name
                    max_samples = sample_count
            
            if best_config:
                print(f"  ℹ️  使用配置 '{best_config}' 作为完整系统对照组（{max_samples}个样本）")
                full_system_metrics = full_system_metrics_by_config[best_config]
            else:
                # 使用第一个配置
                first_config = list(full_system_metrics_by_config.keys())[0]
                sample_count = len(full_system_metrics_by_config[first_config].get("S_comp", []))
                print(f"  ℹ️  使用配置 '{first_config}' 作为完整系统对照组（{sample_count}个样本）")
                full_system_metrics = full_system_metrics_by_config[first_config]
        else:
            print("  ⚠️  无法找到完整系统指标")
            full_system_metrics = {}
    
    print(f"✅ 提取了 {len(full_system_metrics)} 个指标的完整系统数据")
    print()
    
    # 对比每个消融配置
    print("🔄 对比消融配置与完整系统...")
    
    metric_names = [
        "S_comp", "S_mm", "S_tab", "S_bi", "S_var",
        "S_sem", "S_biz", "S_tech", "S_risk", "S_expert",
        "S_ps", "S_uj", "S_hyp"
    ]
    
    comparison_results = {}
    
    # 获取所有消融配置名称（排除full_system）
    ablation_configs = [c for c in ablation_metrics_by_config.keys() if c != "full_system"]
    
    for config_name in ablation_configs:
        print(f"\n📋 配置: {config_name}")
        print("-" * 70)
        
        config_metrics = ablation_metrics_by_config[config_name]
        config_comparison = {}
        
        for metric_name in metric_names:
            full_values = full_system_metrics.get(metric_name, [])
            ablation_values = config_metrics.get(metric_name, [])
            
            if not full_values or not ablation_values:
                continue
            
            comparison = compare_configs(full_values, ablation_values, metric_name)
            config_comparison[metric_name] = comparison
            
            # 显示结果
            significance = ""
            if comparison["wilcoxon"]["p_value"] < 0.001:
                significance = "***"
            elif comparison["wilcoxon"]["p_value"] < 0.01:
                significance = "**"
            elif comparison["wilcoxon"]["p_value"] < 0.05:
                significance = "*"
            
            diff_pct = comparison["difference_percent"]
            if diff_pct > 0:
                print(f"  {metric_name}: 完整={comparison['full_system_mean']:.3f} vs 消融={comparison['ablation_mean']:.3f} (下降{diff_pct:.1f}%) {significance}")
            else:
                print(f"  {metric_name}: 完整={comparison['full_system_mean']:.3f} vs 消融={comparison['ablation_mean']:.3f} (提升{abs(diff_pct):.1f}%) {significance}")
        
        comparison_results[config_name] = config_comparison

    # 多重比较校正（Holm-Bonferroni）：覆盖所有(配置×指标)的Wilcoxon p-value
    tests = []
    pvals = []
    for cfg, cfg_comp in comparison_results.items():
        for metric_name, comp in cfg_comp.items():
            p = comp.get("wilcoxon", {}).get("p_value", 1.0)
            try:
                p = float(p)
            except Exception:
                p = 1.0
            if not math.isfinite(p):
                p = 1.0
            tests.append((cfg, metric_name))
            pvals.append(p)

    qvals = holm_bonferroni(pvals, alpha=0.05)
    for (cfg, metric_name), q in zip(tests, qvals):
        comp = comparison_results[cfg].get(metric_name)
        if not comp:
            continue
        comp["wilcoxon_corrected"] = {
            "method": "holm-bonferroni",
            "q_value": round(float(q), 4),
            "significant": float(q) < 0.05,
        }
    
    # 生成对比表格
    print("\n📊 生成对比表格...")
    
    comparison_table = []
    for metric_name in metric_names:
        row = {"metric": metric_name}
        
        # 完整系统均值
        full_values = full_system_metrics.get(metric_name, [])
        if full_values:
            row["full_system"] = round(sum(full_values) / len(full_values), 4)
        else:
            row["full_system"] = 0.0
        
        # 每个消融配置的均值
        for config_name in ablation_configs:
            config_metrics = ablation_metrics_by_config[config_name]
            config_values = config_metrics.get(metric_name, [])
            if config_values:
                row[config_name] = round(sum(config_values) / len(config_values), 4)
            else:
                row[config_name] = 0.0
        
        comparison_table.append(row)
    
    # 保存结果
    analysis_result = {
        "analysis_date": "2025-11-23",
        "full_system_prd_count": len(full_system_results),
        "ablation_prd_count": len(ablation_results),
        "configs": ablation_configs,
        "comparison_results": comparison_results,
        "comparison_table": comparison_table,
        "multiple_comparison_correction": {
            "method": "holm-bonferroni",
            "alpha": 0.05,
            "num_tests": len(pvals),
        },
        "notes": {
            "wilcoxon_significance": "p < 0.05 indicates significant difference",
            "holm_bonferroni": "wilcoxon_corrected.q_value controls family-wise error rate (FWER) across all (config×metric) tests",
            "cliffs_delta_interpretation": "|delta| > 0.147 = small, > 0.33 = medium, > 0.474 = large effect",
            "bootstrap_ci": "95% confidence interval for the difference (full - ablation)",
            "difference_percent": "positive = ablation worse, negative = ablation better",
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        # ensure strict JSON (no NaN/Infinity)
        json.dumps(analysis_result, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8"
    )
    
    # 保存对比表格（单独文件）
    table_path = output_path.parent / "ablation_comparison_table.json"
    table_path.write_text(
        json.dumps(comparison_table, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ 分析结果已保存: {output_path}")
    print(f"✅ 对比表格已保存: {table_path}")
    
    return analysis_result


def main():
    ablation_dir = Path("results/ablation")
    full_system_dir = Path("results/full_system")
    output_path = Path("results/ablation/ablation_analysis.json")
    
    if not ablation_dir.exists():
        print(f"❌ 消融实验目录不存在: {ablation_dir}")
        print("   请先运行 scripts/run_ablation_experiment.py")
        return
    
    if not full_system_dir.exists():
        print(f"❌ 完整系统目录不存在: {full_system_dir}")
        print("   请先运行 scripts/run_full_system_experiment.py")
        return
    
    print(f"消融实验目录: {ablation_dir}")
    print(f"完整系统目录: {full_system_dir}")
    print(f"输出路径: {output_path}")
    print()
    
    # 执行分析
    analysis_result = analyze_ablation_results(
        ablation_dir=ablation_dir,
        full_system_dir=full_system_dir,
        output_path=output_path,
    )
    
    if analysis_result:
        print("\n" + "=" * 70)
        print("分析完成")
        print("=" * 70)
        print(f"配置数: {len(analysis_result.get('configs', []))}")
        print(f"指标数: {len(analysis_result.get('comparison_table', []))}")
        print("\n下一步: 运行 scripts/generate_visualizations.py 生成可视化图表")


if __name__ == "__main__":
    main()

