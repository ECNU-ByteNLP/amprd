"""
验证15个Brief的质量和可行性

检查项：
1. 结构完整性（必需字段）
2. 内容质量（是否足够详细）
3. 领域分布（是否覆盖多个领域）
4. 复杂度评估（是否适合实验）
5. 一致性检查（格式是否统一）
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# 设置UTF-8编码（Windows兼容）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# 必需字段
REQUIRED_FIELDS = ["title", "domain", "goal"]
RECOMMENDED_FIELDS = ["target_users", "key_constraints", "business_metrics", "problem_statement", "solution_approach"]


def load_brief(brief_path: Path) -> Optional[Dict]:
    """加载Brief文件"""
    try:
        return json.loads(brief_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ❌ 加载失败: {e}")
        return None


def check_structure(brief: Dict, brief_id: str) -> Dict:
    """检查结构完整性"""
    issues = []
    warnings = []
    
    # 检查必需字段
    for field in REQUIRED_FIELDS:
        if field not in brief:
            issues.append(f"缺少必需字段: {field}")
        elif not brief[field] or (isinstance(brief[field], str) and not brief[field].strip()):
            issues.append(f"必需字段为空: {field}")
    
    # 检查推荐字段
    for field in RECOMMENDED_FIELDS:
        if field not in brief:
            warnings.append(f"缺少推荐字段: {field}")
        elif not brief[field]:
            warnings.append(f"推荐字段为空: {field}")
    
    # 检查字段类型
    if "target_users" in brief and not isinstance(brief["target_users"], list):
        issues.append("target_users应该是列表")
    
    if "key_constraints" in brief and not isinstance(brief["key_constraints"], list):
        issues.append("key_constraints应该是列表")
    
    if "business_metrics" in brief and not isinstance(brief["business_metrics"], list):
        issues.append("business_metrics应该是列表")
    
    return {
        "brief_id": brief_id,
        "has_issues": len(issues) > 0,
        "has_warnings": len(warnings) > 0,
        "issues": issues,
        "warnings": warnings,
    }


def check_content_quality(brief: Dict, brief_id: str) -> Dict:
    """检查内容质量"""
    quality_score = 0
    max_score = 10
    feedback = []
    
    # 1. Goal清晰度 (2分)
    if "goal" in brief and brief["goal"]:
        goal_len = len(brief["goal"])
        if goal_len > 100:
            quality_score += 2
            feedback.append("✅ Goal描述详细")
        elif goal_len > 50:
            quality_score += 1
            feedback.append("⚠️ Goal描述中等")
        else:
            feedback.append("❌ Goal描述过短")
    
    # 2. Target Users详细度 (2分)
    if "target_users" in brief and brief["target_users"]:
        user_count = len(brief["target_users"])
        if user_count >= 2:
            quality_score += 2
            feedback.append(f"✅ 有{user_count}个用户画像")
        elif user_count == 1:
            quality_score += 1
            feedback.append("⚠️ 只有1个用户画像")
        else:
            feedback.append("❌ 缺少用户画像")
    else:
        feedback.append("❌ 缺少target_users")
    
    # 3. Constraints详细度 (2分)
    if "key_constraints" in brief and brief["key_constraints"]:
        constraint_count = len(brief["key_constraints"])
        if constraint_count >= 2:
            quality_score += 2
            feedback.append(f"✅ 有{constraint_count}个约束条件")
        elif constraint_count == 1:
            quality_score += 1
            feedback.append("⚠️ 只有1个约束条件")
        else:
            feedback.append("❌ 缺少约束条件")
    else:
        feedback.append("❌ 缺少key_constraints")
    
    # 4. Business Metrics详细度 (2分)
    if "business_metrics" in brief and brief["business_metrics"]:
        metric_count = len(brief["business_metrics"])
        if metric_count >= 2:
            quality_score += 2
            feedback.append(f"✅ 有{metric_count}个业务指标")
        elif metric_count == 1:
            quality_score += 1
            feedback.append("⚠️ 只有1个业务指标")
        else:
            feedback.append("❌ 缺少业务指标")
    else:
        feedback.append("❌ 缺少business_metrics")
    
    # 5. Problem/Solution清晰度 (2分)
    has_problem = "problem_statement" in brief and brief.get("problem_statement")
    has_solution = "solution_approach" in brief and brief.get("solution_approach")
    
    if has_problem and has_solution:
        quality_score += 2
        feedback.append("✅ 有清晰的问题陈述和解决方案")
    elif has_problem or has_solution:
        quality_score += 1
        feedback.append("⚠️ 只有问题陈述或解决方案")
    else:
        feedback.append("❌ 缺少问题陈述和解决方案")
    
    return {
        "brief_id": brief_id,
        "quality_score": quality_score,
        "max_score": max_score,
        "quality_percentage": round(quality_score / max_score * 100, 1),
        "feedback": feedback,
    }


def check_complexity(brief: Dict, brief_id: str) -> Dict:
    """评估复杂度"""
    complexity_score = 0
    
    # 用户数量
    user_count = len(brief.get("target_users", []))
    complexity_score += user_count * 0.5
    
    # 约束数量
    constraint_count = len(brief.get("key_constraints", []))
    complexity_score += constraint_count * 0.5
    
    # 指标数量
    metric_count = len(brief.get("business_metrics", []))
    complexity_score += metric_count * 0.3
    
    # Goal长度
    goal_len = len(brief.get("goal", ""))
    complexity_score += min(goal_len / 100, 2.0)
    
    # 复杂度等级
    if complexity_score >= 5:
        level = "高"
    elif complexity_score >= 3:
        level = "中"
    else:
        level = "低"
    
    return {
        "brief_id": brief_id,
        "complexity_score": round(complexity_score, 2),
        "complexity_level": level,
    }


def validate_all_briefs(benchmark_dir: Path) -> Dict:
    """验证所有Brief"""
    print("=" * 70)
    print("Brief质量验证报告")
    print("=" * 70)
    print()
    
    # 加载所有Brief
    brief_files = list(benchmark_dir.glob("*_brief.json"))
    
    if not brief_files:
        print("❌ 未找到Brief文件")
        return {}
    
    print(f"📋 找到 {len(brief_files)} 个Brief文件")
    print()
    
    results = {
        "total_briefs": len(brief_files),
        "briefs": [],
        "summary": {},
    }
    
    # 按领域分组
    by_domain = defaultdict(list)
    structure_issues = []
    quality_scores = []
    complexity_scores = []
    
    for brief_file in sorted(brief_files):
        brief_id = brief_file.stem.replace("_brief", "")
        brief = load_brief(brief_file)
        
        if not brief:
            continue
        
        # 结构检查
        structure_check = check_structure(brief, brief_id)
        if structure_check["has_issues"]:
            structure_issues.append(brief_id)
        
        # 内容质量检查
        quality_check = check_content_quality(brief, brief_id)
        quality_scores.append(quality_check["quality_score"])
        
        # 复杂度评估
        complexity_check = check_complexity(brief, brief_id)
        complexity_scores.append(complexity_check["complexity_score"])
        
        # 按领域分组
        domain = brief.get("domain", "unknown")
        by_domain[domain].append(brief_id)
        
        # 汇总结果
        brief_result = {
            "brief_id": brief_id,
            "title": brief.get("title", "N/A"),
            "domain": domain,
            "structure": structure_check,
            "quality": quality_check,
            "complexity": complexity_check,
        }
        results["briefs"].append(brief_result)
    
    # 生成摘要
    results["summary"] = {
        "total_briefs": len(brief_files),
        "domains": dict(by_domain),
        "domain_count": len(by_domain),
        "structure_issues_count": len(structure_issues),
        "structure_issues": structure_issues,
        "average_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0,
        "average_complexity": round(sum(complexity_scores) / len(complexity_scores), 2) if complexity_scores else 0,
        "quality_distribution": {
            "high": sum(1 for s in quality_scores if s >= 8),
            "medium": sum(1 for s in quality_scores if 5 <= s < 8),
            "low": sum(1 for s in quality_scores if s < 5),
        },
    }
    
    return results


def print_report(results: Dict):
    """打印验证报告"""
    if not results:
        return
    
    summary = results["summary"]
    
    print("=" * 70)
    print("验证结果摘要")
    print("=" * 70)
    print()
    
    print(f"📊 总体统计:")
    print(f"  总Brief数: {summary['total_briefs']}")
    print(f"  领域数: {summary['domain_count']}")
    print(f"  结构问题数: {summary['structure_issues_count']}")
    print(f"  平均质量分: {summary['average_quality_score']}/10")
    print(f"  平均复杂度: {summary['average_complexity']}")
    print()
    
    print(f"📈 领域分布:")
    for domain, briefs in sorted(summary["domains"].items()):
        print(f"  {domain}: {len(briefs)}个")
    print()
    
    print(f"📊 质量分布:")
    dist = summary["quality_distribution"]
    print(f"  高质量 (≥8分): {dist['high']}个")
    print(f"  中等质量 (5-7分): {dist['medium']}个")
    print(f"  低质量 (<5分): {dist['low']}个")
    print()
    
    if summary["structure_issues"]:
        print(f"⚠️  结构问题Brief:")
        for brief_id in summary["structure_issues"]:
            print(f"  - {brief_id}")
        print()
    
    print("=" * 70)
    print("详细检查结果")
    print("=" * 70)
    print()
    
    for brief_result in results["briefs"]:
        print(f"📄 {brief_result['brief_id']}")
        print(f"   标题: {brief_result['title']}")
        print(f"   领域: {brief_result['domain']}")
        
        # 结构检查
        structure = brief_result["structure"]
        if structure["has_issues"]:
            print(f"   ❌ 结构问题:")
            for issue in structure["issues"]:
                print(f"      - {issue}")
        if structure["has_warnings"]:
            print(f"   ⚠️  结构警告:")
            for warning in structure["warnings"]:
                print(f"      - {warning}")
        if not structure["has_issues"] and not structure["has_warnings"]:
            print(f"   ✅ 结构完整")
        
        # 质量检查
        quality = brief_result["quality"]
        print(f"   质量分: {quality['quality_score']}/10 ({quality['quality_percentage']}%)")
        for feedback in quality["feedback"][:3]:  # 只显示前3条
            print(f"      {feedback}")
        
        # 复杂度
        complexity = brief_result["complexity"]
        print(f"   复杂度: {complexity['complexity_score']} ({complexity['complexity_level']})")
        print()


def main():
    benchmark_dir = Path("data/benchmark")
    
    if not benchmark_dir.exists():
        print(f"❌ Benchmark目录不存在: {benchmark_dir}")
        return
    
    # 验证所有Brief
    results = validate_all_briefs(benchmark_dir)
    
    if results:
        # 打印报告
        print_report(results)
        
        # 保存结果
        output_path = Path("results/brief_validation_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n✅ 验证报告已保存: {output_path}")
        
        # 总体评估
        summary = results["summary"]
        print("\n" + "=" * 70)
        print("总体评估")
        print("=" * 70)
        
        if summary["structure_issues_count"] == 0:
            print("✅ 所有Brief结构完整")
        else:
            print(f"⚠️  {summary['structure_issues_count']}个Brief有结构问题")
        
        if summary["average_quality_score"] >= 7:
            print("✅ Brief质量整体良好")
        elif summary["average_quality_score"] >= 5:
            print("⚠️  Brief质量中等，建议改进")
        else:
            print("❌ Brief质量较低，需要改进")
        
        if summary["domain_count"] >= 4:
            print("✅ 领域覆盖充分")
        else:
            print("⚠️  领域覆盖不足，建议增加")
        
        print("\n建议:")
        if summary["structure_issues_count"] > 0:
            print("  1. 修复结构问题")
        if summary["average_quality_score"] < 7:
            print("  2. 提升Brief内容质量（增加详细信息）")
        if summary["domain_count"] < 4:
            print("  3. 增加更多领域的Brief")


if __name__ == "__main__":
    main()






