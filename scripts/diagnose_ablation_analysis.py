"""诊断消融实验分析问题"""

import sys
import io
import json
from pathlib import Path

# 设置UTF-8编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.metrics.quality import load_prd, compute_all_metrics

def diagnose():
    print("=" * 70)
    print("消融实验分析诊断")
    print("=" * 70)
    print()
    
    ablation_dir = Path("results/ablation")
    full_system_dir = Path("results/full_system")
    
    # 1. 检查各配置的PRD文件数量
    print("📂 检查各配置的PRD文件数量:")
    print("-" * 70)
    config_dirs = [d for d in ablation_dir.iterdir() if d.is_dir()]
    for config_dir in sorted(config_dirs):
        prd_files = list(config_dir.glob("prd_*.json"))
        print(f"  {config_dir.name}: {len(prd_files)} PRD文件")
        if len(prd_files) > 0 and len(prd_files) < 15:
            print(f"    ⚠️  文件列表: {[f.stem.replace('prd_', '') for f in prd_files[:3]]}{'...' if len(prd_files) > 3 else ''}")
    print()
    
    # 2. 检查完整系统的PRD文件
    print("📂 检查完整系统的PRD文件:")
    print("-" * 70)
    full_system_prds = list(full_system_dir.glob("prd_*.json"))
    print(f"  full_system: {len(full_system_prds)} PRD文件")
    print()
    
    # 3. 检查一个完整系统PRD的指标
    print("📊 检查完整系统PRD指标计算:")
    print("-" * 70)
    if full_system_prds:
        sample_prd = full_system_prds[0]
        try:
            prd_data = load_prd(sample_prd)
            metrics = compute_all_metrics(prd_data)
            print(f"  示例文件: {sample_prd.name}")
            print(f"  指标数量: {len(metrics)}")
            print(f"  指标值示例:")
            for i, (k, v) in enumerate(list(metrics.items())[:5]):
                if isinstance(v, dict):
                    print(f"    {k}: {v}")
                else:
                    print(f"    {k}: {v}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    print()
    
    # 4. 模拟加载过程
    print("📊 模拟加载过程:")
    print("-" * 70)
    
    # 加载完整系统
    results = []
    for prd_file in full_system_prds:
        try:
            prd_data = load_prd(prd_file)
            metrics = compute_all_metrics(prd_data)
            prd_id = prd_file.stem.replace("prd_", "")
            results.append({
                "config_name": "full_system",
                "prd_id": prd_id,
                "prd_path": str(prd_file),
                "metrics": metrics,
            })
        except Exception as e:
            print(f"  ⚠️  加载 {prd_file} 失败: {e}")
    
    print(f"  加载了 {len(results)} 个完整系统结果")
    if results:
        print(f"  第一个结果的指标键: {list(results[0]['metrics'].keys())[:5]}")
        print(f"  第一个结果的S_comp值: {results[0]['metrics'].get('S_comp', 'NOT_FOUND')}")
    
    # 5. 检查extract_metrics_by_config
    print()
    print("📊 测试指标提取:")
    print("-" * 70)
    
    metric_names = [
        "S_comp", "S_mm", "S_tab", "S_bi", "S_var",
        "S_sem", "S_biz", "S_tech", "S_risk", "S_expert",
        "S_ps", "S_uj", "S_hyp"
    ]
    
    config_metrics = {}
    for result in results:
        config_name = result.get("config_name", "unknown")
        metrics = result.get("metrics", {})
        
        if config_name not in config_metrics:
            config_metrics[config_name] = {metric: [] for metric in metric_names}
        
        for metric_name in metric_names:
            metric_value = metrics.get(metric_name, 0.0)
            # 使用extract_single_value逻辑
            if isinstance(metric_value, (int, float)):
                single_value = float(metric_value)
            elif isinstance(metric_value, dict):
                if "overall" in metric_value:
                    single_value = float(metric_value["overall"])
                elif "std" in metric_value:
                    single_value = float(metric_value["std"])
                else:
                    single_value = 0.0
            else:
                single_value = 0.0
            config_metrics[config_name][metric_name].append(single_value)
    
    print(f"  提取后的配置数: {len(config_metrics)}")
    if "full_system" in config_metrics:
        full_metrics = config_metrics["full_system"]
        print(f"  full_system的指标值:")
        for metric_name in metric_names[:5]:
            values = full_metrics.get(metric_name, [])
            if values:
                print(f"    {metric_name}: {len(values)}个值, 均值={sum(values)/len(values):.3f}, 示例={values[0]}")
            else:
                print(f"    {metric_name}: 无值")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    diagnose()

