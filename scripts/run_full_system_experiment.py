"""
运行完整系统实验

使用Few-shot和S_expert更新后的完整多智能体系统，为15个Brief生成PRD。

特点：
- 使用Few-shot学习（真实PRD示例）
- 使用S_expert指标（专家对齐度）
- 多智能体协作生成
- 多模态内容生成
- 双语对齐

输出：
- results/full_system/prd_*.json (15个文件)
- results/full_system/metrics_summary.json
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


# 配置日志
def setup_logging(log_dir: Path = None, verbose: bool = True):
    """
    配置日志系统
    
    Args:
        log_dir: 日志文件目录（如果为None，只输出到控制台）
        verbose: 是否显示详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 创建日志格式
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # 如果指定了日志目录，也输出到文件
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"full_system_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        print(f"📝 日志文件: {log_file}")
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True,  # 强制重新配置
    )
    
    return logging.getLogger("FullSystemExperiment")


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
            logging.getLogger("FullSystemExperiment").warning(f"读取中文PRD映射文件失败: {e}")
    
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
            logging.getLogger("FullSystemExperiment").warning(f"读取英文PRD映射文件失败: {e}")
    
    # 如果没有映射文件，尝试默认路径
    expert_dir = Path("data/expert_prds")
    if expert_dir.exists():
        expert_path = expert_dir / f"{prd_id}.json"
        if expert_path.exists():
            return expert_path
    
    return None


def main():
    # 设置日志（输出到控制台和文件）
    log_dir = Path("results/logs")
    logger = setup_logging(log_dir=log_dir, verbose=True)
    
    logger.info("=" * 70)
    logger.info("完整系统实验 - 使用Few-shot和S_expert更新后的系统")
    logger.info("为15个Brief生成完整系统的PRD")
    logger.info("=" * 70)
    logger.info("")
    
    # 加载Brief列表
    benchmark_dir = Path("data/benchmark")
    builder = BenchmarkBuilder(benchmark_dir)
    prds = builder.list_prds()
    
    if not prds:
        logger.error("❌ 未找到Brief文件")
        return
    
    logger.info(f"📋 加载了 {len(prds)} 个Brief")
    
    # 加载所有Brief
    briefs = []
    for prd_info in prds:
        try:
            brief = builder.load_brief(prd_info["prd_id"])
            brief["prd_id"] = prd_info["prd_id"]  # 确保有prd_id
            briefs.append(brief)
        except Exception as e:
            logger.warning(f"  ⚠️  加载Brief失败: {prd_info['prd_id']} - {e}")
    
    logger.info(f"✅ 成功加载 {len(briefs)} 个Brief")
    logger.info("")
    
    # 初始化完整系统（多智能体协作）
    output_dir = Path("results/full_system")
    logger.info(f"初始化完整系统（多智能体协作）...")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"特性:")
    logger.info(f"  - ✅ Few-shot学习（真实PRD示例）")
    logger.info(f"  - ✅ S_expert指标（专家对齐度）")
    logger.info(f"  - ✅ 多智能体协作")
    logger.info(f"  - ✅ 多模态内容生成")
    logger.info(f"  - ✅ 双语对齐")
    logger.info("")
    
    orchestrator = MultiAgentOrchestrator(persist_dir=output_dir)
    
    # 运行完整系统生成
    logger.info("=" * 70)
    logger.info("开始生成完整系统PRD")
    logger.info("=" * 70)
    logger.info("")
    
    generated_count = 0
    failed_count = 0
    results = []
    start_time = time.time()
    
    for idx, brief in enumerate(briefs, 1):
        brief_id = brief.get("prd_id") or f"brief_{idx}"
        logger.info(f"[{idx}/{len(briefs)}] 处理: {brief_id}")
        
        # 在批量处理时添加延迟，避免API限流
        # 根据处理进度动态调整延迟：前面可以快一点，后面慢一点
        if idx > 1:
            if idx <= 5:
                delay = 3.0  # 前5个：3秒延迟
            elif idx <= 10:
                delay = 8.0  # 6-10个：8秒延迟（避免限流）
            else:
                delay = 12.0  # 11个以后：12秒延迟（更保守，避免连续失败）
            logger.debug(f"  等待 {delay:.1f}秒以避免API限流...")
            time.sleep(delay)
        
        try:
            # 生成PRD（使用完整系统）
            gen_start = time.time()
            state = orchestrator.run({"brief": brief})
            gen_time = time.time() - gen_start
            
            # 查找生成的PRD文件
            prd_path = state.get("quality", {}).get("artifact_path")
            if prd_path and Path(prd_path).exists():
                # 加载生成的PRD
                prd_json = json.loads(Path(prd_path).read_text(encoding="utf-8"))
                
                # 查找对应的专家PRD（如果存在）
                expert_prd_path = find_expert_prd(brief_id)
                
                # 计算质量指标
                logger.debug(f"  计算质量指标...")
                basic_metrics = compute_all_metrics(prd_json)
                extended_metrics = compute_all_extended_metrics(prd_json, expert_prd_path=expert_prd_path)
                all_metrics = {**basic_metrics, **extended_metrics}
                
                results.append({
                    "prd_id": brief_id,
                    "prd_path": str(prd_path),
                    "metrics": all_metrics,
                    "generation_time": round(gen_time, 2),
                    "expert_prd_path": str(expert_prd_path) if expert_prd_path else None,
                })
                
                logger.info(f"  ✅ 已保存: {Path(prd_path).name} (生成耗时: {gen_time:.2f}秒)")
                
                # 显示关键指标
                s_comp = all_metrics.get("S_comp", 0)
                s_mm = all_metrics.get("S_mm", {}).get("overall", 0) if isinstance(all_metrics.get("S_mm"), dict) else all_metrics.get("S_mm", 0)
                s_bi = all_metrics.get("S_bi", 0)
                logger.debug(f"    关键指标: S_comp={s_comp:.3f}, S_mm={s_mm:.3f}, S_bi={s_bi:.3f}")
                
                generated_count += 1
            else:
                logger.warning(f"  ⚠️  未找到PRD文件（生成可能失败）")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"  ❌ 错误: {str(e)[:100]}", exc_info=True)
            failed_count += 1
            # 继续处理下一个，不中断整个流程
            continue
    
    total_time = time.time() - start_time
    
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"完整系统生成完成: {generated_count}/{len(briefs)} 成功 (总耗时: {total_time:.2f}秒)")
    if failed_count > 0:
        logger.warning(f"  ⚠️  失败 {failed_count} 个PRD（可能是网络超时，请检查网络连接或稍后重试）")
    logger.info("=" * 70)
    logger.info("")
    
    # 保存指标汇总
    if results:
        logger.info("计算平均质量指标...")
        metrics_summary_path = output_dir / "metrics_summary.json"
        metrics_summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 计算平均指标
        metric_names = [
            "S_comp", "S_mm", "S_tab", "S_bi", "S_var",
            "S_sem", "S_biz", "S_tech", "S_risk", "S_expert",
            "S_ps", "S_uj", "S_hyp"
        ]
        
        avg_metrics = {}
        for metric_name in metric_names:
            values = []
            for r in results:
                metric_value = r["metrics"].get(metric_name)
                if isinstance(metric_value, dict):
                    metric_value = metric_value.get("overall", 0)
                if isinstance(metric_value, (int, float)):
                    values.append(metric_value)
            
            if values:
                avg_metrics[metric_name] = {
                    "mean": round(sum(values) / len(values), 4),
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "count": len(values),
                }
        
        summary = {
            "total_briefs": len(briefs),
            "success_count": generated_count,
            "failed_count": failed_count,
            "total_time_seconds": round(total_time, 2),
            "average_generation_time": round(sum(r["generation_time"] for r in results) / len(results), 2) if results else 0,
            "average_metrics": avg_metrics,
            "detailed_results": results,
        }
        
        metrics_summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        logger.info(f"✅ 指标汇总已保存: {metrics_summary_path}")
        logger.info("")
        logger.info("📊 平均质量指标:")
        for metric_name, stats in avg_metrics.items():
            logger.info(f"  {metric_name}: {stats['mean']:.3f} (范围: {stats['min']:.3f} - {stats['max']:.3f})")
        logger.info("")
    
    logger.info("=" * 70)
    logger.info("完整系统实验完成！")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📁 结果文件:")
    logger.info(f"  - results/full_system/prd_*.json ({generated_count}个文件)")
    logger.info(f"  - results/full_system/metrics_summary.json")
    logger.info(f"  - results/logs/full_system_experiment_*.log")
    logger.info("")
    logger.info("📈 下一步:")
    logger.info("  1. 对比完整系统 vs 基线系统（使用统计分析）")
    logger.info("  2. 运行消融实验（验证各Agent的必要性）")
    logger.info("  3. 生成完整实验报告")
    logger.info("")


if __name__ == "__main__":
    main()

