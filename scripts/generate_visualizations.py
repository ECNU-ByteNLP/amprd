"""
生成实验可视化图表

生成以下图表：
1. 完整系统 vs 基线系统对比图（柱状图）
2. 消融实验热力图
3. 质量指标箱线图
4. 统计显著性可视化
5. 消融实验对比图

输出：
- results/visualizations/*.png: 所有图表
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
load_dotenv()

try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import seaborn as sns
    import numpy as np
    import pandas as pd
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    print("⚠️  可视化库未安装，请运行: pip install matplotlib seaborn pandas numpy")
    print("   将跳过可视化生成")


def setup_plot_style():
    """Set plotting style and fonts (English-first for ACL-ready figures)."""
    if not HAS_VISUALIZATION:
        return
    
    # Seaborn style first (it may override matplotlib defaults).
    sns.set_style("whitegrid")

    # English-first fonts; keep a broad fallback chain for Windows/Linux.
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Liberation Sans"]

    plt.rcParams["axes.unicode_minus"] = False

    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['figure.figsize'] = (12, 8)


def load_comparison_data(comparison_path: Path) -> Optional[Dict]:
    """加载对比数据"""
    if not comparison_path.exists():
        return None
    
    return json.loads(comparison_path.read_text(encoding="utf-8"))


def load_ablation_analysis(ablation_analysis_path: Path) -> Optional[Dict]:
    """加载消融实验分析数据"""
    if not ablation_analysis_path.exists():
        return None
    
    return json.loads(ablation_analysis_path.read_text(encoding="utf-8"))


def plot_full_vs_baseline_comparison(comparison_data: Dict, output_path: Path):
    """Plot Full system vs. Baseline comparison (ACL-friendly English labels)."""
    if not HAS_VISUALIZATION:
        return
    
    results = comparison_data.get("comparison_results", {})
    if not results:
        print("  ⚠️  无对比数据，跳过")
        return
    
    metrics = list(results.keys())
    full_means = [results[m]["full_system_mean"] for m in metrics]
    baseline_means = [results[m]["baseline_mean"] for m in metrics]
    improvements = [results[m]["improvement_percent"] for m in metrics]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 左图：柱状图对比
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, full_means, width, label='Full', color='#2E86AB', alpha=0.85)
    bars2 = ax1.bar(x + width/2, baseline_means, width, label='Baseline', color='#A23B72', alpha=0.85)
    
    ax1.set_xlabel('Metric', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax1.set_title('Full vs. Baseline: Metric Means', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, rotation=45, ha='right')
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim([0, 1.1])
    
    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=8)
    
    # 右图：提升百分比
    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    bars3 = ax2.barh(metrics, improvements, color=colors, alpha=0.7)
    
    ax2.set_xlabel('Relative change (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Full vs. Baseline: Relative Change', fontsize=14, fontweight='bold')
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax2.grid(axis='x', alpha=0.3)
    
    # 添加数值标签
    for i, (bar, imp) in enumerate(zip(bars3, improvements)):
        ax2.text(imp, i, f'{imp:+.1f}%',
                ha='left' if imp > 0 else 'right', va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"  ✅ 已保存: {output_path.name}")


def plot_ablation_heatmap(ablation_data: Dict, output_path: Path):
    """Plot ablation heatmap (ACL-friendly English labels)."""
    if not HAS_VISUALIZATION:
        return
    
    comparison_table = ablation_data.get("comparison_table", [])
    if not comparison_table:
        print("  ⚠️  无消融数据，跳过")
        return
    
    # 构建数据框
    metrics = [row["metric"] for row in comparison_table]
    configs = [k for k in comparison_table[0].keys() if k != "metric"]
    
    data = []
    for row in comparison_table:
        data.append([row.get(config, 0.0) for config in configs])
    
    df = pd.DataFrame(data, index=metrics, columns=configs)
    
    # 创建热力图
    fig, ax = plt.subplots(figsize=(14, 10))
    
    sns.heatmap(
        df,
        annot=True,
        fmt='.3f',
        cmap='RdYlGn',
        vmin=0,
        vmax=1,
        cbar_kws={'label': 'Score'},
        ax=ax,
        linewidths=0.5,
        linecolor='gray',
    )
    
    ax.set_title('Ablation: Metric Heatmap', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Configuration', fontsize=12, fontweight='bold')
    ax.set_ylabel('Metric', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"  ✅ 已保存: {output_path.name}")


def plot_ablation_comparison(ablation_data: Dict, output_path: Path):
    """Plot ablation grouped bars (ACL-friendly English labels)."""
    if not HAS_VISUALIZATION:
        return
    
    comparison_table = ablation_data.get("comparison_table", [])
    if not comparison_table:
        print("  ⚠️  无消融数据，跳过")
        return
    
    # 提取数据
    metrics = [row["metric"] for row in comparison_table]
    configs = [k for k in comparison_table[0].keys() if k != "metric"]
    
    # 创建分组柱状图
    fig, ax = plt.subplots(figsize=(16, 8))
    
    x = np.arange(len(metrics))
    width = 0.8 / len(configs)
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(configs)))
    
    for i, config in enumerate(configs):
        values = [row.get(config, 0.0) for row in comparison_table]
        offset = (i - len(configs)/2 + 0.5) * width
        ax.bar(x + offset, values, width, label=config, color=colors[i], alpha=0.8)
    
    ax.set_xlabel('Metric', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Ablation: Metric Means by Configuration', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=45, ha='right')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"  ✅ 已保存: {output_path.name}")


def plot_statistical_significance(comparison_data: Dict, output_path: Path):
    """Plot statistical significance bars (ACL-friendly English labels)."""
    if not HAS_VISUALIZATION:
        return
    
    results = comparison_data.get("comparison_results", {})
    if not results:
        print("  ⚠️  无对比数据，跳过")
        return
    
    metrics = list(results.keys())
    # 优先使用多重比较校正后的q值（如果存在），否则用原始p值
    def _get_p_or_q(m: str) -> float:
        r = results.get(m, {})
        corr = r.get("wilcoxon_corrected")
        if isinstance(corr, dict) and "q_value" in corr:
            return float(corr.get("q_value", 1.0))
        return float(r.get("wilcoxon", {}).get("p_value", 1.0))

    p_values = [_get_p_or_q(m) for m in metrics]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 根据p值设置颜色
    colors = []
    for p in p_values:
        if p < 0.001:
            colors.append('#2E7D32')  # 深绿：极其显著
        elif p < 0.01:
            colors.append('#66BB6A')  # 浅绿：非常显著
        elif p < 0.05:
            colors.append('#FFC107')  # 黄色：显著
        else:
            colors.append('#E57373')  # 浅红：不显著
    
    bars = ax.barh(metrics, [-np.log10(p) if p > 0 else 10 for p in p_values], color=colors, alpha=0.7)
    
    # 添加显著性阈值线
    ax.axvline(x=-np.log10(0.05), color='red', linestyle='--', linewidth=1, label='0.05')
    ax.axvline(x=-np.log10(0.01), color='orange', linestyle='--', linewidth=1, label='0.01')
    ax.axvline(x=-np.log10(0.001), color='green', linestyle='--', linewidth=1, label='0.001')
    
    # 如果存在校正信息，标题/标签中说明使用q值
    has_corr = any(isinstance(results.get(m, {}).get("wilcoxon_corrected"), dict) for m in metrics)
    ax.set_xlabel(r'$-\log_{10}(q)$' if has_corr else r'$-\log_{10}(p)$', fontsize=12, fontweight='bold')
    ax.set_ylabel('Metric', fontsize=12, fontweight='bold')
    ax.set_title('Statistical significance (Holm--Bonferroni corrected)' if has_corr else 'Statistical significance', fontsize=14, fontweight='bold')
    ax.legend(title='threshold', fontsize=10)
    ax.grid(axis='x', alpha=0.3)
    
    # 添加p值标签
    for i, (bar, p) in enumerate(zip(bars, p_values)):
        height = bar.get_height()
        ax.text(height, i, f'{"q" if has_corr else "p"}={p:.4f}',
                ha='left', va='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"  ✅ 已保存: {output_path.name}")


def main():
    if not HAS_VISUALIZATION:
        print("❌ 可视化库未安装，无法生成图表")
        print("   请运行: pip install matplotlib seaborn pandas numpy")
        return
    
    setup_plot_style()
    
    print("=" * 70)
    print("生成实验可视化图表")
    print("=" * 70)
    print()
    
    # 创建输出目录
    output_dir = Path("results/visualizations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    comparison_path = Path("results/comparison_full_vs_baseline.json")
    ablation_analysis_path = Path("results/ablation/ablation_analysis.json")
    
    print("📂 加载数据...")
    
    # 1. 完整系统 vs 基线系统对比图（默认文件）
    if comparison_path.exists():
        print("\n📊 生成完整系统 vs 基线系统对比图...")
        comparison_data = load_comparison_data(comparison_path)
        if comparison_data:
            plot_full_vs_baseline_comparison(
                comparison_data,
                output_dir / "full_vs_baseline_comparison.png"
            )
    else:
        print("  ⚠️  未找到对比数据文件，跳过")

    # 1b. 完整系统 vs 强提示词基线（若存在）
    strong_cmp_path = Path("results/comparison_full_vs_strong_prompt.json")
    if strong_cmp_path.exists():
        print("\n📊 生成完整系统 vs StrongPrompt基线对比图...")
        strong_data = load_comparison_data(strong_cmp_path)
        if strong_data:
            plot_full_vs_baseline_comparison(
                strong_data,
                output_dir / "full_vs_strong_prompt_comparison.png"
            )
    
    # 2. 消融实验热力图
    if ablation_analysis_path.exists():
        print("\n📊 生成消融实验热力图...")
        ablation_data = load_ablation_analysis(ablation_analysis_path)
        if ablation_data:
            plot_ablation_heatmap(
                ablation_data,
                output_dir / "ablation_heatmap.png"
            )
            
            print("\n📊 生成消融实验对比图...")
            plot_ablation_comparison(
                ablation_data,
                output_dir / "ablation_comparison.png"
            )
    else:
        print("  ⚠️  未找到消融实验分析文件，跳过")
    
    # 3. 统计显著性可视化
    if comparison_path.exists():
        print("\n📊 生成统计显著性可视化...")
        comparison_data = load_comparison_data(comparison_path)
        if comparison_data:
            plot_statistical_significance(
                comparison_data,
                output_dir / "statistical_significance.png"
            )
    
    print("\n" + "=" * 70)
    print("可视化图表生成完成")
    print("=" * 70)
    print(f"输出目录: {output_dir}")
    print(f"生成的图表:")
    for png_file in output_dir.glob("*.png"):
        print(f"  - {png_file.name}")


if __name__ == "__main__":
    main()

