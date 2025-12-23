"""
运行单个消融配置的实验

用于测试或分批运行消融实验。

用法:
    python scripts/run_ablation_single_config.py --config no_alignment
    python scripts/run_ablation_single_config.py --config no_alignment --brief-id ecommerce_amazon_prime_video_personalization
"""

import sys
import io
import json
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import math

# 设置UTF-8编码（Windows兼容）
# 注意：不要直接用 TextIOWrapper(sys.stdout.buffer, ...) 替换 sys.stdout，
# 否则旧的 sys.stdout 被GC时可能关闭底层buffer，导致 logging 报 “I/O operation on closed file”。
if sys.platform == "win32":
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name)
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            try:
                setattr(sys, _stream_name, io.TextIOWrapper(_stream.detach(), encoding="utf-8", line_buffering=True))
            except Exception:
                # 最差情况下保持原样，避免把底层buffer搞坏
                pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import MultiAgentOrchestrator
from src.data.benchmark_builder import BenchmarkBuilder
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics
from src.models.model_client import MockModelClient
from src.models.qwen_client import create_qwen_clients_from_env

load_dotenv()

# 从主脚本导入配置和函数
from scripts.run_ablation_experiment import (
    ABLATION_CONFIGS,
    setup_logging,
    find_expert_prd,
    create_orchestrator,
    run_ablation_for_brief,
)


def main():
    parser = argparse.ArgumentParser(description="运行单个消融配置的实验")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        choices=[c["name"] for c in ABLATION_CONFIGS if c["name"] != "full_system"],
        help="消融配置名称",
    )
    parser.add_argument(
        "--brief-id",
        type=str,
        default=None,
        help="指定Brief ID（如果提供，只运行该Brief；否则运行所有15个Brief）",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试模式：只运行第一个Brief",
    )
    
    args = parser.parse_args()
    
    # 设置日志
    log_dir = Path("results/logs")
    logger = setup_logging(log_dir=log_dir, verbose=True)
    
    logger.info("=" * 70)
    logger.info(f"运行消融配置: {args.config}")
    if args.brief_id:
        logger.info(f"指定Brief: {args.brief_id}")
    if args.test:
        logger.info("测试模式: 只运行第一个Brief")
    logger.info("=" * 70)
    logger.info("")
    
    # 查找配置
    config = next((c for c in ABLATION_CONFIGS if c["name"] == args.config), None)
    if not config:
        logger.error(f"❌ 未找到配置: {args.config}")
        return
    
    logger.info(f"配置信息: {config['description']}")
    logger.info("")
    
    # 加载Brief列表
    benchmark_dir = Path("data/benchmark")
    builder = BenchmarkBuilder(benchmark_dir)
    prds = builder.list_prds()
    
    if not prds:
        logger.error("❌ 未找到Brief文件")
        return
    
    # 加载Brief
    briefs = []
    for prd_info in prds:
        if args.brief_id and prd_info["prd_id"] != args.brief_id:
            continue
        try:
            brief = builder.load_brief(prd_info["prd_id"])
            brief["prd_id"] = prd_info["prd_id"]
            briefs.append(brief)
        except Exception as e:
            logger.warning(f"  ⚠️  加载Brief失败: {prd_info['prd_id']} - {e}")
    
    if args.test:
        briefs = briefs[:1]
        logger.info(f"测试模式: 只运行第一个Brief")
    
    logger.info(f"✅ 将运行 {len(briefs)} 个Brief")
    logger.info("")
    
    # 输出目录
    output_dir = Path("results/ablation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行实验
    logger.info("=" * 70)
    logger.info("开始运行")
    logger.info("=" * 70)
    logger.info("")
    
    results = []
    start_time = time.time()
    
    for idx, brief in enumerate(briefs, 1):
        brief_id = brief.get("prd_id") or f"brief_{idx}"
        logger.info(f"[{idx}/{len(briefs)}] {brief_id}")

        # 如果PRD文件已存在，直接跳过（便于断点续跑，避免重复消耗API/时间）
        config_output_dir = output_dir / config["name"]
        existing_prd = config_output_dir / f"prd_{brief_id}.json"
        if existing_prd.exists():
            logger.info(f"  ⏭️  已存在，跳过生成，改为重算指标: {existing_prd}")
            try:
                prd_data = json.loads(existing_prd.read_text(encoding="utf-8"))
                basic = compute_all_metrics(prd_data)
                expert_prd_path = find_expert_prd(brief_id)
                extended = compute_all_extended_metrics(prd_data, expert_prd_path=expert_prd_path)
                metrics = {**basic, **extended}
                results.append(
                    {
                        "prd_id": brief_id,
                        "config_name": config["name"],
                        "prd_path": str(existing_prd),
                        "metrics": metrics,
                        # 已存在文件不再计入生成耗时
                        "generation_time": 0.0,
                        "expert_prd_path": str(expert_prd_path) if expert_prd_path else None,
                    }
                )
            except Exception as e:
                # 不中断整体流程：至少保证summary可被重建
                logger.warning(f"  ⚠️  已存在PRD但重算指标失败: {existing_prd} - {e}")
                results.append(
                    {
                        "prd_id": brief_id,
                        "config_name": config["name"],
                        "prd_path": str(existing_prd),
                        "metrics": {},
                        "generation_time": 0.0,
                        "expert_prd_path": None,
                        "error": str(e),
                    }
                )
            continue
        
        # 添加延迟
        if idx > 1:
            delay = 5.0
            logger.debug(f"  等待 {delay:.1f}秒以避免API限流...")
            time.sleep(delay)
        
        result = run_ablation_for_brief(brief, config, output_dir, logger)
        
        if result:
            results.append(result)
        
        logger.info("")
    
    # 保存结果
    total_time = time.time() - start_time
    config_output_dir = output_dir / config["name"]
    config_output_dir.mkdir(parents=True, exist_ok=True)

    # 以真实PRD文件存在性重新计算成功数，避免run_ablation_for_brief回退/异常导致summary假阳性
    brief_ids = [b.get("prd_id") for b in briefs if b.get("prd_id")]
    existing_prds = [
        bid for bid in brief_ids if (config_output_dir / f"prd_{bid}.json").exists()
    ]
    successful = len(existing_prds)
    failed = len(brief_ids) - successful
    # 同时过滤results，确保每个prd_id最多一条且prd_path匹配
    dedup = {}
    for r in results:
        rid = r.get("prd_id")
        rpath = r.get("prd_path")
        if not rid or rid not in existing_prds:
            continue
        expected_path = str(config_output_dir / f"prd_{rid}.json")
        if rpath and (Path(rpath).name == f"prd_{rid}.json"):
            dedup[rid] = r
        elif rid not in dedup:
            dedup[rid] = r
    results = [dedup[rid] for rid in sorted(dedup.keys())]
    
    metrics_summary = {
        "config": config,
        "total_briefs": len(briefs),
        "successful": successful,
        "failed": failed,
        "total_time_seconds": round(total_time, 2),
        "total_time_minutes": round(total_time / 60, 2),
        "results": results,
    }
    
    summary_path = config_output_dir / "metrics_summary.json"
    summary_path.write_text(
        json.dumps(metrics_summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    logger.info("=" * 70)
    logger.info("完成")
    logger.info("=" * 70)
    logger.info(f"成功: {successful}/{len(briefs)}")
    logger.info(f"耗时: {total_time/60:.1f}分钟")
    logger.info(f"结果已保存: {summary_path}")


if __name__ == "__main__":
    main()

