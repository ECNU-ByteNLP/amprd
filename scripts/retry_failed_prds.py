"""
补全完整系统失败的PRD

从metrics_summary.json中识别失败的PRD，重新生成这些PRD。

失败原因通常是网络超时，脚本会：
1. 增加更长的延迟时间
2. 使用更智能的重试策略
3. 记录详细的错误信息
"""

import sys
import io
import json
import time
import logging
from datetime import datetime
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

from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics

# 加载环境变量
load_dotenv()


def find_expert_prd(prd_id: str) -> Optional[Path]:
    """根据PRD ID查找对应的专家PRD"""
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
        except Exception:
            pass
    return None


def identify_failed_prds(metrics_summary_path: Path, all_brief_ids: List[str]) -> List[str]:
    """
    从metrics_summary.json中识别失败的PRD ID
    
    Args:
        metrics_summary_path: metrics_summary.json文件路径
        all_brief_ids: 所有Brief的ID列表
    
    Returns:
        List[str]: 失败的PRD ID列表
    """
    if not metrics_summary_path.exists():
        print(f"⚠️  指标汇总文件不存在: {metrics_summary_path}")
        return all_brief_ids
    
    try:
        summary_data = json.loads(metrics_summary_path.read_text(encoding="utf-8"))
        detailed_results = summary_data.get("detailed_results", [])
        
        # 提取成功的PRD ID
        successful_ids = {r["prd_id"] for r in detailed_results if r.get("prd_id")}
        
        # 失败的PRD = 所有Brief ID - 成功的PRD ID
        failed_ids = [brief_id for brief_id in all_brief_ids if brief_id not in successful_ids]
        
        return failed_ids
    except Exception as e:
        print(f"⚠️  读取指标汇总文件失败: {e}")
        return all_brief_ids


def retry_prd_generation(
    brief: Dict,
    output_dir: Path,
    prd_id: str,
    retry_count: int = 3,
    base_delay: float = 15.0,
) -> Optional[Dict]:
    """
    重试PRD生成，使用更长的延迟和更智能的重试策略
    
    Args:
        brief: Brief字典
        output_dir: 输出目录
        prd_id: PRD ID
        retry_count: 重试次数
        base_delay: 基础延迟时间（秒）
    
    Returns:
        Dict: 生成的状态字典，失败返回None
    """
    orchestrator = MultiAgentOrchestrator(persist_dir=output_dir)
    
    for attempt in range(retry_count):
        try:
            # 动态延迟：第一次尝试使用基础延迟，后续尝试延迟更长
            if attempt > 0:
                delay = base_delay * (2 ** attempt)  # 15秒 → 30秒 → 60秒
                print(f"  [尝试 {attempt + 1}/{retry_count}] 等待 {delay:.1f}秒以避免API限流...")
                time.sleep(delay)
            
            # 生成PRD
            state = orchestrator.run({"brief": brief})
            
            # 检查是否成功
            prd_path = state.get("quality", {}).get("artifact_path")
            if prd_path and Path(prd_path).exists():
                # 加载生成的PRD
                prd_json = json.loads(Path(prd_path).read_text(encoding="utf-8"))
                
                # 计算质量指标
                expert_prd_path = find_expert_prd(prd_id)
                basic_metrics = compute_all_metrics(prd_json)
                extended_metrics = compute_all_extended_metrics(prd_json, expert_prd_path=expert_prd_path)
                
                return {
                    "prd_id": prd_id,
                    "prd_path": str(prd_path),
                    "metrics": {**basic_metrics, **extended_metrics},
                    "success": True,
                    "attempt": attempt + 1,
                }
            
        except Exception as e:
            error_msg = str(e)
            print(f"  [尝试 {attempt + 1}/{retry_count}] 失败: {error_msg[:100]}")
            
            # 如果是最后一次尝试，返回失败信息
            if attempt == retry_count - 1:
                return {
                    "prd_id": prd_id,
                    "success": False,
                    "error": error_msg[:200],
                    "attempt": attempt + 1,
                }
            
            # 等待后重试（指数退避）
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    
    return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="补全完整系统失败的PRD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 自动识别失败的PRD并补全
  python scripts/retry_failed_prds.py

  # 指定要重试的PRD ID
  python scripts/retry_failed_prds.py \\
    --prd-ids general_figma_real_time_collaboration,general_miro_template_marketplace

  # 使用更长的延迟时间（避免API限流）
  python scripts/retry_failed_prds.py --base-delay 20.0
        """
    )
    
    parser.add_argument(
        "--metrics-summary",
        type=Path,
        default=Path("results/full_system/metrics_summary.json"),
        help="指标汇总文件路径（用于识别失败的PRD）",
    )
    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        default=Path("data/benchmark"),
        help="基准数据集目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/full_system"),
        help="输出目录",
    )
    parser.add_argument(
        "--prd-ids",
        type=str,
        help="指定要重试的PRD ID列表（逗号分隔），如果不指定则自动识别失败的PRD",
    )
    parser.add_argument(
        "--base-delay",
        type=float,
        default=15.0,
        help="基础延迟时间（秒），用于避免API限流（默认：15.0）",
    )
    parser.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="每个PRD的重试次数（默认：3）",
    )
    
    args = parser.parse_args()
    
    # 配置日志
    log_dir = Path("results/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"retry_failed_prds_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    
    logger = logging.getLogger("RetryFailedPRDs")
    
    logger.info("=" * 70)
    logger.info("补全完整系统失败的PRD")
    logger.info("=" * 70)
    logger.info(f"📝 日志文件: {log_file}")
    logger.info("")
    
    # 加载Brief列表
    builder = BenchmarkBuilder(args.benchmark_dir)
    all_prds_info = builder.list_prds()
    all_brief_ids = [p["prd_id"] for p in all_prds_info]
    
    # 确定要重试的PRD ID
    if args.prd_ids:
        # 使用指定的PRD ID
        failed_prd_ids = [pid.strip() for pid in args.prd_ids.split(",")]
        logger.info(f"📋 使用指定的PRD ID列表: {len(failed_prd_ids)} 个")
    else:
        # 自动识别失败的PRD
        failed_prd_ids = identify_failed_prds(args.metrics_summary, all_brief_ids)
        logger.info(f"📋 自动识别到 {len(failed_prd_ids)} 个失败的PRD")
    
    if not failed_prd_ids:
        logger.info("✅ 没有失败的PRD需要补全")
        return
    
    logger.info(f"失败的PRD ID: {', '.join(failed_prd_ids)}")
    logger.info("")
    
    # 加载失败的Brief
    failed_briefs = []
    for prd_id in failed_prd_ids:
        try:
            brief = builder.load_brief(prd_id)
            brief["prd_id"] = prd_id  # 确保有prd_id
            failed_briefs.append((prd_id, brief))
            logger.info(f"✅ 加载Brief: {prd_id}")
        except Exception as e:
            logger.error(f"❌ 加载Brief失败 {prd_id}: {e}")
    
    if not failed_briefs:
        logger.error("❌ 未找到任何可用的Brief")
        return
    
    logger.info(f"✅ 成功加载 {len(failed_briefs)} 个Brief")
    logger.info("")
    
    # 重试生成失败的PRD
    logger.info("=" * 70)
    logger.info("开始重试生成失败的PRD")
    logger.info("=" * 70)
    logger.info(f"基础延迟: {args.base_delay}秒")
    logger.info(f"重试次数: {args.retry_count}")
    logger.info("")
    
    results = []
    success_count = 0
    failed_count = 0
    
    for idx, (prd_id, brief) in enumerate(failed_briefs, 1):
        logger.info(f"[{idx}/{len(failed_briefs)}] 处理: {prd_id}")
        
        # 在批量处理时添加延迟
        if idx > 1:
            delay = args.base_delay * 1.5  # 每个PRD之间延迟更长
            logger.debug(f"  等待 {delay:.1f}秒以避免API限流...")
            time.sleep(delay)
        
        # 重试生成
        result = retry_prd_generation(
            brief,
            args.output_dir,
            prd_id,
            retry_count=args.retry_count,
            base_delay=args.base_delay,
        )
        
        if result and result.get("success"):
            logger.info(f"  ✅ 成功生成（尝试 {result['attempt']} 次）: {Path(result['prd_path']).name}")
            success_count += 1
        else:
            error_msg = result.get("error", "未知错误") if result else "生成失败"
            logger.error(f"  ❌ 生成失败: {error_msg[:100]}")
            failed_count += 1
        
        results.append(result)
        
        logger.info("")
    
    # 汇总结果
    logger.info("=" * 70)
    logger.info(f"补全完成: {success_count}/{len(failed_briefs)} 成功")
    if failed_count > 0:
        logger.warning(f"  ⚠️  仍有 {failed_count} 个PRD失败")
    logger.info("=" * 70)
    
    # 保存结果
    retry_results_path = args.output_dir / "retry_results.json"
    retry_results_path.write_text(
        json.dumps({
            "total": len(failed_briefs),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    logger.info(f"📝 重试结果已保存: {retry_results_path}")
    
    # 如果成功补全了一些PRD，建议更新metrics_summary
    if success_count > 0:
        logger.info("")
        logger.info("💡 建议：重新运行完整系统的指标计算以更新metrics_summary.json")
        logger.info("   python scripts/run_full_system_experiment.py")


if __name__ == "__main__":
    main()


