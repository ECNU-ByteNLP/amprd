"""
实验报告自动生成器

生成符合顶刊标准的实验报告，包括：
- 指标对比表格
- 统计检验结果
- 消融实验结果
- 可视化图表（可选）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class ExperimentReportGenerator:
    """实验报告生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comparison_report(
        self,
        baseline_results: List[Dict],
        ours_results: List[Dict],
        ablation_results: Optional[Dict] = None,
    ) -> Dict:
        """
        生成对比实验报告
        
        Args:
            baseline_results: 基线系统结果列表
            ours_results: 我们的系统结果列表
            ablation_results: 消融实验结果（可选）
        
        Returns:
            报告字典
        """
        report = {
            "experiment_setup": {
                "baseline_samples": len(baseline_results),
                "ours_samples": len(ours_results),
            },
            "metrics_comparison": self._compare_metrics(baseline_results, ours_results),
        }
        
        if ablation_results:
            report["ablation_analysis"] = ablation_results
        
        # 保存报告
        report_path = self.output_dir / "experiment_report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 生成Markdown报告
        md_report = self._generate_markdown_report(report)
        md_path = self.output_dir / "experiment_report.md"
        md_path.write_text(md_report, encoding="utf-8")
        
        return report
    
    def _compare_metrics(self, baseline: List[Dict], ours: List[Dict]) -> Dict:
        """对比指标"""
        # 聚合指标
        baseline_metrics = self._aggregate_metrics(baseline)
        ours_metrics = self._aggregate_metrics(ours)
        
        comparison = {}
        for metric in ours_metrics:
            if metric in baseline_metrics:
                comparison[metric] = {
                    "baseline_mean": baseline_metrics[metric],
                    "ours_mean": ours_metrics[metric],
                    "improvement": ours_metrics[metric] - baseline_metrics[metric],
                    "relative_improvement": (
                        (ours_metrics[metric] - baseline_metrics[metric]) / baseline_metrics[metric]
                        if baseline_metrics[metric] > 0 else 0.0
                    ),
                }
        
        return comparison
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict[str, float]:
        """聚合指标"""
        aggregated = {}
        counts = {}
        
        for result in results:
            metrics = result.get("metrics", {})
            for key, value in metrics.items():
                # 处理嵌套字典（如S_sem）
                if isinstance(value, dict):
                    if "overall" in value:
                        value = value["overall"]
                    else:
                        continue
                
                if isinstance(value, (int, float)):
                    aggregated.setdefault(key, 0.0)
                    aggregated[key] += value
                    counts.setdefault(key, 0)
                    counts[key] += 1
        
        # 计算平均值
        for key in aggregated:
            if counts[key] > 0:
                aggregated[key] /= counts[key]
        
        return aggregated
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成Markdown格式报告"""
        lines = ["# 实验报告", ""]
        
        # 实验设置
        lines.append("## 实验设置")
        setup = report.get("experiment_setup", {})
        lines.append(f"- 基线样本数: {setup.get('baseline_samples', 0)}")
        lines.append(f"- 我们的系统样本数: {setup.get('ours_samples', 0)}")
        lines.append("")
        
        # 指标对比
        lines.append("## 指标对比")
        lines.append("")
        lines.append("| 指标 | 基线 | 我们的系统 | 提升 | 相对提升 |")
        lines.append("|------|------|------------|------|----------|")
        
        comparison = report.get("metrics_comparison", {})
        for metric, data in comparison.items():
            baseline = data.get("baseline_mean", 0.0)
            ours = data.get("ours_mean", 0.0)
            improvement = data.get("improvement", 0.0)
            rel_improvement = data.get("relative_improvement", 0.0)
            
            lines.append(
                f"| {metric} | {baseline:.3f} | {ours:.3f} | "
                f"{improvement:+.3f} | {rel_improvement:+.1%} |"
            )
        
        lines.append("")
        
        # 消融分析
        if "ablation_analysis" in report:
            lines.append("## 消融实验分析")
            lines.append("")
            ablation = report["ablation_analysis"]
            for config_name, data in ablation.items():
                lines.append(f"### {config_name}")
                lines.append(f"**描述**: {data.get('description', '')}")
                lines.append("")
                lines.append("| 指标 | 基线 | 消融 | 差异 |")
                lines.append("|------|------|------|------|")
                
                metrics_diff = data.get("metrics_diff", {})
                for metric, diff_data in metrics_diff.items():
                    baseline = diff_data.get("baseline", 0.0)
                    ablation_val = diff_data.get("ablation", 0.0)
                    delta = diff_data.get("delta", 0.0)
                    lines.append(f"| {metric} | {baseline:.3f} | {ablation_val:.3f} | {delta:+.3f} |")
                
                lines.append("")
        
        return "\n".join(lines)

