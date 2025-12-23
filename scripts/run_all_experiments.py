"""
主执行脚本 - 运行所有实验

按顺序执行所有实验步骤，完成符合顶会标准的完整实验。

执行步骤：
1. 运行消融实验（可选，如果已完成可跳过）
2. 分析消融实验结果
3. 生成可视化图表
4. 错误分析与案例研究
5. 生成人工评估框架（可选）

使用方法：
    python scripts/run_all_experiments.py [--skip-ablation] [--skip-human-eval]
"""

import sys
import io
import argparse
import subprocess
from pathlib import Path
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


def run_script(script_path: Path, description: str) -> bool:
    """运行Python脚本"""
    print("=" * 70)
    print(f"执行: {description}")
    print(f"脚本: {script_path}")
    print("=" * 70)
    print()
    
    if not script_path.exists():
        print(f"❌ 脚本不存在: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            check=False,
        )
        
        if result.returncode == 0:
            print(f"\n✅ {description} 完成")
            return True
        else:
            print(f"\n❌ {description} 失败 (退出码: {result.returncode})")
            return False
    except Exception as e:
        print(f"\n❌ {description} 执行出错: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="运行所有实验")
    parser.add_argument(
        "--skip-ablation",
        action="store_true",
        help="跳过消融实验（如果已完成）",
    )
    parser.add_argument(
        "--skip-human-eval",
        action="store_true",
        help="跳过人工评估框架生成",
    )
    parser.add_argument(
        "--only-analysis",
        action="store_true",
        help="只运行分析和可视化（跳过实验）",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("完整实验执行流程")
    print("=" * 70)
    print()
    
    scripts_dir = PROJECT_ROOT / "scripts"
    results = []
    
    # Step 1: 运行消融实验
    if not args.skip_ablation and not args.only_analysis:
        ablation_script = scripts_dir / "run_ablation_experiment.py"
        success = run_script(ablation_script, "运行消融实验")
        results.append(("消融实验", success))
        
        if not success:
            print("\n⚠️  消融实验失败，是否继续？(y/n): ", end="")
            response = input().strip().lower()
            if response != 'y':
                print("❌ 已取消")
                return
    else:
        print("⏭️  跳过消融实验（使用 --skip-ablation 或 --only-analysis）")
        print()
    
    # Step 2: 分析消融实验结果
    analysis_script = scripts_dir / "analyze_ablation_results.py"
    success = run_script(analysis_script, "分析消融实验结果")
    results.append(("消融实验结果分析", success))
    
    if not success:
        print("\n⚠️  分析失败，但继续执行后续步骤...")
        print()
    
    # Step 3: 生成可视化图表
    viz_script = scripts_dir / "generate_visualizations.py"
    success = run_script(viz_script, "生成可视化图表")
    results.append(("可视化图表生成", success))
    
    if not success:
        print("\n⚠️  可视化生成失败，但继续执行后续步骤...")
        print()
    
    # Step 4: 错误分析与案例研究
    error_script = scripts_dir / "error_analysis_and_case_study.py"
    success = run_script(error_script, "错误分析与案例研究")
    results.append(("错误分析与案例研究", success))
    
    # Step 5: 生成人工评估框架
    if not args.skip_human_eval:
        human_eval_script = scripts_dir / "human_evaluation_framework.py"
        success = run_script(human_eval_script, "生成人工评估框架")
        results.append(("人工评估框架", success))
    else:
        print("⏭️  跳过人工评估框架生成（使用 --skip-human-eval）")
        print()
    
    # 总结
    print("\n" + "=" * 70)
    print("实验执行总结")
    print("=" * 70)
    print()
    
    for step, success in results:
        status = "✅ 完成" if success else "❌ 失败"
        print(f"{step}: {status}")
    
    print()
    
    success_count = sum(1 for _, s in results if s)
    total_count = len(results)
    
    print(f"完成度: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    print()
    
    if success_count == total_count:
        print("🎉 所有实验步骤完成！")
        print("\n下一步:")
        print("1. 检查 results/ 目录下的所有输出")
        print("2. 运行人工评估（如果生成）")
        print("3. 整理实验报告")
    else:
        print("⚠️  部分步骤失败，请检查日志并修复问题")


if __name__ == "__main__":
    main()

