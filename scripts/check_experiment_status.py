"""
检查当前实验状态

检查所有实验的完成情况，包括：
- 基线系统（45个PRD）
- 完整系统（15个PRD）
- 消融实验（90个PRD）
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def count_prd_files(directory: Path) -> int:
    """统计PRD文件数量"""
    if not directory.exists():
        return 0
    # 只统计有Brief ID的PRD文件（排除UUID格式的）
    prd_files = list(directory.glob("prd_*.json"))
    # 过滤掉UUID格式的文件名
    valid_files = [f for f in prd_files if "_" in f.stem and not f.stem.replace("prd_", "").startswith("0") and len(f.stem.split("_")) > 2]
    return len(valid_files)


def main():
    print("=" * 70)
    print("实验状态检查")
    print("=" * 70)
    print()
    
    # 检查基线系统
    print("📊 基线系统:")
    baseline_txt = count_prd_files(Path("results/baseline_text_only"))
    baseline_tpl = count_prd_files(Path("results/baseline_template"))
    baseline_ret = count_prd_files(Path("results/baseline_retrieval"))
    baseline_total = baseline_txt + baseline_tpl + baseline_ret
    
    print(f"  Baseline-TXT: {baseline_txt}/15")
    print(f"  Baseline-TPL: {baseline_tpl}/15")
    print(f"  Baseline-RET: {baseline_ret}/15")
    print(f"  总计: {baseline_total}/45")
    print()
    
    # 检查完整系统
    print("📊 完整系统:")
    full_system = count_prd_files(Path("results/full_system"))
    print(f"  Full System: {full_system}/15")
    print()
    
    # 检查消融实验
    print("📊 消融实验:")
    ablation_configs = [
        "no_alignment",
        "no_vision",
        "no_table",
        "no_consistency",
        "async_queue",
        "mock_model",
    ]
    
    ablation_total = 0
    for config in ablation_configs:
        config_dir = Path(f"results/ablation/{config}")
        count = count_prd_files(config_dir)
        ablation_total += count
        status = "✅" if count == 15 else ("⚠️" if count > 0 else "❌")
        print(f"  {status} {config}: {count}/15")
    
    print(f"  总计: {ablation_total}/90")
    print()
    
    # 总体统计
    print("=" * 70)
    print("总体统计")
    print("=" * 70)
    print(f"基线系统: {baseline_total}/45 ({baseline_total/45*100:.1f}%)")
    print(f"完整系统: {full_system}/15 ({full_system/15*100:.1f}%)")
    print(f"消融实验: {ablation_total}/90 ({ablation_total/90*100:.1f}%)")
    print(f"总计: {baseline_total + full_system + ablation_total}/150")
    print()
    
    # 下一步建议
    print("=" * 70)
    print("下一步建议")
    print("=" * 70)
    
    if baseline_total < 45:
        print("⚠️  基线系统未完成，建议先完成基线系统")
    
    if full_system < 15:
        print("⚠️  完整系统未完成，建议先完成完整系统")
    
    if ablation_total < 90:
        remaining = 90 - ablation_total
        print(f"⏳ 消融实验未完成，剩余 {remaining} 个PRD")
        print("   建议运行: python scripts/run_ablation_experiment.py")
    
    if baseline_total == 45 and full_system == 15 and ablation_total == 90:
        print("✅ 所有实验已完成！")
        print("   下一步: 运行分析和可视化")
        print("   - python scripts/analyze_ablation_results.py")
        print("   - python scripts/generate_visualizations.py")


if __name__ == "__main__":
    main()
