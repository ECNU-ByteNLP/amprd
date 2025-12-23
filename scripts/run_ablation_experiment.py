"""
运行消融实验

为15个Brief运行所有消融配置，验证各个Agent的必要性。

消融配置（7个）：
1. full_system: 完整系统（对照组，已有15个PRD）
2. no_alignment: 去掉双语对齐Agent
3. no_vision: 去掉视觉生成Agent
4. no_table: 去掉表格生成Agent
5. no_consistency: 去掉一致性检查Agent
6. async_queue: 异步队列通信模式
7. mock_model: 使用Mock模型

总工作量：6个配置 × 15个Brief = 90个PRD（full_system已有，无需重新生成）
预计时间：约27小时
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
from src.models.model_client import MockModelClient
from src.models.qwen_client import create_qwen_clients_from_env

# 加载环境变量
load_dotenv()


# 配置日志
def setup_logging(log_dir: Path = None, verbose: bool = True):
    """配置日志系统"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    log_file = None
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"ablation_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True,
    )
    
    logger = logging.getLogger("AblationExperiment")
    if log_file:
        logger.info(f"📝 日志文件: {log_file}")
    
    return logger


def find_expert_prd(prd_id: str) -> Optional[Path]:
    """根据PRD ID查找对应的专家PRD（真实PRD参考）"""
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
        except Exception as e:
            logging.getLogger("AblationExperiment").warning(f"读取中文PRD映射文件失败: {e}")
    
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
            logging.getLogger("AblationExperiment").warning(f"读取英文PRD映射文件失败: {e}")
    
    return None


# 定义消融配置
ABLATION_CONFIGS = [
    {
        "name": "full_system",
        "disabled_agents": [],
        "communication_mode": "blackboard",
        "use_mock_models": False,
        "description": "完整系统（对照组）",
    },
    {
        "name": "no_alignment",
        "disabled_agents": ["AlignmentAgent"],
        "communication_mode": "blackboard",
        "use_mock_models": False,
        "description": "去掉双语对齐Agent",
    },
    {
        "name": "no_vision",
        "disabled_agents": ["VisionAgent"],
        "communication_mode": "blackboard",
        "use_mock_models": False,
        "description": "去掉视觉生成Agent",
    },
    {
        "name": "no_table",
        "disabled_agents": ["TableAgent"],
        "communication_mode": "blackboard",
        "use_mock_models": False,
        "description": "去掉表格生成Agent",
    },
    {
        "name": "no_consistency",
        "disabled_agents": ["ConsistencyAgent"],
        "communication_mode": "blackboard",
        "use_mock_models": False,
        "description": "去掉一致性检查Agent",
    },
    {
        "name": "async_queue",
        "disabled_agents": [],
        "communication_mode": "async_queue",
        "use_mock_models": False,
        "description": "异步队列通信模式",
    },
    {
        "name": "mock_model",
        "disabled_agents": [],
        "communication_mode": "blackboard",
        "use_mock_models": True,
        "description": "使用Mock模型",
    },
]


def create_orchestrator(config: Dict, output_dir: Path):
    """根据配置创建Orchestrator"""
    if config["use_mock_models"]:
        text_model_cn = MockModelClient()
        text_model_en = MockModelClient()
        vision_model = MockModelClient()
    else:
        env_text_cn, env_text_en, env_vision = create_qwen_clients_from_env()
        text_model_cn = env_text_cn
        text_model_en = env_text_en
        vision_model = env_vision
    
    orchestrator = MultiAgentOrchestrator(
        text_model_cn=text_model_cn,
        text_model_en=text_model_en,
        vision_model=vision_model,
        persist_dir=output_dir / config["name"],
        disabled_agents=config["disabled_agents"],
        communication_mode=config["communication_mode"],
    )
    
    return orchestrator


def run_ablation_for_brief(
    brief: Dict,
    config: Dict,
    output_dir: Path,
    logger: logging.Logger,
) -> Optional[Dict]:
    """为单个Brief运行单个消融配置"""
    brief_id = brief.get("prd_id") or "unknown"
    
    try:
        # 创建Orchestrator
        orchestrator = create_orchestrator(config, output_dir)
        
        # 运行生成
        gen_start = time.time()
        state = orchestrator.run({"brief": brief})
        gen_time = time.time() - gen_start
        
        # 查找生成的PRD文件
        prd_path = state.get("quality", {}).get("artifact_path")
        
        config_output_dir = output_dir / config["name"]

        # 如果artifact_path不存在或文件不存在，只允许两种补救方式：
        # 1) 查找“精确匹配”本brief_id的文件 prd_{brief_id}.json
        # 2) 基于blackboard state + plan 重建PRD并落盘（禁止回退到任意 prd_*.json，避免误把别的brief当作成功）
        if not prd_path or not Path(prd_path).exists():
            exact = config_output_dir / f"prd_{brief_id}.json"
            if exact.exists():
                prd_path = exact
                logger.info(f"  📄 找到PRD文件: {prd_path}")
            else:
                plan = (
                    state.get("planning", {}).get("structure")
                    if isinstance(state.get("planning"), dict)
                    else None
                )
                if isinstance(plan, dict) and state.get("sections"):
                    logger.info("  🔧 artifact_path缺失，尝试从blackboard重建PRD并保存...")
                    from src.agents.assembler import AssemblerAgent

                    config_output_dir.mkdir(parents=True, exist_ok=True)
                    assembler = AssemblerAgent(config_output_dir)
                    bundle = assembler._build_bundle(plan, state)
                    rebuilt_path = assembler._persist(bundle)

                    expected = config_output_dir / f"prd_{brief_id}.json"
                    # Assembler会按plan.prd_id命名；若与brief_id不一致，则认为本次不可用于benchmark对齐
                    if expected.exists():
                        prd_path = expected
                    elif Path(rebuilt_path).exists() and Path(rebuilt_path).name == expected.name:
                        prd_path = rebuilt_path
                    else:
                        logger.warning(
                            f"  ❌ 重建输出文件名不匹配：期望 {expected.name}，实际 {Path(rebuilt_path).name}"
                        )
                        return None
                    logger.info(f"  ✅ 已重建并保存PRD: {prd_path}")
                else:
                    logger.warning(f"  ❌ 未找到PRD文件且无法重建 (目录: {config_output_dir})")
                    return None
        
        # 加载生成的PRD
        prd_json = json.loads(Path(prd_path).read_text(encoding="utf-8"))
        
        # 查找对应的专家PRD
        expert_prd_path = find_expert_prd(brief_id)
        
        # 计算质量指标
        basic_metrics = compute_all_metrics(prd_json)
        extended_metrics = compute_all_extended_metrics(prd_json, expert_prd_path=expert_prd_path)
        all_metrics = {**basic_metrics, **extended_metrics}
        
        result = {
            "prd_id": brief_id,
            "config_name": config["name"],
            "prd_path": str(prd_path),
            "metrics": all_metrics,
            "generation_time": round(gen_time, 2),
            "expert_prd_path": str(expert_prd_path) if expert_prd_path else None,
        }
        
        logger.info(f"  ✅ 成功 (耗时: {gen_time:.2f}秒)")
        
        # 显示关键指标
        s_comp = all_metrics.get("S_comp", 0)
        s_mm = all_metrics.get("S_mm", {}).get("overall", 0) if isinstance(all_metrics.get("S_mm"), dict) else all_metrics.get("S_mm", 0)
        s_bi = all_metrics.get("S_bi", 0)
        logger.debug(f"    关键指标: S_comp={s_comp:.3f}, S_mm={s_mm:.3f}, S_bi={s_bi:.3f}")
        
        return result
        
    except Exception as e:
        logger.error(f"  ❌ 失败: {e}", exc_info=True)
        return None


def main():
    # 设置日志
    log_dir = Path("results/logs")
    logger = setup_logging(log_dir=log_dir, verbose=True)
    
    logger.info("=" * 70)
    logger.info("消融实验 - 验证各个Agent的必要性")
    logger.info("为15个Brief运行所有消融配置（90个PRD）")
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
            brief["prd_id"] = prd_info["prd_id"]
            briefs.append(brief)
        except Exception as e:
            logger.warning(f"  ⚠️  加载Brief失败: {prd_info['prd_id']} - {e}")
    
    logger.info(f"✅ 成功加载 {len(briefs)} 个Brief")
    logger.info("")
    
    # 检查full_system是否已有结果
    full_system_dir = Path("results/full_system")
    full_system_exists = full_system_dir.exists() and any(full_system_dir.glob("prd_*.json"))
    
    if full_system_exists:
        logger.info("✅ 检测到full_system已有结果，将跳过该配置")
        logger.info("   如需重新生成，请先删除 results/full_system/ 目录")
        logger.info("")
    
    # 确定需要运行的配置
    configs_to_run = ABLATION_CONFIGS.copy()
    if full_system_exists:
        configs_to_run = [c for c in configs_to_run if c["name"] != "full_system"]
        logger.info(f"📊 将运行 {len(configs_to_run)} 个配置（跳过full_system）")
    else:
        logger.info(f"📊 将运行 {len(configs_to_run)} 个配置")
    
    logger.info("")
    
    # 输出目录
    output_dir = Path("results/ablation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行消融实验
    logger.info("=" * 70)
    logger.info("开始运行消融实验")
    logger.info("=" * 70)
    logger.info("")
    
    all_results = []
    total_prds = len(briefs) * len(configs_to_run)
    current_prd = 0
    start_time = time.time()
    
    for config_idx, config in enumerate(configs_to_run, 1):
        logger.info(f"[配置 {config_idx}/{len(configs_to_run)}] {config['name']}: {config['description']}")
        logger.info("-" * 70)
        
        config_results = []
        config_start_time = time.time()
        
        for brief_idx, brief in enumerate(briefs, 1):
            brief_id = brief.get("prd_id") or f"brief_{brief_idx}"
            current_prd += 1
            
            logger.info(f"  [{current_prd}/{total_prds}] {config['name']} - {brief_id}")
            
            # 添加延迟，避免API限流
            if current_prd > 1:
                # 根据进度动态调整延迟
                if current_prd <= 10:
                    delay = 5.0
                elif current_prd <= 30:
                    delay = 8.0
                else:
                    delay = 12.0
                logger.debug(f"    等待 {delay:.1f}秒以避免API限流...")
                time.sleep(delay)
            
            result = run_ablation_for_brief(brief, config, output_dir, logger)
            
            if result:
                config_results.append(result)
                all_results.append(result)
            
            logger.info("")
        
        config_time = time.time() - config_start_time
        logger.info(f"  ✅ 配置 {config['name']} 完成: {len(config_results)}/{len(briefs)} 成功 (耗时: {config_time/60:.1f}分钟)")
        logger.info("")
        
        # 保存该配置的结果
        config_output_dir = output_dir / config["name"]
        config_output_dir.mkdir(parents=True, exist_ok=True)
        
        metrics_summary = {
            "config": config,
            "total_briefs": len(briefs),
            "successful": len(config_results),
            "failed": len(briefs) - len(config_results),
            "results": config_results,
        }
        
        summary_path = config_output_dir / "metrics_summary.json"
        summary_path.write_text(
            json.dumps(metrics_summary, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"  💾 已保存: {summary_path}")
        logger.info("")
    
    # 保存所有结果
    total_time = time.time() - start_time
    ablation_summary = {
        "experiment_info": {
            "total_configs": len(configs_to_run),
            "total_briefs": len(briefs),
            "total_prds": len(all_results),
            "total_time_seconds": round(total_time, 2),
            "total_time_hours": round(total_time / 3600, 2),
            "average_time_per_prd": round(total_time / len(all_results), 2) if all_results else 0,
        },
        "configs": [c for c in ABLATION_CONFIGS if c["name"] in [r["config_name"] for r in all_results]],
        "results": all_results,
    }
    
    summary_path = output_dir / "ablation_summary.json"
    summary_path.write_text(
        json.dumps(ablation_summary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    logger.info("=" * 70)
    logger.info("消融实验完成")
    logger.info("=" * 70)
    logger.info(f"总配置数: {len(configs_to_run)}")
    logger.info(f"总Brief数: {len(briefs)}")
    logger.info(f"成功生成: {len(all_results)}/{total_prds} PRD")
    logger.info(f"总耗时: {total_time/3600:.2f}小时 ({total_time/60:.1f}分钟)")
    logger.info(f"平均耗时: {total_time/len(all_results):.2f}秒/PRD" if all_results else "N/A")
    logger.info(f"结果已保存: {summary_path}")
    logger.info("")
    logger.info("下一步: 运行 scripts/analyze_ablation_results.py 分析结果")


if __name__ == "__main__":
    main()

