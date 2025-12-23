"""
系统化消融实验框架

支持多维度消融实验：
1. Agent消融（禁用特定Agent）
2. 通信模式消融（blackboard vs async_queue）
3. Prompt优化消融
4. 模型消融
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.experiments.auto_eval import ExperimentResult, evaluate_system_outputs
from src.metrics.quality import compute_all_metrics
from src.metrics.extended_quality import compute_all_extended_metrics


@dataclass
class AblationConfig:
    """消融实验配置"""
    name: str
    description: str
    disabled_agents: List[str]
    communication_mode: str = "blackboard"
    use_extended_prompts: bool = True
    model_variant: str = "qwen"  # qwen, doubao, mock


class AblationSuite:
    """消融实验套件"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def define_ablation_configs(self) -> List[AblationConfig]:
        """定义所有消融实验配置"""
        configs = []
        
        # 基线：完整系统
        configs.append(AblationConfig(
            name="full_system",
            description="完整多智能体系统（基线）",
            disabled_agents=[],
            communication_mode="blackboard",
            use_extended_prompts=True,
        ))
        
        # Agent消融
        configs.append(AblationConfig(
            name="no_alignment",
            description="无AlignmentAgent（验证双语对齐的必要性）",
            disabled_agents=["AlignmentAgent"],
        ))
        
        configs.append(AblationConfig(
            name="no_vision",
            description="无VisionAgent（验证多模态的必要性）",
            disabled_agents=["VisionAgent"],
        ))
        
        configs.append(AblationConfig(
            name="no_table",
            description="无TableAgent（验证结构化表格的必要性）",
            disabled_agents=["TableAgent"],
        ))
        
        configs.append(AblationConfig(
            name="no_consistency",
            description="无ConsistencyAgent（验证一致性检查的必要性）",
            disabled_agents=["ConsistencyAgent"],
        ))
        
        # 通信模式消融
        configs.append(AblationConfig(
            name="async_queue",
            description="异步队列通信模式",
            disabled_agents=[],
            communication_mode="async_queue",
        ))
        
        # 模型消融
        configs.append(AblationConfig(
            name="mock_model",
            description="使用Mock模型（验证真实模型的重要性）",
            disabled_agents=[],
            model_variant="mock",
        ))
        
        return configs
    
    def run_ablation_experiment(
        self,
        config: AblationConfig,
        brief_paths: List[Path],
        orchestrator_factory,
    ) -> Dict:
        """
        运行单个消融实验
        
        Args:
            config: 消融配置
            brief_paths: Brief文件路径列表
            orchestrator_factory: 创建orchestrator的函数，接受AblationConfig参数
        
        Returns:
            实验结果字典
        """
        results = []
        
        for brief_path in brief_paths:
            # 加载Brief
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
            
            # 创建orchestrator（根据配置）
            orchestrator = orchestrator_factory(config)
            
            # 运行生成
            state = orchestrator.run({"brief": brief})
            
            # 获取生成的PRD路径
            prd_path = Path(state.get("quality", {}).get("artifact_path", ""))
            if not prd_path.exists():
                continue
            
            # 计算指标
            prd = json.loads(prd_path.read_text(encoding="utf-8"))
            basic_metrics = compute_all_metrics(prd)
            extended_metrics = compute_all_extended_metrics(prd)
            
            # 合并指标
            all_metrics = {**basic_metrics, **extended_metrics}
            
            results.append({
                "brief": str(brief_path),
                "prd": str(prd_path),
                "metrics": all_metrics,
            })
        
        # 保存结果
        result_path = self.output_dir / f"ablation_{config.name}.json"
        result_path.write_text(
            json.dumps({
                "config": {
                    "name": config.name,
                    "description": config.description,
                    "disabled_agents": config.disabled_agents,
                    "communication_mode": config.communication_mode,
                },
                "results": results,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return {
            "config": config.name,
            "results": results,
            "result_path": str(result_path),
        }
    
    def compare_ablation_results(self) -> Dict:
        """对比所有消融实验结果"""
        result_files = list(self.output_dir.glob("ablation_*.json"))
        
        if not result_files:
            return {}
        
        # 加载所有结果
        all_results = {}
        for result_file in result_files:
            data = json.loads(result_file.read_text(encoding="utf-8"))
            config_name = data["config"]["name"]
            all_results[config_name] = data
        
        # 以full_system为基线进行对比
        baseline = all_results.get("full_system")
        if not baseline:
            return {"error": "Baseline (full_system) not found"}
        
        comparison = {}
        
        for config_name, results in all_results.items():
            if config_name == "full_system":
                continue
            
            # 计算平均指标
            baseline_metrics = self._aggregate_metrics(baseline["results"])
            ablation_metrics = self._aggregate_metrics(results["results"])
            
            # 计算差异
            diff = {}
            for metric in baseline_metrics:
                if metric in ablation_metrics:
                    baseline_mean = baseline_metrics[metric]
                    ablation_mean = ablation_metrics[metric]
                    diff[metric] = {
                        "baseline": baseline_mean,
                        "ablation": ablation_mean,
                        "delta": ablation_mean - baseline_mean,
                        "relative_change": (ablation_mean - baseline_mean) / baseline_mean if baseline_mean > 0 else 0.0,
                    }
            
            comparison[config_name] = {
                "description": results["config"]["description"],
                "metrics_diff": diff,
            }
        
        # 保存对比结果
        comparison_path = self.output_dir / "ablation_comparison.json"
        comparison_path.write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return comparison
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict[str, float]:
        """聚合多个结果的指标"""
        aggregated = {}
        metric_counts = {}
        
        for result in results:
            metrics = result.get("metrics", {})
            for key, value in metrics.items():
                if isinstance(value, dict):
                    # 对于嵌套字典（如S_sem），取overall值
                    if "overall" in value:
                        value = value["overall"]
                    else:
                        continue
                
                if isinstance(value, (int, float)):
                    aggregated.setdefault(key, 0.0)
                    aggregated[key] += value
                    metric_counts.setdefault(key, 0)
                    metric_counts[key] += 1
        
        # 计算平均值
        for key in aggregated:
            if metric_counts[key] > 0:
                aggregated[key] /= metric_counts[key]
        
        return aggregated

