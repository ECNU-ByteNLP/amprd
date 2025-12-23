"""
检查消融实验进度

用法:
    python scripts/check_ablation_progress.py
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 消融配置列表
ABLATION_CONFIGS = [
    {"name": "full_system", "description": "完整系统"},
    {"name": "no_alignment", "description": "去掉双语对齐Agent"},
    {"name": "no_vision", "description": "去掉视觉生成Agent"},
    {"name": "no_table", "description": "去掉表格生成Agent"},
    {"name": "no_consistency", "description": "去掉一致性检查Agent"},
    {"name": "async_queue", "description": "异步队列通信模式"},
    {"name": "mock_model", "description": "使用Mock模型"},
]

def get_brief_ids() -> List[str]:
    """获取所有Brief ID列表"""
    benchmark_dir = PROJECT_ROOT / "data" / "benchmark"
    brief_files = list(benchmark_dir.glob("*_brief.json"))
    brief_ids = []
    for f in brief_files:
        # 从文件名提取brief_id: xxx_brief.json -> xxx
        brief_id = f.stem.replace("_brief", "")
        brief_ids.append(brief_id)
    return sorted(brief_ids)


def check_config_progress(config_name: str, total_briefs: int = 15) -> Dict:
    """检查单个配置的进度"""
    config_dir = PROJECT_ROOT / "results" / "ablation" / config_name
    
    if not config_dir.exists():
        return {
            "config": config_name,
            "status": "not_started",
            "completed": 0,
            "total": total_briefs,
            "progress": 0.0,
        }
    
    # 检查PRD文件（只统计以brief_id命名的文件）
    brief_ids = get_brief_ids()
    prd_files = []
    for brief_id in brief_ids:
        prd_file = config_dir / f"prd_{brief_id}.json"
        if prd_file.exists():
            prd_files.append(prd_file)
    completed_files = len(prd_files)
    completed = completed_files
    
    # 检查是否有metrics_summary.json
    summary_file = config_dir / "metrics_summary.json"
    if summary_file.exists():
        try:
            summary = json.loads(summary_file.read_text(encoding="utf-8"))
            # 进度以“真实PRD文件”为准，避免summary被错误写入导致假阳性
            reported_successful = summary.get("successful")
            failed = summary.get("failed", 0)
            total_time = summary.get("total_time_seconds", 0)
            mismatch = (
                reported_successful is not None
                and isinstance(reported_successful, int)
                and reported_successful != completed_files
            )
            return {
                "config": config_name,
                "status": "completed" if completed == total_briefs else "in_progress",
                "completed": completed,
                "failed": failed,
                "total": total_briefs,
                "progress": round(completed / total_briefs * 100, 1),
                "total_time_minutes": round(total_time / 60, 1) if total_time else None,
                "summary_mismatch": mismatch,
                "reported_successful": reported_successful,
            }
        except Exception:
            pass
    
    return {
        "config": config_name,
        "status": "in_progress" if completed > 0 else "not_started",
        "completed": completed,
        "total": total_briefs,
        "progress": round(completed / total_briefs * 100, 1),
    }


def main():
    print("=" * 70)
    print("消融实验进度检查")
    print("=" * 70)
    print()
    
    # 检查每个配置的进度
    all_progress = []
    total_completed = 0
    total_prds = 0
    
    brief_ids = get_brief_ids()
    
    for config in ABLATION_CONFIGS:
        if config["name"] == "full_system":
            # full_system在results/full_system目录
            full_system_dir = PROJECT_ROOT / "results" / "full_system"
            if full_system_dir.exists():
                # 只统计以brief_id命名的PRD文件
                prd_files = []
                for brief_id in brief_ids:
                    prd_file = full_system_dir / f"prd_{brief_id}.json"
                    if prd_file.exists():
                        prd_files.append(prd_file)
                completed = len(prd_files)
                status = "completed" if completed == 15 else "in_progress"
            else:
                completed = 0
                status = "not_started"
            
            progress_info = {
                "config": config["name"],
                "description": config["description"],
                "status": status,
                "completed": completed,
                "total": 15,
                "progress": round(completed / 15 * 100, 1),
            }
        else:
            progress_info = check_config_progress(config["name"])
            progress_info["description"] = config["description"]
        
        all_progress.append(progress_info)
        total_completed += progress_info["completed"]
        total_prds += progress_info["total"]
    
    # 显示进度
    print(f"{'配置':<20} {'状态':<12} {'进度':<15} {'描述'}")
    print("-" * 70)
    
    for info in all_progress:
        status_icon = {
            "completed": "✅",
            "in_progress": "🔄",
            "not_started": "⏳",
        }.get(info["status"], "❓")
        
        progress_bar = f"{info['completed']}/{info['total']} ({info['progress']}%)"
        if info.get("total_time_minutes"):
            progress_bar += f" [{info['total_time_minutes']}分钟]"
        if info.get("summary_mismatch"):
            progress_bar += " ⚠️summary不一致"
        
        print(
            f"{info['config']:<20} "
            f"{status_icon} {info['status']:<10} "
            f"{progress_bar:<15} "
            f"{info['description']}"
        )
    
    print()
    print("-" * 70)
    print(f"总体进度: {total_completed}/{total_prds} PRD ({round(total_completed/total_prds*100, 1)}%)")
    
    # 计算剩余工作量
    remaining = total_prds - total_completed
    if remaining > 0:
        # 估算剩余时间（假设每个PRD平均15分钟）
        estimated_minutes = remaining * 15
        estimated_hours = estimated_minutes / 60
        print(f"剩余工作量: {remaining} 个PRD")
        print(f"预计剩余时间: {estimated_hours:.1f} 小时 ({estimated_minutes:.0f} 分钟)")
    
    print()
    
    # 显示未完成的配置
    incomplete = [p for p in all_progress if p["status"] != "completed"]
    if incomplete:
        print("未完成的配置:")
        for info in incomplete:
            print(f"  - {info['config']}: {info['completed']}/{info['total']} ({info['progress']}%)")
        print()
        print("运行命令:")
        for info in incomplete:
            if info["status"] == "not_started":
                print(f"  python scripts/run_ablation_single_config.py --config {info['config']}")


if __name__ == "__main__":
    main()

