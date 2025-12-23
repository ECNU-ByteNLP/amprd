"""
运行基线系统实验

为15个Brief生成3个基线系统的PRD：
1. Baseline-TXT（TextOnly）：单一LLM生成纯文本PRD
2. Baseline-TPL（Template）：基于固定模板的规则系统
3. Baseline-RET（Retrieval）：检索增强生成

输出：
- results/baseline_text_only/prd_*.json
- results/baseline_template/prd_*.json
- results/baseline_retrieval/prd_*.json
"""

import sys
import io
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.baselines.text_only import generate_prd_text_only
from src.baselines.template import generate_prd_template
from src.baselines.retrieval import RetrievalBaseline
from src.data.benchmark_builder import BenchmarkBuilder
from src.models.qwen_client import create_qwen_clients_from_env

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
        log_file = log_dir / f"baseline_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        print(f"📝 日志文件: {log_file}")
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True,  # 强制重新配置
    )
    
    return logging.getLogger("BaselineExperiment")


def run_baseline_text_only(briefs: List[Dict], output_dir: Path) -> Dict[str, str]:
    """
    运行Baseline-TXT（TextOnly）
    
    Args:
        briefs: Brief列表
        output_dir: 输出目录
    
    Returns:
        Dict: {brief_id: output_path}
    """
    logger = logging.getLogger("BaselineExperiment.TextOnly")
    
    logger.info("=" * 70)
    logger.info("运行 Baseline-TXT（TextOnly）")
    logger.info("=" * 70)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    
    # 创建Qwen客户端（如果可用）
    text_cn, _, _ = create_qwen_clients_from_env()
    model = text_cn  # 使用Qwen模型（如果配置了），否则使用Mock
    
    if model and hasattr(model, "name"):
        logger.info(f"使用模型: {model.name}")
    else:
        logger.warning("使用Mock模型（未配置Qwen API密钥）")
    
    results = {}
    start_time = time.time()
    
    for idx, brief in enumerate(briefs, 1):
        brief_id = brief.get("prd_id") or brief.get("brief_id") or f"brief_{idx}"
        logger.info(f"[{idx}/{len(briefs)}] 处理: {brief_id}")
        
        try:
            # 生成PRD
            gen_start = time.time()
            prd_json = generate_prd_text_only(brief, model=model)
            gen_time = time.time() - gen_start
            
            # 保存结果
            output_path = output_dir / f"prd_{brief_id}.json"
            output_path.write_text(
                json.dumps(prd_json, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            results[brief_id] = str(output_path)
            logger.info(f"  ✅ 已保存: {output_path.name} (生成耗时: {gen_time:.2f}秒)")
            
            # 添加延迟，避免API限流
            if idx < len(briefs) and model and hasattr(model, "name") and "qwen" in model.name.lower():
                delay = 2.0 if idx <= 5 else (5.0 if idx <= 10 else 8.0)
                logger.debug(f"  等待 {delay:.1f}秒以避免API限流...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"  ❌ 错误: {str(e)[:100]}", exc_info=True)
            results[brief_id] = f"error: {str(e)[:100]}"
    
    total_time = time.time() - start_time
    success_count = len([r for r in results.values() if not r.startswith('error')])
    logger.info(f"✅ Baseline-TXT 完成: {success_count}/{len(briefs)} 成功 (总耗时: {total_time:.2f}秒)")
    return results


def run_baseline_template(briefs: List[Dict], output_dir: Path) -> Dict[str, str]:
    """
    运行Baseline-TPL（Template）
    
    Args:
        briefs: Brief列表
        output_dir: 输出目录
    
    Returns:
        Dict: {brief_id: output_path}
    """
    logger = logging.getLogger("BaselineExperiment.Template")
    
    logger.info("=" * 70)
    logger.info("运行 Baseline-TPL（Template）")
    logger.info("=" * 70)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    logger.info("使用固定模板规则系统（无需LLM）")
    
    results = {}
    start_time = time.time()
    
    for idx, brief in enumerate(briefs, 1):
        brief_id = brief.get("prd_id") or brief.get("brief_id") or f"brief_{idx}"
        logger.info(f"[{idx}/{len(briefs)}] 处理: {brief_id}")
        
        try:
            # 生成PRD（无需模型）
            gen_start = time.time()
            prd_json = generate_prd_template(brief)
            gen_time = time.time() - gen_start
            
            # 保存结果
            output_path = output_dir / f"prd_{brief_id}.json"
            output_path.write_text(
                json.dumps(prd_json, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            results[brief_id] = str(output_path)
            logger.info(f"  ✅ 已保存: {output_path.name} (生成耗时: {gen_time:.3f}秒)")
            
        except Exception as e:
            logger.error(f"  ❌ 错误: {str(e)[:100]}", exc_info=True)
            results[brief_id] = f"error: {str(e)[:100]}"
    
    total_time = time.time() - start_time
    success_count = len([r for r in results.values() if not r.startswith('error')])
    logger.info(f"✅ Baseline-TPL 完成: {success_count}/{len(briefs)} 成功 (总耗时: {total_time:.2f}秒)")
    return results


def run_baseline_retrieval(briefs: List[Dict], output_dir: Path) -> Dict[str, str]:
    """
    运行Baseline-RET（Retrieval）
    
    Args:
        briefs: Brief列表
        output_dir: 输出目录
    
    Returns:
        Dict: {brief_id: output_path}
    """
    logger = logging.getLogger("BaselineExperiment.Retrieval")
    
    logger.info("=" * 70)
    logger.info("运行 Baseline-RET（Retrieval）")
    logger.info("=" * 70)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    
    # 初始化检索基线（使用中文PRD语料库）
    corpus_dir = PROJECT_ROOT / "data" / "chinese_prds" / "processed"
    try:
        logger.info(f"初始化检索基线，语料库: {corpus_dir}")
        retrieval_baseline = RetrievalBaseline(corpus_dir=corpus_dir)
        logger.info(f"  ✅ 检索基线已初始化，索引大小: {len(retrieval_baseline.index)} 个PRD")
    except Exception as e:
        logger.warning(f"  ⚠️  检索基线初始化失败: {e}")
        logger.warning(f"  ⚠️  将使用空检索结果（回退到TextOnly模式）")
        retrieval_baseline = None
    
    # 创建Qwen客户端（如果可用）
    text_cn, _, _ = create_qwen_clients_from_env()
    model = text_cn  # 使用Qwen模型（如果配置了），否则使用Mock
    
    if model and hasattr(model, "name"):
        logger.info(f"使用模型: {model.name}")
    else:
        logger.warning("使用Mock模型（未配置Qwen API密钥）")
    
    results = {}
    start_time = time.time()
    
    for idx, brief in enumerate(briefs, 1):
        brief_id = brief.get("prd_id") or brief.get("brief_id") or f"brief_{idx}"
        logger.info(f"[{idx}/{len(briefs)}] 处理: {brief_id}")
        
        try:
            if retrieval_baseline:
                # 使用检索基线生成PRD
                gen_start = time.time()
                prd_json = retrieval_baseline.generate(brief, model=model)
                gen_time = time.time() - gen_start
                
                # 记录检索到的参考数量
                retrieved_count = prd_json.get("metadata", {}).get("retrieved_count", 0)
                logger.debug(f"  检索到 {retrieved_count} 个相似PRD参考")
            else:
                # 如果检索基线不可用，回退到简单生成
                logger.debug("  使用TextOnly模式（检索基线不可用）")
                gen_start = time.time()
                from src.baselines.text_only import generate_prd_text_only
                prd_json = generate_prd_text_only(brief, model=model)
                prd_json["metadata"]["baseline_type"] = "retrieval_fallback"
                gen_time = time.time() - gen_start
            
            # 保存结果
            output_path = output_dir / f"prd_{brief_id}.json"
            output_path.write_text(
                json.dumps(prd_json, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            results[brief_id] = str(output_path)
            logger.info(f"  ✅ 已保存: {output_path.name} (生成耗时: {gen_time:.2f}秒)")
            
            # 添加延迟，避免API限流
            if idx < len(briefs) and model and hasattr(model, "name") and "qwen" in model.name.lower():
                delay = 2.0 if idx <= 5 else (5.0 if idx <= 10 else 8.0)
                logger.debug(f"  等待 {delay:.1f}秒以避免API限流...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"  ❌ 错误: {str(e)[:100]}", exc_info=True)
            results[brief_id] = f"error: {str(e)[:100]}"
    
    total_time = time.time() - start_time
    success_count = len([r for r in results.values() if not r.startswith('error')])
    logger.info(f"✅ Baseline-RET 完成: {success_count}/{len(briefs)} 成功 (总耗时: {total_time:.2f}秒)")
    return results


def main():
    # 设置日志（输出到控制台和文件）
    log_dir = Path("results/logs")
    logger = setup_logging(log_dir=log_dir, verbose=True)
    
    logger.info("=" * 70)
    logger.info("基线系统实验 - 为15个Brief生成3个基线系统的PRD")
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
    
    # 运行三个基线系统
    results = {}
    
    # 1. Baseline-TXT
    results["text_only"] = run_baseline_text_only(
        briefs,
        output_dir=Path("results/baseline_text_only")
    )
    
    # 2. Baseline-TPL
    results["template"] = run_baseline_template(
        briefs,
        output_dir=Path("results/baseline_template")
    )
    
    # 3. Baseline-RET
    results["retrieval"] = run_baseline_retrieval(
        briefs,
        output_dir=Path("results/baseline_retrieval")
    )
    
    # 保存结果摘要
    summary = {
        "total_briefs": len(briefs),
        "baselines": {
            "text_only": {
                "success": len([r for r in results["text_only"].values() if not r.startswith("error")]),
                "total": len(results["text_only"]),
            },
            "template": {
                "success": len([r for r in results["template"].values() if not r.startswith("error")]),
                "total": len(results["template"]),
            },
            "retrieval": {
                "success": len([r for r in results["retrieval"].values() if not r.startswith("error")]),
                "total": len(results["retrieval"]),
            },
        },
        "results": results,
    }
    
    summary_path = Path("results/baseline_experiment_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("基线系统实验完成！")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📊 结果摘要:")
    logger.info(f"  Baseline-TXT: {summary['baselines']['text_only']['success']}/{summary['baselines']['text_only']['total']} 成功")
    logger.info(f"  Baseline-TPL: {summary['baselines']['template']['success']}/{summary['baselines']['template']['total']} 成功")
    logger.info(f"  Baseline-RET: {summary['baselines']['retrieval']['success']}/{summary['baselines']['retrieval']['total']} 成功")
    logger.info("")
    logger.info(f"📁 结果文件:")
    logger.info(f"  - results/baseline_text_only/prd_*.json")
    logger.info(f"  - results/baseline_template/prd_*.json")
    logger.info(f"  - results/baseline_retrieval/prd_*.json")
    logger.info(f"  - results/baseline_experiment_summary.json")
    logger.info(f"  - results/logs/baseline_experiment_*.log")
    logger.info("")


if __name__ == "__main__":
    main()

